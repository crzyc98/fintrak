import json
import uuid
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountType,
    ASSET_ACCOUNT_TYPES,
)
from app.models.csv_import import CsvColumnMapping


class AccountService:
    def create(self, data: AccountCreate) -> AccountResponse:
        account_id = str(uuid.uuid4())
        is_asset = data.type in ASSET_ACCOUNT_TYPES
        created_at = datetime.utcnow()

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO accounts (id, name, type, institution, is_asset, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [account_id, data.name, data.type.value, data.institution, is_asset, created_at],
            )

        return AccountResponse(
            id=account_id,
            name=data.name,
            type=data.type,
            institution=data.institution,
            is_asset=is_asset,
            current_balance=None,
            created_at=created_at,
        )

    def _parse_csv_mapping(self, mapping_json) -> Optional[CsvColumnMapping]:
        if mapping_json is None:
            return None
        if isinstance(mapping_json, str):
            mapping_json = json.loads(mapping_json)
        if isinstance(mapping_json, dict):
            return CsvColumnMapping(**mapping_json)
        return None

    def get_all(self) -> list[AccountResponse]:
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT a.id, a.name, a.type, a.institution, a.is_asset, a.created_at,
                       a.csv_column_mapping,
                       (SELECT bs.balance
                        FROM balance_snapshots bs
                        WHERE bs.account_id = a.id
                        ORDER BY bs.snapshot_date DESC, bs.created_at DESC
                        LIMIT 1) as current_balance
                FROM accounts a
                ORDER BY a.type, a.name
                """
            ).fetchall()

        return [
            AccountResponse(
                id=row[0],
                name=row[1],
                type=AccountType(row[2]),
                institution=row[3],
                is_asset=row[4],
                created_at=row[5],
                csv_column_mapping=self._parse_csv_mapping(row[6]),
                current_balance=row[7],
            )
            for row in result
        ]

    def get_by_id(self, account_id: str) -> Optional[AccountResponse]:
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT a.id, a.name, a.type, a.institution, a.is_asset, a.created_at,
                       a.csv_column_mapping,
                       (SELECT bs.balance
                        FROM balance_snapshots bs
                        WHERE bs.account_id = a.id
                        ORDER BY bs.snapshot_date DESC, bs.created_at DESC
                        LIMIT 1) as current_balance
                FROM accounts a
                WHERE a.id = ?
                """,
                [account_id],
            ).fetchone()

        if not result:
            return None

        return AccountResponse(
            id=result[0],
            name=result[1],
            type=AccountType(result[2]),
            institution=result[3],
            is_asset=result[4],
            created_at=result[5],
            csv_column_mapping=self._parse_csv_mapping(result[6]),
            current_balance=result[7],
        )

    def update(self, account_id: str, data: AccountUpdate) -> Optional[AccountResponse]:
        existing = self.get_by_id(account_id)
        if not existing:
            return None

        updates = []
        values = []

        if data.name is not None:
            updates.append("name = ?")
            values.append(data.name)

        if data.type is not None:
            updates.append("type = ?")
            values.append(data.type.value)
            updates.append("is_asset = ?")
            values.append(data.type in ASSET_ACCOUNT_TYPES)

        if data.institution is not None:
            updates.append("institution = ?")
            values.append(data.institution)

        if data.csv_column_mapping is not None:
            updates.append("csv_column_mapping = ?")
            values.append(data.csv_column_mapping.model_dump_json())

        if not updates:
            return existing

        values.append(account_id)

        with get_db() as conn:
            conn.execute(
                f"UPDATE accounts SET {', '.join(updates)} WHERE id = ?",
                values,
            )

        return self.get_by_id(account_id)

    def update_csv_mapping(self, account_id: str, mapping: Optional[CsvColumnMapping]) -> Optional[AccountResponse]:
        existing = self.get_by_id(account_id)
        if not existing:
            return None

        mapping_json = mapping.model_dump_json() if mapping else None

        with get_db() as conn:
            conn.execute(
                "UPDATE accounts SET csv_column_mapping = ? WHERE id = ?",
                [mapping_json, account_id],
            )

        return self.get_by_id(account_id)

    def delete(self, account_id: str) -> tuple[bool, Optional[str]]:
        existing = self.get_by_id(account_id)
        if not existing:
            return False, "Account not found"

        with get_db() as conn:
            transaction_count = conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE account_id = ?",
                [account_id],
            ).fetchone()[0]

            if transaction_count > 0:
                return False, f"Cannot delete account: {transaction_count} transaction(s) exist"

            snapshot_count = conn.execute(
                "SELECT COUNT(*) FROM balance_snapshots WHERE account_id = ?",
                [account_id],
            ).fetchone()[0]

            if snapshot_count > 0:
                return False, f"Cannot delete account: {snapshot_count} balance snapshot(s) exist"

            conn.execute("DELETE FROM accounts WHERE id = ?", [account_id])

        return True, None

    def get_latest_balance(self, account_id: str) -> Optional[int]:
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT balance FROM balance_snapshots
                WHERE account_id = ?
                ORDER BY snapshot_date DESC, created_at DESC
                LIMIT 1
                """,
                [account_id],
            ).fetchone()

        return result[0] if result else None


account_service = AccountService()
