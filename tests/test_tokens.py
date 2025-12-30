"""Tests for token counters."""

import pytest

from pdf2md.tokens.claude_counter import ClaudeTokenCounter
from pdf2md.tokens.custom_counter import CustomTokenCounter
from pdf2md.tokens.openai_counter import OpenAITokenCounter


class TestOpenAITokenCounter:
    """Test OpenAI token counter."""

    def test_cl100k_base_encoding(self) -> None:
        """Test cl100k_base encoding."""
        counter = OpenAITokenCounter("cl100k_base")
        assert counter.name == "openai_cl100k_base"

        # Test basic counting
        text = "Hello, world!"
        count = counter.count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_p50k_base_encoding(self) -> None:
        """Test p50k_base encoding."""
        counter = OpenAITokenCounter("p50k_base")
        assert counter.name == "openai_p50k_base"

        # Test basic counting
        text = "Hello, world!"
        count = counter.count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_empty_string(self) -> None:
        """Test counting empty string."""
        counter = OpenAITokenCounter("cl100k_base")
        count = counter.count_tokens("")
        assert count == 0

    def test_deterministic_counting(self) -> None:
        """Test that token counting is deterministic."""
        counter = OpenAITokenCounter("cl100k_base")
        text = "This is a test sentence for deterministic token counting."

        count1 = counter.count_tokens(text)
        count2 = counter.count_tokens(text)
        assert count1 == count2


class TestClaudeTokenCounter:
    """Test Claude token counter."""

    def test_claude_estimation(self) -> None:
        """Test Claude token estimation."""
        counter = ClaudeTokenCounter()
        assert counter.name == "claude_estimate"

        text = "Hello, world!"
        count = counter.count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_claude_multiplier(self) -> None:
        """Test that Claude estimate is ~1.1x OpenAI."""
        openai_counter = OpenAITokenCounter("cl100k_base")
        claude_counter = ClaudeTokenCounter()

        text = "This is a longer test to verify the multiplier relationship."

        openai_count = openai_counter.count_tokens(text)
        claude_count = claude_counter.count_tokens(text)

        # Claude should be approximately 1.1x OpenAI
        ratio = claude_count / openai_count
        assert 1.0 <= ratio <= 1.2  # Allow some variance

    def test_deterministic_estimation(self) -> None:
        """Test that Claude estimation is deterministic."""
        counter = ClaudeTokenCounter()
        text = "Deterministic token estimation test."

        count1 = counter.count_tokens(text)
        count2 = counter.count_tokens(text)
        assert count1 == count2


class TestCustomTokenCounter:
    """Test custom token counter."""

    def test_custom_tokenizer(self) -> None:
        """Test custom tokenizer function."""

        def simple_tokenizer(text: str) -> int:
            """Simple whitespace tokenizer."""
            return len(text.split())

        counter = CustomTokenCounter(simple_tokenizer, "whitespace")
        assert counter.name == "whitespace"

        count = counter.count_tokens("Hello world this is a test")
        assert count == 6  # 6 words

    def test_invalid_tokenizer(self) -> None:
        """Test that non-callable raises ValueError."""
        with pytest.raises(ValueError, match="must be callable"):
            CustomTokenCounter("not_a_function", "invalid")  # type: ignore[arg-type]

    def test_tokenizer_returning_non_int(self) -> None:
        """Test that tokenizer returning non-int raises error."""

        def bad_tokenizer(text: str) -> str:  # type: ignore[misc]
            """Returns string instead of int."""
            return "not an int"  # type: ignore[return-value]

        counter = CustomTokenCounter(bad_tokenizer, "bad")  # type: ignore[arg-type]

        from pdf2md.tokens.base import TokenCountingError

        with pytest.raises(TokenCountingError, match="expected int"):
            counter.count_tokens("test")

    def test_tokenizer_returning_negative(self) -> None:
        """Test that negative count raises error."""

        def negative_tokenizer(text: str) -> int:
            """Returns negative count."""
            return -1

        counter = CustomTokenCounter(negative_tokenizer, "negative")

        from pdf2md.tokens.base import TokenCountingError

        with pytest.raises(TokenCountingError, match="negative count"):
            counter.count_tokens("test")