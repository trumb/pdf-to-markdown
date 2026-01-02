"""OpenAI token counter using tiktoken."""

from typing import Literal

import tiktoken

from pdf2md.tokens.base import TokenCounter, TokenCountingError


class OpenAITokenCounter(TokenCounter):
    """Token counter for OpenAI models using tiktoken."""

    def __init__(
        self, encoding: Literal["cl100k_base", "p50k_base"] = "cl100k_base"
    ) -> None:
        """
        Initialize OpenAI token counter.

        Args:
            encoding: Encoding to use
                - cl100k_base: GPT-4, GPT-3.5-turbo, text-embedding-ada-002
                - p50k_base: GPT-3 (davinci, curie, babbage, ada)

        Raises:
            TokenCountingError: If encoding is invalid
        """
        self.encoding_name = encoding

        try:
            self.encoding = tiktoken.get_encoding(encoding)
        except Exception as e:
            raise TokenCountingError(
                f"Failed to load tiktoken encoding '{encoding}': {e}"
            ) from e

    @property
    def name(self) -> str:
        """Return counter name."""
        return f"openai_{self.encoding_name}"

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using tiktoken.

        Args:
            text: Text to count tokens in

        Returns:
            Number of tokens

        Raises:
            TokenCountingError: If counting fails
        """
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            raise TokenCountingError(f"Token counting failed: {e}") from e
