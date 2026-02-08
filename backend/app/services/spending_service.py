from datetime import date
from calendar import monthrange

from app.database import get_db
from app.models.transaction import MonthlySpendingResponse, SpendingDataPoint


class SpendingService:
    def get_monthly_spending(self) -> MonthlySpendingResponse:
        """
        Get monthly spending data for the dashboard chart.

        Returns cumulative daily spending for the current month,
        with pace line and comparison to last month.
        """
        today = date.today()
        current_year = today.year
        current_month = today.month
        current_day = today.day

        # Calculate first/last day of current month
        first_of_month = date(current_year, current_month, 1)
        days_in_month = monthrange(current_year, current_month)[1]
        last_of_month = date(current_year, current_month, days_in_month)

        # Calculate last month's range
        if current_month == 1:
            last_month = 12
            last_month_year = current_year - 1
        else:
            last_month = current_month - 1
            last_month_year = current_year

        first_of_last_month = date(last_month_year, last_month, 1)
        days_in_last_month = monthrange(last_month_year, last_month)[1]
        last_of_last_month = date(last_month_year, last_month, days_in_last_month)

        # For comparison: same day in last month (or last day if month is shorter)
        same_day_last_month = min(current_day, days_in_last_month)
        last_month_comparison_date = date(last_month_year, last_month, same_day_last_month)

        with get_db() as conn:
            # Get daily spending for current month (only expenses, i.e., negative amounts)
            daily_spending = conn.execute(
                """
                SELECT
                    EXTRACT(DAY FROM date) as day,
                    SUM(ABS(amount)) as daily_total
                FROM transactions
                WHERE date >= ? AND date <= ?
                AND amount < 0
                GROUP BY EXTRACT(DAY FROM date)
                ORDER BY day
                """,
                [first_of_month, last_of_month],
            ).fetchall()

            # Get total spending for last month
            last_month_result = conn.execute(
                """
                SELECT COALESCE(SUM(ABS(amount)), 0) as total
                FROM transactions
                WHERE date >= ? AND date <= ?
                AND amount < 0
                """,
                [first_of_last_month, last_of_last_month],
            ).fetchone()
            last_month_total = int(last_month_result[0]) if last_month_result else 0

            # Get spending up to same point last month
            last_month_same_point_result = conn.execute(
                """
                SELECT COALESCE(SUM(ABS(amount)), 0) as total
                FROM transactions
                WHERE date >= ? AND date <= ?
                AND amount < 0
                """,
                [first_of_last_month, last_month_comparison_date],
            ).fetchone()
            last_month_same_point = int(last_month_same_point_result[0]) if last_month_same_point_result else 0

        # Build daily totals map
        daily_totals = {int(row[0]): int(row[1]) for row in daily_spending}

        # Calculate cumulative spending by day
        chart_data = [SpendingDataPoint(day=0, amount=0, pace=0)]
        cumulative = 0

        # Use last month's total as the expected pace for this month
        # If no last month data, use a reasonable default or current month's projection
        expected_monthly_total = last_month_total if last_month_total > 0 else 0

        for day in range(1, current_day + 1):
            cumulative += daily_totals.get(day, 0)
            # Linear pace: expected_monthly_total * (day / days_in_month)
            pace = int(expected_monthly_total * day / days_in_month) if expected_monthly_total > 0 else 0
            chart_data.append(SpendingDataPoint(day=day, amount=cumulative, pace=pace))

        # Month label
        month_names = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        month_label = f"{month_names[current_month]} {current_year}"

        return MonthlySpendingResponse(
            chart_data=chart_data,
            current_month_total=cumulative,
            last_month_total=last_month_total,
            last_month_same_point=last_month_same_point,
            days_in_month=days_in_month,
            current_day=current_day,
            month_label=month_label,
        )


spending_service = SpendingService()
