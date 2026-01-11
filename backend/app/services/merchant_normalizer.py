"""
Merchant name normalization service.
Cleans up bank transaction descriptions to extract readable merchant names.
"""
import re
from typing import Tuple, List


# Common bank noise tokens to remove (case-insensitive)
NOISE_PREFIXES = [
    "POS DEBIT",
    "POS PURCHASE",
    "POS",
    "CHECKCARD",
    "CHECK CARD",
    "ACH WITHDRAWAL",
    "ACH PAYMENT",
    "ACH TRANSFER",
    "ACH",
    "PURCHASE",
    "DEBIT",
    "RECURRING",
    "AUTOPAY",
    "AUTO PAY",
    "PAYMENT",
    "BILL PAY",
    "ONLINE",
    "MOBILE",
    "TRANSFER",
    "WIRE",
    "EXTERNAL",
    "INTERNAL",
    "ELECTRONIC",
    "PREAUTHORIZED",
    "PENDING",
    "VISA",
    "MASTERCARD",
    "AMEX",
    "DISCOVER",
]

# Regex patterns for noise removal
NOISE_PATTERNS = [
    (r"\b\d{4,}\b", "card/reference numbers"),  # Card last 4+ digits, reference numbers
    (r"\b[A-Z]{2}\s*\d{5}(-\d{4})?\b", "state + ZIP"),  # State + ZIP (e.g., "CA 90210")
    (r"\b\d{1,2}/\d{1,2}(/\d{2,4})?\b", "date fragments"),  # Date fragments (e.g., "01/15")
    (r"#\d+", "store numbers"),  # Store numbers (e.g., "#1234")
    (r"\*+\d+", "masked numbers"),  # Masked numbers (e.g., "***1234")
    (r"\bXXX+\d*\b", "masked account"),  # Masked account (e.g., "XXXX1234")
    (r"\b\d{2}:\d{2}(:\d{2})?\b", "timestamps"),  # Timestamps
    (r"\b\d+\.\d{2}\b", "dollar amounts"),  # Dollar amounts without $
    (r"\$\d+(\.\d{2})?", "dollar amounts"),  # Dollar amounts with $
]


def normalize(description: str) -> Tuple[str, List[str]]:
    """
    Normalize a transaction description to extract merchant name.

    Args:
        description: Raw transaction description from bank

    Returns:
        Tuple of (normalized_merchant, tokens_removed)
    """
    if not description:
        return "", []

    tokens_removed = []
    result = description.strip()

    # Convert to uppercase for consistent matching
    upper_result = result.upper()

    # Remove noise prefixes
    for prefix in NOISE_PREFIXES:
        if upper_result.startswith(prefix):
            tokens_removed.append(prefix)
            result = result[len(prefix):].strip()
            upper_result = result.upper()
        # Also check if prefix appears elsewhere with word boundaries
        pattern = r"\b" + re.escape(prefix) + r"\b"
        if re.search(pattern, upper_result):
            tokens_removed.append(prefix)
            result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()
            upper_result = result.upper()

    # Apply regex noise patterns
    for pattern, description_text in NOISE_PATTERNS:
        matches = re.findall(pattern, result, flags=re.IGNORECASE)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else ""
                if match:
                    tokens_removed.append(match)
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)

    # Collapse multiple spaces
    result = re.sub(r"\s+", " ", result).strip()

    # Remove leading/trailing punctuation
    result = re.sub(r"^[\s\-_.,;:]+|[\s\-_.,;:]+$", "", result)

    # Handle .COM, .NET, etc. - extract domain name
    domain_match = re.search(r"(\w+)\.(COM|NET|ORG|IO|CO)\b", result, re.IGNORECASE)
    if domain_match:
        # Keep just the brand name
        brand = domain_match.group(1)
        # Replace the full domain with just the brand
        result = re.sub(
            r"\b\w+\.(COM|NET|ORG|IO|CO)\b",
            brand,
            result,
            flags=re.IGNORECASE
        )

    # Final cleanup
    result = re.sub(r"\s+", " ", result).strip()

    # Convert to title case for display
    if result:
        result = title_case_merchant(result)

    return result, tokens_removed


def title_case_merchant(name: str) -> str:
    """
    Convert merchant name to title case, handling special cases.
    """
    # Known brands that should stay uppercase
    uppercase_brands = {
        "USPS", "UPS", "FEDEX", "DHL", "ATM", "CVS", "HBO", "ESPN",
        "NBC", "CBS", "ABC", "PBS", "NPR", "BBC", "CNN", "IKEA",
        "H&M", "AT&T", "T-MOBILE", "USA", "UK", "EU"
    }

    words = name.split()
    result = []

    for word in words:
        upper_word = word.upper()
        if upper_word in uppercase_brands:
            result.append(upper_word)
        elif len(word) <= 2 and word.isupper():
            # Keep short uppercase words as-is (likely acronyms)
            result.append(word)
        else:
            result.append(word.capitalize())

    return " ".join(result)


def normalize_for_matching(merchant: str) -> str:
    """
    Normalize merchant name for rule matching.
    Returns lowercase version for case-insensitive matching.
    """
    normalized, _ = normalize(merchant)
    return normalized.lower()
