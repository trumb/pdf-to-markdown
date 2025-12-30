"""Permission checks and role-based access control."""

from enum import Enum

from pdf2md.auth.models import Role, User
from pdf2md.database import Database


class Permission(str, Enum):
    """API permissions."""

    # Job permissions
    CREATE_JOB = "create_job"
    VIEW_OWN_JOBS = "view_own_jobs"
    VIEW_ALL_JOBS = "view_all_jobs"
    STOP_OWN_JOBS = "stop_own_jobs"
    STOP_ALL_JOBS = "stop_all_jobs"
    THROTTLE_JOBS = "throttle_jobs"
    GRANT_JOB_ACCESS = "grant_job_access"

    # Admin permissions
    CREATE_TOKEN = "create_token"
    CREATE_ADMIN_TOKEN = "create_admin_token"
    VIEW_TOKENS = "view_tokens"
    REVOKE_TOKEN = "revoke_token"
    MODIFY_TOKEN = "modify_token"
    VIEW_TOKEN_USAGE = "view_token_usage"


# Role-based permission matrix
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: {
        # Admin has all permissions
        Permission.CREATE_JOB,
        Permission.VIEW_OWN_JOBS,
        Permission.VIEW_ALL_JOBS,
        Permission.STOP_OWN_JOBS,
        Permission.STOP_ALL_JOBS,
        Permission.THROTTLE_JOBS,
        Permission.GRANT_JOB_ACCESS,
        Permission.CREATE_TOKEN,
        Permission.CREATE_ADMIN_TOKEN,
        Permission.VIEW_TOKENS,
        Permission.REVOKE_TOKEN,
        Permission.MODIFY_TOKEN,
        Permission.VIEW_TOKEN_USAGE,
    },
    Role.JOB_MANAGER: {
        Permission.CREATE_JOB,
        Permission.VIEW_OWN_JOBS,
        Permission.VIEW_ALL_JOBS,
        Permission.STOP_OWN_JOBS,
        Permission.STOP_ALL_JOBS,
        Permission.THROTTLE_JOBS,
    },
    Role.JOB_WRITER: {
        Permission.CREATE_JOB,
        Permission.VIEW_OWN_JOBS,
        Permission.STOP_OWN_JOBS,
        Permission.GRANT_JOB_ACCESS,
    },
    Role.JOB_READER: {
        Permission.VIEW_OWN_JOBS,
    },
}


def check_permission(user: User, permission: Permission) -> bool:
    """
    Check if user has permission.
    
    Args:
        user: User to check
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    setPermissions = ROLE_PERMISSIONS.get(user.role, set())
    return permission in setPermissions


async def check_job_ownership(database: Database, strJobId: str, strUserId: str) -> bool:
    """
    Check if user owns a job.
    
    Args:
        database: Database connection
        strJobId: Job ID to check
        strUserId: User ID to check
        
    Returns:
        True if user owns job, False otherwise
    """
    row = await database.fetch_one(
        "SELECT owner_user_id FROM jobs WHERE job_id = ?", (strJobId,)
    )

    if row is None:
        return False

    return row["owner_user_id"] == strUserId


async def check_job_access(database: Database, strJobId: str, strUserId: str) -> bool:
    """
    Check if user has access to a job (owns it or has been granted access).
    
    Args:
        database: Database connection
        strJobId: Job ID to check
        strUserId: User ID to check
        
    Returns:
        True if user has access, False otherwise
    """
    # Check ownership
    boolOwns = await check_job_ownership(database, strJobId, strUserId)
    if boolOwns:
        return True

    # Check grants
    row = await database.fetch_one(
        "SELECT 1 FROM job_access_grants WHERE job_id = ? AND granted_to_user_id = ?",
        (strJobId, strUserId),
    )

    return row is not None