"""Tests for job API endpoints."""

import pytest

from pdf2md.auth.models import Role
from pdf2md.auth.token_manager import TokenManager
from pdf2md.database import Database
from pdf2md.jobs.models import JobStatus
from pdf2md.jobs.queue import JobQueue


@pytest.fixture
async def database():
    """Create test database."""
    db = Database(":memory:")
    await db.connect()
    yield db
    await db.disconnect()


@pytest.fixture
async def job_queue(database):
    """Create job queue."""
    return JobQueue(database)


@pytest.fixture
async def admin_token(database):
    """Create admin token."""
    token_manager = TokenManager(database)
    _, token = await token_manager.create_token("admin-test", Role.ADMIN)
    return token


@pytest.fixture
async def writer_token(database):
    """Create writer token."""
    token_manager = TokenManager(database)
    _, token = await token_manager.create_token("writer-test", Role.JOB_WRITER)
    return token


@pytest.mark.asyncio
async def test_create_job(job_queue):
    """Test job creation."""
    job_id = await job_queue.create_job(
        "test-user",
        "/path/to/test.pdf",
        {"output_format": "markdown"}
    )
    
    assert len(job_id) == 10
    
    job = await job_queue.get_job(job_id)
    assert job is not None
    assert job.strOwnerUserId == "test-user"
    assert job.status == JobStatus.PENDING


@pytest.mark.asyncio
async def test_job_id_uniqueness(job_queue):
    """Test that job IDs are unique."""
    job_id_1 = await job_queue.create_job("user1", "/test1.pdf", {})
    job_id_2 = await job_queue.create_job("user1", "/test2.pdf", {})
    
    assert job_id_1 != job_id_2


@pytest.mark.asyncio
async def test_job_status_transitions(job_queue):
    """Test job status transitions."""
    job_id = await job_queue.create_job("test-user", "/test.pdf", {})
    
    # PENDING -> RUNNING
    success = await job_queue.update_job_status(job_id, JobStatus.RUNNING)
    assert success
    
    job = await job_queue.get_job(job_id)
    assert job.status == JobStatus.RUNNING
    assert job.optStartedAt is not None
    
    # RUNNING -> COMPLETED
    success = await job_queue.update_job_status(
        job_id, JobStatus.COMPLETED, optResultPath="/results/test.md"
    )
    assert success
    
    job = await job_queue.get_job(job_id)
    assert job.status == JobStatus.COMPLETED
    assert job.optCompletedAt is not None
    assert job.optResultPath == "/results/test.md"


@pytest.mark.asyncio
async def test_cancel_job(job_queue):
    """Test job cancellation."""
    job_id = await job_queue.create_job("test-user", "/test.pdf", {})
    
    # Can cancel pending job
    success = await job_queue.cancel_job(job_id)
    assert success
    
    job = await job_queue.get_job(job_id)
    assert job.status == JobStatus.CANCELLED


@pytest.mark.asyncio
async def test_throttle_job(job_queue):
    """Test job throttling."""
    job_id = await job_queue.create_job("test-user", "/test.pdf", {})
    
    # Throttle job
    success = await job_queue.throttle_job(job_id, True, "admin-user")
    assert success
    
    job = await job_queue.get_job(job_id)
    assert job.boolThrottled is True
    assert job.optThrottledBy == "admin-user"
    
    # Unthrottle job
    success = await job_queue.throttle_job(job_id, False, "admin-user")
    assert success
    
    job = await job_queue.get_job(job_id)
    assert job.boolThrottled is False


@pytest.mark.asyncio
async def test_grant_job_access(job_queue):
    """Test granting job access."""
    job_id = await job_queue.create_job("owner-user", "/test.pdf", {})
    
    # Grant access
    success = await job_queue.grant_job_access(job_id, "reader-user", "owner-user")
    assert success
    
    # Check access
    from pdf2md.auth.permissions import check_job_access
    
    has_access = await check_job_access(job_queue.database, job_id, "reader-user")
    assert has_access