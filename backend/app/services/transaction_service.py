import uuid
import logging
from typing import Optional
from datetime import datetime, date

from app.database import get_db
from app.models.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionFilters,
    TransactionListResponse,
)
from app.models.categorization import CategorizationRuleCreate
from app.services.merchant_normalizer import normalize

logger = logging.getLogger(__name__)


class TransactionService:
    def create(self, data: TransactionCreate) -> TransactionResponse:
        """Create a new transaction"""
        transaction_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        reviewed_at = datetime.utcnow() if data.reviewed else None

        # Normalize merchant name from description
        normalized_merchant, _ = normalize(data.original_description)

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO transactions (
                    id, account_id, date, description, original_description,
                    amount, category_id, reviewed, reviewed_at, notes, created_at,
                    normalized_merchant
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    transaction_id,
                    data.account_id,
                    data.date,
                    data.description,
                    data.original_description,
                    data.amount,
                    data.category_id,
                    data.reviewed,
                    reviewed_at,
                    data.notes,
                    created_at,
                    normalized_merchant or None,
                ],
            )

        return TransactionResponse(
            id=transaction_id,
            account_id=data.account_id,
            date=data.date,
            description=data.description,
            original_description=data.original_description,
            amount=data.amount,
            category_id=data.category_id,
            reviewed=data.reviewed,
            reviewed_at=reviewed_at,
            notes=data.notes,
            created_at=created_at,
            normalized_merchant=normalized_merchant or None,
        )

    def get_all(
        self,
        filters: Optional[TransactionFilters] = None,
    ) -> list[TransactionResponse]:
        """Get all transactions with optional filters"""
        if filters is None:
            filters = TransactionFilters()

        conditions = []
        params = []

        if filters.account_id:
            conditions.append("t.account_id = ?")
            params.append(filters.account_id)

        if filters.category_id:
            if filters.category_id == "__uncategorized__":
                conditions.append("t.category_id IS NULL")
            else:
                conditions.append("t.category_id = ?")
                params.append(filters.category_id)

        if filters.date_from:
            conditions.append("t.date >= ?")
            params.append(filters.date_from)

        if filters.date_to:
            conditions.append("t.date <= ?")
            params.append(filters.date_to)

        if filters.amount_min is not None:
            conditions.append("t.amount >= ?")
            params.append(filters.amount_min)

        if filters.amount_max is not None:
            conditions.append("t.amount <= ?")
            params.append(filters.amount_max)

        if filters.reviewed is not None:
            conditions.append("t.reviewed = ?")
            params.append(filters.reviewed)

        if filters.search:
            conditions.append("LOWER(t.description) LIKE LOWER(?)")
            params.append(f"%{filters.search}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT t.id, t.account_id, t.date, t.description, t.original_description,
                   t.amount, t.category_id, t.reviewed, t.reviewed_at, t.notes, t.created_at,
                   t.normalized_merchant, t.confidence_score, t.categorization_source,
                   a.name as account_name,
                   c.name as category_name, c.emoji as category_emoji
            FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.id
            LEFT JOIN categories c ON t.category_id = c.id
            {where_clause}
            ORDER BY t.date DESC, t.created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([filters.limit, filters.offset])

        with get_db() as conn:
            result = conn.execute(query, params).fetchall()

        return [
            TransactionResponse(
                id=row[0],
                account_id=row[1],
                date=row[2],
                description=row[3],
                original_description=row[4],
                amount=row[5],
                category_id=row[6],
                reviewed=row[7],
                reviewed_at=row[8],
                notes=row[9],
                created_at=row[10],
                normalized_merchant=row[11],
                confidence_score=row[12],
                categorization_source=row[13],
                account_name=row[14],
                category_name=row[15],
                category_emoji=row[16],
            )
            for row in result
        ]

    def count(self, filters: Optional[TransactionFilters] = None) -> int:
        """Count transactions matching filters"""
        if filters is None:
            filters = TransactionFilters()

        conditions = []
        params = []

        if filters.account_id:
            conditions.append("account_id = ?")
            params.append(filters.account_id)

        if filters.category_id:
            if filters.category_id == "__uncategorized__":
                conditions.append("category_id IS NULL")
            else:
                conditions.append("category_id = ?")
                params.append(filters.category_id)

        if filters.date_from:
            conditions.append("date >= ?")
            params.append(filters.date_from)

        if filters.date_to:
            conditions.append("date <= ?")
            params.append(filters.date_to)

        if filters.amount_min is not None:
            conditions.append("amount >= ?")
            params.append(filters.amount_min)

        if filters.amount_max is not None:
            conditions.append("amount <= ?")
            params.append(filters.amount_max)

        if filters.reviewed is not None:
            conditions.append("reviewed = ?")
            params.append(filters.reviewed)

        if filters.search:
            conditions.append("LOWER(description) LIKE LOWER(?)")
            params.append(f"%{filters.search}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"SELECT COUNT(*) FROM transactions {where_clause}"

        with get_db() as conn:
            result = conn.execute(query, params).fetchone()

        return result[0]

    def get_by_id(self, transaction_id: str) -> Optional[TransactionResponse]:
        """Get a single transaction by ID"""
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT t.id, t.account_id, t.date, t.description, t.original_description,
                       t.amount, t.category_id, t.reviewed, t.reviewed_at, t.notes, t.created_at,
                       t.normalized_merchant, t.confidence_score, t.categorization_source,
                       a.name as account_name,
                       c.name as category_name, c.emoji as category_emoji
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.id = ?
                """,
                [transaction_id],
            ).fetchone()

        if not result:
            return None

        return TransactionResponse(
            id=result[0],
            account_id=result[1],
            date=result[2],
            description=result[3],
            original_description=result[4],
            amount=result[5],
            category_id=result[6],
            reviewed=result[7],
            reviewed_at=result[8],
            notes=result[9],
            created_at=result[10],
            normalized_merchant=result[11],
            confidence_score=result[12],
            categorization_source=result[13],
            account_name=result[14],
            category_name=result[15],
            category_emoji=result[16],
        )

    def update(
        self, transaction_id: str, data: TransactionUpdate
    ) -> Optional[TransactionResponse]:
        """Update a transaction"""
        existing = self.get_by_id(transaction_id)
        if not existing:
            return None

        updates = []
        values = []
        category_changed = False
        new_category_id = None

        if data.description is not None:
            updates.append("description = ?")
            values.append(data.description)

        # Handle category_id - need to check if it's being explicitly set
        # Use a sentinel to detect if category_id was provided
        if "category_id" in data.model_fields_set:
            updates.append("category_id = ?")
            values.append(data.category_id)
            # Track if category actually changed
            if data.category_id != existing.category_id:
                category_changed = True
                new_category_id = data.category_id
                # When category is manually changed, mark as manual source
                updates.append("categorization_source = ?")
                values.append("manual")

        if data.reviewed is not None:
            updates.append("reviewed = ?")
            values.append(data.reviewed)
            # Auto-manage reviewed_at timestamp
            if data.reviewed:
                updates.append("reviewed_at = ?")
                values.append(datetime.utcnow())
            else:
                updates.append("reviewed_at = ?")
                values.append(None)

        # Handle notes - check if explicitly set
        if "notes" in data.model_fields_set:
            updates.append("notes = ?")
            values.append(data.notes)

        if not updates:
            return existing

        # DuckDB has a known bug where UPDATE on tables with primary key
        # indexes throws spurious "duplicate key" errors. Work around it
        # with DELETE + INSERT.
        with get_db() as conn:
            row = conn.execute(
                """SELECT id, account_id, date, description, original_description,
                          amount, category_id, reviewed, reviewed_at, notes,
                          normalized_merchant, confidence_score, categorization_source,
                          created_at
                   FROM transactions WHERE id = ?""",
                [transaction_id],
            ).fetchone()

            # Apply updates to a mutable copy
            cols = ["id", "account_id", "date", "description", "original_description",
                    "amount", "category_id", "reviewed", "reviewed_at", "notes",
                    "normalized_merchant", "confidence_score", "categorization_source",
                    "created_at"]
            row_dict = dict(zip(cols, row))

            for clause, val in zip(updates, values):
                col_name = clause.split(" = ")[0].strip()
                row_dict[col_name] = val

            conn.execute("DELETE FROM transactions WHERE id = ?", [transaction_id])
            conn.execute(
                f"INSERT INTO transactions ({', '.join(cols)}) VALUES ({', '.join(['?'] * len(cols))})",
                [row_dict[c] for c in cols],
            )

        # If category changed and transaction has normalized_merchant, create a merchant rule
        if category_changed and new_category_id and existing.normalized_merchant:
            self._create_rule_from_correction(existing.normalized_merchant, new_category_id)
        elif category_changed and new_category_id and not existing.normalized_merchant:
            # No normalized merchant — try creating a description-based pattern rule
            if existing.description and existing.description.strip():
                self._create_desc_rule_from_correction(
                    existing.description, existing.account_id, new_category_id
                )

        return self.get_by_id(transaction_id)

    def _create_rule_from_correction(
        self,
        normalized_merchant: str,
        category_id: str,
    ) -> None:
        """
        Create a categorization rule when user manually corrects a category.

        Args:
            normalized_merchant: The normalized merchant name
            category_id: The new category ID
        """
        # Avoid circular import
        from app.services.rule_service import rule_service

        try:
            rule_data = CategorizationRuleCreate(
                merchant_pattern=normalized_merchant,
                category_id=category_id,
            )
            rule_service.create_rule(rule_data)
            logger.info(
                f"Created rule from correction: '{normalized_merchant}' -> {category_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to create rule from correction: {e}")

    def _create_desc_rule_from_correction(
        self,
        description: str,
        account_id: str,
        category_id: str,
    ) -> None:
        """
        Create a description pattern rule when user manually corrects a category
        and the transaction has no normalized merchant.
        """
        from app.services.pattern_extractor import extract_pattern
        from app.services.desc_rule_service import desc_rule_service
        from app.models.categorization import DescriptionPatternRuleCreate

        try:
            pattern = extract_pattern(description)
            if not pattern:
                return

            rule_data = DescriptionPatternRuleCreate(
                description_pattern=pattern,
                account_id=account_id,
                category_id=category_id,
            )
            desc_rule_service.create_rule(rule_data)
            logger.info(
                f"Created desc rule from correction: '{pattern}' "
                f"for account {account_id} -> {category_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to create desc rule from correction: {e}")

    def delete(self, transaction_id: str) -> bool:
        """Delete a transaction"""
        existing = self.get_by_id(transaction_id)
        if not existing:
            return False

        with get_db() as conn:
            conn.execute("DELETE FROM transactions WHERE id = ?", [transaction_id])

        return True

    def get_list(
        self, filters: Optional[TransactionFilters] = None
    ) -> TransactionListResponse:
        """Get paginated list of transactions"""
        if filters is None:
            filters = TransactionFilters()

        items = self.get_all(filters)
        total = self.count(filters)
        has_more = (filters.offset + len(items)) < total

        return TransactionListResponse(
            items=items,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
            has_more=has_more,
        )


transaction_service = TransactionService()
