"""
Service for generating AI-powered spending insights.
Aggregates transaction data from DuckDB and uses Gemini for natural language summaries.
"""
import json
import logging
from datetime import date, datetime, timedelta
from calendar import monthrange

from app.database import get_db
from app.models.insights import (
    InsightPeriod,
    CategorySpendingResponse,
    AnomalyResponse,
    InsightResponse,
)

logger = logging.getLogger(__name__)


class InsightsService:

    @staticmethod
    def resolve_period(
        period: InsightPeriod,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[date, date]:
        """Convert period enum to concrete date range."""
        today = date.today()
        if period == InsightPeriod.CUSTOM:
            return (date_from, date_to)  # type: ignore[return-value]
        elif period == InsightPeriod.CURRENT_MONTH:
            start = today.replace(day=1)
            return (start, today)
        elif period == InsightPeriod.LAST_MONTH:
            first_of_current = today.replace(day=1)
            last_month_end = first_of_current - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return (last_month_start, last_month_end)
        elif period == InsightPeriod.LAST_3_MONTHS:
            start = (today.replace(day=1) - timedelta(days=85)).replace(day=1)
            return (start, today)
        raise ValueError(f"Unknown period: {period}")

    @staticmethod
    def _get_previous_period_dates(
        period_start: date, period_end: date
    ) -> tuple[date, date]:
        """Calculate the equivalent prior period for comparison."""
        if period_start.day == 1:
            # Month-based: go back one month
            if period_start.month == 1:
                prev_start = period_start.replace(year=period_start.year - 1, month=12)
            else:
                prev_start = period_start.replace(month=period_start.month - 1)
            _, last_day = monthrange(prev_start.year, prev_start.month)
            prev_end_day = min(period_end.day, last_day)
            prev_end = prev_start.replace(day=prev_end_day)
        else:
            # Custom range: shift back by the same duration
            duration = (period_end - period_start).days
            prev_end = period_start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=duration)
        return (prev_start, prev_end)

    @staticmethod
    def get_category_spending(
        date_from: date, date_to: date
    ) -> list[dict]:
        """Get top 5 categories by spending for a period."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.category_id,
                    c.name AS category_name,
                    c.emoji AS category_emoji,
                    SUM(ABS(t.amount)) AS total_amount_cents,
                    COUNT(*) AS transaction_count
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.date >= ? AND t.date <= ?
                  AND t.amount < 0
                  AND t.category_id IS NOT NULL
                GROUP BY t.category_id, c.name, c.emoji
                ORDER BY total_amount_cents DESC
                LIMIT 5
                """,
                [date_from, date_to],
            ).fetchall()
        return [
            {
                "category_id": r[0],
                "category_name": r[1],
                "category_emoji": r[2],
                "total_amount_cents": int(r[3]),
                "transaction_count": int(r[4]),
            }
            for r in rows
        ]

    @staticmethod
    def get_all_category_spending(
        date_from: date, date_to: date
    ) -> list[dict]:
        """Get all categories by spending for a period (no limit)."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.category_id,
                    c.name AS category_name,
                    c.emoji AS category_emoji,
                    SUM(ABS(t.amount)) AS total_amount_cents,
                    COUNT(*) AS transaction_count
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.date >= ? AND t.date <= ?
                  AND t.amount < 0
                  AND t.category_id IS NOT NULL
                GROUP BY t.category_id, c.name, c.emoji
                ORDER BY total_amount_cents DESC
                """,
                [date_from, date_to],
            ).fetchall()
        return [
            {
                "category_id": r[0],
                "category_name": r[1],
                "category_emoji": r[2],
                "total_amount_cents": int(r[3]),
                "transaction_count": int(r[4]),
            }
            for r in rows
        ]

    @staticmethod
    def get_previous_period_spending(
        current_spending: list[dict],
        prev_start: date,
        prev_end: date,
    ) -> list[dict]:
        """Enrich current spending with previous period comparison data."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.category_id,
                    SUM(ABS(t.amount)) AS total_amount_cents
                FROM transactions t
                WHERE t.date >= ? AND t.date <= ?
                  AND t.amount < 0
                  AND t.category_id IS NOT NULL
                GROUP BY t.category_id
                """,
                [prev_start, prev_end],
            ).fetchall()

        prev_map = {r[0]: int(r[1]) for r in rows}

        enriched = []
        for cat in current_spending:
            prev_amount = prev_map.get(cat["category_id"])
            change_pct = None
            if prev_amount and prev_amount > 0:
                change_pct = round(
                    ((cat["total_amount_cents"] - prev_amount) / prev_amount) * 100, 1
                )
            enriched.append(
                {
                    **cat,
                    "previous_period_amount_cents": prev_amount,
                    "change_percentage": change_pct,
                }
            )
        return enriched

    @staticmethod
    def get_transaction_counts(
        date_from: date, date_to: date
    ) -> dict:
        """Get categorized and uncategorized transaction counts."""
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(CASE WHEN category_id IS NOT NULL AND amount < 0 THEN 1 END) AS categorized,
                    COUNT(CASE WHEN category_id IS NULL AND amount < 0 THEN 1 END) AS uncategorized
                FROM transactions
                WHERE date >= ? AND date <= ?
                """,
                [date_from, date_to],
            ).fetchone()
        return {
            "categorized_count": int(row[0]) if row else 0,
            "uncategorized_count": int(row[1]) if row else 0,
        }

    @staticmethod
    def get_category_averages(
        date_from: date, date_to: date
    ) -> dict[str, dict]:
        """Get average transaction amount per category over a period."""
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.category_id,
                    c.name AS category_name,
                    AVG(ABS(t.amount)) AS avg_amount_cents
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.date >= ? AND t.date <= ?
                  AND t.amount < 0
                  AND t.category_id IS NOT NULL
                GROUP BY t.category_id, c.name
                HAVING COUNT(*) >= 3
                """,
                [date_from, date_to],
            ).fetchall()
        return {
            r[0]: {"category_name": r[1], "avg_amount_cents": int(r[2])}
            for r in rows
        }

    @staticmethod
    def get_anomaly_candidates(
        period_start: date,
        period_end: date,
    ) -> list[dict]:
        """Find transactions exceeding 3x their category average (past 3 months)."""
        # Compute 3-month lookback from period start
        lookback_start = period_start - timedelta(days=90)

        with get_db() as conn:
            rows = conn.execute(
                """
                WITH category_avgs AS (
                    SELECT category_id, AVG(ABS(amount)) AS avg_amount
                    FROM transactions
                    WHERE date >= ? AND date <= ?
                      AND amount < 0
                      AND category_id IS NOT NULL
                    GROUP BY category_id
                    HAVING COUNT(*) >= 3
                )
                SELECT
                    t.id, t.date, t.description, t.normalized_merchant,
                    t.amount, t.category_id,
                    c.name AS category_name,
                    ca.avg_amount AS category_avg,
                    ABS(t.amount) / ca.avg_amount AS deviation_factor
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                JOIN category_avgs ca ON t.category_id = ca.category_id
                WHERE t.date >= ? AND t.date <= ?
                  AND t.amount < 0
                  AND ABS(t.amount) > ca.avg_amount * 3
                ORDER BY deviation_factor DESC
                LIMIT 10
                """,
                [lookback_start, period_end, period_start, period_end],
            ).fetchall()

        return [
            {
                "transaction_id": r[0],
                "transaction_date": r[1],
                "description": r[2],
                "merchant": r[3],
                "amount_cents": abs(int(r[4])),
                "category_name": r[6],
                "category_avg_cents": int(r[7]),
                "deviation_factor": round(float(r[8]), 1),
            }
            for r in rows
        ]

    @staticmethod
    def get_income_totals(date_from: date, date_to: date) -> int:
        """Get total income (positive transactions) for a period."""
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM transactions
                WHERE date >= ? AND date <= ?
                  AND amount > 0
                """,
                [date_from, date_to],
            ).fetchone()
        return int(row[0]) if row else 0

    @staticmethod
    def _format_cents_as_dollars(cents: int) -> str:
        """Format cents as dollar string for prompts."""
        return f"${cents / 100:,.2f}"

    @classmethod
    def _build_summary_prompt(
        cls,
        period_start: date,
        period_end: date,
        total_spending_cents: int,
        categories: list[dict],
        income_cents: int = 0,
        anomalies: list[dict] | None = None,
    ) -> str:
        """Build Gemini prompt from pre-aggregated data."""
        cat_lines = []
        for c in categories:
            line = f"- {c['category_name']}: {cls._format_cents_as_dollars(c['total_amount_cents'])} ({c['transaction_count']} transactions)"
            if c.get("change_percentage") is not None:
                line += f", {c['change_percentage']:+.1f}% vs prior period"
            cat_lines.append(line)

        has_comparison = any(c.get("change_percentage") is not None for c in categories)
        single_category = len(categories) == 1

        prompt = f"""Analyze this spending data and provide a concise, friendly summary.

