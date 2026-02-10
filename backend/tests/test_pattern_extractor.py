"""Unit tests for description pattern extraction."""
import pytest
from app.services.pattern_extractor import extract_pattern


class TestExtractPattern:
    """Tests for the extract_pattern function."""

    def test_fidelity_brokerage_description(self):
        result = extract_pattern("DIRECT DEPOSIT Fidelity Bro461026 (Cash)")
        assert result == "direct deposit fidelity * (cash)"

    def test_check_number(self):
        result = extract_pattern("CHECK #1234 DEPOSIT")
        assert result == "check #* deposit"

    def test_trailing_reference_number(self):
        result = extract_pattern("DIVIDEND REINVEST 98765")
        assert result == "dividend reinvest *"

    def test_no_numbers(self):
        result = extract_pattern("GROCERY STORE")
        assert result == "grocery store"

    def test_short_description(self):
        result = extract_pattern("ATM")
        assert result == "atm"

    def test_empty_string(self):
        result = extract_pattern("")
        assert result == ""

    def test_whitespace_only(self):
        result = extract_pattern("   ")
        assert result == ""

    def test_two_digit_number_preserved(self):
        """2-digit numbers (like Route 66) should NOT be replaced."""
        result = extract_pattern("Route 66 Diner")
        assert result == "route 66 diner"

    def test_multiple_numeric_sequences(self):
        result = extract_pattern("Transfer 12345 to 67890")
        assert result == "transfer * to *"

    def test_case_insensitivity(self):
        """Output should always be lowercase."""
        result = extract_pattern("DIRECT DEPOSIT FIDELITY")
        assert result == "direct deposit fidelity"

    def test_leading_trailing_whitespace(self):
        result = extract_pattern("  DIRECT DEPOSIT 12345  ")
        assert result == "direct deposit *"

    def test_none_input(self):
        result = extract_pattern(None)
        assert result == ""

    def test_date_like_trailing_number(self):
        result = extract_pattern("PAYMENT CHASE CREDIT CRD AUTOPAY 240315")
        assert result == "payment chase credit crd autopay *"

    def test_long_trailing_reference(self):
        result = extract_pattern("ACH CREDIT EMPLOYER INC 20240315001234")
        assert result == "ach credit employer inc *"

    def test_no_numbers_interest(self):
        result = extract_pattern("INTEREST PAYMENT")
        assert result == "interest payment"

    def test_mixed_alphanumeric_token(self):
        """Tokens with 3+ digits embedded should be generalized."""
        result = extract_pattern("INV461026BUY")
        assert result == "*"

    def test_pattern_roundtrip_fidelity(self):
        """Extracted pattern matches the original and similar descriptions."""
        from app.services.desc_rule_service import _wildcard_to_regex

        original = "DIRECT DEPOSIT Fidelity Bro461026 (Cash)"
        pattern = extract_pattern(original)
        assert pattern == "direct deposit fidelity * (cash)"

        regex = _wildcard_to_regex(pattern)
        # Should match the original (lowercased)
        assert regex.match(original.lower())
        # Should match a variant with different numbers
        assert regex.match("direct deposit fidelity bro999999 (cash)")
        # Should NOT match something completely different
        assert not regex.match("some other description")

    def test_pattern_roundtrip_check(self):
        """Check number pattern roundtrips correctly."""
        from app.services.desc_rule_service import _wildcard_to_regex

        pattern = extract_pattern("CHECK #1234 DEPOSIT")
        regex = _wildcard_to_regex(pattern)
        assert regex.match("check #5678 deposit")
        assert regex.match("check #9999 deposit")
        assert not regex.match("wire transfer deposit")

    def test_payment_chase_autopay(self):
        """PAYMENT CHASE CREDIT CRD AUTOPAY with trailing date-like number."""
        result = extract_pattern("PAYMENT CHASE CREDIT CRD AUTOPAY 240315")
        assert result == "payment chase credit crd autopay *"

    def test_ach_credit_long_reference(self):
        """ACH CREDIT with long trailing reference number."""
        result = extract_pattern("ACH CREDIT EMPLOYER INC 20240315001234")
        assert result == "ach credit employer inc *"

    def test_interest_payment_no_numbers(self):
        """INTEREST PAYMENT has no numbers, returned as-is lowercase."""
        result = extract_pattern("INTEREST PAYMENT")
        assert result == "interest payment"

    def test_mixed_alphanumeric_inv(self):
        """INV461026BUY - mixed alphanumeric with 3+ digits gets wildcarded."""
        result = extract_pattern("INV461026BUY")
        assert result == "*"
