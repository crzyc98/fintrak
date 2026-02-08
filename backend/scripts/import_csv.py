#!/usr/bin/env python3
"""
Import transactions from CSV file.

Usage:
    python scripts/import_csv.py <csv_file> <account_id> [--format chase|bank_of_america|generic]

Example:
    python scripts/import_csv.py ~/Downloads/transactions.csv acc-123 --format chase
"""

import argparse
import csv
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, get_db
from app.services.transaction_service import transaction_service
from app.services.account_service import account_service
from app.models.transaction import TransactionCreate


def parse_date(date_str: str) -> datetime:
    """Try multiple date formats."""
    formats = [
        "%m/%d/%Y",      # 01/15/2024
        "%Y-%m-%d",      # 2024-01-15
        "%m-%d-%Y",      # 01-15-2024
        "%d/%m/%Y",      # 15/01/2024
        "%Y/%m/%d",      # 2024/01/15
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def parse_amount(amount_str: str) -> int:
    """Parse amount string to cents (integer)."""
    # Remove currency symbols, commas, spaces
    cleaned = amount_str.replace("$", "").replace(",", "").replace(" ", "").strip()
    # Handle parentheses for negative (accounting format)
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    # Convert to cents
    return int(float(cleaned) * 100)


def detect_format(headers: list[str]) -> str:
    """Auto-detect CSV format from headers."""
    headers_lower = [h.lower().strip() for h in headers]

    if "posting date" in headers_lower and "description" in headers_lower:
        return "chase"
    if "posted date" in headers_lower and "payee" in headers_lower:
        return "bank_of_america"
    if "date" in headers_lower and "description" in headers_lower:
        return "generic"

    return "generic"


def get_column_mapping(format_name: str) -> dict:
    """Get column name mapping for different bank formats."""
    mappings = {
        "chase": {
            "date": "Posting Date",
            "description": "Description",
            "amount": "Amount",
        },
        "bank_of_america": {
            "date": "Posted Date",
            "description": "Payee",
            "amount": "Amount",
        },
        "generic": {
            "date": "Date",
            "description": "Description",
            "amount": "Amount",
        },
    }
    return mappings.get(format_name, mappings["generic"])


def import_csv(filepath: str, account_id: str, format_name: str = None):
    """Import transactions from CSV file."""

    # Initialize database
    init_db()

    # Verify account exists
    account = account_service.get_by_id(account_id)
    if not account:
        print(f"Error: Account '{account_id}' not found.")
        print("\nAvailable accounts:")
        for acc in account_service.get_all():
            print(f"  {acc.id}: {acc.name}")
        sys.exit(1)

    print(f"Importing to account: {account.name}")

    # Read CSV
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        # Detect or use specified format
        if format_name is None:
            format_name = detect_format(headers)
            print(f"Auto-detected format: {format_name}")

        mapping = get_column_mapping(format_name)

        # Verify required columns exist
        for key, col in mapping.items():
            if col not in headers:
                # Try case-insensitive match
                matched = [h for h in headers if h.lower() == col.lower()]
                if matched:
                    mapping[key] = matched[0]
                else:
                    print(f"Error: Column '{col}' not found in CSV.")
                    print(f"Available columns: {headers}")
                    sys.exit(1)

        imported = 0
        skipped = 0

        for row in reader:
            try:
                date_str = row[mapping["date"]]
                description = row[mapping["description"]].strip()
                amount_str = row[mapping["amount"]]

                # Skip empty rows
                if not date_str or not description or not amount_str:
                    skipped += 1
                    continue

                date = parse_date(date_str)
                amount = parse_amount(amount_str)

                # Create transaction
                tx = TransactionCreate(
                    account_id=account_id,
                    date=date.date(),
                    description=description,
                    original_description=description,
                    amount=amount,
                    reviewed=False,
                )

                transaction_service.create(tx)
                imported += 1

                if imported % 50 == 0:
                    print(f"  Imported {imported} transactions...")

            except Exception as e:
                print(f"  Warning: Skipping row - {e}")
                skipped += 1

    print(f"\nDone! Imported {imported} transactions, skipped {skipped}.")
    print(f"Run categorization: curl -X POST http://localhost:8000/api/categorization/trigger")


def list_accounts():
    """List all accounts."""
    init_db()
    accounts = account_service.get_all()

    if not accounts:
        print("No accounts found. Create one first:")
        print('  curl -X POST http://localhost:8000/api/accounts -H "Content-Type: application/json" -d \'{"name": "My Bank", "type": "Checking"}\'')
        return

    print("Available accounts:")
    for acc in accounts:
        print(f"  {acc.id}: {acc.name} ({acc.type})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import transactions from CSV")
    parser.add_argument("csv_file", nargs="?", help="Path to CSV file")
    parser.add_argument("account_id", nargs="?", help="Account ID to import into")
    parser.add_argument("--format", choices=["chase", "bank_of_america", "generic"],
                        help="CSV format (auto-detected if not specified)")
    parser.add_argument("--list-accounts", action="store_true", help="List available accounts")

    args = parser.parse_args()

    if args.list_accounts:
        list_accounts()
    elif args.csv_file and args.account_id:
        if not os.path.exists(args.csv_file):
            print(f"Error: File not found: {args.csv_file}")
            sys.exit(1)
        import_csv(args.csv_file, args.account_id, args.format)
    else:
        parser.print_help()
        print("\n--- Accounts ---")
        list_accounts()
