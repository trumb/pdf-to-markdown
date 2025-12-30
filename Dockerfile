# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and source code
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md LICENSE ./

# Install dependencies
RUN pip install --no-cache-dir --user .

# =============================================================================
# Runtime stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 pdf2md && \
    mkdir -p /app /data /results /certs && \
    chown -R pdf2md:pdf2md /app /data /results

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/pdf2md/.local

# Copy application code
COPY --chown=pdf2md:pdf2md src/ ./src/
COPY --chown=pdf2md:pdf2md LICENSE README.md ./

# Update PATH
ENV PATH=/home/pdf2md/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER pdf2md

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run FastAPI with uvicorn
CMD ["uvicorn", "pdf2md.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]