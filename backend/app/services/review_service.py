"""Service for transaction review workflow and bulk operations"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models.transaction import TransactionResponse
from app.models.review import (
    BulkOperationRequest,
    BulkOperationType,
    BulkOperationResponse,
    DateGroupedTransactions,
    ReviewQueueResponse,
)

logger = logging.getLogger(__name__)


class ReviewService:
    def get_review_queue(
        self, limit: int = 50, offset: int = 0
    ) -> ReviewQueueResponse:
        """
        Get unreviewed transactions grouped by day.

        Returns transactions where reviewed=false, ordered by date descending,
        with day labels (Today, Yesterday, or formatted date).
        """
        # Get total count first
        total_count = self._count_unreviewed()

        # Fetch transactions
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
                WHERE t.reviewed = false
                ORDER BY t.date DESC, t.created_at DESC
                LIMIT ? OFFSET ?
                """,
                [limit, offset],
            ).fetchall()

        transactions = [
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

        # Group by date with labels
        groups = self._group_by_date(transactions)

        displayed_count = len(transactions)
        has_more = (offset + displayed_count) < total_count

        return ReviewQueueResponse(
            groups=groups,
            total_count=total_count,
            displayed_count=displayed_count,
            has_more=has_more,
        )

    def _count_unreviewed(self) -> int:
        """Count unreviewed transactions"""
        with get_db() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE reviewed = false"
            ).fetchone()
        return result[0] if result else 0

    def _group_by_date(
        self, transactions: list[TransactionResponse]
    ) -> list[DateGroupedTransactions]:
        """Group transactions by date with friendly labels"""
        if not transactions:
            return []

        today = date.today()
        yesterday = today - timedelta(days=1)

        groups_dict: dict[date, list[TransactionResponse]] = {}
        for tx in transactions:
            tx_date = tx.date
            if tx_date not in groups_dict:
                groups_dict[tx_date] = []
            groups_dict[tx_date].append(tx)

        groups = []
        for tx_date in sorted(groups_dict.keys(), reverse=True):
            label = self._get_date_label(tx_date, today, yesterday)
            groups.append(
                DateGroupedTransactions(
                    date_label=label,
                    date=tx_date,
                    transactions=groups_dict[tx_date],
                )
            )

        return groups

    def _get_date_label(self, tx_date: date, today: date, yesterday: date) -> str:
        """Get friendly date label"""
        if tx_date == today:
            return "Today"
        elif tx_date == yesterday:
            return "Yesterday"
        else:
            # Format as "Jan 8" style
            return tx_date.strftime("%b %-d")

    def bulk_mark_reviewed(self, transaction_ids: list[str]) -> BulkOperationResponse:
        """Mark multiple transactions as reviewed atomically"""
        if not transaction_ids:
            return BulkOperationResponse(
                success=True,
                affected_count=0,
                operation=BulkOperationType.MARK_REVIEWED,
                transaction_ids=[],
            )

        reviewed_at = datetime.utcnow()

        with get_db() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # Validate all transaction IDs exist
                self._validate_transaction_ids(conn, transaction_ids)

                # Update transactions
                placeholders = ", ".join(["?" for _ in transaction_ids])
                conn.execute(
                    f"""
                    UPDATE transactions
                    SET reviewed = true, reviewed_at = ?
                    WHERE id IN ({placeholders})
                    """,
                    [reviewed_at] + transaction_ids,
                )

                conn.execute("COMMIT")

                logger.info(f"Bulk marked {len(transaction_ids)} transactions as reviewed")

                return BulkOperationResponse(
                    success=True,
                    affected_count=len(transaction_ids),
                    operation=BulkOperationType.MARK_REVIEWED,
                    transaction_ids=transaction_ids,
                )

            except Exception as e:
                conn.execute("ROLLBACK")
                logger.error(f"Bulk mark reviewed failed: {e}")
                raise

    def bulk_set_category(
        self, transaction_ids: list[str], category_id: str
    ) -> BulkOperationResponse:
        """Set category for multiple transactions atomically"""
        if not transaction_ids:
            return BulkOperationResponse(
                success=True,
                affected_count=0,
                operation=BulkOperationType.SET_CATEGORY,
                transaction_ids=[],
            )

        with get_db() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # Validate category exists
                self._validate_category_id(conn, category_id)

                # Validate all transaction IDs exist
                self._validate_transaction_ids(conn, transaction_ids)

                # Update transactions
                placeholders = ", ".join(["?" for _ in transaction_ids])
                conn.execute(
                    f"""
                    UPDATE transactions
                    SET category_id = ?, categorization_source = 'manual'
                    WHERE id IN ({placeholders})
                    """,
                    [category_id] + transaction_ids,
                )

                conn.execute("COMMIT")

                logger.info(
                    f"Bulk set category {category_id} for {len(transaction_ids)} transactions"
                )

                return BulkOperationResponse(
                    success=True,
                    affected_count=len(transaction_ids),
                    operation=BulkOperationType.SET_CATEGORY,
                    transaction_ids=transaction_ids,
                )

            except Exception as e:
                conn.execute("ROLLBACK")
                logger.error(f"Bulk set category failed: {e}")
                raise

    def bulk_add_note(
        self, transaction_ids: list[str], note: str
    ) -> BulkOperationResponse:
        """Add note to multiple transactions atomically (appending to existing)"""
        if not transaction_ids:
            return BulkOperationResponse(
                success=True,
                affected_count=0,
                operation=BulkOperationType.ADD_NOTE,
                transaction_ids=[],
            )

        with get_db() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # Validate all transaction IDs exist
                self._validate_transaction_ids(conn, transaction_ids)

                # Update transactions - append note with newline separator
                placeholders = ", ".join(["?" for _ in transaction_ids])
                conn.execute(
                    f"""
                    UPDATE transactions
                    SET notes = CASE
                        WHEN notes IS NOT NULL AND notes != ''
                        THEN notes || '\n' || ?
                        ELSE ?
                    END
                    WHERE id IN ({placeholders})
                    """,
                    [note, note] + transaction_ids,
                )

                conn.execute("COMMIT")

                logger.info(f"Bulk added note to {len(transaction_ids)} transactions")

                return BulkOperationResponse(
                    success=True,
                    affected_count=len(transaction_ids),
                    operation=BulkOperationType.ADD_NOTE,
                    transaction_ids=transaction_ids,
                )

            except Exception as e:
                conn.execute("ROLLBACK")
                logger.error(f"Bulk add note failed: {e}")
                raise

    def _validate_transaction_ids(self, conn, transaction_ids: list[str]) -> None:
        """Validate that all transaction IDs exist"""
        placeholders = ", ".join(["?" for _ in transaction_ids])
        result = conn.execute(
            f"SELECT id FROM transactions WHERE id IN ({placeholders})",
            transaction_ids,
        ).fetchall()

        found_ids = {row[0] for row in result}
        missing_ids = set(transaction_ids) - found_ids

        if missing_ids:
            missing_list = ", ".join(sorted(missing_ids)[:5])
            if len(missing_ids) > 5:
                missing_list += f" and {len(missing_ids) - 5} more"
            raise ValueError(f"Transactions not found: {missing_list}")

    def _validate_category_id(self, conn, category_id: str) -> None:
        """Validate that the category exists"""
        result = conn.execute(
            "SELECT id FROM categories WHERE id = ?", [category_id]
        ).fetchone()

        if not result:
            raise ValueError(f"Category not found: {category_id}")


review_service = ReviewService()
