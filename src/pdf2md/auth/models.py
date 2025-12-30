"""Authentication models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Role(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    JOB_MANAGER = "job_manager"
    JOB_WRITER = "job_writer"
    JOB_READER = "job_reader"


@dataclass
class User:
    """
    User model representing an authenticated API user.
    
    A User is derived from a Token at authentication time.
    """

    strTokenId: str  # UUID - references tokens table
    strUserId: str  # Human-readable identifier
    role: Role
    intRateLimit: int  # Requests per minute
    boolIsActive: bool
    optExpiresAt: Optional[datetime]


@dataclass
class Token:
    """
    Token database model.
    
    Represents a stored API token with bcrypt hash.
    """

    strTokenId: str  # UUID
    strTokenHash: str  # bcrypt hash
    strUserId: str  # Human-readable identifier
    role: Role
    datetimeCreatedAt: datetime
    optExpiresAt: Optional[datetime]
    boolIsActive: bool
    intRateLimit: int
    optScopes: Optional[str]  # JSON array
    optCreatedBy: Optional[str]  # token_id of creator