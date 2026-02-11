"""
Natural language transaction search service.
Interprets NL queries via Gemini, merges with manual filters, and executes search.
"""
import json
import logging
import re
from datetime import date
from typing import Optional

from app.config import NL_SEARCH_TIMEOUT_SECONDS
from app.database import get_db
from app.models.transaction import (
    InterpretedFilters,
    NLSearchRequest,
    NLSearchResponse,
    TransactionFilters,
    TransactionResponse,
)
from app.services.gemini_client import (
    invoke_and_parse,
    AIClientError,
)
from app.services.categorization_service import SENSITIVE_PATTERNS

logger = logging.getLogger(__name__)


def sanitize_nl_query(query: str) -> str:
    """Remove sensitive data patterns from user query before sending to AI."""
    if not query:
        return ""
    result = query
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result.strip()


def build_nl_search_prompt(
    query: str,
    categories: list[dict],
    accounts: list[dict],
    current_date: date,
) -> str:
    """
    Build the Gemini prompt for NL query interpretation.

    Args:
        query: Sanitized user query
        categories: List of category dicts with id, name, group
        accounts: List of account dicts with id, name
        current_date: Today's date for resolving relative dates
    """
    categories_json = json.dumps(categories, indent=2)
    accounts_json = json.dumps(accounts, indent=2)

    return f"""You are a financial transaction search assistant. Parse the user's natural language query into structured search filters.

Today's date: {current_date.isoformat()}

Available categories:
{categories_json}

Available accounts:
{accounts_json}

User query: "{query}"

Return a JSON array containing a single object with these fields (omit fields not mentioned in the query):
- date_from: ISO date string (YYYY-MM-DD)
- date_to: ISO date string (YYYY-MM-DD)
- amount_min: integer in cents (e.g., $50 = 5000)
- amount_max: integer in cents
- category_ids: array of category ID strings from the list above
- merchant_keywords: array of merchant name strings to match. For merchant names, include both the brand name AND common bank description abbreviations/codes (e.g., for Amazon include: amazon, amzn, amzn*mktp; for Walmart include: walmart, wmt; for Starbucks include: starbucks, sbux). Include at least 2-3 variants per merchant.
- description_keywords: array of general search terms
- summary: human-readable description of what the query means (e.g., "Coffee purchases in January 2026")

Only include fields that the query explicitly or implicitly references.
For amounts, convert dollar values to cents (multiply by 100).

IMPORTANT: Return the result as a JSON array with a single element, like this: [{{...}}]"""


def interpret_query(query: str) -> Optional[InterpretedFilters]:
    """
    Interpret a NL query into structured filters using Gemini.

    Returns None if AI is unavailable or query is uninterpretable.
    """
    from app.services.category_service import category_service
    from app.services.account_service import account_service

    sanitized = sanitize_nl_query(query)
    if not sanitized:
        return None

    # Fetch user's categories and accounts for prompt context
    try:
        categories_raw = category_service.get_all()
        categories = [
            {"id": c.id, "name": c.name, "group": c.group_name.value if hasattr(c.group_name, 'value') else str(c.group_name)}
            for c in categories_raw
        ]
    except Exception:
        categories = []

    try:
        accounts_raw = account_service.get_all()
        accounts = [{"id": a.id, "name": a.name} for a in accounts_raw]
    except Exception:
        accounts = []

    prompt = build_nl_search_prompt(sanitized, categories, accounts, date.today())

    try:
        results = invoke_and_parse(prompt, timeout=NL_SEARCH_TIMEOUT_SECONDS)
    except AIClientError as e:
        logger.warning(f"AI interpretation failed: {e}")
        return None

    if not results:
        return None

    # Extract the first element from the returned list
    raw = results[0]
    if not isinstance(raw, dict):
        return None

    # Lenient validation: silently discard invalid fields
    try:
        # Validate category_ids against actual categories
        valid_category_ids = {c["id"] for c in categories}
        raw_category_ids = raw.get("category_ids")
        if raw_category_ids and isinstance(raw_category_ids, list):
            raw["category_ids"] = [
                cid for cid in raw_category_ids
                if isinstance(cid, str) and cid in valid_category_ids
            ]
            if not raw["category_ids"]:
                del raw["category_ids"]

        # Clamp keyword lists
        for key in ("merchant_keywords", "description_keywords"):
            if key in raw and isinstance(raw[key], list):
                raw[key] = [
                    str(kw)[:100] for kw in raw[key][:10]
                    if kw
                ]
                if not raw[key]:
                    del raw[key]

        return InterpretedFilters(**{
            k: v for k, v in raw.items()
            if k in InterpretedFilters.model_fields
        })
    except Exception as e:
        logger.warning(f"Failed to parse interpreted filters: {e}")
        return None


