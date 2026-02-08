# Quickstart: Gemini API Integration

**Feature**: 007-gemini-api-integration
**Date**: 2026-02-08

## Prerequisites

1. Python 3.12+
2. Google AI Studio API key (get one at https://aistudio.google.com/apikey)

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

After implementation, requirements.txt will include `google-generativeai`.

### 2. Configure Environment

Create or update your environment with:

```bash
export GEMINI_API_KEY="your-api-key-here"

# Optional: Use a different model
export GEMINI_MODEL="gemini-1.5-flash"  # default
```

Or add to a `.env` file in the project root:

```env
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-1.5-flash
```

### 3. Verify Configuration

Start the backend and check logs:

```bash
cd backend
uvicorn app.main:app --reload
```

The first categorization request will confirm Gemini connectivity.

## Usage

### Trigger Categorization

The Gemini integration is transparent to the API. Use the existing categorization endpoint:

```bash
curl -X POST http://localhost:8000/api/categorization/trigger
```

### Expected Response

```json
{
  "id": "batch-uuid",
  "transaction_count": 10,
  "success_count": 9,
  "failure_count": 1,
  "rule_match_count": 3,
  "ai_match_count": 6,
  "skipped_count": 0,
  "duration_ms": 2500
}
```

## Troubleshooting

### "GEMINI_API_KEY not configured"

Set the environment variable:
```bash
export GEMINI_API_KEY="your-key"
```

### "API key invalid" / 403 errors

1. Verify your API key at https://aistudio.google.com/apikey
2. Ensure the key has Generative Language API enabled
3. Check for typos in the key

### Rate limit errors (429)

The client automatically retries with exponential backoff. If persistent:
1. Wait a few minutes for rate limit reset
2. Consider upgrading to a paid tier
3. Reduce batch size via `CATEGORIZATION_BATCH_SIZE`

### Timeout errors

Increase timeout if needed:
```bash
export CATEGORIZATION_TIMEOUT_SECONDS=180
```

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_gemini_client.py -v
```

## Rollback

If issues arise, the original Claude client remains available:

1. Update `categorization_service.py` imports:
   ```python
   # Change from:
   from app.services.gemini_client import invoke_and_parse, AIClientError
   # Back to:
   from app.services.claude_client import invoke_and_parse, ClaudeClientError as AIClientError
   ```

2. Ensure Claude CLI is available:
   ```bash
   export CLAUDE_CODE_PATH="/path/to/claude"
   ```
