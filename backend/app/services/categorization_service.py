"""
AI-powered unified transaction classification service.
Orchestrates batching, rule matching, and Gemini AI invocation
for both categorization and enrichment in a single pass.
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
from app.database import get_db, safe_update_transaction
from app.models.categorization import (
    CategorizationResult,
    UnifiedAIResult,
    CategorizationBatchResponse,
    CategorizationTriggerRequest,
)
from app.services.gemini_client import (
    invoke_and_parse,
    AIClientError,
)
from app.services.merchant_normalizer import normalize
from app.services.batch_service import batch_service
from app.services.category_service import category_service

logger = logging.getLogger(__name__)


def _sanitize_for_log(value: str, max_len: int = 50) -> str:
    """Sanitize a value for logging (truncate, no sensitive data)."""
    if not value:
        return ""
    if len(value) > max_len:
        return value[:max_len] + "..."
    return value


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


class CategorizationService:
    """Service for unified AI-powered transaction classification."""

    def get_unclassified_transactions(
        self,
        transaction_ids: Optional[list[str]] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """
        Get transactions that need classification (categorization OR enrichment).

        Returns transactions where category_id IS NULL OR enrichment_source IS NULL.
        """
        with get_db() as conn:
            if transaction_ids:
                placeholders = ",".join(["?" for _ in transaction_ids])
                query = f"""
                    SELECT id, description, original_description, amount,
                           normalized_merchant, account_id, category_id
                    FROM transactions
                    WHERE (category_id IS NULL OR enrichment_source IS NULL)
                    AND id IN ({placeholders})
                    ORDER BY date DESC
                    LIMIT ?
                """
                params = transaction_ids + [limit]
            else:
                query = """
                    SELECT id, description, original_description, amount,
                           normalized_merchant, account_id, category_id
                    FROM transactions
                    WHERE (category_id IS NULL OR enrichment_source IS NULL)
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
                "account_id": row[5],
                "category_id": row[6],
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

    def build_unified_prompt(
        self,
        transactions: list[dict],
        categories: list[dict],
    ) -> str:
        """Build the prompt for unified AI classification (categorization + enrichment)."""
        categories_json = json.dumps(
            [{"name": c["name"], "group": c["group"]} for c in categories],
            indent=2,
        )

        transactions_for_prompt = []
        for t in transactions:
            merchant = t.get("normalized_merchant") or t["description"]
            original_desc = t.get("original_description", "") or ""
            sanitized_desc = _sanitize_for_ai(original_desc)[:500]
            tx_type = "expense" if t["amount"] < 0 else "income"
            transactions_for_prompt.append({
                "transaction_id": t["id"],
                "merchant": _sanitize_for_ai(merchant),
                "description": sanitized_desc,
                "type": tx_type,
            })

        transactions_json = json.dumps(transactions_for_prompt, indent=2)

        prompt = f"""You are a financial transaction classifier. For each transaction, assign a category AND provide enrichment data.

Available Categories (prefer these; only invent a new category if nothing fits):
{categories_json}

Transactions to classify:
{transactions_json}

For each transaction, respond with a JSON array of objects with these fields:
- transaction_id: The ID from the input
- category_name: The name of the best matching category from the list above, or a new descriptive name if nothing fits
- category_group: The group of the category (Essential, Lifestyle, Income, Transfer, or Other)
- subcategory: A specific subcategory tag (e.g., "Coffee Shop", "Streaming Service", "Grocery Store"). Use title case, 2-3 words max.
- is_discretionary: true if discretionary (wants, entertainment, dining out, subscriptions), false if essential (housing, utilities, groceries, insurance, medical). For income, set false.
- normalized_merchant: A clean, human-readable merchant name. Convert cryptic bank descriptions like "SQ *JOES COFFEE #123" to "Joe's Coffee". Remove transaction codes, location suffixes, and card network prefixes.
- confidence: A number from 0.0 to 1.0 indicating your confidence in the category assignment

Example response:
[
  {{"transaction_id": "abc-123", "category_name": "Dining Out", "category_group": "Lifestyle", "subcategory": "Coffee Shop", "is_discretionary": true, "normalized_merchant": "Starbucks", "confidence": 0.95}},
  {{"transaction_id": "def-456", "category_name": "Utilities", "category_group": "Essential", "subcategory": "Internet Bill", "is_discretionary": false, "normalized_merchant": "Comcast", "confidence": 0.90}}
]

Only respond with the JSON array, no additional text."""

        return prompt

    def classify_batch(
        self,
        transactions: list[dict],
        categories: list[dict],
    ) -> list[UnifiedAIResult]:
        """Send a batch of transactions to AI for unified classification."""
        if not transactions:
            return []

        prompt = self.build_unified_prompt(transactions, categories)

        try:
            raw_results = invoke_and_parse(prompt)
        except AIClientError as e:
            logger.error(f"AI invocation failed: {e}")
            return []

        results = []
        for item in raw_results:
            try:
                tx_id = item.get("transaction_id")
                cat_name = item.get("category_name")
                if not tx_id or not cat_name:
                    logger.warning(f"Missing required fields in AI response: {item}")
                    continue

                confidence = float(item.get("confidence", 0))

                results.append(UnifiedAIResult(
                    transaction_id=tx_id,
                    category_name=cat_name,
                    category_group=item.get("category_group", "Other"),
                    subcategory=item.get("subcategory"),
                    is_discretionary=item.get("is_discretionary"),
                    normalized_merchant=item.get("normalized_merchant"),
                    confidence=confidence,
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse AI result item: {item}, error: {e}")
                continue

        return results

    def apply_unified_results(
        self,
        results: list[UnifiedAIResult],
        transactions: list[dict],
    ) -> tuple[int, int, int]:
        """
        Apply unified AI results to transactions.

        For transactions that already have a category_id (from rules), only
        enrichment fields are applied — the category is not overridden.

        Returns:
            Tuple of (success_count, skipped_count, categories_created_count)
        """
        success_count = 0
        skipped_count = 0
        categories_created = 0

        # Build a lookup of existing category_id by transaction_id
        tx_category_map = {tx["id"]: tx.get("category_id") for tx in transactions}

        # Cache resolved categories within this batch to avoid duplicate creates
        category_cache: dict[str, str] = {}  # normalized_name -> category_id

        with get_db() as conn:
            for result in results:
                # Skip low-confidence results
                if result.confidence < CATEGORIZATION_CONFIDENCE_THRESHOLD:
                    skipped_count += 1
                    logger.debug(
                        f"Skipping transaction {result.transaction_id}: "
                        f"confidence {result.confidence} below threshold"
                    )
                    continue

                existing_category_id = tx_category_map.get(result.transaction_id)

                updates: dict = {}

                # Only assign category if the transaction doesn't already have one
                if not existing_category_id:
                    cache_key = category_service._normalize_category_name(result.category_name)
                    if cache_key in category_cache:
                        category_id = category_cache[cache_key]
                    else:
                        # Check if category exists before find_or_create to detect new ones
                        existed = category_service.find_by_name(result.category_name) is not None
                        cat = category_service.find_or_create(
                            name=result.category_name,
                            group_name=result.category_group,
                        )
                        category_id = cat.id
                        category_cache[cache_key] = category_id
                        if not existed:
                            categories_created += 1

                    updates["category_id"] = category_id
                    updates["confidence_score"] = result.confidence
                    updates["categorization_source"] = "ai"

                # Always apply enrichment fields
                if result.subcategory is not None:
                    updates["subcategory"] = result.subcategory
                if result.is_discretionary is not None:
                    updates["is_discretionary"] = result.is_discretionary
                if result.normalized_merchant is not None:
                    updates["normalized_merchant"] = result.normalized_merchant
                updates["enrichment_source"] = "ai"

                if updates:
                    safe_update_transaction(conn, result.transaction_id, updates)
                    success_count += 1

        return success_count, skipped_count, categories_created

    def apply_categorization_results(
        self,
        results: list[CategorizationResult],
        source: str = "ai",
    ) -> tuple[int, int]:
        """
        Apply categorization results to transactions (used by rule matching).

        Returns:
            Tuple of (success_count, skipped_count)
        """
        success_count = 0
        skipped_count = 0

        with get_db() as conn:
            for result in results:
                if source == "ai" and result.confidence < CATEGORIZATION_CONFIDENCE_THRESHOLD:
                    skipped_count += 1
                    continue

                safe_update_transaction(conn, result.transaction_id, {
                    "category_id": result.category_id,
                    "confidence_score": result.confidence,
                    "categorization_source": source,
                })
                success_count += 1

        return success_count, skipped_count

    def trigger_categorization(
        self,
        request: Optional[CategorizationTriggerRequest] = None,
    ) -> CategorizationBatchResponse:
        """
        Trigger unified classification for transactions.

        Applies learned rules first, then sends remaining to AI in batches
        for both categorization and enrichment.
        """
        started_at = datetime.utcnow()

        total_count = 0
        success_count = 0
        failure_count = 0
        rule_match_count = 0
        desc_rule_match_count = 0
        ai_match_count = 0
        skipped_count = 0
        categories_created_count = 0
        error_message = None
        batch_id = None

        try:
            transaction_ids = request.transaction_ids if request else None
            transactions = self.get_unclassified_transactions(transaction_ids)
            total_count = len(transactions)

            if total_count == 0:
                logger.info(
                    "[CLASSIFICATION] No transactions to process",
                    extra={"event": "classification_empty"}
                )
                return self._create_batch_response(
                    str(uuid.uuid4()), started_at, 0, 0, 0, 0, 0, 0, 0, 0, None
                )

            batch_id = batch_service.create_batch(
                import_id=None,
                transaction_count=total_count,
            )

            logger.info(
                f"[CLASSIFICATION] Starting batch {batch_id} for {total_count} transactions",
                extra={
                    "event": "classification_start",
                    "batch_id": batch_id,
                    "transaction_count": total_count,
                }
            )

            categories = self.get_all_categories()

            # Apply rules first (unless force_ai is set) — only to uncategorized transactions
            force_ai = request.force_ai if request else False
            uncategorized = [t for t in transactions if not t.get("category_id")]
            already_categorized = [t for t in transactions if t.get("category_id")]

            remaining_transactions = uncategorized
            if not force_ai and uncategorized:
                remaining_transactions, rule_matches, desc_rule_matches = self._apply_rules(uncategorized)
                rule_match_count = rule_matches
                desc_rule_match_count = desc_rule_matches
                success_count += rule_matches + desc_rule_matches
                logger.info(
                    f"[CLASSIFICATION] Rule matching complete: {rule_matches} merchant rules, "
                    f"{desc_rule_matches} desc rules, {len(remaining_transactions)} remaining",
                    extra={
                        "event": "classification_rules_applied",
                        "batch_id": batch_id,
                    }
                )

            # Combine: uncategorized remaining + already-categorized needing enrichment
            ai_transactions = remaining_transactions + already_categorized

            if ai_transactions:
                logger.info(
                    f"[CLASSIFICATION] Starting AI processing for {len(ai_transactions)} transactions",
                    extra={
                        "event": "classification_ai_start",
                        "batch_id": batch_id,
                        "ai_transaction_count": len(ai_transactions),
                    }
                )
                ai_results = self._process_ai_batches(ai_transactions, categories)
                ai_match_count = ai_results["success"]
                skipped_count = ai_results["skipped"]
                failure_count = ai_results["failure"]
                categories_created_count = ai_results["categories_created"]
                success_count += ai_match_count

                logger.info(
                    f"[CLASSIFICATION] AI processing complete: {ai_match_count} success, "
                    f"{skipped_count} skipped, {failure_count} failed, "
                    f"{categories_created_count} categories created",
                    extra={
                        "event": "classification_ai_complete",
                        "batch_id": batch_id,
                    }
                )

        except Exception as e:
            logger.exception(
                f"[CLASSIFICATION] Batch failed: {_sanitize_for_log(str(e))}",
                extra={
                    "event": "classification_error",
                    "batch_id": batch_id,
                    "error_type": type(e).__name__,
                }
            )
            error_message = str(e)
            failure_count = total_count - success_count

        if batch_id:
            batch_service.complete_batch(
                batch_id,
                success_count,
                failure_count,
                rule_match_count,
                desc_rule_match_count,
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
            desc_rule_match_count,
            ai_match_count,
            skipped_count,
            categories_created_count,
            error_message,
        )

    def _apply_rules(
        self,
        transactions: list[dict],
    ) -> tuple[list[dict], int, int]:
        """
        Apply learned rules to transactions.

        Returns:
            Tuple of (remaining_transactions, merchant_rule_match_count, desc_rule_match_count)
        """
        from app.services.rule_service import rule_service
        from app.services.desc_rule_service import desc_rule_service

        remaining = []
        match_count = 0

        for tx in transactions:
            normalized_merchant = tx.get("normalized_merchant")
            if not normalized_merchant:
                remaining.append(tx)
                continue

            rule = rule_service.find_matching_rule(normalized_merchant)
            if rule:
                result = CategorizationResult(
                    transaction_id=tx["id"],
                    category_id=rule.category_id,
                    confidence=1.0,
                )
                self.apply_categorization_results([result], source="rule")
                match_count += 1
                logger.debug(
                    f"Rule matched: '{rule.merchant_pattern}' -> {rule.category_id} "
                    f"for transaction {tx['id']}"
                )
            else:
                remaining.append(tx)

        # Second pass: description-based pattern rules
        desc_remaining = []
        desc_match_count = 0

        for tx in remaining:
            description = tx.get("description", "")
            account_id = tx.get("account_id", "")

            if description and account_id:
                desc_rule = desc_rule_service.find_matching_rule(description, account_id)
                if desc_rule:
                    result = CategorizationResult(
                        transaction_id=tx["id"],
                        category_id=desc_rule.category_id,
                        confidence=1.0,
                    )
                    self.apply_categorization_results([result], source="desc_rule")
                    desc_match_count += 1
                    logger.debug(
                        f"Desc rule matched: '{desc_rule.description_pattern}' -> "
                        f"{desc_rule.category_id} for transaction {tx['id']}"
                    )
                else:
                    desc_remaining.append(tx)
            else:
                desc_remaining.append(tx)

        return desc_remaining, match_count, desc_match_count

    def _process_ai_batches(
        self,
        transactions: list[dict],
        categories: list[dict],
    ) -> dict:
        """
        Process transactions in batches with unified AI classification.

        Returns:
            Dict with 'success', 'skipped', 'failure', 'categories_created' counts
        """
        success_total = 0
        skipped_total = 0
        failure_total = 0
        categories_created_total = 0

        # Filter out transactions with empty descriptions
        processable = []
        for tx in transactions:
            description = tx.get("original_description") or tx.get("description") or ""
            if not description.strip():
                logger.warning(
                    f"[CLASSIFICATION] Skipping transaction {tx['id']}: empty description",
                    extra={
                        "event": "classification_empty_description",
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
                "categories_created": categories_created_total,
            }

        transactions = processable

        for i in range(0, len(transactions), CATEGORIZATION_BATCH_SIZE):
            batch = transactions[i:i + CATEGORIZATION_BATCH_SIZE]
            batch_num = (i // CATEGORIZATION_BATCH_SIZE) + 1
            total_batches = (len(transactions) + CATEGORIZATION_BATCH_SIZE - 1) // CATEGORIZATION_BATCH_SIZE

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} transactions)")

            try:
                # Count categories before to detect new ones
                cats_before = len(categories)
                results = self.classify_batch(batch, categories)

                if results:
                    success, skipped, created = self.apply_unified_results(results, batch)
                    success_total += success
                    skipped_total += skipped
                    categories_created_total += created
                    failure_total += len(batch) - len(results)

                    # If new categories were created, refresh the list for subsequent batches
                    if created > 0:
                        categories = self.get_all_categories()
                else:
                    failure_total += len(batch)
                    logger.warning(f"Batch {batch_num} returned no results")

            except Exception as e:
                logger.exception(f"Batch {batch_num} failed: {e}")
                failure_total += len(batch)

        return {
            "success": success_total,
            "skipped": skipped_total,
            "failure": failure_total,
            "categories_created": categories_created_total,
        }

    def _create_batch_response(
        self,
        batch_id: str,
        started_at: datetime,
        transaction_count: int,
        success_count: int,
        failure_count: int,
        rule_match_count: int,
        desc_rule_match_count: int,
        ai_match_count: int,
        skipped_count: int,
        categories_created_count: int,
        error_message: Optional[str],
    ) -> CategorizationBatchResponse:
        """Create a batch response and log completion."""
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        logger.info(
            f"Classification complete: {success_count}/{transaction_count} successful "
            f"(merchant rules: {rule_match_count}, desc rules: {desc_rule_match_count}, "
            f"AI: {ai_match_count}, skipped: {skipped_count}, "
            f"new categories: {categories_created_count}) in {duration_ms}ms"
        )

        return CategorizationBatchResponse(
            id=batch_id,
            transaction_count=transaction_count,
            success_count=success_count,
            failure_count=failure_count,
            rule_match_count=rule_match_count,
            desc_rule_match_count=desc_rule_match_count,
            ai_match_count=ai_match_count,
            skipped_count=skipped_count,
            categories_created_count=categories_created_count,
            duration_ms=duration_ms,
            error_message=error_message,
            started_at=started_at,
            completed_at=completed_at,
        )


categorization_service = CategorizationService()
