# Research: AI-Powered Transaction Categorization

**Feature**: 003-ai-categorization
**Date**: 2026-01-11

## Research Tasks

### 1. Claude Code CLI Integration Pattern

**Decision**: Use subprocess with stdin piping for large prompts

**Rationale**:
- Claude Code CLI (`claude -p "prompt"`) has shell argument length limits (~128KB on Linux)
- For batches of 50 transactions with full context, prompts can exceed 10KB
- Piping via stdin (`echo "prompt" | claude -p`) avoids argument limits
- Subprocess allows timeout control and process isolation

**Alternatives Considered**:
- Direct API calls: Rejected - requires API keys and incurs costs; goal is "zero API cost"
- File-based prompts: More complex, requires temp file management
- Shell argument: Works for small prompts but not scalable

**Implementation Pattern**:
```python
import subprocess
import json

def invoke_claude(prompt: str, timeout: int = 120) -> str:
    result = subprocess.run(
        ["claude", "-p"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return result.stdout
```

---

### 2. Merchant Normalization Strategy

**Decision**: Rule-based normalization with ordered token removal

**Rationale**:
- Bank transaction descriptions follow predictable patterns
- Common prefixes (POS, CHECKCARD, ACH) are easily identified
- Location suffixes (city, state, zip) can be stripped with regex
- No ML/AI needed - deterministic rules provide consistent results

**Alternatives Considered**:
- ML-based entity extraction: Overkill for structured bank data, adds complexity
- External API (Plaid, Yodlee): Adds cost and external dependency
- No normalization: Reduces AI accuracy and user experience

**Noise Tokens to Remove** (case-insensitive):
```python
NOISE_PREFIXES = [
    "POS DEBIT", "POS PURCHASE", "POS", "CHECKCARD", "CHECK CARD",
    "ACH WITHDRAWAL", "ACH PAYMENT", "ACH", "PURCHASE", "DEBIT",
    "RECURRING", "AUTOPAY", "PAYMENT", "BILL PAY", "ONLINE",
    "MOBILE", "TRANSFER", "WIRE", "EXTERNAL", "INTERNAL"
]

NOISE_PATTERNS = [
    r'\b\d{4,}\b',              # Card last 4 digits, reference numbers
    r'\b[A-Z]{2}\s*\d{5}\b',    # State + ZIP (e.g., "CA 90210")
    r'\b\d{1,2}/\d{1,2}\b',     # Date fragments (e.g., "01/15")
    r'#\d+',                     # Store numbers (e.g., "#1234")
    r'\*+\d+',                   # Masked numbers (e.g., "***1234")
]
```

---

### 3. AI Response Parsing Strategy

**Decision**: JSON extraction with markdown code block handling

**Rationale**:
- Claude often wraps JSON in markdown code blocks (```json ... ```)
- Response may include explanatory text before/after JSON
- Need robust extraction that handles variations

**Alternatives Considered**:
- Strict JSON-only response: Claude doesn't always comply
- XML/structured output: More complex parsing, no benefit
- Line-by-line parsing: Fragile, doesn't handle nested structures

**Extraction Pattern**:
```python
import re
import json

def extract_json(response: str) -> list[dict]:
    # Try to find JSON in markdown code block first
    code_block = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if code_block:
        response = code_block.group(1)

    # Find array boundaries
    start = response.find('[')
    end = response.rfind(']') + 1
    if start >= 0 and end > start:
        return json.loads(response[start:end])

    return []  # Return empty on parse failure
```

---

### 4. Retry and Backoff Implementation

**Decision**: Exponential backoff with 3 retries (2s, 4s, 8s)

**Rationale**:
- Per clarification session, agreed on 3 retries max
- Exponential backoff prevents thundering herd on recovery
- Total max wait: 14s (2+4+8) + 3x timeout reasonable for background task
- Jitter not needed for single-user app

**Alternatives Considered**:
- Linear backoff: Less effective at spreading retry load
- More retries (5+): Extends total processing time unacceptably
- No retry: Transient failures cause unnecessary categorization gaps

**Implementation Pattern**:
```python
import time

def with_retry(func, max_retries=3, base_delay=2):
    delays = [base_delay * (2 ** i) for i in range(max_retries)]  # [2, 4, 8]

    last_error = None
    for attempt, delay in enumerate(delays + [0]):  # +[0] for final attempt
        try:
            return func()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(delay)

    raise last_error
```