Period: {period_start} to {period_end}
Total spending: {cls._format_cents_as_dollars(total_spending_cents)}
"""
        if income_cents > 0:
            savings = income_cents - total_spending_cents
            savings_rate = round((savings / income_cents) * 100, 1)
            prompt += f"""Total income: {cls._format_cents_as_dollars(income_cents)}
Net savings: {cls._format_cents_as_dollars(savings)} ({savings_rate}% savings rate)
"""
        prompt += f"""
Top spending categories:
{chr(10).join(cat_lines)}

"""
        if income_cents <= 0:
            prompt += "IMPORTANT: No income data is available. Do NOT invent or estimate income, savings, or savings rates.\n\n"

        if has_comparison:
            prompt += "Include period-over-period comparison insights where changes are notable.\n"
        else:
            prompt += "No prior period data is available for comparison.\n"

        if single_category:
            prompt += "Note: The user has spending in only one category, so skip cross-category comparisons.\n"

        if anomalies:
            anomaly_lines = []
            for a in anomalies:
                anomaly_lines.append(
                    f"- {a['description']}: {cls._format_cents_as_dollars(a['amount_cents'])} "
                    f"in {a['category_name']} (average: {cls._format_cents_as_dollars(a['category_avg_cents'])}, "
                    f"{a['deviation_factor']}x above average)"
                )
            prompt += f"""
