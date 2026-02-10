"""
Service for tracking categorization batch processing.
Provides functions to create, update, and query batch records.
"""
import uuid
import logging
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.categorization import (
    CategorizationBatchResponse,
    CategorizationBatchListResponse,
)

logger = logging.getLogger(__name__)


class BatchService:
    """Service for managing categorization batch records."""

    def create_batch(
        self,
        import_id: Optional[str] = None,
        transaction_count: int = 0,
    ) -> str:
        """
        Create a new categorization batch record.

        Args:
            import_id: Optional import ID this batch is associated with
            transaction_count: Initial count of transactions to process

        Returns:
            The new batch ID
        """
        batch_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO categorization_batches (
                    id, import_id, transaction_count, success_count, failure_count,
                    rule_match_count, desc_rule_match_count, ai_match_count, skipped_count,
                    duration_ms, error_message, started_at, completed_at
                )
                VALUES (?, ?, ?, 0, 0, 0, 0, 0, 0, NULL, NULL, ?, NULL)
                """,
                [batch_id, import_id, transaction_count, started_at],
            )

        logger.info(
            f"Created batch {batch_id} for {transaction_count} transactions"
        )
        return batch_id

    def update_batch(
        self,
        batch_id: str,
        success_count: Optional[int] = None,
        failure_count: Optional[int] = None,
        rule_match_count: Optional[int] = None,
        desc_rule_match_count: Optional[int] = None,
        ai_match_count: Optional[int] = None,
        skipped_count: Optional[int] = None,
    ) -> None:
        """
        Update batch counters during processing.

        Args:
            batch_id: The batch ID to update
            success_count: New success count (or None to keep current)
            failure_count: New failure count
            rule_match_count: New rule match count
            desc_rule_match_count: New description rule match count
            ai_match_count: New AI match count
            skipped_count: New skipped count
        """
        updates = []
        values = []

        if success_count is not None:
            updates.append("success_count = ?")
            values.append(success_count)
        if failure_count is not None:
            updates.append("failure_count = ?")
            values.append(failure_count)
        if rule_match_count is not None:
            updates.append("rule_match_count = ?")
            values.append(rule_match_count)
        if desc_rule_match_count is not None:
            updates.append("desc_rule_match_count = ?")
            values.append(desc_rule_match_count)
        if ai_match_count is not None:
            updates.append("ai_match_count = ?")
            values.append(ai_match_count)
        if skipped_count is not None:
            updates.append("skipped_count = ?")
            values.append(skipped_count)

        if not updates:
            return

        values.append(batch_id)

        with get_db() as conn:
            conn.execute(
                f"UPDATE categorization_batches SET {', '.join(updates)} WHERE id = ?",
                values,
            )

    def complete_batch(
        self,
        batch_id: str,
        success_count: int,
        failure_count: int,
        rule_match_count: int,
        desc_rule_match_count: int,
        ai_match_count: int,
        skipped_count: int,
        error_message: Optional[str] = None,
    ) -> Optional[CategorizationBatchResponse]:
        """
        Mark a batch as complete with final metrics.

        Args:
            batch_id: The batch ID to complete
            success_count: Final success count
            failure_count: Final failure count
            rule_match_count: Final merchant rule match count
            desc_rule_match_count: Final description rule match count
            ai_match_count: Final AI match count
            skipped_count: Final skipped count
            error_message: Optional error message if batch failed

        Returns:
            The completed batch record, or None if not found
        """
        completed_at = datetime.utcnow()

        with get_db() as conn:
            # Get started_at to calculate duration
            result = conn.execute(
                "SELECT started_at FROM categorization_batches WHERE id = ?",
                [batch_id],
            ).fetchone()

            if not result:
                logger.warning(f"Batch {batch_id} not found for completion")
                return None

            started_at = result[0]
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))

            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            conn.execute(
                """
                UPDATE categorization_batches
                SET success_count = ?,
                    failure_count = ?,
                    rule_match_count = ?,
                    desc_rule_match_count = ?,
                    ai_match_count = ?,
                    skipped_count = ?,
                    duration_ms = ?,
                    error_message = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                [
                    success_count,
                    failure_count,
                    rule_match_count,
                    desc_rule_match_count,
                    ai_match_count,
                    skipped_count,
                    duration_ms,
                    error_message,
                    completed_at,
                    batch_id,
                ],
            )

        logger.info(
            f"Completed batch {batch_id}: "
            f"{success_count} success, {failure_count} failed, "
            f"{rule_match_count} merchant rules, {desc_rule_match_count} desc rules, "
            f"{ai_match_count} AI, {skipped_count} skipped in {duration_ms}ms"
        )

        return self.get_by_id(batch_id)

    def get_by_id(self, batch_id: str) -> Optional[CategorizationBatchResponse]:
        """Get a batch by ID."""
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT id, import_id, transaction_count, success_count, failure_count,
                       rule_match_count, desc_rule_match_count, ai_match_count, skipped_count,
                       duration_ms, error_message, started_at, completed_at
                FROM categorization_batches
                WHERE id = ?
                """,
                [batch_id],
            ).fetchone()

        if not result:
            return None

        return CategorizationBatchResponse(
            id=result[0],
            import_id=result[1],
            transaction_count=result[2],
            success_count=result[3],
            failure_count=result[4],
            rule_match_count=result[5],
            desc_rule_match_count=result[6],
            ai_match_count=result[7],
            skipped_count=result[8],
            duration_ms=result[9],
            error_message=result[10],
            started_at=result[11],
            completed_at=result[12],
        )

    def get_list(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> CategorizationBatchListResponse:
        """
        Get paginated list of batches.

        Args:
            limit: Maximum number of batches to return
            offset: Number of batches to skip

        Returns:
            Paginated list response
        """
        with get_db() as conn:
            # Get total count
            count_result = conn.execute(
                "SELECT COUNT(*) FROM categorization_batches"
            ).fetchone()
            total = count_result[0] if count_result else 0

            # Get batches
            result = conn.execute(
                """
                SELECT id, import_id, transaction_count, success_count, failure_count,
                       rule_match_count, desc_rule_match_count, ai_match_count, skipped_count,
                       duration_ms, error_message, started_at, completed_at
                FROM categorization_batches
                ORDER BY started_at DESC
                LIMIT ? OFFSET ?
                """,
                [limit, offset],
            ).fetchall()

        batches = [
            CategorizationBatchResponse(
                id=row[0],
                import_id=row[1],
                transaction_count=row[2],
                success_count=row[3],
                failure_count=row[4],
                rule_match_count=row[5],
                desc_rule_match_count=row[6],
                ai_match_count=row[7],
                skipped_count=row[8],
                duration_ms=row[9],
                error_message=row[10],
                started_at=row[11],
                completed_at=row[12],
            )
            for row in result
        ]

        has_more = (offset + len(batches)) < total

        return CategorizationBatchListResponse(
            batches=batches,
            total=total,
            has_more=has_more,
        )


batch_service = BatchService()