def merge_filters(
    request: NLSearchRequest,
    interpretation: InterpretedFilters,
) -> TransactionFilters:
    """
    Merge manual filters from the request with AI-interpreted filters.
    Manual filters take precedence on a per-dimension basis.
    """
    # Date dimension: manual wins if either date is set
    if request.date_from is not None or request.date_to is not None:
        date_from = request.date_from
        date_to = request.date_to
    else:
        date_from = interpretation.date_from
        date_to = interpretation.date_to

    # Amount dimension: manual wins if either bound is set
    if request.amount_min is not None or request.amount_max is not None:
        amount_min = request.amount_min
        amount_max = request.amount_max
    else:
        amount_min = interpretation.amount_min
        amount_max = interpretation.amount_max

    # Category: manual wins if set
    if request.category_id is not None:
        category_id = request.category_id
    elif interpretation.category_ids and len(interpretation.category_ids) == 1:
        category_id = interpretation.category_ids[0]
    else:
        category_id = None

    # Build search string from description_keywords for LIKE matching
    search = None
    if interpretation.description_keywords:
        # Use the first keyword as the basic search term
        search = interpretation.description_keywords[0]

    return TransactionFilters(
        account_id=request.account_id,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        reviewed=request.reviewed,
        search=search,
        limit=request.limit,
        offset=request.offset,
    )


