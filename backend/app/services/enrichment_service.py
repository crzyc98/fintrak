"""
AI-powered transaction enrichment service.
Normalizes merchant names, assigns subcategories, and classifies
transactions as essential vs. discretionary using Gemini.
"""
import json
import logging
import re
from datetime import datetime
from typing import Optional

from app.config import CATEGORIZATION_BATCH_SIZE
from app.database import get_db, safe_update_transaction
from app.models.enrichment import (
    EnrichmentTriggerRequest,
    EnrichmentResult,
    EnrichmentBatchResponse,
)
from app.services.gemini_client import invoke_and_parse, AIClientError

logger = logging.getLogger(__name__)

# Patterns for sensitive data that should be sanitized before sending to AI
SENSITIVE_PATTERNS = [
    (r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", "[CARD]"),
    (r"\b\d{8,17}\b", "[ACCT]"),
    (r"\b\d{9}\b", "[ROUTING]"),
    (r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b", "[SSN]"),
]


def _sanitize_for_ai(description: str) -> str:
    """Remove sensitive data patterns from description before sending to AI."""
    if not description:
        return ""
    result = description
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


class EnrichmentService:
    """Service for AI-powered transaction enrichment."""

    def get_unenriched_transactions(
        self,
        transaction_ids: Optional[list[str]] = None,
        limit: int = 200,
    ) -> list[dict]:
        """
        Get transactions that need enrichment (enrichment_source IS NULL).
        """
        with get_db() as conn:
            if transaction_ids:
                placeholders = ",".join(["?" for _ in transaction_ids])
                query = f"""
                    SELECT t.id, t.description, t.original_description,
                           t.normalized_merchant, t.amount,
                           c.name as category_name
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE t.enrichment_source IS NULL
                    AND t.id IN ({placeholders})
                    ORDER BY t.date DESC
                    LIMIT ?
                """
                params = transaction_ids + [limit]
            else:
                query = """
                    SELECT t.id, t.description, t.original_description,
                           t.normalized_merchant, t.amount,
                           c.name as category_name
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.id
                    WHERE t.enrichment_source IS NULL
                    ORDER BY t.date DESC
                    LIMIT ?
                """
                params = [limit]

            result = conn.execute(query, params).fetchall()

        return [
            {
                "id": row[0],
                "description": row[1],
                "original_description": row[2],
                "normalized_merchant": row[3],
                "amount": row[4],
                "category_name": row[5],
            }
            for row in result
        ]

    def build_enrichment_prompt(self, transactions: list[dict]) -> str:
        """Build the Gemini prompt for transaction enrichment."""
        transactions_for_prompt = []
        for t in transactions:
            merchant = t.get("normalized_merchant") or t["description"]
            original_desc = t.get("original_description", "") or ""
            sanitized_desc = _sanitize_for_ai(original_desc)[:500]
            transactions_for_prompt.append({
                "transaction_id": t["id"],
                "merchant": _sanitize_for_ai(merchant),
                "description": sanitized_desc,
                "category": t.get("category_name") or "Uncategorized",
            })

        transactions_json = json.dumps(transactions_for_prompt, indent=2)

        prompt = f"""You are a financial transaction enrichment engine. For each transaction, provide:

1. **normalized_merchant**: A clean, human-readable merchant name. Convert cryptic bank descriptions like "SQ *JOES COFFEE #123" to "Joe's Coffee". Remove transaction codes, location suffixes, and card network prefixes. Keep it concise.

2. **subcategory**: A specific subcategory tag (e.g., "Coffee Shop", "Streaming Service", "Grocery Store", "Gas Station", "Fast Food", "Pharmacy", "Electric Bill", "Rent Payment"). Use title case, 2-3 words max.

3. **is_discretionary**: true if the spending is discretionary (wants, entertainment, dining out, subscriptions), false if essential (housing, utilities, groceries, insurance, medical). For income transactions, set to false.

Transactions to enrich:
{transactions_json}

Respond with a JSON array containing objects with these fields:
- transaction_id: The ID from the input
- normalized_merchant: Clean merchant name
- subcategory: Specific subcategory tag
- is_discretionary: boolean

Example response:
[
  {{"transaction_id": "abc-123", "normalized_merchant": "Starbucks", "subcategory": "Coffee Shop", "is_discretionary": true}},
  {{"transaction_id": "def-456", "normalized_merchant": "Comcast", "subcategory": "Internet Bill", "is_discretionary": false}}
]

Only respond with the JSON array, no additional text."""

        return prompt

    def enrich_batch(self, transactions: list[dict]) -> list[EnrichmentResult]:
        """Send a batch of transactions to Gemini for enrichment."""
        if not transactions:
            return []

        prompt = self.build_enrichment_prompt(transactions)

        try:
            raw_results = invoke_and_parse(prompt)
        except AIClientError as e:
            logger.error(f"AI enrichment invocation failed: {e}")
            return []

        results = []
        for item in raw_results:
            try:
                tx_id = item.get("transaction_id")
                if not tx_id:
                    logger.warning(f"Missing transaction_id in AI response: {item}")
                    continue

                results.append(EnrichmentResult(
                    transaction_id=tx_id,
                    normalized_merchant=item.get("normalized_merchant"),
                    subcategory=item.get("subcategory"),
                    is_discretionary=item.get("is_discretionary"),
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse enrichment result: {item}, error: {e}")
                continue

        return results

    def apply_enrichment_results(self, results: list[EnrichmentResult]) -> int:
        """
        Apply enrichment results to transactions in the database.

        Returns the number of successfully updated transactions.
        """
        success_count = 0

        with get_db() as conn:
            for result in results:
                try:
                    updates = {
                        "subcategory": result.subcategory,
                        "is_discretionary": result.is_discretionary,
                        "enrichment_source": "ai",
                    }
                    if result.normalized_merchant is not None:
                        updates["normalized_merchant"] = result.normalized_merchant

                    if safe_update_transaction(conn, result.transaction_id, updates):
                        success_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to apply enrichment for {result.transaction_id}: {e}"
                    )

        return success_count

    def trigger_enrichment(
        self,
        request: Optional[EnrichmentTriggerRequest] = None,
    ) -> EnrichmentBatchResponse:
        """
        Trigger enrichment for unenriched transactions.
        Processes in batches using the same batch size as categorization.
        """
        started_at = datetime.utcnow()
        total_count = 0
        success_count = 0
        failure_count = 0
        skipped_count = 0
        error_message = None

        try:
            transaction_ids = request.transaction_ids if request else None
            limit = request.limit if request else 200
            transactions = self.get_unenriched_transactions(transaction_ids, limit)
            total_count = len(transactions)

            if total_count == 0:
                logger.info("[ENRICHMENT] No unenriched transactions to process")
                return self._create_response(started_at, 0, 0, 0, 0, None)

            logger.info(f"[ENRICHMENT] Starting enrichment for {total_count} transactions")

            # Filter out transactions with empty descriptions
            processable = []
            for tx in transactions:
                description = tx.get("original_description") or tx.get("description") or ""
                if not description.strip():
                    skipped_count += 1
                else:
                    processable.append(tx)

            # Process in batches
            for i in range(0, len(processable), CATEGORIZATION_BATCH_SIZE):
                batch = processable[i:i + CATEGORIZATION_BATCH_SIZE]
                batch_num = (i // CATEGORIZATION_BATCH_SIZE) + 1
                total_batches = (len(processable) + CATEGORIZATION_BATCH_SIZE - 1) // CATEGORIZATION_BATCH_SIZE

                logger.info(f"[ENRICHMENT] Processing batch {batch_num}/{total_batches} ({len(batch)} transactions)")

                try:
                    results = self.enrich_batch(batch)
                    if results:
                        batch_success = self.apply_enrichment_results(results)
                        success_count += batch_success
                        failure_count += len(batch) - len(results)
                    else:
                        failure_count += len(batch)
                        logger.warning(f"[ENRICHMENT] Batch {batch_num} returned no results")
                except Exception as e:
                    logger.exception(f"[ENRICHMENT] Batch {batch_num} failed: {e}")
                    failure_count += len(batch)

        except Exception as e:
            logger.exception(f"[ENRICHMENT] Enrichment failed: {e}")
            error_message = str(e)
            failure_count = total_count - success_count

        return self._create_response(
            started_at, total_count, success_count, failure_count, skipped_count, error_message
        )

    def _create_response(
        self,
        started_at: datetime,
        total_count: int,
        success_count: int,
        failure_count: int,
        skipped_count: int,
        error_message: Optional[str],
    ) -> EnrichmentBatchResponse:
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        logger.info(
            f"[ENRICHMENT] Complete: {success_count}/{total_count} successful, "
            f"{skipped_count} skipped, {failure_count} failed in {duration_ms}ms"
        )

        return EnrichmentBatchResponse(
            total_count=total_count,
            success_count=success_count,
            failure_count=failure_count,
            skipped_count=skipped_count,
            duration_ms=duration_ms,
            error_message=error_message,
        )


enrichment_service = EnrichmentService()
