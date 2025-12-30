# PDF-to-Markdown Converter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://hub.docker.com/)

Enterprise-grade PDF-to-Markdown conversion service with multi-cloud storage, RBAC, and enterprise security features.

## ✨ Features

- **Accurate Conversion**: High-quality PDF-to-Markdown with pdfplumber and PyMuPDF
- **Token Counting**: Built-in token counting for OpenAI (cl100k_base, p50k_base) and Claude
- **Security Sandbox**: Process isolation for malicious PDF handling
- **REST API**: FastAPI with Swagger documentation
- **4-Tier RBAC**: admin, job_manager, job_writer, job_reader roles
- **Multi-Cloud Storage**: Azure Blob, GCS, S3 with automatic fallback
- **Docker Ready**: Complete container setup with nginx and TLS
- **Certificate Support**: Self-signed, custom PKI, mTLS, Let's Encrypt
- **Background Jobs**: Async job processing with 10-character IDs
- **Rate Limiting**: Per-role rate limiting with Redis backend for scaling

## 🚀 Quick Start

### CLI Usage

```bash
# Install
pip install pdf2md

# Convert PDF
cat document.pdf | pdf2md convert --output markdown --tokens openai

# Get PDF info
pdf2md info document.pdf

# Validate PDF
pdf2md validate document.pdf
```

### API Usage

```bash
# Start API server
docker-compose up -d

# Convert PDF
curl -X POST https://localhost/api/v1/convert \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN" \
  -F "file=@document.pdf"

# Get job status
curl https://localhost/api/v1/jobs/{job_id} \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN"

# Download result
curl https://localhost/api/v1/jobs/{job_id}/result \
  -H "Authorization: Bearer pdf2md_YOUR_TOKEN" \
  -o result.md
```

## 📚 Documentation

- **[API Reference](docs/api/README.md)** - Complete API documentation
- **[Security Guide](docs/security/README.md)** - RBAC, tokens, sandboxing
- **[Deployment Guide](docs/deployment/README.md)** - Docker, cloud, enterprise
- **[CLI Guide](docs/guides/cli-usage.md)** - Command-line usage
- **[Troubleshooting](docs/guides/troubleshooting.md)** - Common issues

## 🔐 Security

This project implements enterprise-grade security:

- **Sandboxed PDF Processing**: All PDFs processed in isolated subprocess
- **RBAC System**: 4-tier role-based access control
- **TLS 1.3**: Primary encryption with TLS 1.2 fallback
- **mTLS Support**: Mutual TLS for client verification
- **Token-based Auth**: bcrypt-hashed tokens with expiration
- **Rate Limiting**: Per-role request throttling with Redis backend

See [Security Documentation](docs/security/README.md) for details.

## 🌐 Cloud Storage

Supports multiple cloud providers with automatic fallback:

1. **Azure Blob Storage** (Priority 1)
2. **Google Cloud Storage** (Priority 2)
3. **AWS S3** (Priority 3)
4. **Local Filesystem** (Development)

Configuration via environment variables. See [Cloud Storage Guide](docs/guides/cloud-storage.md).

## 📖 Example Output

```markdown
---
source_file: "document.pdf"
source_hash: "sha256:abc123..."
converted_at: "2025-12-29T20:00:00Z"
converter_version: "1.0.0"
pages: 10
tokens:
  openai_cl100k: 5000
  openai_p50k: 5100
  claude_estimate: 5500
extraction_method: "pdfplumber"
warnings: []
---

# Document Title

Content here...
```

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/trumb/pdf-to-markdown.git
cd pdf-to-markdown

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
mypy src/ --strict
ruff check src/
```

See [Contributing Guidelines](CONTRIBUTING.md) for development setup.

## 📋 Requirements

- Python 3.11+
- Docker (for API deployment)
- Redis (for horizontal scaling with multiple API instances)
- Cloud credentials (optional, for cloud storage)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/trumb/pdf-to-markdown/issues)
- **Discussions**: [GitHub Discussions](https://github.com/trumb/pdf-to-markdown/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for reporting vulnerabilities

## 🙏 Acknowledgments

- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF extraction
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - Fallback PDF extraction
- [tiktoken](https://github.com/openai/tiktoken) - Token counting
- [FastAPI](https://fastapi.tiangolo.com/) - REST API framework