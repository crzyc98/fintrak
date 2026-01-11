"""
Claude Code CLI client for AI-powered categorization.
Uses subprocess to invoke Claude in headless mode.
"""
import json
import logging
import re
import subprocess
import time
from typing import Optional

from app.config import (
    CLAUDE_CODE_PATH,
    CATEGORIZATION_TIMEOUT_SECONDS,
    CATEGORIZATION_MAX_RETRIES,
    CATEGORIZATION_RETRY_DELAYS,
)

logger = logging.getLogger(__name__)


class ClaudeClientError(Exception):
    """Base exception for Claude client errors"""
    pass


class ClaudeTimeoutError(ClaudeClientError):
    """Raised when Claude CLI times out"""
    pass


class ClaudeInvocationError(ClaudeClientError):
    """Raised when Claude CLI invocation fails"""
    pass


def invoke_claude(prompt: str, timeout: Optional[int] = None) -> str:
    """
    Invoke Claude Code CLI with the given prompt.

    Args:
        prompt: The prompt to send to Claude
        timeout: Timeout in seconds (defaults to config value)

    Returns:
        The raw response text from Claude

    Raises:
        ClaudeTimeoutError: If the invocation times out
        ClaudeInvocationError: If the invocation fails
    """
    if timeout is None:
        timeout = CATEGORIZATION_TIMEOUT_SECONDS

    try:
        result = subprocess.run(
            [CLAUDE_CODE_PATH, "-p"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            logger.error(
                f"Claude CLI returned non-zero exit code: {result.returncode}. "
                f"stderr: {result.stderr[:500] if result.stderr else 'empty'}"
            )
            raise ClaudeInvocationError(
                f"Claude CLI failed with exit code {result.returncode}"
            )

        return result.stdout

    except subprocess.TimeoutExpired:
        logger.error(f"Claude CLI timed out after {timeout} seconds")
        raise ClaudeTimeoutError(f"Claude CLI timed out after {timeout} seconds")

    except FileNotFoundError:
        logger.error(f"Claude CLI not found at path: {CLAUDE_CODE_PATH}")
        raise ClaudeInvocationError(
            f"Claude CLI not found at path: {CLAUDE_CODE_PATH}"
        )

    except Exception as e:
        logger.error(f"Unexpected error invoking Claude CLI: {e}")
        raise ClaudeInvocationError(f"Unexpected error: {e}")


def with_retry(func, *args, **kwargs):
    """
    Execute a function with retry logic and exponential backoff.

    Uses configured retry delays (2s, 4s, 8s by default).

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
        except (ClaudeTimeoutError, ClaudeInvocationError) as e:
            last_error = e
            if attempt < CATEGORIZATION_MAX_RETRIES:
                delay = delays[attempt] if attempt < len(delays) else delays[-1]
                logger.warning(
                    f"Claude invocation failed (attempt {attempt + 1}/{CATEGORIZATION_MAX_RETRIES + 1}), "
                    f"retrying in {delay}s: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"Claude invocation failed after {CATEGORIZATION_MAX_RETRIES + 1} attempts"
                )

    raise last_error


def extract_json(response: str) -> list[dict]:
    """
    Extract JSON array from Claude response.

    Handles responses that may include:
    - Markdown code blocks (```json ... ```)
    - Explanatory text before/after JSON
    - Multiple JSON structures (takes the first array)

    Args:
        response: Raw response text from Claude

    Returns:
        List of dictionaries parsed from JSON

    Raises:
        ValueError: If no valid JSON array can be extracted
    """
    if not response:
        logger.warning("Empty response from Claude")
        return []

    # Try to find JSON in markdown code block first
    code_block_match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        response,
        re.IGNORECASE
    )
    if code_block_match:
        response = code_block_match.group(1)

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
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}")
        logger.debug(f"JSON string was: {json_str[:500]}")
        return []


def invoke_and_parse(prompt: str, timeout: Optional[int] = None) -> list[dict]:
    """
    Invoke Claude and parse the JSON response.

    Combines invoke_claude with retry logic and JSON extraction.

    Args:
        prompt: The prompt to send to Claude
        timeout: Timeout in seconds (defaults to config value)

    Returns:
        List of dictionaries parsed from the response

    Raises:
        ClaudeClientError: If invocation fails after retries
    """
    response = with_retry(invoke_claude, prompt, timeout)
    return extract_json(response)
