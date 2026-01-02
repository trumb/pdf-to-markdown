"""Job management endpoints."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pdf2md.api.dependencies import get_current_user, get_database, get_job_queue
from pdf2md.auth.models import User
from pdf2md.auth.permissions import (
    Permission,
    check_job_access,
    check_job_ownership,
    check_permission,
)
from pdf2md.database import Database
from pdf2md.jobs.models import JobStatus
from pdf2md.jobs.queue import JobQueue

router = APIRouter()


class JobResponse(BaseModel):
    """Job details response."""

    job_id: str
    owner_user_id: str
    status: str
    pdf_path: str
    result_path: Optional[str]
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    throttled: bool
    throttled_by: Optional[str]


class JobListResponse(BaseModel):
    """Job list response with pagination."""

    jobs: list[JobResponse]
    total: int
    limit: int
    offset: int


class ThrottleRequest(BaseModel):
    """Request to throttle/unthrottle a job."""

    throttled: bool


class GrantAccessRequest(BaseModel):
    """Request to grant job access to another user."""

    user_id: str


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    job_queue: JobQueue = Depends(get_job_queue),
) -> JobListResponse:
    """
    List jobs.
    
    - admin/job_manager: See all jobs
    - job_writer/job_reader: See only own jobs and granted jobs
    
    Args:
        status: Filter by status (optional)
        limit: Maximum jobs to return
        offset: Offset for pagination
        user: Current user
        job_queue: Job queue instance
        
    Returns:
        List of jobs with pagination info
    """
    # Parse status filter
    optStatusFilter: Optional[JobStatus] = None
    if status:
        try:
            optStatusFilter = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {status}"
            )

    # Check if user can see all jobs
    boolCanSeeAll = check_permission(user, Permission.VIEW_ALL_JOBS)

    if boolCanSeeAll:
        # Admin/job_manager: see all jobs
        listJobs, intTotal = await job_queue.list_jobs(
            optStatus=optStatusFilter, intLimit=limit, intOffset=offset
        )
    else:
        # Others: see only own jobs
        listJobs, intTotal = await job_queue.list_jobs(
            optStatus=optStatusFilter,
            optOwnerUserId=user.strUserId,
            intLimit=limit,
            intOffset=offset,
        )

    # Convert to response format
    listJobResponses = [
        JobResponse(
            job_id=job.strJobId,
            owner_user_id=job.strOwnerUserId,
            status=job.status.value,
            pdf_path=job.strPdfPath,
            result_path=job.optResultPath,
            error_message=job.optErrorMessage,
            created_at=job.datetimeCreatedAt.isoformat(),
            started_at=job.optStartedAt.isoformat() if job.optStartedAt else None,
            completed_at=job.optCompletedAt.isoformat() if job.optCompletedAt else None,
            throttled=job.boolThrottled,
            throttled_by=job.optThrottledBy,
        )
        for job in listJobs
    ]

    return JobListResponse(jobs=listJobResponses, total=intTotal, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    job_queue: JobQueue = Depends(get_job_queue),
    database: Database = Depends(get_database),
) -> JobResponse:
    """
    Get job details.
    
    Args:
        job_id: Job ID
        user: Current user
        job_queue: Job queue instance
        database: Database instance
        
    Returns:
        Job details
        
    Raises:
        HTTPException: If job not found or access denied
    """
    optJob = await job_queue.get_job(job_id)
    if optJob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check access
    boolCanSeeAll = check_permission(user, Permission.VIEW_ALL_JOBS)
    if not boolCanSeeAll:
        boolHasAccess = await check_job_access(database, job_id, user.strUserId)
        if not boolHasAccess:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this job"
            )

    return JobResponse(
        job_id=optJob.strJobId,
        owner_user_id=optJob.strOwnerUserId,
        status=optJob.status.value,
        pdf_path=optJob.strPdfPath,
        result_path=optJob.optResultPath,
        error_message=optJob.optErrorMessage,
        created_at=optJob.datetimeCreatedAt.isoformat(),
        started_at=optJob.optStartedAt.isoformat() if optJob.optStartedAt else None,
        completed_at=optJob.optCompletedAt.isoformat() if optJob.optCompletedAt else None,
        throttled=optJob.boolThrottled,
        throttled_by=optJob.optThrottledBy,
    )


@router.get("/{job_id}/result")
async def get_job_result(
    job_id: str,
    user: User = Depends(get_current_user),
    job_queue: JobQueue = Depends(get_job_queue),
    database: Database = Depends(get_database),
) -> FileResponse:
    """
    Download job result.
    
    Args:
        job_id: Job ID
        user: Current user
        job_queue: Job queue instance
        database: Database instance
        
    Returns:
        Result file
        
    Raises:
        HTTPException: If job not found, not completed, or access denied
    """
    optJob = await job_queue.get_job(job_id)
    if optJob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check access
    boolCanSeeAll = check_permission(user, Permission.VIEW_ALL_JOBS)
    if not boolCanSeeAll:
        boolHasAccess = await check_job_access(database, job_id, user.strUserId)
        if not boolHasAccess:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this job"
            )

    # Check if job is completed
    if optJob.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (status: {optJob.status.value})",
        )

    # Check if result file exists
    if not optJob.optResultPath:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Result file not found"
        )

    pathResult = Path(optJob.optResultPath)
    if not pathResult.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Result file not found on disk"
        )

    return FileResponse(
        path=str(pathResult),
        media_type="text/markdown",
        filename=f"{job_id}.md",
    )


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    user: User = Depends(get_current_user),
    job_queue: JobQueue = Depends(get_job_queue),
    database: Database = Depends(get_database),
) -> dict[str, str]:
    """
    Cancel a job.
    
    Permissions: admin, job_manager, job_writer (if owner)
    
    Args:
        job_id: Job ID
        user: Current user
        job_queue: Job queue instance
        database: Database instance
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If job not found or access denied
    """
    optJob = await job_queue.get_job(job_id)
    if optJob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check permission
    boolCanStopAll = check_permission(user, Permission.STOP_ALL_JOBS)
    if not boolCanStopAll:
        # Check if user owns job
        boolOwns = await check_job_ownership(database, job_id, user.strUserId)
        if not boolOwns:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own jobs",
            )

    # Cancel job
    boolSuccess = await job_queue.cancel_job(job_id)
    if not boolSuccess:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled (already completed or failed)",
        )

    return {"message": "Job cancelled successfully"}


@router.post("/{job_id}/throttle")
async def throttle_job(
    job_id: str,
    request: ThrottleRequest,
    user: User = Depends(get_current_user),
    job_queue: JobQueue = Depends(get_job_queue),
) -> dict[str, str]:
    """
    Throttle or unthrottle a job.
    
    Permissions: admin, job_manager
    
    Args:
        job_id: Job ID
        request: Throttle request
        user: Current user
        job_queue: Job queue instance
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If job not found or access denied
    """
    # Check permission
    if not check_permission(user, Permission.THROTTLE_JOBS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role.value}' cannot throttle jobs",
        )

    # Throttle job
    boolSuccess = await job_queue.throttle_job(job_id, request.throttled, user.strUserId)
    if not boolSuccess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    strAction = "throttled" if request.throttled else "unthrottled"
    return {"message": f"Job {strAction} successfully"}


@router.post("/{job_id}/grant-access")
async def grant_job_access(
    job_id: str,
    request: GrantAccessRequest,
    user: User = Depends(get_current_user),
    job_queue: JobQueue = Depends(get_job_queue),
    database: Database = Depends(get_database),
) -> dict[str, str]:
    """
    Grant another user access to a job.
    
    Permissions: admin, job_writer (if owner)
    
    Args:
        job_id: Job ID
        request: Grant access request
        user: Current user
        job_queue: Job queue instance
        database: Database instance
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If job not found or access denied
    """
    optJob = await job_queue.get_job(job_id)
    if optJob is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check permission
    if not check_permission(user, Permission.GRANT_JOB_ACCESS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role.value}' cannot grant job access",
        )

    # If not admin, must own the job
    if user.role.value != "admin":
        boolOwns = await check_job_ownership(database, job_id, user.strUserId)
        if not boolOwns:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only grant access to your own jobs",
            )

    # Grant access
    await job_queue.grant_job_access(job_id, request.user_id, user.strUserId)

    return {"message": f"Access granted to user '{request.user_id}'"}
