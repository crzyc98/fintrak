"""
Unit tests for the Gemini client module.
Uses mocking to avoid real API calls.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.services.gemini_client import (
    AIClientError,
    AITimeoutError,
    AIInvocationError,
    extract_json,
    invoke_gemini,
    invoke_and_parse,
    with_retry,
    _get_client,
)


class TestExtractJson:
    """Tests for the extract_json function."""

    def test_extract_json_direct_array(self):
        """Test parsing a direct JSON array."""
        response = '[{"transaction_id": "123", "category_id": "456", "confidence": 0.9}]'
        result = extract_json(response)
        assert len(result) == 1
        assert result[0]["transaction_id"] == "123"
        assert result[0]["confidence"] == 0.9

    def test_extract_json_wrapped_in_object(self):
        """Test parsing JSON with results wrapper."""
        response = '{"results": [{"transaction_id": "123", "category_id": "456"}]}'
        result = extract_json(response)
        assert len(result) == 1
        assert result[0]["transaction_id"] == "123"

    def test_extract_json_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        response = '''Here are the categorizations:
```json
[{"transaction_id": "123", "category_id": "456", "confidence": 0.85}]
```
'''
        result = extract_json(response)
        assert len(result) == 1
        assert result[0]["confidence"] == 0.85

    def test_extract_json_with_surrounding_text(self):
        """Test extracting JSON with text before/after."""
        response = '''Based on my analysis, here are the results:
[{"transaction_id": "abc", "category_id": "def", "confidence": 0.75}]
I hope this helps!'''
        result = extract_json(response)
        assert len(result) == 1
        assert result[0]["transaction_id"] == "abc"

    def test_extract_json_empty_response(self):
        """Test handling empty response."""
        result = extract_json("")
        assert result == []

    def test_extract_json_no_array(self):
        """Test handling response without JSON array."""
        result = extract_json("This is just some text without JSON.")
        assert result == []

    def test_extract_json_invalid_json(self):
        """Test handling invalid JSON."""
        result = extract_json('[{"incomplete": true')
        assert result == []

    def test_extract_json_multiple_items(self):
        """Test parsing array with multiple items."""
        response = '''[
            {"transaction_id": "1", "category_id": "cat1", "confidence": 0.9},
            {"transaction_id": "2", "category_id": "cat2", "confidence": 0.8},
            {"transaction_id": "3", "category_id": "cat1", "confidence": 0.7}
        ]'''
        result = extract_json(response)
        assert len(result) == 3
        assert result[1]["transaction_id"] == "2"


class TestExceptionHierarchy:
    """Tests for the exception class hierarchy."""

    def test_ai_timeout_error_inherits_from_base(self):
        """Test AITimeoutError is a subclass of AIClientError."""
        assert issubclass(AITimeoutError, AIClientError)

    def test_ai_invocation_error_inherits_from_base(self):
        """Test AIInvocationError is a subclass of AIClientError."""
        assert issubclass(AIInvocationError, AIClientError)

    def test_catching_base_catches_timeout(self):
        """Test catching AIClientError catches AITimeoutError."""
        try:
            raise AITimeoutError("test timeout")
        except AIClientError as e:
            assert "test timeout" in str(e)

    def test_catching_base_catches_invocation(self):
        """Test catching AIClientError catches AIInvocationError."""
        try:
            raise AIInvocationError("test invocation error")
        except AIClientError as e:
            assert "test invocation error" in str(e)


class TestInvokeGemini:
    """Tests for the invoke_gemini function."""

    @patch("app.services.gemini_client.GEMINI_API_KEY", None)
    @patch("app.services.gemini_client._client", None)
    def test_invoke_gemini_no_api_key(self):
        """Test that missing API key raises AIInvocationError."""
        with pytest.raises(AIInvocationError) as exc_info:
            invoke_gemini("test prompt")
        assert "GEMINI_API_KEY not configured" in str(exc_info.value)

    @patch("app.services.gemini_client._get_client")
    def test_invoke_gemini_success(self, mock_get_client):
        """Test successful API invocation."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '[{"transaction_id": "123", "category_id": "456"}]'
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = invoke_gemini("test prompt")

        assert result == '[{"transaction_id": "123", "category_id": "456"}]'
        mock_client.models.generate_content.assert_called_once()

    @patch("app.services.gemini_client._get_client")
    def test_invoke_gemini_empty_response(self, mock_get_client):
        """Test that empty response raises AIInvocationError."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = None
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        with pytest.raises(AIInvocationError) as exc_info:
            invoke_gemini("test prompt")
        assert "empty response" in str(exc_info.value)


class TestWithRetry:
    """Tests for the with_retry function."""

    def test_with_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        mock_func = MagicMock(return_value="success")

        result = with_retry(mock_func, "arg1", key="value")

        assert result == "success"
        assert mock_func.call_count == 1
        mock_func.assert_called_with("arg1", key="value")

    @patch("app.services.gemini_client.time.sleep")
    def test_with_retry_success_after_failures(self, mock_sleep):
        """Test successful execution after retries."""
        mock_func = MagicMock(side_effect=[
            AITimeoutError("timeout 1"),
            AITimeoutError("timeout 2"),
            "success"
        ])

        result = with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("app.services.gemini_client.time.sleep")
    def test_with_retry_all_attempts_fail(self, mock_sleep):
        """Test that exception is raised after all retries fail."""
        mock_func = MagicMock(side_effect=AITimeoutError("persistent timeout"))

        with pytest.raises(AITimeoutError) as exc_info:
            with_retry(mock_func)

        assert "persistent timeout" in str(exc_info.value)
        assert mock_func.call_count == 4  # Initial + 3 retries

    def test_with_retry_no_retry_on_auth_error(self):
        """Test that authentication errors are not retried."""
        mock_func = MagicMock(side_effect=AIInvocationError("Authentication error"))

        with pytest.raises(AIInvocationError):
            with_retry(mock_func)

        assert mock_func.call_count == 1  # No retries

    def test_with_retry_no_retry_on_not_configured(self):
        """Test that 'not configured' errors are not retried."""
        mock_func = MagicMock(side_effect=AIInvocationError("GEMINI_API_KEY not configured"))

        with pytest.raises(AIInvocationError):
            with_retry(mock_func)

        assert mock_func.call_count == 1  # No retries

    def test_with_retry_no_retry_on_invalid_request(self):
        """Test that invalid request errors are not retried."""
        mock_func = MagicMock(side_effect=AIInvocationError("Invalid argument in request"))

        with pytest.raises(AIInvocationError):
            with_retry(mock_func)

        assert mock_func.call_count == 1  # No retries

    @patch("app.services.gemini_client.time.sleep")
    def test_with_retry_retries_rate_limit(self, mock_sleep):
        """Test that rate limit errors are retried."""
        mock_func = MagicMock(side_effect=[
            AIInvocationError("Rate limit exceeded"),
            "success"
        ])

        result = with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 2


class TestInvokeAndParse:
    """Tests for the invoke_and_parse function."""

    @patch("app.services.gemini_client.with_retry")
    def test_invoke_and_parse_success(self, mock_with_retry):
        """Test successful invocation and parsing."""
        mock_with_retry.return_value = '[{"transaction_id": "123", "category_id": "456", "confidence": 0.9}]'

        result = invoke_and_parse("test prompt")

        assert len(result) == 1
        assert result[0]["transaction_id"] == "123"
        assert result[0]["confidence"] == 0.9

    @patch("app.services.gemini_client.with_retry")
    def test_invoke_and_parse_empty_response(self, mock_with_retry):
        """Test handling of response with no valid JSON."""
        mock_with_retry.return_value = "No categorizations found."

        result = invoke_and_parse("test prompt")

        assert result == []

    @patch("app.services.gemini_client.with_retry")
    def test_invoke_and_parse_propagates_exception(self, mock_with_retry):
        """Test that exceptions from retry logic are propagated."""
        mock_with_retry.side_effect = AIClientError("test error")

        with pytest.raises(AIClientError) as exc_info:
            invoke_and_parse("test prompt")
        assert "test error" in str(exc_info.value)
