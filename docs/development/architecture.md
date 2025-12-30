# Architecture

System architecture overview.

## Components

### CLI (`src/pdf2md/cli/`)
- Command-line interface
- PDF conversion, info, validation
- Admin token management

### API (`src/pdf2md/api/`)
- FastAPI REST API
- Background job processing
- RBAC enforcement
- Rate limiting

### Storage (`src/pdf2md/storage/`)
- Multi-cloud abstraction
- Azure Blob, GCS, S3, Local
- Automatic fallback chain

### Security
- Token-based authentication
- 4-tier RBAC
- PDF sandboxing
- TLS/mTLS support

## Data Flow

```
Client Request
    ↓
nginx (TLS termination)
    ↓
FastAPI (Auth, RBAC, Rate Limiting)
    ↓
Job Queue
    ↓
PDF Processing (Subprocess)
    ↓
Storage (Cloud/Local)
    ↓
Response to Client
```

## Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **PDF Processing**: pdfplumber, PyMuPDF
- **Token Counting**: tiktoken
- **Database**: SQLite
- **Cache/Rate Limiting**: Redis
- **Web Server**: nginx
- **Containers**: Docker

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for development guidelines.