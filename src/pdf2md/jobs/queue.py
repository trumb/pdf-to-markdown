"""Job queue management."""

import json
from datetime import datetime
from typing import Optional

from pdf2md.database import Database
from pdf2md.jobs.id_generator import generate_job_id
from pdf2md.jobs.models import Job, JobStatus


class JobQueue:
    """
    Manage job queue with SQLite backend.
    
    Handles job creation, status updates, and retrieval.
    """

    def __init__(self, database: Database) -> None:
        """
        Initialize job queue.
        
        Args:
            database: Database connection
        """
        self.database: Database = database

    async def create_job(
        self,
        strOwnerUserId: str,
        strPdfPath: str,
        dictOptions: dict[str, any],
    ) -> str:
        """
        Create a new job.
        
        Args:
            strOwnerUserId: User ID of job creator
            strPdfPath: Path to PDF file
            dictOptions: Job options (output format, image handling, etc.)
            
        Returns:
            Job ID
        """
        # Generate unique job ID
        strJobId = generate_job_id()

        # Check for collision (extremely unlikely but handle it)
        intAttempts = 0
        while intAttempts < 10:
            row = await self.database.fetch_one(
                "SELECT job_id FROM jobs WHERE job_id = ?", (strJobId,)
            )
            if row is None:
                break
            strJobId = generate_job_id()
            intAttempts += 1

        if intAttempts == 10:
            raise RuntimeError("Failed to generate unique job ID after 10 attempts")

        # Insert job
        datetimeNow = datetime.now()
        strOptionsJson = json.dumps(dictOptions)

        await self.database.execute(
            """
            INSERT INTO jobs (
                job_id, owner_user_id, pdf_path, status, created_at,
                throttled, options
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strJobId,
                strOwnerUserId,
                strPdfPath,
                JobStatus.PENDING.value,
                datetimeNow.isoformat(),
                0,
                strOptionsJson,
            ),
        )

        return strJobId

    async def get_job(self, strJobId: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            strJobId: Job ID
            
        Returns:
            Job object or None if not found
        """
        row = await self.database.fetch_one("SELECT * FROM jobs WHERE job_id = ?", (strJobId,))

        if row is None:
            return None

        return Job(
            strJobId=row["job_id"],
            strOwnerUserId=row["owner_user_id"],
            strPdfPath=row["pdf_path"],
            status=JobStatus(row["status"]),
            optResultPath=row["result_path"],
            optErrorMessage=row["error_message"],
            datetimeCreatedAt=datetime.fromisoformat(row["created_at"]),
            optStartedAt=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            optCompletedAt=(
                datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
            ),
            boolThrottled=bool(row["throttled"]),
            optThrottledBy=row["throttled_by"],
            strOptions=row["options"],
        )

    async def list_jobs(
        self,
        optStatus: Optional[JobStatus] = None,
        optOwnerUserId: Optional[str] = None,
        intLimit: int = 50,
        intOffset: int = 0,
    ) -> tuple[list[Job], int]:
        """
        List jobs with optional filtering.
        
        Args:
            optStatus: Filter by status
            optOwnerUserId: Filter by owner user ID
            intLimit: Maximum number of jobs to return
            intOffset: Offset for pagination
            
        Returns:
            Tuple of (jobs list, total count)
        """
        # Build query
        strQuery = "SELECT * FROM jobs WHERE 1=1"
        listParams: list[any] = []

        if optStatus:
            strQuery += " AND status = ?"
            listParams.append(optStatus.value)

        if optOwnerUserId:
            strQuery += " AND owner_user_id = ?"
            listParams.append(optOwnerUserId)

        # Get total count
        strCountQuery = strQuery.replace("SELECT *", "SELECT COUNT(*)")
        row = await self.database.fetch_one(strCountQuery, tuple(listParams))
        intTotal = row[0] if row else 0

        # Get paginated results
        strQuery += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        listParams.extend([intLimit, intOffset])

        listRows = await self.database.fetch_all(strQuery, tuple(listParams))

        listJobs: list[Job] = []
        for row in listRows:
            listJobs.append(
                Job(
                    strJobId=row["job_id"],
                    strOwnerUserId=row["owner_user_id"],
                    strPdfPath=row["pdf_path"],
                    status=JobStatus(row["status"]),
                    optResultPath=row["result_path"],
                    optErrorMessage=row["error_message"],
                    datetimeCreatedAt=datetime.fromisoformat(row["created_at"]),
                    optStartedAt=(
                        datetime.fromisoformat(row["started_at"]) if row["started_at"] else None
                    ),
                    optCompletedAt=(
                        datetime.fromisoformat(row["completed_at"])
                        if row["completed_at"]
                        else None
                    ),
                    boolThrottled=bool(row["throttled"]),
                    optThrottledBy=row["throttled_by"],
                    strOptions=row["options"],
                )
            )

        return listJobs, intTotal

    async def update_job_status(
        self,
        strJobId: str,
        status: JobStatus,
        optResultPath: Optional[str] = None,
        optErrorMessage: Optional[str] = None,
    ) -> bool:
        """
        Update job status.
        
        Args:
            strJobId: Job ID
            status: New status
            optResultPath: Path to result file (for COMPLETED)
            optErrorMessage: Error message (for FAILED)
            
        Returns:
            True if updated, False if job not found
        """
        job = await self.get_job(strJobId)
        if job is None:
            return False

        datetimeNow = datetime.now()

        # Build update query based on status
        if status == JobStatus.RUNNING:
            await self.database.execute(
                "UPDATE jobs SET status = ?, started_at = ? WHERE job_id = ?",
                (status.value, datetimeNow.isoformat(), strJobId),
            )
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            await self.database.execute(
                """
                UPDATE jobs SET status = ?, completed_at = ?, result_path = ?,
                error_message = ? WHERE job_id = ?
                """,
                (status.value, datetimeNow.isoformat(), optResultPath, optErrorMessage, strJobId),
            )
        else:
            await self.database.execute(
                "UPDATE jobs SET status = ? WHERE job_id = ?", (status.value, strJobId)
            )

        return True

    async def cancel_job(self, strJobId: str) -> bool:
        """
        Cancel a job.
        
        Args:
            strJobId: Job ID
            
        Returns:
            True if cancelled, False if not found or already completed
        """
        job = await self.get_job(strJobId)
        if job is None:
            return False

        # Can only cancel pending or running jobs
        if job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
            return False

        await self.update_job_status(strJobId, JobStatus.CANCELLED)
        return True

    async def throttle_job(self, strJobId: str, boolThrottled: bool, strUserId: str) -> bool:
        """
        Throttle or unthrottle a job.
        
        Args:
            strJobId: Job ID
            boolThrottled: True to throttle, False to unthrottle
            strUserId: User ID of admin/manager throttling the job
            
        Returns:
            True if updated, False if job not found
        """
        job = await self.get_job(strJobId)
        if job is None:
            return False

        await self.database.execute(
            "UPDATE jobs SET throttled = ?, throttled_by = ? WHERE job_id = ?",
            (1 if boolThrottled else 0, strUserId if boolThrottled else None, strJobId),
        )

        return True

    async def grant_job_access(
        self, strJobId: str, strGrantedToUserId: str, strGrantedByUserId: str
    ) -> bool:
        """
        Grant user access to a job.
        
        Args:
            strJobId: Job ID
            strGrantedToUserId: User ID to grant access to
            strGrantedByUserId: User ID granting access
            
        Returns:
            True if granted, False if job not found
        """
        job = await self.get_job(strJobId)
        if job is None:
            return False

        # Check if already granted
        row = await self.database.fetch_one(
            "SELECT 1 FROM job_access_grants WHERE job_id = ? AND granted_to_user_id = ?",
            (strJobId, strGrantedToUserId),
        )

        if row is not None:
            return True  # Already granted

        # Grant access
        await self.database.execute(
            """
            INSERT INTO job_access_grants (
                job_id, granted_to_user_id, granted_by_user_id, granted_at
            ) VALUES (?, ?, ?, ?)
            """,
            (strJobId, strGrantedToUserId, strGrantedByUserId, datetime.now().isoformat()),
        )

        return True