Unusual transactions detected:
{chr(10).join(anomaly_lines)}

Provide a brief, plain-English explanation of each anomaly.
"""

        prompt += """
Return a JSON object with these fields:
{
  "summary": "A 2-4 sentence plain-English spending summary",
  "suggestions": ["actionable suggestion 1", "actionable suggestion 2"],
"""
        if anomalies:
            prompt += '  "anomaly_explanations": "Plain-English explanation of the unusual transactions"\n'
        prompt += "}\n"

        return prompt

    @classmethod
    def _build_report_prompt(
        cls,
        period_start: date,
        period_end: date,
        total_spending_cents: int,
        categories: list[dict],
        income_cents: int = 0,
        anomalies: list[dict] | None = None,
    ) -> str:
        """Build a richer Gemini prompt for a full monthly report."""
        cat_lines = []
        for c in categories:
            line = f"- {c['category_name']}: {cls._format_cents_as_dollars(c['total_amount_cents'])} ({c['transaction_count']} transactions)"
            if c.get("change_percentage") is not None:
                line += f", {c['change_percentage']:+.1f}% vs prior period"
            cat_lines.append(line)

        prompt = f"""Generate a comprehensive monthly financial health report.

Period: {period_start} to {period_end}
Total spending: {cls._format_cents_as_dollars(total_spending_cents)}
"""
        if income_cents > 0:
            savings = income_cents - total_spending_cents
            savings_rate = round((savings / income_cents) * 100, 1)
            prompt += f"""Total income: {cls._format_cents_as_dollars(income_cents)}
Net savings: {cls._format_cents_as_dollars(savings)} ({savings_rate}% savings rate)
"""
        prompt += f"""
All spending categories:
{chr(10).join(cat_lines)}

"""
        if income_cents <= 0:
            prompt += "IMPORTANT: No income data is available. Do NOT invent or estimate income, savings, or savings rates.\n\n"


        if anomalies:
            anomaly_lines = []
            for a in anomalies:
                anomaly_lines.append(
                    f"- {a['description']}: {cls._format_cents_as_dollars(a['amount_cents'])} "
                    f"in {a['category_name']} ({a['deviation_factor']}x above average)"
                )
            prompt += f"""Unusual transactions:
{chr(10).join(anomaly_lines)}

"""
        prompt += """Provide a detailed financial health report with actionable recommendations.

Return a JSON object with these fields:
{
  "summary": "A comprehensive 4-6 sentence financial health overview including income, expenses, and savings",
  "suggestions": ["actionable recommendation 1", "actionable recommendation 2", "actionable recommendation 3"]"""

        if anomalies:
            prompt += ',\n  "anomaly_explanations": "Plain-English explanation of the unusual transactions"'
        prompt += "\n}\n"

        return prompt

    @classmethod
    def generate_summary(
        cls,
        period: InsightPeriod,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> InsightResponse:
        """Generate a spending summary using aggregated data + Gemini."""
        from app.services.gemini_client import invoke_gemini, with_retry, AIClientError

        period_start, period_end = cls.resolve_period(period, date_from, date_to)

        # Check data sufficiency
        counts = cls.get_transaction_counts(period_start, period_end)
        categorized = counts["categorized_count"]
        uncategorized = counts["uncategorized_count"]

        if categorized < 5:
            return InsightResponse(
                period_start=period_start,
                period_end=period_end,
                total_spending_cents=0,
                total_transactions=categorized,
                uncategorized_count=uncategorized,
                generated_at=datetime.utcnow(),
                insufficient_data=True,
                insufficient_data_message=(
                    f"You have only {categorized} categorized transaction{'s' if categorized != 1 else ''} "
                    f"this period. We need at least 5 to generate meaningful insights. "
                    f"Try selecting a wider date range or keep adding transactions."
                ),
            )

        # Aggregate data
        categories = cls.get_category_spending(period_start, period_end)
        total_spending = sum(c["total_amount_cents"] for c in categories)

        # Previous period comparison
        prev_start, prev_end = cls._get_previous_period_dates(period_start, period_end)
        categories = cls.get_previous_period_spending(categories, prev_start, prev_end)

        # Anomaly detection
        anomalies = cls.get_anomaly_candidates(period_start, period_end)
        income_cents = cls.get_income_totals(period_start, period_end)

        # Build prompt and call Gemini
        prompt = cls._build_summary_prompt(
            period_start, period_end, total_spending, categories, income_cents, anomalies or None
        )

        try:
            raw_response = with_retry(invoke_gemini, prompt)
            parsed = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
            if isinstance(parsed, list) and len(parsed) > 0:
                parsed = parsed[0]

            summary_text = parsed.get("summary") if isinstance(parsed, dict) else None
            suggestions = parsed.get("suggestions", []) if isinstance(parsed, dict) else []
            anomaly_explanations = parsed.get("anomaly_explanations") if isinstance(parsed, dict) else None

            if not summary_text:
                # Fallback: build summary from raw data
                summary_text = cls._build_fallback_summary(total_spending, categories)

        except (AIClientError, Exception) as e:
            logger.warning(f"Gemini call failed, using fallback summary: {e}")
            summary_text = cls._build_fallback_summary(total_spending, categories)
            suggestions = []
            anomaly_explanations = None

        # Add uncategorized warning to suggestions
        if uncategorized > 0:
            total_txns = categorized + uncategorized
            if categorized == 0:
                suggestions.insert(
                    0,
                    "All your transactions are uncategorized. Categorize them to get better insights.",
                )
            elif uncategorized / total_txns > 0.2:
                suggestions.append(
                    f"You have {uncategorized} uncategorized transaction{'s' if uncategorized != 1 else ''}. "
                    f"Categorizing them will improve future insights."
                )

        top_categories = [
            CategorySpendingResponse(**c) for c in categories
        ]

        anomaly_responses = [
            AnomalyResponse(**a) for a in anomalies
        ]

        return InsightResponse(
            period_start=period_start,
            period_end=period_end,
            total_spending_cents=total_spending,
            total_transactions=categorized,
            uncategorized_count=uncategorized,
            summary=summary_text,
            top_categories=top_categories,
            anomalies=anomaly_responses,
            anomaly_explanations=anomaly_explanations,
            suggestions=suggestions,
            generated_at=datetime.utcnow(),
        )

    @classmethod
    def generate_report(
        cls,
        period: InsightPeriod,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> InsightResponse:
        """Generate a comprehensive monthly financial health report."""
        from app.services.gemini_client import invoke_gemini, with_retry, AIClientError

        period_start, period_end = cls.resolve_period(period, date_from, date_to)

        counts = cls.get_transaction_counts(period_start, period_end)
        categorized = counts["categorized_count"]
        uncategorized = counts["uncategorized_count"]

        if categorized < 5:
            return InsightResponse(
                period_start=period_start,
                period_end=period_end,
                total_spending_cents=0,
                total_transactions=categorized,
                uncategorized_count=uncategorized,
                generated_at=datetime.utcnow(),
                insufficient_data=True,
                insufficient_data_message=(
                    f"You have only {categorized} categorized transaction{'s' if categorized != 1 else ''} "
                    f"this period. We need at least 5 to generate a comprehensive report. "
                    f"Try selecting a wider date range or keep adding transactions."
                ),
            )

        # Use all categories for report (not just top 5)
        all_categories = cls.get_all_category_spending(period_start, period_end)
        total_spending = sum(c["total_amount_cents"] for c in all_categories)

        prev_start, prev_end = cls._get_previous_period_dates(period_start, period_end)
        all_categories = cls.get_previous_period_spending(all_categories, prev_start, prev_end)

        anomalies = cls.get_anomaly_candidates(period_start, period_end)
        income_cents = cls.get_income_totals(period_start, period_end)

        prompt = cls._build_report_prompt(
            period_start, period_end, total_spending,
            all_categories, income_cents, anomalies or None,
        )

        try:
            raw_response = with_retry(invoke_gemini, prompt)
            parsed = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
            if isinstance(parsed, list) and len(parsed) > 0:
                parsed = parsed[0]

            summary_text = parsed.get("summary") if isinstance(parsed, dict) else None
            suggestions = parsed.get("suggestions", []) if isinstance(parsed, dict) else []
            anomaly_explanations = parsed.get("anomaly_explanations") if isinstance(parsed, dict) else None

            if not summary_text:
                summary_text = cls._build_fallback_summary(total_spending, all_categories[:5])

        except (AIClientError, Exception) as e:
            logger.warning(f"Gemini call failed for report, using fallback: {e}")
            summary_text = cls._build_fallback_summary(total_spending, all_categories[:5])
            suggestions = []
            anomaly_explanations = None

        if uncategorized > 0:
            total_txns = categorized + uncategorized
            if categorized == 0:
                suggestions.insert(
                    0,
                    "All your transactions are uncategorized. Categorize them to get better insights.",
                )
            elif uncategorized / total_txns > 0.2:
                suggestions.append(
                    f"You have {uncategorized} uncategorized transaction{'s' if uncategorized != 1 else ''}. "
                    f"Categorizing them will improve future insights."
                )

        # Return top 5 for the response (full list was used in the prompt)
        top_categories = [
            CategorySpendingResponse(**c) for c in all_categories[:5]
        ]

        anomaly_responses = [
            AnomalyResponse(**a) for a in anomalies
        ]

        return InsightResponse(
            period_start=period_start,
            period_end=period_end,
            total_spending_cents=total_spending,
            total_transactions=categorized,
            uncategorized_count=uncategorized,
            summary=summary_text,
            top_categories=top_categories,
            anomalies=anomaly_responses,
            anomaly_explanations=anomaly_explanations,
            suggestions=suggestions,
            generated_at=datetime.utcnow(),
        )

    @staticmethod
    def _build_fallback_summary(total_spending_cents: int, categories: list[dict]) -> str:
        """Build a basic summary without AI when Gemini is unavailable."""
        total_dollars = f"${total_spending_cents / 100:,.2f}"
        if not categories:
            return f"You've spent {total_dollars} this period."

        top = categories[0]
        top_dollars = f"${top['total_amount_cents'] / 100:,.2f}"
        summary = (
            f"You've spent {total_dollars} this period across {len(categories)} "
            f"{'category' if len(categories) == 1 else 'categories'}. "
            f"Your {'only' if len(categories) == 1 else 'top'} spending category is "
            f"{top['category_name']} at {top_dollars}."
        )
        return summary
