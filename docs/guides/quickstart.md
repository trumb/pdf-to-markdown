# Quickstart Guide

Get started with PDF-to-Markdown in 5 minutes.

## Docker (Recommended)

```bash
# 1. Clone and setup
git clone https://github.com/trumb/pdf-to-markdown.git
cd pdf-to-markdown
cp .env.example .env
./certs/generate-selfsigned.sh

# 2. Start services
docker-compose up -d

# 3. Create admin token
docker exec -it pdf2md-app pdf2md admin create-token --role admin --user-id admin

# 4. Test conversion
curl -X POST https://localhost/api/v1/convert \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -k  # -k for self-signed cert
```

## CLI

```bash
# 1. Install
pip install pdf2md

# 2. Convert PDF
cat document.pdf | pdf2md convert --output markdown --tokens openai > output.md

# 3. Get info
pdf2md info document.pdf
```

See [CLI Usage](cli-usage.md) for complete CLI reference.