"""
Service for managing description-based pattern rules.

Description rules are account-scoped and use wildcard patterns
to match transaction descriptions. They serve as a fallback
when no normalized merchant is available.
"""
import re
import uuid
import logging
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.categorization import (
    DescriptionPatternRuleCreate,
    DescriptionPatternRuleResponse,
)

logger = logging.getLogger(__name__)


def _wildcard_to_regex(pattern: str) -> re.Pattern:
    """Convert a wildcard pattern (with *) to an anchored regex."""
    # Escape all regex special chars, then replace escaped \* with .*
    escaped = re.escape(pattern)
    regex_str = escaped.replace(r"\*", ".*")
    return re.compile(f"^{regex_str}$", re.IGNORECASE)


class DescRuleService:
    """Service for CRUD operations on description pattern rules."""

    def create_rule(
        self,
        data: DescriptionPatternRuleCreate,
    ) -> DescriptionPatternRuleResponse:
        """
        Create or update a description pattern rule.

        If a rule with the same (account_id, description_pattern) exists,
        its category_id and created_at are updated (upsert).
        Patterns are stored lowercase for case-insensitive matching.
        """
        normalized_pattern = data.description_pattern.strip().lower()
        source = data.source or "manual"

        with get_db() as conn:
            existing = conn.execute(
                """SELECT id FROM description_pattern_rules
                   WHERE account_id = ? AND description_pattern = ?""",
                [data.account_id, normalized_pattern],
            ).fetchone()

            if existing:
                rule_id = existing[0]
                # DuckDB workaround: DELETE + INSERT instead of UPDATE
                # (DuckDB has a known bug with UPDATE on tables with primary key indexes)
                conn.execute(
                    "DELETE FROM description_pattern_rules WHERE id = ?",
                    [rule_id],
                )
                conn.execute(
                    """INSERT INTO description_pattern_rules
                       (id, account_id, description_pattern, category_id, created_at, source)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    [rule_id, data.account_id, normalized_pattern,
                     data.category_id, datetime.utcnow(), source],
                )
                logger.info(
                    f"Updated desc rule '{normalized_pattern}' for account {data.account_id} "
                    f"-> category {data.category_id}"
                )
            else:
                rule_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO description_pattern_rules
                       (id, account_id, description_pattern, category_id, created_at, source)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    [rule_id, data.account_id, normalized_pattern,
                     data.category_id, datetime.utcnow(), source],
                )
                logger.info(
                    f"Created desc rule '{normalized_pattern}' for account {data.account_id} "
                    f"-> category {data.category_id}"
                )

        return self.get_by_id(rule_id)

    def find_matching_rule(
        self,
        description: str,
        account_id: str,
    ) -> Optional[DescriptionPatternRuleResponse]:
        """
        Find a description rule that matches the given description for an account.

        Converts stored wildcard patterns to regex for matching.
        Most recently created rule wins on conflict.

        Args:
            description: Transaction description to match
            account_id: Account to scope the search to

        Returns:
            Matching rule or None
        """
        if not description or not account_id:
            return None

        description_lower = description.strip().lower()

        rules = self.get_all_rules(account_id=account_id, limit=1000)

        for rule in rules:
            try:
                pattern_re = _wildcard_to_regex(rule.description_pattern)
                if pattern_re.match(description_lower):
                    logger.debug(
                        f"Desc rule match: '{rule.description_pattern}' matched "
                        f"'{description_lower}' for account {account_id}"
                    )
                    return rule
            except re.error:
                logger.warning(
                    f"Invalid regex from pattern '{rule.description_pattern}', skipping"
                )
                continue

        return None

    def get_all_rules(
        self,
        account_id: Optional[str] = None,
        category_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DescriptionPatternRuleResponse]:
        """Get description pattern rules ordered by created_at DESC."""
        conditions = []
        params = []

        if account_id:
            conditions.append("r.account_id = ?")
            params.append(account_id)

        if category_id:
            conditions.append("r.category_id = ?")
            params.append(category_id)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        params.extend([limit, offset])

        with get_db() as conn:
            result = conn.execute(
                f"""SELECT r.id, r.account_id, r.description_pattern,
                           r.category_id, r.created_at,
                           c.name as category_name,
                           a.name as account_name,
                           r.source
                    FROM description_pattern_rules r
                    LEFT JOIN categories c ON r.category_id = c.id
                    LEFT JOIN accounts a ON r.account_id = a.id
                    {where_clause}
                    ORDER BY r.created_at DESC
                    LIMIT ? OFFSET ?""",
                params,
            ).fetchall()

        return [
            DescriptionPatternRuleResponse(
                id=row[0],
                account_id=row[1],
                description_pattern=row[2],
                category_id=row[3],
                created_at=row[4],
                category_name=row[5],
                account_name=row[6],
                source=row[7] or "manual",
            )
            for row in result
        ]

    def get_by_id(self, rule_id: str) -> Optional[DescriptionPatternRuleResponse]:
        """Get a single description pattern rule by ID."""
        with get_db() as conn:
            result = conn.execute(
                """SELECT r.id, r.account_id, r.description_pattern,
                          r.category_id, r.created_at,
                          c.name as category_name,
                          a.name as account_name,
                          r.source
                   FROM description_pattern_rules r
                   LEFT JOIN categories c ON r.category_id = c.id
                   LEFT JOIN accounts a ON r.account_id = a.id
                   WHERE r.id = ?""",
                [rule_id],
            ).fetchone()

        if not result:
            return None

        return DescriptionPatternRuleResponse(
            id=result[0],
            account_id=result[1],
            description_pattern=result[2],
            category_id=result[3],
            created_at=result[4],
            category_name=result[5],
            account_name=result[6],
            source=result[7] or "manual",
        )

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a description pattern rule."""
        existing = self.get_by_id(rule_id)
        if not existing:
            return False

        with get_db() as conn:
            conn.execute(
                "DELETE FROM description_pattern_rules WHERE id = ?",
                [rule_id],
            )

        logger.info(f"Deleted desc rule: {existing.description_pattern}")
        return True

    def count_rules(
        self,
        account_id: Optional[str] = None,
        category_id: Optional[str] = None,
    ) -> int:
        """Count description pattern rules."""
        conditions = []
        params = []

        if account_id:
            conditions.append("account_id = ?")
            params.append(account_id)

        if category_id:
            conditions.append("category_id = ?")
            params.append(category_id)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with get_db() as conn:
            result = conn.execute(
                f"SELECT COUNT(*) FROM description_pattern_rules {where_clause}",
                params,
            ).fetchone()

        return result[0]


desc_rule_service = DescRuleService()
