"""Dependency injection for FastAPI."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pdf2md.auth.models import User
from pdf2md.auth.token_manager import TokenManager
from pdf2md.database import Database
from pdf2md.jobs.queue import JobQueue

security = HTTPBearer()


async def get_database(request: Request) -> Database:
    """
    Get database instance from app state.
    
    Args:
        request: FastAPI request
        
    Returns:
        Database instance
    """
    return request.app.state.database


async def get_job_queue(request: Request) -> JobQueue:
    """
    Get job queue instance from app state.
    
    Args:
        request: FastAPI request
        
    Returns:
        JobQueue instance
    """
    return request.app.state.job_queue


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    database: Database = Depends(get_database),
) -> User:
    """
    Authenticate user from Bearer token.
    
    Args:
        credentials: HTTP authorization credentials
        database: Database instance
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    strToken = credentials.credentials

    # Validate token format
    if not strToken.startswith("pdf2md_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token
    token_manager = TokenManager(database)
    optUser = await token_manager.validate_token(strToken)

    if optUser is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return optUser
