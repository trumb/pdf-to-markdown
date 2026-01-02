"""Custom token counter for user-provided tokenizers."""

from typing import Callable

from pdf2md.tokens.base import TokenCounter, TokenCountingError


class CustomTokenCounter(TokenCounter):
    """
    Custom token counter using user-provided tokenizer function.

    Allows integration with any tokenizer by providing a callable
    that takes text and returns token count.
    """

    def __init__(self, tokenizer_func: Callable[[str], int], counter_name: str) -> None:
        """
        Initialize custom token counter.

        Args:
            tokenizer_func: Callable that takes text string and returns token count
            counter_name: Name for this counter (e.g., 'custom_bpe')

        Raises:
            ValueError: If tokenizer_func is not callable
        """
        if not callable(tokenizer_func):
            raise ValueError("tokenizer_func must be callable")

        self.tokenizer_func = tokenizer_func
        self.counter_name = counter_name

    @property
    def name(self) -> str:
        """Return counter name."""
        return self.counter_name

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using custom tokenizer.

        Args:
            text: Text to count tokens in

        Returns:
            Number of tokens

        Raises:
            TokenCountingError: If counting fails
        """
        try:
            count = self.tokenizer_func(text)

            if not isinstance(count, int):
                raise TokenCountingError(
                    f"Tokenizer function returned {type(count)}, expected int"
                )

            if count < 0:
                raise TokenCountingError(
                    f"Tokenizer function returned negative count: {count}"
                )

            return count

        except TokenCountingError:
            raise
        except Exception as e:
            raise TokenCountingError(
                f"Custom tokenizer '{self.counter_name}' failed: {e}"
            ) from e
