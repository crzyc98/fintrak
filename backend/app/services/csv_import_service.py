import base64
import csv
import io
import re
import uuid
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.csv_import import (
    AmountMode,
    CsvColumnMapping,
    CsvPreviewRequest,
    CsvPreviewResponse,
    CsvParseRequest,
    CsvParseResponse,
    ParsedTransaction,
    BulkTransactionCreateRequest,
    BulkTransactionCreateResponse,
)
from app.services.account_service import account_service


# Common column name patterns for auto-detection
DATE_PATTERNS = ['date', 'transaction date', 'trans date', 'posted date', 'post date']
DESCRIPTION_PATTERNS = ['description', 'memo', 'narrative', 'details', 'transaction', 'payee']
AMOUNT_PATTERNS = ['amount', 'sum', 'value', 'total']
DEBIT_PATTERNS = ['debit', 'withdrawal', 'out', 'expense']
CREDIT_PATTERNS = ['credit', 'deposit', 'in', 'income']
CATEGORY_PATTERNS = ['category', 'type', 'classification', 'group', 'class']

# Supported date formats with Python strptime equivalents
DATE_FORMATS = {
    'YYYY-MM-DD': '%Y-%m-%d',
    'MM/DD/YYYY': '%m/%d/%Y',
    'DD/MM/YYYY': '%d/%m/%Y',
    'MM-DD-YYYY': '%m-%d-%Y',
    'DD-MM-YYYY': '%d-%m-%Y',
    'M/D/YYYY': '%m/%d/%Y',
    'D/M/YYYY': '%d/%m/%Y',
}


