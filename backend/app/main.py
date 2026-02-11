import logging
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # loads .env from cwd; in Docker, use real env vars instead

from app.database import init_db, close_connection
from app.routers import accounts, categories, transactions, categorization, csv_import, insights, enrichment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FinTrack API",
    description="Personal finance tracking API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )
    return response


@app.on_event("startup")
async def startup_event():
    logger.info("Starting FinTrack API...")
    init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FinTrack API...")
    close_connection()
    logger.info("Shutdown complete")


app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(categorization.router)
app.include_router(csv_import.router)
app.include_router(insights.router)
app.include_router(enrichment.router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
