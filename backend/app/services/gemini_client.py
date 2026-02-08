"""
Google Gemini API client for AI-powered categorization.
Uses the google-genai package with JSON output mode.
"""
import json
import logging
import re
import time
from typing import Optional

from google import genai
from google.genai import types

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    CATEGORIZATION_TIMEOUT_SECONDS,
    CATEGORIZATION_MAX_RETRIES,
    CATEGORIZATION_RETRY_DELAYS,
)

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """Base exception for AI client errors"""
    pass


class AITimeoutError(AIClientError):
    """Raised when AI API call times out"""
    pass


class AIInvocationError(AIClientError):
    """Raised when AI API invocation fails"""
    pass


# Module-level client instance (initialized on first use)
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """
    Get or initialize the Gemini client instance.

    Raises:
        AIInvocationError: If GEMINI_API_KEY is not configured
    """
    global _client

    if _client is None:
        if not GEMINI_API_KEY:
            raise AIInvocationError(
                "GEMINI_API_KEY not configured. "
                "Set the environment variable or add it to your .env file. "
                "Get an API key at https://aistudio.google.com/apikey"
            )

        _client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info(f"Gemini client initialized with model: {GEMINI_MODEL}")

    return _client


def invoke_gemini(prompt: str, timeout: Optional[int] = None) -> str:
    """
    Invoke Gemini API with the given prompt.

    Args:
        prompt: The prompt to send to Gemini
        timeout: Timeout in seconds (defaults to config value)

    Returns:
        The raw response text from Gemini

    Raises:
        AITimeoutError: If the invocation times out
        AIInvocationError: If the invocation fails
    """
    if timeout is None:
        timeout = CATEGORIZATION_TIMEOUT_SECONDS

    try:
        client = _get_client()

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                http_options=types.HttpOptions(timeout=timeout * 1000),  # Convert to ms
            ),
        )

        if not response.text:
            raise AIInvocationError("Gemini returned empty response")

        return response.text

    except TimeoutError:
        logger.error(f"Gemini API timed out after {timeout} seconds")
        raise AITimeoutError(f"Gemini API timed out after {timeout} seconds")

    except Exception as e:
        error_str = str(e).lower()

        # Handle rate limiting
        if "resource exhausted" in error_str or "429" in error_str or "rate" in error_str:
            logger.error(f"Gemini API rate limit exceeded: {e}")
            raise AIInvocationError(f"Rate limit exceeded: {e}")

        # Handle authentication errors
        if "permission denied" in error_str or "403" in error_str or "invalid api key" in error_str:
            logger.error(f"Gemini API permission denied: {e}")
            raise AIInvocationError(f"Authentication error: {e}")

        # Handle invalid arguments
        if "invalid argument" in error_str or "400" in error_str:
            logger.error(f"Gemini API invalid argument: {e}")
            raise AIInvocationError(f"Invalid request: {e}")

        # Handle timeout-like errors
        if "deadline" in error_str or "timeout" in error_str:
            logger.error(f"Gemini API timed out: {e}")
            raise AITimeoutError(f"Gemini API timed out: {e}")

        # Re-raise our own exceptions
        if isinstance(e, AIClientError):
            raise

        logger.error(f"Unexpected error invoking Gemini API: {e}")
        raise AIClientError(f"Unexpected error: {e}")


def with_retry(func, *args, **kwargs):
    """
    Execute a function with retry logic and exponential backoff.

    Retries on:
    - AITimeoutError
    - AIInvocationError (rate limits only)

    Does not retry on:
    - Authentication errors
    - Invalid request errors

    Args:
        func: Function to execute
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from func

    Raises:
        The last exception if all retries fail
    """
    last_error = None
    delays = CATEGORIZATION_RETRY_DELAYS[:CATEGORIZATION_MAX_RETRIES]

    for attempt in range(CATEGORIZATION_MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except AITimeoutError as e:
            # Always retry timeouts
            last_error = e
        except AIInvocationError as e:
            error_msg = str(e).lower()
            # Only retry rate limits, not auth or invalid request errors
            if "rate limit" in error_msg or "resource exhausted" in error_msg:
                last_error = e
            elif "authentication" in error_msg or "permission denied" in error_msg or "not configured" in error_msg:
                logger.error(f"Non-retryable authentication error: {e}")
                raise
            elif "invalid" in error_msg:
                logger.error(f"Non-retryable invalid request error: {e}")
                raise
            else:
                last_error = e
        except AIClientError as e:
            last_error = e

        if attempt < CATEGORIZATION_MAX_RETRIES:
            delay = delays[attempt] if attempt < len(delays) else delays[-1]
            logger.warning(
                f"Gemini invocation failed (attempt {attempt + 1}/{CATEGORIZATION_MAX_RETRIES + 1}), "
                f"retrying in {delay}s: {last_error}"
            )
            time.sleep(delay)
        else:
            logger.error(
                f"Gemini invocation failed after {CATEGORIZATION_MAX_RETRIES + 1} attempts"
            )

    raise last_error


def extract_json(response: str) -> list[dict]:
    """
    Extract JSON array from Gemini response.

    Handles responses that may include:
    - Direct JSON (from JSON output mode)
    - Markdown code blocks (```json ... ```)
    - Explanatory text before/after JSON
    - Multiple JSON structures (takes the first array)

    Args:
        response: Raw response text from Gemini

    Returns:
        List of dictionaries parsed from JSON, or empty list if parsing fails
    """
    if not response:
        logger.warning("Empty response from Gemini")
        return []

    # First, try direct JSON parse (most common with JSON mode)
    try:
        result = json.loads(response)
        if isinstance(result, list):
            return result
        # If it's a dict, check if it has a common wrapper key
        if isinstance(result, dict):
            for key in ["results", "data", "categorizations", "items"]:
                if key in result and isinstance(result[key], list):
                    return result[key]
        logger.warning(f"JSON parsed but not an array: {type(result)}")
    except json.JSONDecodeError:
        pass  # Fall through to other extraction methods

    # Try to find JSON in markdown code block
    code_block_match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        response,
        re.IGNORECASE
    )
    if code_block_match:
        try:
            result = json.loads(code_block_match.group(1))
            if isinstance(result, list):
                logger.debug("Extracted JSON from markdown code block")
                return result
        except json.JSONDecodeError:
            pass

    # Find array boundaries
    start = response.find("[")
    end = response.rfind("]") + 1

    if start < 0 or end <= start:
        logger.warning("No JSON array found in response")
        return []

    json_str = response[start:end]

    try:
        result = json.loads(json_str)
        if not isinstance(result, list):
            logger.warning(f"JSON is not an array: {type(result)}")
            return []
        logger.debug("Extracted JSON using array boundary detection")
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}")
        logger.debug(f"JSON string was: {json_str[:500]}")
        return []


def invoke_and_parse(prompt: str, timeout: Optional[int] = None) -> list[dict]:
    """
    Invoke Gemini and parse the JSON response.

    Combines invoke_gemini with retry logic and JSON extraction.

    Args:
        prompt: The prompt to send to Gemini
        timeout: Timeout in seconds (defaults to config value)

    Returns:
        List of dictionaries parsed from the response

    Raises:
        AIClientError: If invocation fails after retries
    """
    response = with_retry(invoke_gemini, prompt, timeout)
    return extract_json(response)
