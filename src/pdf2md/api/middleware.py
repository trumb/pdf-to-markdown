"""Middleware for rate limiting and RBAC enforcement."""

import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from pdf2md.api.dependencies import get_current_user


async def rate_limit_middleware(request: Request, call_next: any) -> Response:
    """
    Rate limiting middleware.
    
    Applies rate limits to authenticated endpoints based on user role.
    Skips rate limiting for health/docs endpoints.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/route handler
        
    Returns:
        Response
    """
    # Skip rate limiting for public endpoints
    listPublicPaths = ["/health", "/ready", "/docs", "/openapi.json"]
    if request.url.path in listPublicPaths:
        return await call_next(request)

    # Skip rate limiting for OPTIONS requests
    if request.method == "OPTIONS":
        return await call_next(request)

    # Get rate limiter from app state
    rate_limiter = request.app.state.rate_limiter

    # Try to get current user
    try:
        # Extract token from Authorization header
        strAuthHeader = request.headers.get("Authorization", "")
        if not strAuthHeader.startswith("Bearer "):
            # No auth header, let the endpoint handle authentication
            return await call_next(request)

        # Get current user
        from pdf2md.auth.token_manager import TokenManager

        database = request.app.state.database
        token_manager = TokenManager(database)
        strToken = strAuthHeader.replace("Bearer ", "")
        optUser = await token_manager.validate_token(strToken)

        if optUser is None:
            # Invalid token, let the endpoint handle authentication
            return await call_next(request)

        # Check rate limit
        boolAllowed = await rate_limiter.check_rate_limit(optUser)

        if not boolAllowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."},
                headers={"Retry-After": "60"},
            )

        # Record request start time for usage logging
        request.state.start_time = time.time()
        request.state.user = optUser

        # Process request
        response = await call_next(request)

        # Log token usage
        floatResponseTime = (time.time() - request.state.start_time) * 1000
        await token_manager.log_token_usage(
            optUser.strTokenId,
            request.url.path,
            request.method,
            response.status_code,
            optResponseTimeMs=int(floatResponseTime),
        )

        return response

    except Exception as e:
        # Error in middleware, let request continue
        return await call_next(request)