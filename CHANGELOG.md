# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of PDF-to-Markdown converter
- CLI interface with convert, info, and validate commands
- FastAPI REST API with background job processing
- 4-tier RBAC system (admin, job_manager, job_writer, job_reader)
- Token-based authentication with bcrypt hashing
- Rate limiting with Redis backend for horizontal scaling
- Multi-cloud storage support (Azure Blob, GCS, S3, Local)
- Automatic cloud provider fallback chain
- PDF sandboxing with subprocess isolation
- Token counting for OpenAI (cl100k_base, p50k_base) and Claude
- Docker deployment with nginx reverse proxy
- TLS 1.3 support with TLS 1.2 fallback
- mTLS (mutual TLS) support for client verification
- Self-signed certificate generation
- Let's Encrypt integration
- Custom PKI support
- Background job system with 10-character IDs
- Job access control and delegation
- Swagger/OpenAPI documentation
- Health check and readiness endpoints
- Comprehensive test suite with pytest
- Type checking with mypy
- Code linting with ruff

### Security
- Subprocess isolation for PDF processing
- bcrypt password hashing for tokens
- TLS 1.3 encryption
- Role-based access control (RBAC)
- Rate limiting to prevent abuse
- Redis fail-closed mode for production safety

## [1.0.0] - TBD

Initial stable release.

### Migration Notes
- No migrations required for initial release
- See deployment documentation for setup instructions

---

## Version History

- **Unreleased** - Current development version
- **1.0.0** - Initial stable release (planned)

---

## Links

- [GitHub Repository](https://github.com/trumb/pdf-to-markdown)
- [Issue Tracker](https://github.com/trumb/pdf-to-markdown/issues)
- [Documentation](docs/README.md)