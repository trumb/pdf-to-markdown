"""Claude token counter (approximation based on OpenAI)."""

import tiktoken

from pdf2md.tokens.base import TokenCounter, TokenCountingError


class ClaudeTokenCounter(TokenCounter):
    """
    Token counter for Claude models (approximation).

    Claude uses a different tokenizer, but we approximate using
    OpenAI's cl100k_base encoding with a 1.1x multiplier.

    This provides a conservative estimate for token budgeting.
    """

    MULTIPLIER = 1.1

    def __init__(self) -> None:
        """Initialize Claude token counter."""
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            raise TokenCountingError(
                f"Failed to load tiktoken encoding for Claude approximation: {e}"
            ) from e

    @property
    def name(self) -> str:
        """Return counter name."""
        return "claude_estimate"

    def count_tokens(self, text: str) -> int:
        """
        Estimate Claude tokens.

        Args:
            text: Text to count tokens in

        Returns:
            Estimated number of tokens (conservative)

        Raises:
            TokenCountingError: If counting fails
        """
        try:
            # Use OpenAI cl100k_base encoding
            tokens = self.encoding.encode(text)
            base_count = len(tokens)

            # Apply multiplier for conservative estimate
            estimated_count = int(base_count * self.MULTIPLIER)

            return estimated_count
        except Exception as e:
            raise TokenCountingError(f"Claude token estimation failed: {e}") from e
