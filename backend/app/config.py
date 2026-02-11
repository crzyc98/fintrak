"""
Configuration settings for the FinTrack application.
Environment variables with sensible defaults.
"""
import os


# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "fintrak.duckdb")

# AI Categorization Settings
CLAUDE_CODE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")  # Deprecated: retained for rollback
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
CATEGORIZATION_BATCH_SIZE = int(os.getenv("CATEGORIZATION_BATCH_SIZE", "50"))
CATEGORIZATION_CONFIDENCE_THRESHOLD = float(
    os.getenv("CATEGORIZATION_CONFIDENCE_THRESHOLD", "0.7")
)
CATEGORIZATION_TIMEOUT_SECONDS = int(
    os.getenv("CATEGORIZATION_TIMEOUT_SECONDS", "120")
)

# NL Search Settings
NL_SEARCH_TIMEOUT_SECONDS = int(os.getenv("NL_SEARCH_TIMEOUT_SECONDS", "15"))

# Retry settings for AI calls
CATEGORIZATION_MAX_RETRIES = 3
CATEGORIZATION_RETRY_DELAYS = [2, 4, 8]  # Exponential backoff in seconds
