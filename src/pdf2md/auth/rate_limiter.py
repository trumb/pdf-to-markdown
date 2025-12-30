"""Rate limiting with in-memory and Redis backends."""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from pdf2md.auth.models import User

logger = logging.getLogger(__name__)


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    async def check_rate_limit(self, user: User) -> bool:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user: User to check
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        pass


class InMemoryRateLimiter(RateLimiter):
    """
    In-memory rate limiter using fixed window algorithm.
    
    Suitable for single-process deployments and development.
    """

    def __init__(self) -> None:
        """Initialize in-memory rate limiter."""
        self.dictRequests: dict[str, list[datetime]] = defaultdict(list)

    async def check_rate_limit(self, user: User) -> bool:
        """
        Check rate limit using in-memory storage.
        
        Algorithm: Fixed 60-second window
        
        Args:
            user: User to check
            
        Returns:
            True if request allowed, False if rate limit exceeded
        """
        datetimeNow = datetime.now()
        datetimeWindowStart = datetimeNow - timedelta(minutes=1)

        # Clean old requests
        self.dictRequests[user.strTokenId] = [
            ts for ts in self.dictRequests[user.strTokenId] if ts > datetimeWindowStart
        ]

        # Check limit
        if len(self.dictRequests[user.strTokenId]) >= user.intRateLimit:
            return False

        # Record this request
        self.dictRequests[user.strTokenId].append(datetimeNow)
        return True


class RedisRateLimiter(RateLimiter):
    """
    Redis-backed rate limiter using fixed window algorithm.
    
    Required for multi-worker and distributed deployments.
    Uses atomic operations for thread safety.
    """

    def __init__(
        self, strRedisUrl: str, strFailMode: str = "closed"
    ) -> None:
        """
        Initialize Redis rate limiter.
        
        Args:
            strRedisUrl: Redis connection URL
            strFailMode: Behavior when Redis unavailable ("open" or "closed")
        """
        self.strRedisUrl: str = strRedisUrl
        self.strFailMode: str = strFailMode
        self.optRedisClient: Optional[any] = None
        self._boolRedisAvailable: bool = True

    async def connect(self) -> None:
        """Connect to Redis server."""
        try:
            import redis.asyncio as redis

            self.optRedisClient = redis.from_url(
                self.strRedisUrl, encoding="utf-8", decode_responses=True
            )
            # Test connection
            await self.optRedisClient.ping()
            self._boolRedisAvailable = True
            logger.info(f"Redis rate limiter connected: {self.strRedisUrl}")
        except Exception as e:
            self._boolRedisAvailable = False
            logger.error(f"Failed to connect to Redis: {e}")
            if self.strFailMode == "closed":
                raise

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self.optRedisClient:
            await self.optRedisClient.close()

    async def check_rate_limit(self, user: User) -> bool:
        """
        Check rate limit using Redis storage.
        
        Algorithm: Fixed window with atomic INCR operations
        Key format: rate_limit:{token_id}:{window_epoch}
        
        Args:
            user: User to check
            
        Returns:
            True if request allowed, False if rate limit exceeded
        """
        # Handle Redis unavailability
        if not self._boolRedisAvailable:
            if self.strFailMode == "open":
                logger.warning("Redis unavailable, allowing request (fail-open mode)")
                return True
            else:
                logger.error("Redis unavailable, rejecting request (fail-closed mode)")
                return False

        try:
            assert self.optRedisClient is not None

            # Calculate window start epoch (60-second windows)
            intWindowStart = int(datetime.now().timestamp()) // 60

            # Generate key
            strKey = f"rate_limit:{user.strTokenId}:{intWindowStart}"

            # Atomic increment
            intCurrentCount = await self.optRedisClient.incr(strKey)

            # Set expiry on first request in window
            if intCurrentCount == 1:
                await self.optRedisClient.expire(strKey, 60)

            # Check limit
            return intCurrentCount <= user.intRateLimit

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            self._boolRedisAvailable = False

            # Handle failure mode
            if self.strFailMode == "open":
                logger.warning("Redis error, allowing request (fail-open mode)")
                return True
            else:
                logger.error("Redis error, rejecting request (fail-closed mode)")
                return False


def get_rate_limiter(
    strBackend: str = "inmemory",
    optRedisUrl: Optional[str] = None,
    strFailMode: str = "closed",
) -> RateLimiter:
    """
    Get rate limiter instance based on backend type.
    
    Args:
        strBackend: Backend type ("inmemory" or "redis")
        optRedisUrl: Redis URL (required if backend is "redis")
        strFailMode: Redis failure mode ("open" or "closed")
        
    Returns:
        RateLimiter instance
        
    Raises:
        ValueError: If backend is invalid or Redis URL not provided
    """
    if strBackend == "inmemory":
        return InMemoryRateLimiter()
    elif strBackend == "redis":
        if not optRedisUrl:
            raise ValueError("Redis URL required for redis backend")
        return RedisRateLimiter(optRedisUrl, strFailMode)
    else:
        raise ValueError(f"Invalid rate limiter backend: {strBackend}")