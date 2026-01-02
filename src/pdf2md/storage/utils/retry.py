"""Retry logic with exponential backoff."""

import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_retry(
    intMaxRetries: int = 3, floatBackoffBase: float = 2.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        intMaxRetries: Maximum number of retry attempts
        floatBackoffBase: Base for exponential backoff (wait = base^attempt)
        
    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: any, **kwargs: any) -> T:
            optLastException: Exception | None = None

            for intAttempt in range(intMaxRetries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    optLastException = e

                    if intAttempt < intMaxRetries - 1:
                        floatWaitTime = floatBackoffBase**intAttempt
                        logger.warning(
                            f"Retry {intAttempt + 1}/{intMaxRetries} for {func.__name__} "
                            f"after {floatWaitTime}s: {e}"
                        )
                        await asyncio.sleep(floatWaitTime)
                    else:
                        logger.error(
                            f"All {intMaxRetries} retries failed for {func.__name__}: {e}"
                        )

            if optLastException:
                raise optLastException

            raise RuntimeError("Unexpected retry logic failure")

        return wrapper

    return decorator
