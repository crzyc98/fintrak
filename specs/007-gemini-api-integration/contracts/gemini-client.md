# Contract: Gemini Client Module

**Module**: `backend/app/services/gemini_client.py`
**Date**: 2026-02-08

## Public Interface

### Functions

#### `invoke_and_parse(prompt: str, timeout: Optional[int] = None) -> list[dict]`

Primary entry point for AI categorization requests.

**Parameters**:
- `prompt` (str): The categorization prompt containing transactions and categories
- `timeout` (int, optional): Request timeout in seconds. Defaults to `CATEGORIZATION_TIMEOUT_SECONDS`

**Returns**:
- `list[dict]`: Parsed JSON array of categorization results

**Raises**:
- `AIClientError`: Base exception for any AI client failure
- `AITimeoutError`: When the API call exceeds timeout
- `AIInvocationError`: When the API returns an error or invalid response

**Behavior**:
1. Validates API key is configured (raises `AIInvocationError` if missing)
2. Calls Gemini API with JSON output mode
3. Applies retry logic with exponential backoff on transient failures
4. Parses response using fallback JSON extraction if needed
5. Returns parsed results or empty list if parsing fails

---

#### `invoke_gemini(prompt: str, timeout: Optional[int] = None) -> str`

Low-level function to invoke Gemini API.

**Parameters**:
- `prompt` (str): The prompt to send
- `timeout` (int, optional): Request timeout in seconds

**Returns**:
- `str`: Raw response text from Gemini

**Raises**:
- `AITimeoutError`: On timeout
- `AIInvocationError`: On API errors

---

#### `extract_json(response: str) -> list[dict]`

Parse JSON from API response with fallback handling.

**Parameters**:
- `response` (str): Raw response text

**Returns**:
- `list[dict]`: Parsed JSON array, or empty list if parsing fails

**Behavior**:
- First attempts direct JSON parse (for JSON mode responses)
- Falls back to markdown code block extraction
- Falls back to finding JSON array boundaries
- Returns empty list on parse failure (does not raise)

---

#### `with_retry(func, *args, **kwargs)`

Execute function with retry logic and exponential backoff.

**Parameters**:
- `func`: Function to execute
- `*args, **kwargs`: Arguments to pass to function

**Returns**:
- Result from successful function call

**Raises**:
- Last exception if all retries exhausted

**Retry Behavior**:
- Retries on: `AITimeoutError`, `AIInvocationError` (rate limits only)
- Does not retry on: Authentication errors, invalid requests
- Delays: 2s, 4s, 8s (configurable via `CATEGORIZATION_RETRY_DELAYS`)
- Max attempts: 4 (initial + 3 retries)

---

### Exception Classes

```python
class AIClientError(Exception):
    """Base exception for AI client errors"""

class AITimeoutError(AIClientError):
    """Raised when AI API call times out"""

class AIInvocationError(AIClientError):
    """Raised when AI API invocation fails"""
```

## Dependencies

### External
- `google.generativeai`: Gemini SDK

### Internal
- `app.config`: Configuration settings

## Configuration

Required environment:
- `GEMINI_API_KEY`: Must be set for API authentication

Optional environment:
- `GEMINI_MODEL`: Model to use (default: gemini-1.5-flash)
