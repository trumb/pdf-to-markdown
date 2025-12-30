# Local Development

Quick setup guide for local development.

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/trumb/pdf-to-markdown.git
cd pdf-to-markdown

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Run API server
uvicorn pdf2md.api.main:app --reload --port 8000

# 5. Test
curl http://localhost:8000/health
```

## Development Configuration

**No Redis required** for single-worker development:

```bash
# .env
DATABASE_PATH=./dev-data/pdf2md.db
LOG_LEVEL=DEBUG
RATE_LIMIT_BACKEND=memory  # Single worker only
```

## Running Tests

```bash
pytest
mypy src/ --strict
ruff check src/
```

See [Docker Deployment](docker.md) for production setup.