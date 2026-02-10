"""
Category mapping service for AI-powered CSV import category suggestions.
Handles CRUD operations for saved mappings and AI-based suggestions.
"""
import json
import logging
import uuid
from typing import Optional

from app.database import get_db
from app.models.category_mapping import (
    CategoryMappingSuggestion,
    CategoryMappingData,
)
from app.services.claude_client import (
    invoke_and_parse,
    ClaudeClientError,
)

logger = logging.getLogger(__name__)


class CategoryMappingService:
    """Service for managing category mappings during CSV import."""

    def get_all_categories(self) -> list[dict]:
        """Get all categories for mapping suggestions."""
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT id, name, emoji, group_name
                FROM categories
                ORDER BY group_name, name
                """
            ).fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "emoji": row[2],
                "group": row[3],
            }
            for row in result
        ]

    def get_mappings_for_account(
        self,
        account_id: Optional[str] = None,
    ) -> list[CategoryMappingData]:
        """
        Fetch saved mappings for an account.

        Args:
            account_id: The account ID to get mappings for.
                       If None, returns only global mappings.

        Returns:
            List of CategoryMappingData objects
        """
        with get_db() as conn:
            if account_id:
                # Get both account-specific and global mappings
                result = conn.execute(
                    """
                    SELECT cm.id, cm.account_id, cm.source_category,
                           cm.target_category_id, c.name, c.emoji, cm.source, cm.created_at
                    FROM category_mappings cm
                    LEFT JOIN categories c ON cm.target_category_id = c.id
                    WHERE cm.account_id = ? OR cm.account_id IS NULL
                    ORDER BY cm.created_at DESC
                    """,
                    [account_id],
                ).fetchall()
            else:
                # Only get global mappings
                result = conn.execute(
                    """
                    SELECT cm.id, cm.account_id, cm.source_category,
                           cm.target_category_id, c.name, c.emoji, cm.source, cm.created_at
                    FROM category_mappings cm
                    LEFT JOIN categories c ON cm.target_category_id = c.id
                    WHERE cm.account_id IS NULL
                    ORDER BY cm.created_at DESC
                    """
                ).fetchall()

        return [
            CategoryMappingData(
                id=row[0],
                account_id=row[1],
                source_category=row[2],
                target_category_id=row[3],
                target_category_name=row[4],
                target_category_emoji=row[5],
                source=row[6],
                created_at=row[7],
            )
            for row in result
        ]

    def find_mapping(
        self,
        account_id: str,
        source_category: str,
    ) -> Optional[CategoryMappingData]:
        """
        Lookup a single mapping for a source category.

        Priority: account-specific mapping > global mapping

        Args:
            account_id: The account ID
            source_category: The source category name to look up

        Returns:
            CategoryMappingData if found, None otherwise
        """
        source_lower = source_category.lower()

        with get_db() as conn:
            # First try account-specific mapping
            result = conn.execute(
                """
                SELECT cm.id, cm.account_id, cm.source_category,
                       cm.target_category_id, c.name, c.emoji, cm.source, cm.created_at
                FROM category_mappings cm
                LEFT JOIN categories c ON cm.target_category_id = c.id
                WHERE cm.account_id = ? AND LOWER(cm.source_category) = ?
                """,
                [account_id, source_lower],
            ).fetchone()

            if result:
                return CategoryMappingData(
                    id=result[0],
                    account_id=result[1],
                    source_category=result[2],
                    target_category_id=result[3],
                    target_category_name=result[4],
                    target_category_emoji=result[5],
                    source=result[6],
                    created_at=result[7],
                )

            # Fall back to global mapping
            result = conn.execute(
                """
                SELECT cm.id, cm.account_id, cm.source_category,
                       cm.target_category_id, c.name, c.emoji, cm.source, cm.created_at
                FROM category_mappings cm
                LEFT JOIN categories c ON cm.target_category_id = c.id
                WHERE cm.account_id IS NULL AND LOWER(cm.source_category) = ?
                """,
                [source_lower],
            ).fetchone()

            if result:
                return CategoryMappingData(
                    id=result[0],
                    account_id=result[1],
                    source_category=result[2],
                    target_category_id=result[3],
                    target_category_name=result[4],
                    target_category_emoji=result[5],
                    source=result[6],
                    created_at=result[7],
                )

        return None

    def save_mappings(
        self,
        account_id: str,
        mappings: list[tuple[str, str]],
        source: str = "user",
    ) -> int:
        """
        Persist user-confirmed mappings.

        Args:
            account_id: The account ID to save mappings for
            mappings: List of (source_category, target_category_id) tuples
            source: Source of the mapping ('ai' or 'user')

        Returns:
            Number of mappings saved
        """
        saved_count = 0

        with get_db() as conn:
            for source_category, target_category_id in mappings:
                mapping_id = str(uuid.uuid4())

                # Delete existing mapping if present, then insert
                conn.execute(
                    """
                    DELETE FROM category_mappings
                    WHERE account_id = ? AND source_category = ?
                    """,
                    [account_id, source_category],
                )
                conn.execute(
                    """
                    INSERT INTO category_mappings
                    (id, account_id, source_category, target_category_id, source)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [mapping_id, account_id, source_category, target_category_id, source],
                )
                saved_count += 1

        logger.info(
            f"Saved {saved_count} category mappings for account {account_id}"
        )

        return saved_count

    def delete_mapping(self, mapping_id: str) -> bool:
        """Delete a saved mapping by ID."""
        with get_db() as conn:
            result = conn.execute(
                "DELETE FROM category_mappings WHERE id = ?",
                [mapping_id],
            )
            return result.rowcount > 0

    def build_mapping_prompt(
        self,
        source_categories: list[str],
        categories: list[dict],
    ) -> str:
        """
        Build the prompt for Claude to suggest category mappings.

        Args:
            source_categories: List of source category names from CSV
            categories: List of app category dicts with id, name, group

        Returns:
            Formatted prompt string
        """
        categories_json = json.dumps(
            [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "group": c["group"],
                }
                for c in categories
            ],
            indent=2,
        )

        source_categories_json = json.dumps(source_categories, indent=2)

        prompt = f"""You are a financial category mapper. Your job is to match bank/credit card category names to a standardized set of categories.

Available Target Categories:
{categories_json}

Source Categories to Map (from bank CSV export):
{source_categories_json}

For each source category, find the best matching target category from the list above.

Respond with a JSON array containing objects with these fields:
- source: The source category name (exactly as provided)
- target_id: The UUID of the best matching target category, or null if no good match
- confidence: A number from 0.0 to 1.0 indicating your confidence in the match

Matching Guidelines:
- "Restaurant", "Dining", "Food & Drink" should map to a food/dining category
- "Grocery", "Supermarket" should map to a groceries category
- "Gas", "Fuel", "Petrol" should map to a transportation/gas category
- "Amazon", "Online Shopping" should map to a shopping category
- If a source category is very specific (like "Restaurant-Restaurant"), extract the main concept
- Only return confidence >= 0.5 if you're reasonably sure about the match
- Return null for target_id if there's no reasonable match

Example response format:
[
  {{"source": "Restaurant-Restaurant", "target_id": "uuid-here", "confidence": 0.95}},
  {{"source": "Unknown Category", "target_id": null, "confidence": 0.0}}
]

Only respond with the JSON array, no additional text."""

        return prompt

    def suggest_mappings_with_ai(
        self,
        account_id: str,
        source_categories: list[str],
    ) -> list[CategoryMappingSuggestion]:
        """
        Call Claude to suggest mappings for source categories.

        Args:
            account_id: The account ID (for context, not currently used in prompt)
            source_categories: List of source category names to map

        Returns:
            List of CategoryMappingSuggestion objects
        """
        if not source_categories:
            return []

        categories = self.get_all_categories()
        if not categories:
            logger.warning("No categories available for mapping suggestions")
            return [
                CategoryMappingSuggestion(
                    source_category=sc,
                    target_category_id=None,
                    confidence=0.0,
                )
                for sc in source_categories
            ]

        # Build category lookup for enriching results
        category_lookup = {c["id"]: c for c in categories}

        prompt = self.build_mapping_prompt(source_categories, categories)

        try:
            raw_results = invoke_and_parse(prompt)
        except ClaudeClientError as e:
            logger.error(f"Claude invocation failed for category mapping: {e}")
            # Return empty suggestions on failure
            return [
                CategoryMappingSuggestion(
                    source_category=sc,
                    target_category_id=None,
                    confidence=0.0,
                )
                for sc in source_categories
            ]

        # Parse results and validate
        suggestions = []
        result_by_source = {item.get("source", "").lower(): item for item in raw_results}

        for sc in source_categories:
            item = result_by_source.get(sc.lower(), {})
            target_id = item.get("target_id")
            confidence = float(item.get("confidence", 0))

            # Validate target_id exists
            if target_id and target_id not in category_lookup:
                logger.warning(f"AI returned invalid category_id: {target_id}")
                target_id = None
                confidence = 0.0

            # Get category details
            target_name = None
            target_emoji = None
            if target_id:
                cat = category_lookup.get(target_id)
                if cat:
                    target_name = cat["name"]
                    target_emoji = cat["emoji"]

            suggestions.append(
                CategoryMappingSuggestion(
                    source_category=sc,
                    target_category_id=target_id,
                    target_category_name=target_name,
                    target_category_emoji=target_emoji,
                    confidence=confidence,
                )
            )

        logger.info(
            f"Generated {len(suggestions)} category mapping suggestions for account {account_id}"
        )

        return suggestions

    def build_transaction_categorization_prompt(
        self,
        transactions: list[dict],
        categories: list[dict],
    ) -> str:
        """
        Build the prompt for Claude to categorize transactions by description.

        Args:
            transactions: List of dicts with row_number, description, amount
            categories: List of category dicts with id, name, group

        Returns:
            Formatted prompt string
        """
        categories_json = json.dumps(
            [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "group": c["group"],
                }
                for c in categories
            ],
            indent=2,
        )

        # Format transactions for the prompt
        transactions_for_prompt = []
        for t in transactions:
            tx_type = "expense" if t["amount"] < 0 else "income"
            transactions_for_prompt.append({
                "row": t["row_number"],
                "description": t["description"][:200],  # Truncate long descriptions
                "type": tx_type,
            })

        transactions_json = json.dumps(transactions_for_prompt, indent=2)

        prompt = f"""You are a financial transaction categorizer. Analyze each transaction description and assign the most appropriate category.

Available Categories:
{categories_json}

Transactions to categorize:
{transactions_json}

For each transaction, respond with a JSON array containing objects with these fields:
- row: The row number from the input
- category_id: The UUID of the best matching category
- confidence: A number from 0.0 to 1.0 indicating your confidence

Guidelines:
- Look for merchant/vendor names in the description (e.g., "AMAZON", "STARBUCKS", "SHELL")
- "expense" type transactions are typically purchases, bills, etc.
- "income" type transactions are typically salary, refunds, transfers in
- If unsure, pick the most likely category based on common spending patterns
- Only return confidence >= 0.5 if you're reasonably sure

Example response format:
[
  {{"row": 1, "category_id": "cat-uuid-here", "confidence": 0.95}},
  {{"row": 2, "category_id": "cat-uuid-here", "confidence": 0.72}}
]

Only respond with the JSON array, no additional text."""

        return prompt

    def categorize_transactions_with_ai(
        self,
        transactions: list[dict],
    ) -> dict[int, dict]:
        """
        Use AI to categorize transactions by their descriptions.

        Args:
            transactions: List of dicts with row_number, description, amount

        Returns:
            Dict mapping row_number to category info (category_id, category_name, category_emoji, confidence)
        """
        if not transactions:
            return {}

        categories = self.get_all_categories()
        if not categories:
            logger.warning("No categories available for transaction categorization")
            return {}

        # Build category lookup
        category_lookup = {c["id"]: c for c in categories}

        prompt = self.build_transaction_categorization_prompt(transactions, categories)

        try:
            raw_results = invoke_and_parse(prompt)
        except ClaudeClientError as e:
            logger.error(f"Claude invocation failed for transaction categorization: {e}")
            return {}

        # Parse results and validate
        results = {}
        for item in raw_results:
            try:
                row = item.get("row")
                category_id = item.get("category_id")
                confidence = float(item.get("confidence", 0))

                if row is None or not category_id:
                    continue

                # Validate category_id exists
                if category_id not in category_lookup:
                    logger.warning(f"AI returned invalid category_id: {category_id}")
                    continue

                # Only include if confidence is reasonable
                if confidence < 0.5:
                    continue

                cat = category_lookup[category_id]
                results[row] = {
                    "category_id": category_id,
                    "category_name": cat["name"],
                    "category_emoji": cat["emoji"],
                    "confidence": confidence,
                }
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse AI result item: {item}, error: {e}")
                continue

        logger.info(
            f"AI categorized {len(results)} of {len(transactions)} transactions"
        )

        return results


category_mapping_service = CategoryMappingService()