class CsvImportService:
    def _decode_csv(self, file_content: str) -> str:
        try:
            decoded = base64.b64decode(file_content)
            # Try UTF-8 first, then fallback to latin-1
            try:
                return decoded.decode('utf-8')
            except UnicodeDecodeError:
                return decoded.decode('latin-1')
        except Exception as e:
            raise ValueError(f"Invalid base64 content: {str(e)}")

    def _detect_delimiter(self, content: str) -> str:
        first_line = content.split('\n')[0]
        delimiters = [',', ';', '\t']
        counts = {d: first_line.count(d) for d in delimiters}
        return max(counts, key=counts.get) if max(counts.values()) > 0 else ','

    def _match_column(self, header: str, patterns: list[str]) -> bool:
        header_lower = header.lower().strip()
        return any(pattern in header_lower for pattern in patterns)

    def _get_category_map(self) -> dict[str, tuple[str, str, str | None]]:
        """Returns a dict mapping lowercase category names to (id, name, emoji)."""
        with get_db() as conn:
            result = conn.execute(
                "SELECT id, name, emoji FROM categories"
            ).fetchall()
        return {row[1].lower(): (row[0], row[1], row[2]) for row in result}

    def _auto_detect_mapping(self, headers: list[str]) -> Optional[CsvColumnMapping]:
        date_col = None
        desc_col = None
        amount_col = None
        debit_col = None
        credit_col = None
        category_col = None

        for header in headers:
            header_lower = header.lower().strip()
            if date_col is None and self._match_column(header, DATE_PATTERNS):
                date_col = header
            elif desc_col is None and self._match_column(header, DESCRIPTION_PATTERNS):
                desc_col = header
            elif amount_col is None and self._match_column(header, AMOUNT_PATTERNS):
                amount_col = header
            elif debit_col is None and self._match_column(header, DEBIT_PATTERNS):
                debit_col = header
            elif credit_col is None and self._match_column(header, CREDIT_PATTERNS):
                credit_col = header
            elif category_col is None and self._match_column(header, CATEGORY_PATTERNS):
                category_col = header

        # Need at least date and description
        if not date_col or not desc_col:
            return None

        # Prefer single amount column, fallback to debit/credit
        if amount_col:
            return CsvColumnMapping(
                date_column=date_col,
                description_column=desc_col,
                amount_mode=AmountMode.SINGLE,
                amount_column=amount_col,
                date_format='YYYY-MM-DD',
                category_column=category_col,
            )
        elif debit_col and credit_col:
            return CsvColumnMapping(
                date_column=date_col,
                description_column=desc_col,
                amount_mode=AmountMode.SPLIT,
                debit_column=debit_col,
                credit_column=credit_col,
                date_format='YYYY-MM-DD',
                category_column=category_col,
            )

        return None

    def preview_csv(self, request: CsvPreviewRequest) -> CsvPreviewResponse:
        content = self._decode_csv(request.file_content)

        if not content.strip():
            raise ValueError("CSV file is empty")

        delimiter = self._detect_delimiter(content)
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)

        rows = list(reader)
        if len(rows) == 0:
            raise ValueError("CSV file has no data")

        headers = rows[0]
        data_rows = rows[1:]

        sample_rows = data_rows[:5]
        suggested_mapping = self._auto_detect_mapping(headers)

        return CsvPreviewResponse(
            headers=headers,
            sample_rows=sample_rows,
            row_count=len(data_rows),
            suggested_mapping=suggested_mapping,
        )

    def _parse_date(self, date_str: str, date_format: str) -> Optional[str]:
        strptime_format = DATE_FORMATS.get(date_format)
        if not strptime_format:
            strptime_format = DATE_FORMATS['YYYY-MM-DD']

        # Handle flexible parsing for M/D/YYYY and D/M/YYYY formats
        date_str = date_str.strip()

        try:
            parsed = datetime.strptime(date_str, strptime_format)
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            # Try alternative formats
            for fmt_name, fmt in DATE_FORMATS.items():
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    return parsed.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None

    def _parse_amount(self, amount_str: str) -> Optional[int]:
        if not amount_str or not amount_str.strip():
            return 0

        # Remove currency symbols, spaces, and handle parentheses for negative
        amount_str = amount_str.strip()
        is_negative = amount_str.startswith('(') and amount_str.endswith(')')
        amount_str = re.sub(r'[^\d.,\-]', '', amount_str)

        if not amount_str:
            return 0

        # Handle different decimal separators
        # If both comma and period present, last one is decimal
        if ',' in amount_str and '.' in amount_str:
            if amount_str.rfind(',') > amount_str.rfind('.'):
                amount_str = amount_str.replace('.', '').replace(',', '.')
            else:
                amount_str = amount_str.replace(',', '')
        elif ',' in amount_str:
            # Could be decimal comma (1.234,56) or thousands (1,234)
            parts = amount_str.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                amount_str = amount_str.replace(',', '.')
            else:
                amount_str = amount_str.replace(',', '')

        try:
            amount = float(amount_str)
            if is_negative:
                amount = -abs(amount)
            return int(amount * 100)
        except ValueError:
            return None

    def _get_existing_transactions(self, account_id: str) -> set[tuple]:
        with get_db() as conn:
            result = conn.execute(
                """
                SELECT date, description, amount
                FROM transactions
                WHERE account_id = ?
                """,
                [account_id],
            ).fetchall()

        return {(str(row[0]), row[1], row[2]) for row in result}

    def parse_csv(self, request: CsvParseRequest) -> CsvParseResponse:
        content = self._decode_csv(request.file_content)

        if not content.strip():
            raise ValueError("CSV file is empty")

        delimiter = self._detect_delimiter(content)
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

        mapping = request.mapping
        existing = self._get_existing_transactions(request.account_id)

        # Build category lookup if category column is mapped
        category_map: dict[str, tuple[str, str, str | None]] = {}
        if mapping.category_column:
            category_map = self._get_category_map()

        transactions = []
        valid_count = 0
        warning_count = 0
        error_count = 0
        unmatched_categories: set[str] = set()

        for row_num, row in enumerate(reader, start=2):
            date_str = row.get(mapping.date_column, '').strip()
            description = row.get(mapping.description_column, '').strip()

            # Parse amount based on mode
            if mapping.amount_mode == AmountMode.SINGLE:
                amount_str = row.get(mapping.amount_column, '').strip()
                amount = self._parse_amount(amount_str)
            else:
                debit_str = row.get(mapping.debit_column, '').strip()
                credit_str = row.get(mapping.credit_column, '').strip()
                debit = self._parse_amount(debit_str) or 0
                credit = self._parse_amount(credit_str) or 0
                # Debit is negative (money out), credit is positive (money in)
                amount = credit - abs(debit)

            # Parse date
            parsed_date = self._parse_date(date_str, mapping.date_format)

            # Extract and match category
            csv_category = None
            category_id = None
            category_name = None
            category_emoji = None

            if mapping.category_column:
                csv_category = row.get(mapping.category_column, '').strip()
                if csv_category:
                    category_lower = csv_category.lower()
                    if category_lower in category_map:
                        category_id, category_name, category_emoji = category_map[category_lower]
                    else:
                        unmatched_categories.add(csv_category)

            # Determine status
            status = "valid"
            status_reason = None

            if not parsed_date:
                status = "error"
                status_reason = f"Invalid date: {date_str}"
            elif amount is None:
                status = "error"
                status_reason = "Invalid amount"
            elif not description:
                status = "error"
                status_reason = "Missing description"
            else:
                # Check for duplicates
                tx_key = (parsed_date, description, amount)
                if tx_key in existing:
                    status = "warning"
                    status_reason = "Potential duplicate"

            if status == "valid":
                valid_count += 1
            elif status == "warning":
                warning_count += 1
            else:
                error_count += 1

            transactions.append(ParsedTransaction(
                row_number=row_num,
                date=parsed_date or date_str,
                description=description,
                amount=amount or 0,
                status=status,
                status_reason=status_reason,
                csv_category=csv_category,
                category_id=category_id,
                category_name=category_name,
                category_emoji=category_emoji,
            ))

        return CsvParseResponse(
            transactions=transactions,
            valid_count=valid_count,
            warning_count=warning_count,
            error_count=error_count,
            unmatched_categories=sorted(unmatched_categories),
        )

    def create_transactions(self, request: BulkTransactionCreateRequest) -> BulkTransactionCreateResponse:
        # Filter to only valid and warning transactions (user chose to include warnings)
        transactions_to_create = [
            t for t in request.transactions
            if t.status in ("valid", "warning")
        ]

        if not transactions_to_create:
            return BulkTransactionCreateResponse(
                created_count=0,
                account_id=request.account_id,
            )

        with get_db() as conn:
            for tx in transactions_to_create:
                tx_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO transactions (
                        id, account_id, date, description, original_description,
                        amount, category_id, categorization_source, reviewed, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        tx_id,
                        request.account_id,
                        tx.date,
                        tx.description,
                        tx.description,
                        tx.amount,
                        tx.category_id,
                        'import' if tx.category_id else None,
                        False,
                        datetime.utcnow(),
                    ],
                )

        # Save mapping if requested
        if request.save_mapping and request.mapping:
            account_service.update_csv_mapping(request.account_id, request.mapping)

        return BulkTransactionCreateResponse(
            created_count=len(transactions_to_create),
            account_id=request.account_id,
        )


csv_import_service = CsvImportService()
