# Azure Deployment

Deploy PDF-to-Markdown on Azure.

## Quick Start

```bash
# 1. Create resource group
az group create --name pdf2md-rg --location eastus

# 2. Create Azure Blob Storage
az storage account create \
  --name pdf2mdstorage \
  --resource-group pdf2md-rg \
  --sku Standard_LRS

# 3. Create Redis Cache
az redis create \
  --name pdf2md-redis \
  --resource-group pdf2md-rg \
  --sku Basic \
  --vm-size c0

# 4. Deploy Container
az container create \
  --name pdf2md-app \
  --resource-group pdf2md-rg \
  --image your-registry/pdf2md:latest \
  --environment-variables \
    AZURE_STORAGE_CONNECTION_STRING="..." \
    REDIS_URL="..." \
    RATE_LIMIT_BACKEND=redis \
    RATE_LIMIT_FAIL_MODE=closed
```

## Configuration

```bash
# Get connection strings
az storage account show-connection-string \
  --name pdf2mdstorage \
  --resource-group pdf2md-rg

az redis list-keys \
  --name pdf2md-redis \
  --resource-group pdf2md-rg
```

## Secrets

Store secrets in Azure Key Vault:

```bash
az keyvault create \
  --name pdf2md-vault \
  --resource-group pdf2md-rg

az keyvault secret set \
  --vault-name pdf2md-vault \
  --name storage-key \
  --value "your_key"
```

See [Docker Deployment](docker.md) for container configuration details.