"""Abstract base class for token counters."""

from abc import ABC, abstractmethod


class TokenCounter(ABC):
    """Abstract base class for token counting."""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens in

        Returns:
            Number of tokens

        Raises:
            TokenCountingError: If counting fails
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return counter name (e.g., 'openai_cl100k', 'claude')."""
        pass


class TokenCountingError(Exception):
    """Raised when token counting fails."""

    pass