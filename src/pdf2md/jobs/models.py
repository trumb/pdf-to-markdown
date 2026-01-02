"""Job models and status definitions."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    """Job status values."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class Job:
    """
    Job database model.
    
    Represents a PDF conversion job.
    """

    strJobId: str  # 10-character case-sensitive ID
    strOwnerUserId: str  # user_id of job creator
    strPdfPath: str  # Path to PDF file
    status: JobStatus
    optResultPath: Optional[str]  # Path to result markdown
    optErrorMessage: Optional[str]  # Error message if failed
    datetimeCreatedAt: datetime
    optStartedAt: Optional[datetime]
    optCompletedAt: Optional[datetime]
    boolThrottled: bool  # Whether job is throttled
    optThrottledBy: Optional[str]  # user_id of admin/manager who throttled
    strOptions: str  # JSON: output format, image handling, etc.
