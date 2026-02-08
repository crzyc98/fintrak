# Research: Gemini API Integration

**Feature**: 007-gemini-api-integration
**Date**: 2026-02-08

## Research Tasks

### 1. Google Gen AI Python SDK

**Decision**: Use `google-genai` package (official Google SDK)

**Rationale**:
- Official SDK maintained by Google (GA as of 2025)
- Simple API for text generation with structured output
- Supports JSON output mode via `response_mime_type`
- Handles authentication via API key automatically
- **NOTE**: The `google-generativeai` package is deprecated (support ended Nov 2025)

**Alternatives Considered**:
- `google-generativeai`: DEPRECATED - support ended November 2025
- `google-cloud-aiplatform`: More complex, requires GCP project setup, overkill for API key auth
- Raw HTTP requests: No SDK benefits, manual error handling, more code to maintain

**Key API Usage**:
```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
    ),
)

result = response.text  # JSON string when mime_type is application/json
```

### 2. Error Handling Patterns

**Decision**: Map Gemini SDK exceptions to generic AI error classes

**Rationale**:
- Maintains consistent error handling across AI providers
- Allows future provider swaps without changing calling code
- Matches existing retry logic patterns

**Error Mapping**:
| Gemini SDK Exception | Maps To |
|---------------------|---------|
| `google.api_core.exceptions.DeadlineExceeded` | `AITimeoutError` |
| `google.api_core.exceptions.ResourceExhausted` | `AIInvocationError` (rate limit) |
| `google.api_core.exceptions.InvalidArgument` | `AIInvocationError` |
| `google.api_core.exceptions.PermissionDenied` | `AIInvocationError` (auth error) |
| `ValueError` (from SDK) | `AIInvocationError` |
| Generic `Exception` | `AIClientError` |

### 3. JSON Output Mode Best Practices

**Decision**: Use `response_mime_type="application/json"` with fallback parsing

**Rationale**:
- Native JSON mode produces cleaner output
- Fallback parsing (from existing claude_client.py) provides resilience
- No additional prompt engineering required for JSON format

**Implementation Notes**:
- JSON mode in Gemini 1.5 is reliable but fallback parsing handles edge cases
- Keep existing `extract_json()` function logic for robustness
- Log when fallback is triggered for monitoring

### 4. Retry Strategy

**Decision**: Reuse existing exponential backoff pattern (2s, 4s, 8s delays)

**Rationale**:
- Proven pattern already in codebase
- Appropriate for transient API failures and rate limits
- 3 retries matches Gemini's recommended retry guidance

**Retryable Conditions**:
- Timeout errors
- Rate limit errors (ResourceExhausted)
- Transient server errors (5xx equivalent)

**Non-Retryable Conditions**:
- Authentication errors (invalid API key)
- Invalid request errors (malformed prompt)

### 5. Model Selection

**Decision**: Default to `gemini-1.5-flash`, configurable via environment

**Rationale**:
- gemini-1.5-flash is fast and cost-effective
- Available on free tier for development
- Sufficient capability for transaction categorization
- Environment variable allows upgrade to gemini-1.5-pro if needed

**Available Models** (as of 2026):
- `gemini-1.5-flash` - Fast, economical (default)
- `gemini-1.5-pro` - More capable, higher cost
- `gemini-2.0-flash-exp` - Experimental, may not be stable

## Dependencies

**Package to Add**: `google-genai>=1.0.0`

**Note**: The `google-generativeai` package is deprecated. Use `google-genai` instead.

**Transitive Dependencies** (handled by pip):
- `google-auth`
- `google-api-core`
- `protobuf`

## Configuration

**New Environment Variables**:
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | None | Google AI Studio API key |
| `GEMINI_MODEL` | No | `gemini-1.5-flash` | Model identifier |

**Existing Variables** (unchanged):
- `CATEGORIZATION_TIMEOUT_SECONDS` - Applies to Gemini calls
- `CATEGORIZATION_MAX_RETRIES` - Number of retry attempts
- `CATEGORIZATION_RETRY_DELAYS` - Backoff delays

## Open Questions Resolved

All technical unknowns from the spec have been resolved through this research:

1. ✅ SDK choice: google-generativeai
2. ✅ Error handling: Map to generic AI exceptions
3. ✅ JSON mode: Use native + fallback parsing
4. ✅ Retry strategy: Reuse existing pattern
5. ✅ Model default: gemini-1.5-flash
