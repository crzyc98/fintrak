# Data Model: Gemini API Integration

**Feature**: 007-gemini-api-integration
**Date**: 2026-02-08

## Overview

This feature does not introduce new data entities. The Gemini client operates as a stateless service that:
- Receives prompts (string)
- Returns parsed JSON (list of dictionaries)

Existing database entities (transactions, categories) remain unchanged.

## Interface Contracts

### Input: Prompt String

The categorization service builds prompts containing:
- List of transactions with IDs, merchants, descriptions
- List of available categories with IDs and names
- Expected response format instructions

No changes to prompt structure required.

### Output: Categorization Results

```python
# Response structure (unchanged from claude_client)
list[dict]  # Each dict contains:
{
    "transaction_id": str,   # UUID of transaction
    "category_id": str,      # UUID of matched category
    "confidence": float      # 0.0 to 1.0
}
```

## Error Classes

### New Generic Error Hierarchy

```python
class AIClientError(Exception):
    """Base exception for AI client errors"""
    pass

class AITimeoutError(AIClientError):
    """Raised when AI API call times out"""
    pass

class AIInvocationError(AIClientError):
    """Raised when AI API invocation fails"""
    pass
```

These replace the Claude-specific error classes while maintaining the same inheritance pattern for backward compatibility with existing error handling.

## Configuration Model

### New Settings (config.py)

| Setting | Type | Default | Source |
|---------|------|---------|--------|
| `GEMINI_API_KEY` | str | None (required) | Environment |
| `GEMINI_MODEL` | str | "gemini-1.5-flash" | Environment |

### Existing Settings (unchanged)

| Setting | Type | Default | Used By |
|---------|------|---------|---------|
| `CATEGORIZATION_TIMEOUT_SECONDS` | int | 120 | Gemini client |
| `CATEGORIZATION_MAX_RETRIES` | int | 3 | Retry logic |
| `CATEGORIZATION_RETRY_DELAYS` | list[int] | [2, 4, 8] | Retry logic |
