# Feature Specification: Gemini API Integration

**Feature Branch**: `007-gemini-api-integration`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "Implement Gemini API integration for AI categorization - Replace the current Claude CLI subprocess approach with a Google Gemini API integration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Categorization with Gemini (Priority: P1)

As a user, I want the transaction categorization feature to use the Google Gemini API so that I can categorize my transactions using a fast, cost-effective AI service without needing the Claude CLI installed locally.

**Why this priority**: This is the core functionality of the feature. Without the Gemini API integration working, no other aspects of the feature can function.

**Independent Test**: Can be fully tested by triggering categorization on uncategorized transactions and verifying they receive AI-assigned categories using the Gemini API.

**Acceptance Scenarios**:

1. **Given** uncategorized transactions exist in the database and a valid GEMINI_API_KEY is configured, **When** I trigger AI categorization, **Then** transactions receive categories assigned by Gemini with confidence scores.
2. **Given** the GEMINI_API_KEY environment variable is not set, **When** I trigger AI categorization, **Then** the system returns a clear error indicating the API key is missing.
3. **Given** valid API credentials and transactions to categorize, **When** Gemini returns categorization results, **Then** the results are parsed and applied to transactions in the same format as the previous Claude integration.

---

### User Story 2 - Graceful Error Handling (Priority: P2)

As a user, I want the system to handle API errors gracefully with automatic retries so that temporary network issues or API rate limits don't cause permanent categorization failures.

**Why this priority**: Reliability is essential for a good user experience, but the core functionality must work first before we polish error handling.

**Independent Test**: Can be tested by simulating API failures and verifying retry behavior with exponential backoff.

**Acceptance Scenarios**:

1. **Given** a temporary API failure occurs, **When** the system retries, **Then** it uses exponential backoff (configurable delays) before each retry attempt.
2. **Given** all retry attempts fail, **When** the final attempt fails, **Then** an appropriate error is logged and returned to the caller without crashing the application.
3. **Given** an API timeout occurs, **When** the timeout is detected, **Then** the system treats it as a retryable error and attempts retry with backoff.

---

### User Story 3 - Configuration Flexibility (Priority: P3)

As a developer, I want to configure the Gemini model and API key through environment variables so that I can easily switch models or update credentials without code changes.

**Why this priority**: Configuration is important for deployment flexibility but is not core to the feature's primary function.

**Independent Test**: Can be tested by changing environment variables and verifying the system uses the configured values.

**Acceptance Scenarios**:

1. **Given** GEMINI_MODEL environment variable is set to a specific model name, **When** the AI client is invoked, **Then** it uses the specified model.
2. **Given** GEMINI_MODEL environment variable is not set, **When** the AI client is invoked, **Then** it defaults to gemini-1.5-flash.

---

### Edge Cases

- What happens when the API key is invalid or revoked? The system returns a clear authentication error.
- What happens when Gemini returns malformed JSON? The system handles parsing errors gracefully and returns an empty result set rather than crashing.
- What happens when Gemini returns an empty response? The system treats this as no categorizations available and returns an empty result.
- What happens when the API rate limit is exceeded? The system retries with exponential backoff and eventually returns an appropriate error if limits persist.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a new gemini_client.py module that interfaces with the Google Generative AI API.
- **FR-002**: System MUST read the API key from the GEMINI_API_KEY environment variable.
- **FR-003**: System MUST expose an `invoke_and_parse(prompt: str) -> list[dict]` function with the same interface as the existing claude_client.
- **FR-004**: System MUST use the gemini-1.5-flash model by default, configurable via GEMINI_MODEL environment variable.
- **FR-005**: System MUST configure Gemini for JSON output using response_mime_type="application/json".
- **FR-006**: System MUST implement retry logic with exponential backoff matching the existing pattern (delays of 2s, 4s, 8s).
- **FR-007**: System MUST rename error classes to be generic: AIClientError, AITimeoutError, AIInvocationError.
- **FR-008**: System MUST update categorization_service.py to import from gemini_client instead of claude_client.
- **FR-009**: System MUST add google-generativeai to backend/requirements.txt.
- **FR-010**: System MUST add GEMINI_API_KEY entry to .env.example.
- **FR-011**: System MUST add GEMINI_API_KEY and GEMINI_MODEL settings to backend/app/config.py.
- **FR-012**: System MUST retain claude_client.py as a deprecated backup module (not actively used) to allow fallback if needed.
- **FR-013**: System MUST include fallback JSON parsing logic (handling markdown blocks, text around JSON) for resilience even when using Gemini's native JSON output mode.

### Key Entities

- **Gemini Client**: The new module responsible for API communication with Google's Generative AI service. Replaces the Claude CLI subprocess approach.
- **AI Error Classes**: Generic exception classes (AIClientError, AITimeoutError, AIInvocationError) that can be used with any AI provider.
- **Configuration Settings**: Environment-driven settings for API key and model selection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully categorize transactions using Gemini API without requiring the Claude CLI to be installed.
- **SC-002**: Categorization requests complete successfully at least 95% of the time when API credentials are valid and the service is available.
- **SC-003**: Failed API requests are automatically retried up to 3 times with increasing delays before returning an error.
- **SC-004**: The new integration maintains the same interface as the previous implementation, requiring no changes to calling code beyond import statements.
- **SC-005**: Configuration changes (API key, model) take effect without code modifications, only requiring environment variable updates.

## Clarifications

### Session 2026-02-08

- Q: What should happen to the existing claude_client.py file? → A: Keep as deprecated backup (no active use)
- Q: Should fallback JSON parsing logic be retained with Gemini's native JSON mode? → A: Keep fallback parsing logic for resilience

## Assumptions

- The google-generativeai Python package provides a stable API for interacting with Gemini models.
- The gemini-1.5-flash model is appropriate for transaction categorization tasks and available on the free tier.
- Response time from the Gemini API is comparable to or faster than the Claude CLI subprocess approach.
- The JSON output mode (response_mime_type="application/json") produces consistently parseable responses.
- Existing retry delays (2s, 4s, 8s) are appropriate for Gemini API rate limiting and transient failures.
