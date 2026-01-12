"""
AI-powered transaction categorization service.
Orchestrates batching, rule matching, and Claude CLI invocation.
"""
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Optional

from app.config import (
    CATEGORIZATION_BATCH_SIZE,
    CATEGORIZATION_CONFIDENCE_THRESHOLD,
)
from app.database import get_db
from app.models.categorization import (
    CategorizationResult,
    CategorizationBatchResponse,
    CategorizationTriggerRequest,
)
from app.services.claude_client import (
    invoke_and_parse,
    ClaudeClientError,
)
from app.services.merchant_normalizer import normalize
from app.services.batch_service import batch_service

logger = logging.getLogger(__name__)


def _sanitize_for_log(value: str, max_len: int = 50) -> str:
    """Sanitize a value for logging (truncate, no sensitive data)."""
    if not value:
        return ""
    # Truncate if needed
    if len(value) > max_len:
        return value[:max_len] + "..."
    return value


# Patterns for sensitive data that should be sanitized before sending to AI
SENSITIVE_PATTERNS = [
    # Credit/Debit card numbers (16 digits, with or without separators)
    (r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", "[CARD]"),
    # Account numbers (8-17 digits)
    (r"\b\d{8,17}\b", "[ACCT]"),
    # Routing numbers (9 digits)
    (r"\b\d{9}\b", "[ROUTING]"),
    # SSN patterns (XXX-XX-XXXX)
    (r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b", "[SSN]"),
]


def _sanitize_for_ai(description: str) -> str:
    """
    Remove sensitive data patterns from description before sending to AI.

    Args:
        description: Raw transaction description

    Returns:
        Sanitized description with sensitive data replaced
    """
    if not description:
        return ""

    result = description
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result)

    return result


class CategorizationService:
    """Service for AI-powered transaction categorization."""

    def get_uncategorized_transactions(
        self,
        transaction_ids: Optional[list[str]] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """
        Get transactions that need categorization.

        Args:
            transaction_ids: Optional specific IDs to filter (otherwise all uncategorized)
            limit: Maximum number of transactions to return

        Returns:
            List of transaction dicts with id, description, original_description, amount
        """
        with get_db() as conn:
            if transaction_ids:
                placeholders = ",".join(["?" for _ in transaction_ids])
                query = f"""
                    SELECT id, description, original_description, amount, normalized_merchant
                    FROM transactions
                    WHERE category_id IS NULL
                    AND id IN ({placeholders})
                    ORDER BY date DESC
                    LIMIT ?
                """
                params = transaction_ids + [limit]
            else:
                query = """
                    SELECT id, description, original_description, amount, normalized_merchant
                    FROM transactions
                    WHERE category_id IS NULL
                    ORDER BY date DESC
                    LIMIT ?
                """
                params = [limit]

            result = conn.execute(query, params).fetchall()

        return [
            {
                "id": row[0],
                "description": row[1],
                "original_description": row[2],
                "amount": row[3],
                "normalized_merchant": row[4],
            }
            for row in result
        ]

    def get_all_categories(self) -> list[dict]:
        """Get all categories for the AI prompt."""
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

    def build_categorization_prompt(
        self,
        transactions: list[dict],
        categories: list[dict],
    ) -> str:
        """
        Build the prompt for Claude to categorize transactions.

        Args:
            transactions: List of transaction dicts
            categories: List of category dicts

        Returns:
            Formatted prompt string
        """
        # Format categories for the prompt
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
            merchant = t.get("normalized_merchant") or t["description"]
            # Sanitize and truncate description for AI safety
            original_desc = t.get("original_description", "") or ""
            sanitized_desc = _sanitize_for_ai(original_desc)[:500]  # Sanitize + truncate
            tx_type = "expense" if t["amount"] < 0 else "income"
            transactions_for_prompt.append({
                "transaction_id": t["id"],
                "merchant": _sanitize_for_ai(merchant),  # Also sanitize merchant
                "description": sanitized_desc,
                "type": tx_type,
            })

        transactions_json = json.dumps(transactions_for_prompt, indent=2)

        prompt = f"""You are a financial transaction categorizer. Analyze each transaction and assign the most appropriate category.

Available Categories:
{categories_json}

Transactions to categorize:
{transactions_json}

For each transaction, respond with a JSON array containing objects with these fields:
- transaction_id: The ID from the input
- category_id: The UUID of the best matching category
- confidence: A number from 0.0 to 1.0 indicating your confidence

Example response format:
[
  {{"transaction_id": "abc-123", "category_id": "cat-456", "confidence": 0.95}},
  {{"transaction_id": "def-789", "category_id": "cat-012", "confidence": 0.72}}
]

Only respond with the JSON array, no additional text."""

        return prompt

    def categorize_batch(
        self,
        transactions: list[dict],
        categories: list[dict],
    ) -> list[CategorizationResult]:
        """
        Send a batch of transactions to Claude for categorization.

        Args:
            transactions: List of transaction dicts
            categories: List of category dicts

        Returns:
            List of CategorizationResult objects
        """
        if not transactions:
            return []

        prompt = self.build_categorization_prompt(transactions, categories)

        try:
            raw_results = invoke_and_parse(prompt)
        except ClaudeClientError as e:
            logger.error(f"Claude invocation failed: {e}")
            return []

        # Parse and validate results
        results = []
        valid_category_ids = {c["id"] for c in categories}

        for item in raw_results:
            try:
                tx_id = item.get("transaction_id")
                cat_id = item.get("category_id")
                confidence = float(item.get("confidence", 0))

                if not tx_id or not cat_id:
                    logger.warning(f"Missing required fields in AI response: {item}")
                    continue

                if cat_id not in valid_category_ids:
                    logger.warning(f"AI returned invalid category_id: {cat_id}")
                    continue

                results.append(CategorizationResult(
                    transaction_id=tx_id,
                    category_id=cat_id,
                    confidence=confidence,
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse AI result item: {item}, error: {e}")
                continue

        return results

    def apply_categorization_results(
        self,
        results: list[CategorizationResult],
        source: str = "ai",
    ) -> tuple[int, int]:
        """
        Apply categorization results to transactions in the database.

        Args:
            results: List of CategorizationResult objects
            source: Categorization source ('ai' or 'rule')

        Returns:
            Tuple of (success_count, skipped_count)
        """
        success_count = 0
        skipped_count = 0

        with get_db() as conn:
            for result in results:
                # Skip if confidence below threshold (for AI results)
                if source == "ai" and result.confidence < CATEGORIZATION_CONFIDENCE_THRESHOLD:
                    skipped_count += 1
                    logger.debug(
                        f"Skipping transaction {result.transaction_id}: "
                        f"confidence {result.confidence} below threshold"
                    )
                    continue

                conn.execute(
                    """
                    UPDATE transactions
                    SET category_id = ?,
                        confidence_score = ?,
                        categorization_source = ?
                    WHERE id = ?
                    """,
                    [
                        result.category_id,
                        result.confidence,
                        source,
                        result.transaction_id,
                    ],
                )
                success_count += 1

        return success_count, skipped_count

    def trigger_categorization(
        self,
        request: Optional[CategorizationTriggerRequest] = None,
    ) -> CategorizationBatchResponse:
        """
        Trigger categorization for uncategorized transactions.

        Applies learned rules first, then sends remaining to AI in batches.

        Args:
            request: Optional trigger request with specific transaction IDs

        Returns:
            CategorizationBatchResponse with processing results
        """
        started_at = datetime.utcnow()

        # Initialize counters
        total_count = 0
        success_count = 0
        failure_count = 0
        rule_match_count = 0
        ai_match_count = 0
        skipped_count = 0
        error_message = None
        batch_id = None

        try:
            # Get transactions to categorize
            transaction_ids = request.transaction_ids if request else None
            transactions = self.get_uncategorized_transactions(transaction_ids)
            total_count = len(transactions)

            if total_count == 0:
                logger.info(
                    "[CATEGORIZATION] No uncategorized transactions to process",
                    extra={"event": "categorization_empty"}
                )
                return self._create_batch_response(
                    str(uuid.uuid4()), started_at, 0, 0, 0, 0, 0, 0, None
                )

            # Create batch record in database
            batch_id = batch_service.create_batch(
                import_id=None,
                transaction_count=total_count,
            )

            logger.info(
                f"[CATEGORIZATION] Starting batch {batch_id} for {total_count} transactions",
                extra={
                    "event": "categorization_start",
                    "batch_id": batch_id,
                    "transaction_count": total_count,
                }
            )

            # Get categories
            categories = self.get_all_categories()
            if not categories:
                logger.warning(
                    "[CATEGORIZATION] No categories available",
                    extra={"event": "categorization_no_categories", "batch_id": batch_id}
                )
                error_message = "No categories available"
                batch_service.complete_batch(
                    batch_id, 0, total_count, 0, 0, 0, error_message
                )
                return self._create_batch_response(
                    batch_id, started_at, total_count, 0, total_count,
                    0, 0, 0, error_message
                )

            # Apply rules first (unless force_ai is set)
            force_ai = request.force_ai if request else False
            remaining_transactions = transactions

            if not force_ai:
                remaining_transactions, rule_matches = self._apply_rules(transactions)
                rule_match_count = rule_matches
                success_count += rule_matches
                logger.info(
                    f"[CATEGORIZATION] Rule matching complete: {rule_matches} matched, "
                    f"{len(remaining_transactions)} remaining",
                    extra={
                        "event": "categorization_rules_applied",
                        "batch_id": batch_id,
                        "rule_match_count": rule_matches,
                        "remaining_count": len(remaining_transactions),
                    }
                )

            # Process remaining in batches with AI
            if remaining_transactions:
                logger.info(
                    f"[CATEGORIZATION] Starting AI processing for {len(remaining_transactions)} transactions",
                    extra={
                        "event": "categorization_ai_start",
                        "batch_id": batch_id,
                        "ai_transaction_count": len(remaining_transactions),
                    }
                )
                ai_results = self._process_ai_batches(
                    remaining_transactions,
                    categories,
                )
                ai_match_count = ai_results["success"]
                skipped_count = ai_results["skipped"]
                failure_count = ai_results["failure"]
                success_count += ai_match_count

                logger.info(
                    f"[CATEGORIZATION] AI processing complete: {ai_match_count} success, "
                    f"{skipped_count} skipped, {failure_count} failed",
                    extra={
                        "event": "categorization_ai_complete",
                        "batch_id": batch_id,
                        "ai_success_count": ai_match_count,
                        "ai_skipped_count": skipped_count,
                        "ai_failure_count": failure_count,
                    }
                )

        except Exception as e:
            logger.exception(
                f"[CATEGORIZATION] Batch failed: {_sanitize_for_log(str(e))}",
                extra={
                    "event": "categorization_error",
                    "batch_id": batch_id,
                    "error_type": type(e).__name__,
                }
            )
            error_message = str(e)
            failure_count = total_count - success_count

        # Complete the batch record in database
        if batch_id:
            batch_service.complete_batch(
                batch_id,
                success_count,
                failure_count,
                rule_match_count,
                ai_match_count,
                skipped_count,
                error_message,
            )

        return self._create_batch_response(
            batch_id or str(uuid.uuid4()),
            started_at,
            total_count,
            success_count,
            failure_count,
            rule_match_count,
            ai_match_count,
            skipped_count,
            error_message,
        )

    def _apply_rules(
        self,
        transactions: list[dict],
    ) -> tuple[list[dict], int]:
        """
        Apply learned rules to transactions.

        Returns:
            Tuple of (remaining_transactions, match_count)
        """
        from app.services.rule_service import rule_service

        remaining = []
        match_count = 0

        for tx in transactions:
            normalized_merchant = tx.get("normalized_merchant")
            if not normalized_merchant:
                # No normalized merchant, can't match rules
                remaining.append(tx)
                continue

            # Find matching rule
            rule = rule_service.find_matching_rule(normalized_merchant)
            if rule:
                # Apply rule directly
                result = CategorizationResult(
                    transaction_id=tx["id"],
                    category_id=rule.category_id,
                    confidence=1.0,  # Rules are 100% confidence
                )
                self.apply_categorization_results([result], source="rule")
                match_count += 1
                logger.debug(
                    f"Rule matched: '{rule.merchant_pattern}' -> {rule.category_id} "
                    f"for transaction {tx['id']}"
                )
            else:
                # No rule match, send to AI
                remaining.append(tx)

        return remaining, match_count

    def _process_ai_batches(
        self,
        transactions: list[dict],
        categories: list[dict],
    ) -> dict:
        """
        Process transactions in batches with AI.

        Returns:
            Dict with 'success', 'skipped', 'failure' counts
        """
        success_total = 0
        skipped_total = 0
        failure_total = 0

        # Filter out transactions with empty descriptions - they can't be categorized by AI
        processable = []
        for tx in transactions:
            description = tx.get("original_description") or tx.get("description") or ""
            if not description.strip():
                logger.warning(
                    f"[CATEGORIZATION] Skipping transaction {tx['id']}: empty description",
                    extra={
                        "event": "categorization_empty_description",
                        "transaction_id": tx["id"],
                    }
                )
                skipped_total += 1
            else:
                processable.append(tx)

        if not processable:
            return {
                "success": success_total,
                "skipped": skipped_total,
                "failure": failure_total,
            }

        transactions = processable

        # Process in batches
        for i in range(0, len(transactions), CATEGORIZATION_BATCH_SIZE):
            batch = transactions[i:i + CATEGORIZATION_BATCH_SIZE]
            batch_num = (i // CATEGORIZATION_BATCH_SIZE) + 1
            total_batches = (len(transactions) + CATEGORIZATION_BATCH_SIZE - 1) // CATEGORIZATION_BATCH_SIZE

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} transactions)")

            try:
                results = self.categorize_batch(batch, categories)

                if results:
                    success, skipped = self.apply_categorization_results(results)
                    success_total += success
                    skipped_total += skipped
                    failure_total += len(batch) - len(results)
                else:
                    # AI returned empty results
                    failure_total += len(batch)
                    logger.warning(f"Batch {batch_num} returned no results")

            except Exception as e:
                logger.exception(f"Batch {batch_num} failed: {e}")
                failure_total += len(batch)

        return {
            "success": success_total,
            "skipped": skipped_total,
            "failure": failure_total,
        }

    def _create_batch_response(
        self,
        batch_id: str,
        started_at: datetime,
        transaction_count: int,
        success_count: int,
        failure_count: int,
        rule_match_count: int,
        ai_match_count: int,
        skipped_count: int,
        error_message: Optional[str],
    ) -> CategorizationBatchResponse:
        """Create a batch response and log completion."""
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        logger.info(
            f"Categorization complete: {success_count}/{transaction_count} successful "
            f"(rules: {rule_match_count}, AI: {ai_match_count}, skipped: {skipped_count}) "
            f"in {duration_ms}ms"
        )

        return CategorizationBatchResponse(
            id=batch_id,
            transaction_count=transaction_count,
            success_count=success_count,
            failure_count=failure_count,
            rule_match_count=rule_match_count,
            ai_match_count=ai_match_count,
            skipped_count=skipped_count,
            duration_ms=duration_ms,
            error_message=error_message,
            started_at=started_at,
            completed_at=completed_at,
        )


categorization_service = CategorizationService()