def _execute_merchant_keyword_search(
    base_filters: TransactionFilters,
    merchant_keywords: list[str],
    interpretation: InterpretedFilters,
) -> NLSearchResponse:
    """
    Execute search with OR'd LIKE conditions for merchant keywords
    across both description and normalized_merchant columns.
    """
    conditions = []
    params = []

    # Standard filters
    if base_filters.account_id:
        conditions.append("t.account_id = ?")
        params.append(base_filters.account_id)

    if base_filters.category_id:
        if base_filters.category_id == "__uncategorized__":
            conditions.append("t.category_id IS NULL")
        else:
            conditions.append("t.category_id = ?")
            params.append(base_filters.category_id)

    if base_filters.date_from:
        conditions.append("t.date >= ?")
        params.append(base_filters.date_from)

    if base_filters.date_to:
        conditions.append("t.date <= ?")
        params.append(base_filters.date_to)

    if base_filters.amount_min is not None:
        conditions.append("t.amount >= ?")
        params.append(base_filters.amount_min)

    if base_filters.amount_max is not None:
        conditions.append("t.amount <= ?")
        params.append(base_filters.amount_max)

    if base_filters.reviewed is not None:
        conditions.append("t.reviewed = ?")
        params.append(base_filters.reviewed)

    # Merchant keywords: OR'd LIKE on description + normalized_merchant
    keyword_conditions = []
    for kw in merchant_keywords:
        keyword_conditions.append(
            "(LOWER(t.description) LIKE LOWER(?) OR LOWER(t.normalized_merchant) LIKE LOWER(?))"
        )
        params.extend([f"%{kw}%", f"%{kw}%"])

    # Also add description_keywords if present
    if interpretation.description_keywords:
        for kw in interpretation.description_keywords:
            keyword_conditions.append("LOWER(t.description) LIKE LOWER(?)")
            params.append(f"%{kw}%")

    if keyword_conditions:
        conditions.append(f"({' OR '.join(keyword_conditions)})")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Count query
    count_query = f"SELECT COUNT(*) FROM transactions t {where_clause}"
    # We need params without limit/offset for count
    count_params = list(params)

    # Data query
    query = f"""
        SELECT t.id, t.account_id, t.date, t.description, t.original_description,
               t.amount, t.category_id, t.reviewed, t.reviewed_at, t.notes, t.created_at,
               t.normalized_merchant, t.confidence_score, t.categorization_source,
               t.subcategory, t.is_discretionary, t.enrichment_source,
               a.name as account_name,
               c.name as category_name, c.emoji as category_emoji
        FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        {where_clause}
        ORDER BY t.date DESC, t.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([base_filters.limit, base_filters.offset])

    with get_db() as conn:
        total = conn.execute(count_query, count_params).fetchone()[0]
        rows = conn.execute(query, params).fetchall()

    items = [
        TransactionResponse(
            id=row[0], account_id=row[1], date=row[2], description=row[3],
            original_description=row[4], amount=row[5], category_id=row[6],
            reviewed=row[7], reviewed_at=row[8], notes=row[9], created_at=row[10],
            normalized_merchant=row[11], confidence_score=row[12],
            categorization_source=row[13], subcategory=row[14],
            is_discretionary=row[15], enrichment_source=row[16],
            account_name=row[17], category_name=row[18], category_emoji=row[19],
        )
        for row in rows
    ]

    has_more = (base_filters.offset + len(items)) < total

    return NLSearchResponse(
        items=items,
        total=total,
        limit=base_filters.limit,
        offset=base_filters.offset,
        has_more=has_more,
        interpretation=interpretation,
        fallback=False,
        fallback_reason=None,
    )


def execute_nl_search(request: NLSearchRequest) -> NLSearchResponse:
    """
    Orchestrate NL search: interpret query, merge filters, execute search.
    Falls back to basic text search if AI fails.
    """
    from app.services.transaction_service import transaction_service

    interpretation = interpret_query(request.query)

    if interpretation is not None:
        # Check if interpretation is meaningful (at least one non-null filter field)
        has_filters = any([
            interpretation.date_from,
            interpretation.date_to,
            interpretation.amount_min is not None,
            interpretation.amount_max is not None,
            interpretation.category_ids,
            interpretation.merchant_keywords,
            interpretation.description_keywords,
        ])

        if not has_filters:
            # Uninterpretable query — all filter fields are null
            fallback_filters = TransactionFilters(
                account_id=request.account_id,
                category_id=request.category_id,
                date_from=request.date_from,
                date_to=request.date_to,
                amount_min=request.amount_min,
                amount_max=request.amount_max,
                reviewed=request.reviewed,
                search=request.query,
                limit=request.limit,
                offset=request.offset,
            )
            result = transaction_service.get_list(fallback_filters)
            return NLSearchResponse(
                items=result.items,
                total=result.total,
                limit=result.limit,
                offset=result.offset,
                has_more=result.has_more,
                fallback=True,
                fallback_reason="Could not interpret your query. Try something like: 'coffee purchases last month' or 'groceries over $50'.",
            )

        # Merge manual + NL filters
        merged = merge_filters(request, interpretation)

        # If we have merchant keywords, use custom query with OR'd LIKE
        if interpretation.merchant_keywords:
            return _execute_merchant_keyword_search(
                merged, interpretation.merchant_keywords, interpretation,
            )

        # Otherwise use standard transaction service
        result = transaction_service.get_list(merged)
        return NLSearchResponse(
            items=result.items,
            total=result.total,
            limit=result.limit,
            offset=result.offset,
            has_more=result.has_more,
            interpretation=interpretation,
            fallback=False,
            fallback_reason=None,
        )

    # AI failed — fallback to basic text search
    fallback_filters = TransactionFilters(
        account_id=request.account_id,
        category_id=request.category_id,
        date_from=request.date_from,
        date_to=request.date_to,
        amount_min=request.amount_min,
        amount_max=request.amount_max,
        reviewed=request.reviewed,
        search=request.query,
        limit=request.limit,
        offset=request.offset,
    )
    result = transaction_service.get_list(fallback_filters)
    return NLSearchResponse(
        items=result.items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        has_more=result.has_more,
        fallback=True,
        fallback_reason="AI search unavailable — showing basic text results",
    )
