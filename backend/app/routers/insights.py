import logging
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.insights import InsightRequest, InsightResponse, InsightType
from app.services.insights_service import InsightsService
from app.services.gemini_client import AIClientError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insights", tags=["insights"])

COOLDOWN_SECONDS = 30
_last_generation_time: float = 0.0


@router.post("/generate", response_model=InsightResponse)
async def generate_insights(request: InsightRequest):
    """Generate AI-powered spending insights for a given time period."""
    global _last_generation_time

    # Enforce cooldown
    now = time.time()
    elapsed = now - _last_generation_time
    if elapsed < COOLDOWN_SECONDS and _last_generation_time > 0:
        remaining = int(COOLDOWN_SECONDS - elapsed) + 1
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Please wait before generating new insights.",
                "retry_after_seconds": remaining,
            },
        )

    try:
        if request.type == InsightType.REPORT:
            result = InsightsService.generate_report(
                request.period, request.date_from, request.date_to
            )
        else:
            result = InsightsService.generate_summary(
                request.period, request.date_from, request.date_to
            )

        _last_generation_time = time.time()
        return result

    except AIClientError as e:
        logger.error(f"AI service error generating insights: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again in a few minutes.",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating insights: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again.",
        )
