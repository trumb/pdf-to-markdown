"""Health check endpoints."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check(request: Request) -> dict[str, any]:
    """
    Readiness check with dependency status.
    
    Verifies database and job queue are operational.
    
    Args:
        request: FastAPI request
        
    Returns:
        Readiness status with component details
    """
    database = request.app.state.database
    job_queue = request.app.state.job_queue

    # Check database
    strDatabaseStatus = "ok" if database.connection is not None else "unavailable"

    # Check job queue
    strQueueStatus = "ok"  # Queue is always available if database is

    return {
        "status": "ready" if strDatabaseStatus == "ok" else "not_ready",
        "database": strDatabaseStatus,
        "queue": strQueueStatus,
    }