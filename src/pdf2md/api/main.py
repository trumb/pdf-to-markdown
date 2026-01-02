"""FastAPI application with lifespan management."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pdf2md.api.middleware import rate_limit_middleware
from pdf2md.api.routes import admin, convert, health, jobs
from pdf2md.auth.rate_limiter import RedisRateLimiter, get_rate_limiter
from pdf2md.database import Database
from pdf2md.jobs import JobQueue, JobWorker

logger = logging.getLogger(__name__)

# Global state
database: Database
job_queue: JobQueue
job_worker: JobWorker
rate_limiter: Any


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.
    
    Handles startup and shutdown of database, rate limiter, and job worker.
    """
    global database, job_queue, job_worker, rate_limiter

    # Startup
    logger.info("Starting PDF2MD API")

    # Initialize database
    strDbPath = os.getenv("DATABASE_PATH", "data/pdf2md.db")
    database = Database(strDbPath)
    await database.connect()
    logger.info("Database connected")

    # Initialize job queue
    job_queue = JobQueue(database)
    logger.info("Job queue initialized")

    # Initialize rate limiter
    strRateLimitBackend = os.getenv("RATE_LIMIT_BACKEND", "inmemory")
    strRedisUrl = os.getenv("REDIS_URL")
    strFailMode = os.getenv("RATE_LIMIT_FAIL_MODE", "closed")

    rate_limiter = get_rate_limiter(strRateLimitBackend, strRedisUrl, strFailMode)

    if isinstance(rate_limiter, RedisRateLimiter):
        await rate_limiter.connect()

    logger.info(f"Rate limiter initialized: {strRateLimitBackend}")

    # Initialize and start job worker
    strResultsDir = os.getenv("RESULTS_DIR", "data/results")
    job_worker = JobWorker(job_queue, strResultsDir)
    await job_worker.start()
    logger.info("Job worker started")

    # Store in app state
    app.state.database = database
    app.state.job_queue = job_queue
    app.state.job_worker = job_worker
    app.state.rate_limiter = rate_limiter

    yield

    # Shutdown
    logger.info("Shutting down PDF2MD API")

    # Stop job worker
    await job_worker.stop()
    logger.info("Job worker stopped")

    # Disconnect rate limiter
    if isinstance(rate_limiter, RedisRateLimiter):
        await rate_limiter.disconnect()

    # Disconnect database
    await database.disconnect()
    logger.info("Database disconnected")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title="PDF2MD API",
        description="Enterprise-grade PDF-to-Markdown converter with RBAC",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
        root_path="/api",  # Support reverse proxy at /api/ prefix
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add rate limiting middleware
    app.middleware("http")(rate_limit_middleware)

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(convert.router, prefix="/v1", tags=["Convert"])
    app.include_router(jobs.router, prefix="/v1/jobs", tags=["Jobs"])
    app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])

    return app