---

### 5. Rule Matching Implementation

**Decision**: Substring/contains matching with case-insensitive comparison

**Rationale**:
- Per clarification session, substring matching selected
- Handles merchant variations (e.g., "STARBUCKS" matches "STARBUCKS #1234")
- Case-insensitive for robustness
- Most recent rule wins on conflict (per edge case specification)

**Alternatives Considered**:
- Exact match: Too strict, misses valid variations
- Fuzzy matching: Adds complexity, potential false positives
- Prefix matching: Misses mid-string matches

**Implementation Pattern**:
```python
def find_matching_rule(normalized_merchant: str, rules: list[Rule]) -> Rule | None:
    # Rules ordered by created_at DESC (most recent first)
    normalized_lower = normalized_merchant.lower()
    for rule in rules:
        if rule.merchant_pattern.lower() in normalized_lower:
            return rule
    return None
```

---

### 6. Prompt Engineering for Categorization

**Decision**: Structured prompt with explicit JSON schema and examples

**Rationale**:
- Clear schema reduces parsing errors
- Examples improve category matching accuracy
- Including category descriptions helps AI make informed choices
- Batch format reduces per-transaction overhead

**Prompt Template**:
```
You are a financial transaction categorizer. Analyze each transaction and assign the most appropriate category.

Available Categories:
{categories_json}

Transactions to categorize:
{transactions_json}

For each transaction, respond with a JSON array containing objects with these fields:
- transaction_id: The ID from the input
- category_id: The UUID of the best matching category
- confidence: A number from 0.0 to 1.0 indicating your confidence

Example response format:
[
  {"transaction_id": "abc-123", "category_id": "cat-456", "confidence": 0.95},
  {"transaction_id": "def-789", "category_id": "cat-012", "confidence": 0.72}
]

Only respond with the JSON array, no additional text.
```

---

### 7. Database Schema Extension

**Decision**: Add two new tables; extend transactions table with new columns

**Rationale**:
- `categorization_rules` stores learned merchant->category mappings
- `categorization_batches` tracks processing metrics for observability
- Transaction table needs: `normalized_merchant`, `confidence_score`, `categorization_source`
- Minimal schema changes, compatible with existing queries

**Schema Additions**:
```sql
-- New columns on transactions table
ALTER TABLE transactions ADD COLUMN normalized_merchant VARCHAR;
ALTER TABLE transactions ADD COLUMN confidence_score DECIMAL(3,2);
ALTER TABLE transactions ADD COLUMN categorization_source VARCHAR(10);
-- source values: 'rule', 'ai', 'manual', 'none'

-- New table for learned rules
CREATE TABLE categorization_rules (
    id VARCHAR(36) PRIMARY KEY,
    merchant_pattern VARCHAR(255) NOT NULL,
    category_id VARCHAR(36) NOT NULL REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(merchant_pattern)
);

-- New table for batch tracking
CREATE TABLE categorization_batches (
    id VARCHAR(36) PRIMARY KEY,
    import_id VARCHAR(36),  -- Links to future import tracking
    transaction_count INTEGER NOT NULL,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    rule_match_count INTEGER NOT NULL DEFAULT 0,
    ai_match_count INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

---

### 8. Configuration via Environment Variables

**Decision**: Standard env vars with sensible defaults

**Rationale**:
- Follows twelve-factor app methodology
- Easy to override in Docker/production
- Defaults work for development

**Configuration**:
| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_CODE_PATH` | `claude` | Path to Claude CLI executable |
| `CATEGORIZATION_BATCH_SIZE` | `50` | Transactions per AI batch |
| `CATEGORIZATION_CONFIDENCE_THRESHOLD` | `0.7` | Minimum confidence to apply |
| `CATEGORIZATION_TIMEOUT_SECONDS` | `120` | Timeout per AI invocation |

---

## Summary

All technical unknowns have been resolved:

| Unknown | Resolution |
|---------|------------|
| CLI invocation | Subprocess with stdin piping |
| Normalization approach | Rule-based token removal |
| Response parsing | JSON extraction with markdown handling |
| Retry strategy | 3 retries, exponential backoff (2s/4s/8s) |
| Rule matching | Case-insensitive substring matching |
| Prompt format | Structured JSON schema with examples |
| Schema changes | 2 new tables, 3 new transaction columns |
| Configuration | Environment variables with defaults |

Ready for Phase 1: Design & Contracts.
