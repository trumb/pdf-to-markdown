"""Azure Blob Storage provider."""

import logging
import os
from datetime import datetime
from typing import Any, AsyncIterator, Optional

from pdf2md.storage.base import BlobStorageProvider

logger = logging.getLogger(__name__)


class AzureBlobStorage(BlobStorageProvider):
    """Azure Blob Storage implementation."""

    def __init__(self) -> None:
        """Initialize Azure Blob Storage client."""
        strConnectionString = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not strConnectionString:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable not set")

        self.strContainerName: str = os.getenv("AZURE_STORAGE_CONTAINER", "pdf2md")

        # Import here to allow optional dependency
        try:
            from azure.storage.blob.aio import BlobServiceClient

            self.client = BlobServiceClient.from_connection_string(strConnectionString)
        except ImportError:
            raise ImportError("azure-storage-blob not installed. Install with: pip install azure-storage-blob")

        logger.info(f"Azure Blob Storage initialized: container={self.strContainerName}")

    async def _ensure_container_exists(self) -> None:
        """Ensure container exists, create if not."""
        containerClient = self.client.get_container_client(self.strContainerName)

        try:
            await containerClient.create_container()
            logger.info(f"Created container: {self.strContainerName}")
        except Exception:
            pass  # Container already exists

    async def upload(
        self,
        strBlobName: str,
        bytesData: bytes,
        strContentType: str = "application/octet-stream",
        optMetadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Upload blob to Azure Blob Storage."""
        await self._ensure_container_exists()

        containerClient = self.client.get_container_client(self.strContainerName)
        blobClient = containerClient.get_blob_client(strBlobName)

        await blobClient.upload_blob(
            bytesData,
            overwrite=True,
            content_settings={"content_type": strContentType},
            metadata=optMetadata or {},
        )

        return blobClient.url

    async def download(self, strBlobName: str) -> bytes:
        """Download blob from Azure Blob Storage."""
        from azure.core.exceptions import ResourceNotFoundError

        containerClient = self.client.get_container_client(self.strContainerName)
        blobClient = containerClient.get_blob_client(strBlobName)

        try:
            stream = await blobClient.download_blob()
            return await stream.readall()
        except ResourceNotFoundError:
            raise FileNotFoundError(f"Blob not found: {strBlobName}")

    async def delete(self, strBlobName: str) -> bool:
        """Delete blob from Azure Blob Storage."""
        from azure.core.exceptions import ResourceNotFoundError

        containerClient = self.client.get_container_client(self.strContainerName)
        blobClient = containerClient.get_blob_client(strBlobName)

        try:
            await blobClient.delete_blob()
            return True
        except ResourceNotFoundError:
            return False

    async def exists(self, strBlobName: str) -> bool:
        """Check if blob exists in Azure Blob Storage."""
        containerClient = self.client.get_container_client(self.strContainerName)
        blobClient = containerClient.get_blob_client(strBlobName)
        return await blobClient.exists()

    async def list_blobs(
        self, optPrefix: Optional[str] = None, intLimit: int = 1000
    ) -> AsyncIterator[dict[str, Any]]:
        """List blobs in Azure Blob Storage."""
        containerClient = self.client.get_container_client(self.strContainerName)

        intCount = 0
        async for blob in containerClient.list_blobs(name_starts_with=optPrefix):
            if intCount >= intLimit:
                break

            yield {
                "name": blob.name,
                "size": blob.size,
                "created": blob.creation_time,
                "modified": blob.last_modified,
                "metadata": blob.metadata or {},
            }

            intCount += 1

    async def get_metadata(self, strBlobName: str) -> dict[str, str]:
        """Get blob metadata from Azure Blob Storage."""
        containerClient = self.client.get_container_client(self.strContainerName)
        blobClient = containerClient.get_blob_client(strBlobName)

        properties = await blobClient.get_blob_properties()
        return properties.metadata or {}

    async def set_metadata(self, strBlobName: str, dictMetadata: dict[str, str]) -> bool:
        """Set blob metadata in Azure Blob Storage."""
        from azure.core.exceptions import ResourceNotFoundError

        containerClient = self.client.get_container_client(self.strContainerName)
        blobClient = containerClient.get_blob_client(strBlobName)

        try:
            await blobClient.set_blob_metadata(dictMetadata)
            return True
        except ResourceNotFoundError:
            return False
