# Contributing to PDF-to-Markdown

Thank you for considering contributing to PDF-to-Markdown! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guide](#code-style-guide)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Docker and docker-compose (for integration testing)
- Redis (for rate limiting tests)

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/pdf-to-markdown.git
cd pdf-to-markdown

# Add upstream remote
git remote add upstream https://github.com/trumb/pdf-to-markdown.git
```

## Development Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install in development mode with all extras
pip install -e ".[dev,all-cloud]"
```

### 3. Set Up Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# For development, local storage is sufficient
```

## Code Style Guide

### Hungarian Notation

**All variables must use reverse Hungarian notation:**

```python
# Strings
strFilename: str = "document.pdf"
strJobId: str = "abc123xyz9"

# Integers
intPageCount: int = 42
intTokenCount: int = 5000

# Booleans
boolIsComplete: bool = True
boolHasError: bool = False

# Lists
listJobs: list[Job] = []
listTokenCounts: list[int] = [100, 200, 300]

# Dictionaries
dictConfig: dict[str, Any] = {}
dictMetadata: dict[str, str] = {}

# Optional values
optError: Optional[str] = None
optResult: Optional[bytes] = None

# Bytes
bytesContent: bytes = b"..."
bytesHash: bytes = hashlib.sha256(data).digest()

# Floats
floatProgress: float = 0.75
floatCpuUsage: float = 45.2
```

### Function Standards

**Maximum 60 lines per function:**

```python
async def process_pdf(
    strFilename: str,
    bytesContent: bytes,
    dictOptions: dict[str, Any]
) -> ProcessingResult:
    """
    Process PDF file and return result.
    
    Args:
        strFilename: Name of PDF file
        bytesContent: PDF file bytes
        dictOptions: Processing options
        
    Returns:
        ProcessingResult with markdown and metadata
        
    Raises:
        PDFProcessingError: If processing fails
    """
    # Implementation (max 60 lines)
    pass
```

**Maximum 4 parameters per function:**
- If you need more than 4 parameters, use a configuration object or dataclass

### No Placeholders

**Never commit:**
- `TODO` comments
- `pass` statements without implementation
- Stub functions
- Placeholder text

**All code must be complete and functional when committed.**

### Type Hints

**All functions must have complete type hints:**

```python
# Good
async def fetch_job(strJobId: str) -> Optional[Job]:
    """Fetch job by ID."""
    return await db.get_job(strJobId)

# Bad - missing type hints
async def fetch_job(job_id):
    return await db.get_job(job_id)
```

### Docstrings

**All public functions must have docstrings:**

```python
def calculate_tokens(strText: str, strEncoding: str) -> int:
    """
    Calculate token count for text.
    
    Args:
        strText: Input text to tokenize
        strEncoding: Encoding name (cl100k_base, p50k_base)
        
    Returns:
        Number of tokens
        
    Raises:
        ValueError: If encoding is not supported
    """
    pass
```

## Testing Requirements

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_converter.py

# Run with verbose output
pytest -v
```

### Type Checking

```bash
# Type check all source code
mypy src/ --strict

# Type check tests
mypy tests/ --strict
```

### Linting

```bash
# Run ruff linter
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Format code
ruff format src/
```

### Test Coverage Requirements

- **Minimum 80% coverage** for new code
- All critical paths must be tested
- Include both success and error cases

### Writing Tests

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
        assert result.dictTokenCounts["openai_cl100k"] > 0
    
    async def test_convert_invalid_pdf(
        self,
        converter: PDFConverter
    ) -> None:
        """Test converting invalid PDF raises error."""
        with pytest.raises(PDFProcessingError):
            await converter.convert(b"not a pdf")
```

## Pull Request Process

### 1. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow code style guide
- Write tests for new functionality
- Update documentation if needed
- Ensure all tests pass

### 3. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add PDF validation functionality

- Add validate_pdf function
- Add validation tests
- Update CLI with validate command
- Add validation documentation"
```

**Commit message format:**
```
<type>: <description>

<optional body>

<optional footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `chore`: Build/tooling changes

### 4. Push Changes

```bash
# Push to your fork
git push origin feature/your-feature-name
```

### 5. Create Pull Request

1. Go to GitHub and create pull request
2. Fill out PR template
3. Link related issues
4. Request review from maintainers

### 6. Address Review Comments

```bash
# Make requested changes
git add .
git commit -m "fix: address review comments"
git push origin feature/your-feature-name
```

### 7. Merge

- Maintainers will merge when approved
- Delete your feature branch after merge

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality
- **PATCH**: Backward-compatible bug fixes

### Creating a Release

**For maintainers only:**

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md

# Create release commit
git add .
git commit -m "chore: release v1.0.0"

# Create tag
git tag -a v1.0.0 -m "Release v1.0.0"

# Push
git push origin main
git push origin v1.0.0
```

## Documentation

### Updating Documentation

- Keep README.md updated with new features
- Add examples for new functionality
- Update API documentation for endpoint changes
- Add entries to CHANGELOG.md

### Documentation Standards

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Test all code examples

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/trumb/pdf-to-markdown/issues)
- **Discussions**: [GitHub Discussions](https://github.com/trumb/pdf-to-markdown/discussions)
- **Email**: Contact maintainers directly

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to PDF-to-Markdown!