"""Admin token management endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from pdf2md.api.dependencies import get_current_user, get_database
from pdf2md.auth.models import Role, User
from pdf2md.auth.permissions import Permission, check_permission
from pdf2md.auth.token_manager import TokenManager
from pdf2md.database import Database

router = APIRouter()


class CreateTokenRequest(BaseModel):
    """Request to create a new token."""

    user_id: str
    role: str
    expires_days: Optional[int] = None
    rate_limit: Optional[int] = None


class CreateTokenResponse(BaseModel):
    """Response for token creation."""

    token: str
    token_id: str
    user_id: str
    role: str
    expires_at: Optional[str]
    rate_limit: int


class TokenSummary(BaseModel):
    """Token summary (without hash)."""

    token_id: str
    user_id: str
    role: str
    created_at: str
    expires_at: Optional[str]
    is_active: bool
    rate_limit: int
    created_by: Optional[str]


class TokenListResponse(BaseModel):
    """List of tokens."""

    tokens: list[TokenSummary]


class UpdateTokenRequest(BaseModel):
    """Request to update token."""

    is_active: Optional[bool] = None
    rate_limit: Optional[int] = None


class TokenUsageResponse(BaseModel):
    """Token usage audit trail."""

    usage: list[dict[str, Any]]


@router.post("/tokens", response_model=CreateTokenResponse)
async def create_token(
    request: CreateTokenRequest,
    user: User = Depends(get_current_user),
    database: Database = Depends(get_database),
) -> CreateTokenResponse:
    """
    Create a new API token.
    
    SECURITY: Cannot create admin tokens via API. Admin tokens must be
    created via CLI with direct database access.
    
    Permissions: admin only
    
    Args:
        request: Token creation request
        user: Current user (must be admin)
        database: Database instance
        
    Returns:
        New token details
        
    Raises:
        HTTPException: If not admin or trying to create admin token
    """
    # Check permission
    if not check_permission(user, Permission.CREATE_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role.value}' cannot create tokens",
        )

    # Validate role
    try:
        role = Role(request.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {request.role}",
        )

    # SECURITY: Admin tokens can only be created via CLI
    if role == Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin tokens can only be created via CLI (pdf2md admin create-token)",
        )

    # Create token
    token_manager = TokenManager(database)
    strTokenId, strToken = await token_manager.create_token(
        request.user_id,
        role,
        optExpiresDays=request.expires_days,
        optCreatedBy=user.strTokenId,
        intRateLimit=request.rate_limit,
    )

    # Get token details
    optTokenDetails = await token_manager.get_token_by_id(strTokenId)
    assert optTokenDetails is not None

    return CreateTokenResponse(
        token=strToken,
        token_id=strTokenId,
        user_id=request.user_id,
        role=role.value,
        expires_at=(
            optTokenDetails.optExpiresAt.isoformat() if optTokenDetails.optExpiresAt else None
        ),
        rate_limit=optTokenDetails.intRateLimit,
    )


@router.get("/tokens", response_model=TokenListResponse)
async def list_tokens(
    user: User = Depends(get_current_user),
    database: Database = Depends(get_database),
) -> TokenListResponse:
    """
    List all tokens.
    
    Permissions: admin only
    
    Args:
        user: Current user (must be admin)
        database: Database instance
        
    Returns:
        List of all tokens
        
    Raises:
        HTTPException: If not admin
    """
    # Check permission
    if not check_permission(user, Permission.VIEW_TOKENS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role.value}' cannot view tokens",
        )

    token_manager = TokenManager(database)
    listTokens = await token_manager.list_tokens()

    listTokenSummaries = [
        TokenSummary(
            token_id=token.strTokenId,
            user_id=token.strUserId,
            role=token.role.value,
            created_at=token.datetimeCreatedAt.isoformat(),
            expires_at=token.optExpiresAt.isoformat() if token.optExpiresAt else None,
            is_active=token.boolIsActive,
            rate_limit=token.intRateLimit,
            created_by=token.optCreatedBy,
        )
        for token in listTokens
    ]

    return TokenListResponse(tokens=listTokenSummaries)


@router.delete("/tokens/{token_id}")
async def revoke_token(
    token_id: str,
    user: User = Depends(get_current_user),
    database: Database = Depends(get_database),
) -> dict[str, str]:
    """
    Revoke (permanently delete) a token.
    
    Permissions: admin only
    
    Args:
        token_id: Token ID to revoke
        user: Current user (must be admin)
        database: Database instance
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If not admin or token not found
    """
    # Check permission
    if not check_permission(user, Permission.REVOKE_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role.value}' cannot revoke tokens",
        )

    token_manager = TokenManager(database)
    boolSuccess = await token_manager.revoke_token(token_id)

    if not boolSuccess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    return {"message": "Token revoked successfully"}


@router.patch("/tokens/{token_id}")
async def update_token(
    token_id: str,
    request: UpdateTokenRequest,
    user: User = Depends(get_current_user),
    database: Database = Depends(get_database),
) -> dict[str, str]:
    """
    Update token properties.
    
    Can enable/disable tokens and update rate limits.
    
    Permissions: admin only
    
    Args:
        token_id: Token ID to update
        request: Update request
        user: Current user (must be admin)
        database: Database instance
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If not admin or token not found
    """
    # Check permission
    if not check_permission(user, Permission.MODIFY_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role.value}' cannot modify tokens",
        )

    token_manager = TokenManager(database)

    # Check token exists
    optToken = await token_manager.get_token_by_id(token_id)
    if optToken is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    # Update is_active
    if request.is_active is not None:
        if request.is_active:
            await token_manager.enable_token(token_id)
        else:
            await token_manager.disable_token(token_id)

    # Update rate_limit
    if request.rate_limit is not None:
        await token_manager.update_rate_limit(token_id, request.rate_limit)

    return {"message": "Token updated successfully"}


@router.get("/tokens/{token_id}/usage", response_model=TokenUsageResponse)
async def get_token_usage(
    token_id: str,
    days: int = 7,
    user: User = Depends(get_current_user),
    database: Database = Depends(get_database),
) -> TokenUsageResponse:
    """
    Get token usage audit trail.
    
    Permissions: admin only
    
    Args:
        token_id: Token ID
        days: Number of days to look back
        user: Current user (must be admin)
        database: Database instance
        
    Returns:
        Token usage records
        
    Raises:
        HTTPException: If not admin or token not found
    """
    # Check permission
    if not check_permission(user, Permission.VIEW_TOKEN_USAGE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role.value}' cannot view token usage",
        )

    token_manager = TokenManager(database)

    # Check token exists
    optToken = await token_manager.get_token_by_id(token_id)
    if optToken is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    listUsage = await token_manager.get_token_usage(token_id, days)

    return TokenUsageResponse(usage=listUsage)
