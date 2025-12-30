# Development Setup

Setup development environment for PDF-to-Markdown.

## Prerequisites

- Python 3.11+
- Git
- Docker (optional)

## Setup

```bash
# 1. Clone repository
git clone https://github.com/trumb/pdf-to-markdown.git
cd pdf-to-markdown

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install in development mode
pip install -e ".[dev]"

# 4. Set up pre-commit hooks (optional)
pre-commit install
```

## Configuration

```bash
# Create .env file
cp .env.example .env

# Edit with your settings
nano .env
```

## Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Type checking
mypy src/ --strict

# Linting
ruff check src/
```

## Running Locally

```bash
# Run API server
uvicorn pdf2md.api.main:app --reload --port 8000

# Or use Docker
docker-compose up -d
```

See [Testing Guide](testing.md) for detailed testing information.