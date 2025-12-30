# Testing

Testing guide for PDF-to-Markdown.

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_converter.py

# Verbose output
pytest -v
```

## Test Structure

```
tests/
├── test_cli.py           # CLI tests
├── test_api.py           # API endpoint tests
├── test_auth.py          # Authentication tests
├── test_converter.py     # PDF conversion tests
├── test_storage_blob.py  # Storage tests
└── conftest.py           # Shared fixtures
```

## Writing Tests

```python
import pytest
from pdf2md.converter import PDFConverter

class TestPDFConverter:
    """Test suite for PDFConverter."""
    
    @pytest.fixture
    def converter(self) -> PDFConverter:
        """Create converter instance."""
        return PDFConverter()
    
    async def test_convert_valid_pdf(
        self,
        converter: PDFConverter,
        bytesValidPdf: bytes
    ) -> None:
        """Test converting valid PDF."""
        result = await converter.convert(bytesValidPdf)
        
        assert result.strMarkdown is not None
        assert result.intPageCount > 0
```

## Type Checking

```bash
# Check all source code
mypy src/ --strict

# Check specific module
mypy src/pdf2md/api/ --strict
```

## Linting

```bash
# Check code
ruff check src/

# Auto-fix
ruff check src/ --fix

# Format
ruff format src/
```

## Coverage Requirements

- Minimum 80% coverage for new code
- All critical paths tested
- Both success and error cases

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for test standards.