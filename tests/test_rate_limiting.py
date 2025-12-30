"""Tests for rate limiting functionality."""

import pytest
from datetime import datetime

from pdf2md.auth.models import Role, User
from pdf2md.auth.rate_limiter import InMemoryRateLimiter, get_rate_limiter


@pytest.fixture
def user():
    """Create test user."""
    return User(
        strTokenId="test-token-id",
        strUserId="test-user",
        role=Role.JOB_WRITER,
        intRateLimit=10,
        boolIsActive=True,
        optExpiresAt=None,
    )


@pytest.mark.asyncio
async def test_inmemory_rate_limiter_allows_under_limit(user):
    """Test that requests under rate limit are allowed."""
    rate_limiter = InMemoryRateLimiter()
    
    # Make 5 requests (under limit of 10)
    for _ in range(5):
        allowed = await rate_limiter.check_rate_limit(user)
        assert allowed is True


@pytest.mark.asyncio
async def test_inmemory_rate_limiter_blocks_over_limit(user):
    """Test that requests over rate limit are blocked."""
    rate_limiter = InMemoryRateLimiter()
    
    # Make 10 requests (at limit)
    for _ in range(10):
        allowed = await rate_limiter.check_rate_limit(user)
        assert allowed is True
    
    # 11th request should be blocked
    allowed = await rate_limiter.check_rate_limit(user)
    assert allowed is False


@pytest.mark.asyncio
async def test_rate_limiter_factory_inmemory():
    """Test rate limiter factory for in-memory backend."""
    rate_limiter = get_rate_limiter("inmemory")
    assert isinstance(rate_limiter, InMemoryRateLimiter)


@pytest.mark.asyncio
async def test_rate_limiter_factory_invalid_backend():
    """Test rate limiter factory with invalid backend."""
    with pytest.raises(ValueError, match="Invalid rate limiter backend"):
        get_rate_limiter("invalid")


@pytest.mark.asyncio
async def test_different_users_independent_limits():
    """Test that different users have independent rate limits."""
    rate_limiter = InMemoryRateLimiter()
    
    user1 = User(
        strTokenId="token-1",
        strUserId="user-1",
        role=Role.JOB_WRITER,
        intRateLimit=5,
        boolIsActive=True,
        optExpiresAt=None,
    )
    
    user2 = User(
        strTokenId="token-2",
        strUserId="user-2",
        role=Role.JOB_WRITER,
        intRateLimit=5,
        boolIsActive=True,
        optExpiresAt=None,
    )
    
    # Use up user1's limit
    for _ in range(5):
        assert await rate_limiter.check_rate_limit(user1) is True
    
    # user1 should be blocked
    assert await rate_limiter.check_rate_limit(user1) is False
    
    # user2 should still be allowed
    assert await rate_limiter.check_rate_limit(user2) is True