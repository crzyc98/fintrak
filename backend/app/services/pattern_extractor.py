"""
Pattern extraction for description-based categorization rules.

Extracts generalized wildcard patterns from transaction descriptions
by replacing variable numeric portions with '*' wildcards.
"""
import re


def extract_pattern(description: str) -> str:
    """
    Extract a generalized wildcard pattern from a transaction description.

    Replaces sequences of 3+ digits (and alphanumeric tokens ending in 3+ digits)
    with '*' wildcards, then lowercases the result.

    Args:
        description: Raw transaction description

    Returns:
        Lowercase wildcard pattern, or empty string if description is empty/blank
    """
    if not description or not description.strip():
        return ""

    result = description.strip()

    # Replace alphanumeric tokens that contain 3+ consecutive digits with *
    # This handles cases like "Bro461026" → "*" and "INV461026BUY" → "*"
    # as well as standalone numbers like "98765" → "*"
    result = re.sub(r'\b\w*\d{3,}\w*\b', '*', result)

    # Also replace standalone sequences of 3+ digits that might not be
    # word-bounded (e.g., after # like "#1234")
    result = re.sub(r'(?<=#)\d{3,}', '*', result)

    # Collapse multiple * separated by whitespace into a single *
    result = re.sub(r'\*(\s+\*)+', '*', result)

    # Clean up any double spaces left over
    result = re.sub(r'\s+', ' ', result).strip()

    return result.lower()
