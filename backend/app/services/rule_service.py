"""
Service for managing categorization rules.
Rules are learned from user corrections and applied before AI categorization.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.categorization import (
    CategorizationRuleCreate,
    CategorizationRuleResponse,
    CategorizationRuleListResponse,
)

logger = logging.getLogger(__name__)


class RuleService:
    """Service for CRUD operations on categorization rules."""

    def create_rule(
        self,
        data: CategorizationRuleCreate,
    ) -> CategorizationRuleResponse:
        """
        Create or update a categorization rule.

        If a rule with the same merchant_pattern exists, it will be updated.
        Patterns are stored lowercase for case-insensitive matching.

        Args:
            data: Rule creation data

        Returns:
            Created or updated rule
        """
        # Normalize pattern to lowercase for case-insensitive matching
        normalized_pattern = data.merchant_pattern.strip().lower()

        with get_db() as conn:
            # Check if rule already exists
            existing = conn.execute(
                "SELECT id FROM categorization_rules WHERE merchant_pattern = ?",
                [normalized_pattern],
            ).fetchone()

            if existing:
                # Update existing rule
                rule_id = existing[0]
                conn.execute(
                    """
                    UPDATE categorization_rules
                    SET category_id = ?, created_at = ?
                    WHERE id = ?
                    """,
                    [data.category_id, datetime.utcnow(), rule_id],
                )
                logger.info(
                    f"Updated rule '{normalized_pattern}' -> category {data.category_id}"
                )
            else:
                # Create new rule
                rule_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO categorization_rules (id, merchant_pattern, category_id, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    [rule_id, normalized_pattern, data.category_id, datetime.utcnow()],
                )
                logger.info(
                    f"Created rule '{normalized_pattern}' -> category {data.category_id}"
                )

        return self.get_by_id(rule_id)

    def get_all_rules(
        self,
        category_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CategorizationRuleResponse]:
        """
        Get all categorization rules ordered by created_at DESC.

        Args:
            category_id: Optional filter by category
            limit: Maximum number of rules to return
            offset: Pagination offset

        Returns:
            List of rules with category names
        """
        with get_db() as conn:
            if category_id:
                result = conn.execute(
                    """
                    SELECT r.id, r.merchant_pattern, r.category_id, r.created_at,
                           c.name as category_name
                    FROM categorization_rules r
                    LEFT JOIN categories c ON r.category_id = c.id
                    WHERE r.category_id = ?
                    ORDER BY r.created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    [category_id, limit, offset],
                ).fetchall()
            else:
                result = conn.execute(
                    """
                    SELECT r.id, r.merchant_pattern, r.category_id, r.created_at,
                           c.name as category_name
                    FROM categorization_rules r
                    LEFT JOIN categories c ON r.category_id = c.id
                    ORDER BY r.created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    [limit, offset],
                ).fetchall()

        return [
            CategorizationRuleResponse(
                id=row[0],
                merchant_pattern=row[1],
                category_id=row[2],
                created_at=row[3],
                category_name=row[4],
            )
            for row in result
        ]

    def count_rules(self, category_id: Optional[str] = None) -> int:
        """Count total number of rules."""
        with get_db() as conn:
            if category_id:
                result = conn.execute(
                    "SELECT COUNT(*) FROM categorization_rules WHERE category_id = ?",
                    [category_id],
                ).fetchone()
            else:
                result = conn.execute(
                    "SELECT COUNT(*) FROM categorization_rules"
                ).fetchone()
        return result[0]

    def get_list(
        self,
        category_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> CategorizationRuleListResponse:
        """Get paginated list of rules."""
        rules = self.get_all_rules(category_id, limit, offset)
        total = self.count_rules(category_id)
        has_more = (offset + len(rules)) < total

        return CategorizationRuleListResponse(
            rules=rules,
            total=total,
            has_more=has_more,
        )

    def find_matching_rule(
        self,
        normalized_merchant: str,
    ) -> Optional[CategorizationRuleResponse]:
        """
        Find a rule that matches the given merchant name.

        Uses substring/contains matching (case-insensitive).
        Most recently created rule wins on conflict.

        Args:
            normalized_merchant: Normalized merchant name to match

        Returns:
            Matching rule or None
        """
        if not normalized_merchant:
            return None

        merchant_lower = normalized_merchant.lower()

        # Get all rules ordered by created_at DESC (most recent first)
        rules = self.get_all_rules(limit=1000)

        for rule in rules:
            # Substring/contains match
            if rule.merchant_pattern in merchant_lower:
                logger.debug(
                    f"Rule match: '{rule.merchant_pattern}' found in '{merchant_lower}'"
                )
                return rule

        return None

    def get_by_id(self, rule_id: str) -> Optional[CategorizationRuleResponse]:
        """Get a single rule by ID."""
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT r.id, r.merchant_pattern, r.category_id, r.created_at,
                       c.name as category_name
                FROM categorization_rules r
                LEFT JOIN categories c ON r.category_id = c.id
                WHERE r.id = ?
                """,
                [rule_id],
            ).fetchone()

        if not result:
            return None

        return CategorizationRuleResponse(
            id=result[0],
            merchant_pattern=result[1],
            category_id=result[2],
            created_at=result[3],
            category_name=result[4],
        )

    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a categorization rule.

        Does not affect already-categorized transactions.

        Args:
            rule_id: Rule ID to delete

        Returns:
            True if rule was deleted, False if not found
        """
        existing = self.get_by_id(rule_id)
        if not existing:
            return False

        with get_db() as conn:
            conn.execute(
                "DELETE FROM categorization_rules WHERE id = ?",
                [rule_id],
            )

        logger.info(f"Deleted rule: {existing.merchant_pattern}")
        return True


rule_service = RuleService()
