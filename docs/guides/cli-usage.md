# CLI Usage

Complete command-line interface reference.

## Installation

```bash
pip install pdf2md
```

## Commands

### convert

Convert PDF to Markdown:

```bash
# From stdin
cat document.pdf | pdf2md convert > output.md

# With token counting
cat document.pdf | pdf2md convert --tokens openai > output.md

# Specify output format
pdf2md convert --input document.pdf --output markdown --tokens claude
```

### info

Get PDF information:

```bash
pdf2md info document.pdf

# Output:
# Pages: 10
# Size: 1.5 MB
# Version: 1.7
```

### validate

Validate PDF file:

```bash
pdf2md validate document.pdf

# Output:
# ✓ Valid PDF file
# ✓ Readable
# ✓ No encryption
```

### admin create-token

Create authentication token (admin only):

```bash
pdf2md admin create-token --role job_writer --user-id app-service

# Output:
# Token created successfully:
# pdf2md_kF8j2NmP9qR3sT5vU7wX...
```

See [API Usage](api-usage.md) for REST API examples.