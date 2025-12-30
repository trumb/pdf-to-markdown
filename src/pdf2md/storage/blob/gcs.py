"""Google Cloud Storage provider."""

import logging
import os
from datetime import datetime
from typing import AsyncIterator, Optional

from pdf2md.storage.base import BlobStorageProvider

logger = logging.getLogger(__name__)


class GoogleCloudStorage(BlobStorageProvider):
    """Google Cloud Storage implementation."""

    def __init__(self) -> None:
        """Initialize Google Cloud Storage client."""
        strCredentialsPath = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not strCredentialsPath:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

        self.strBucketName: str = os.getenv("GCS_BUCKET", "pdf2md")

        # Import here to allow optional dependency
        try:
            from google.cloud import storage

            self.client = storage.Client()
            self.bucket = self.client.bucket(self.strBucketName)
        except ImportError:
            raise ImportError(
                "google-cloud-storage not installed. Install with: pip install google-cloud-storage"
            )

        logger.info(f"Google Cloud Storage initialized: bucket={self.strBucketName}")

    async def upload(
        self,
        strBlobName: str,
        bytesData: bytes,
        strContentType: str = "application/octet-stream",
        optMetadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Upload blob to Google Cloud Storage."""
        blob = self.bucket.blob(strBlobName)
        blob.content_type = strContentType

        if optMetadata:
            blob.metadata = optMetadata

        blob.upload_from_string(bytesData)

        return blob.public_url

    async def download(self, strBlobName: str) -> bytes:
        """Download blob from Google Cloud Storage."""
        from google.cloud.exceptions import NotFound

        blob = self.bucket.blob(strBlobName)

        try:
            return blob.download_as_bytes()
        except NotFound:
            raise FileNotFoundError(f"Blob not found: {strBlobName}")

    async def delete(self, strBlobName: str) -> bool:
        """Delete blob from Google Cloud Storage."""
        from google.cloud.exceptions import NotFound

        blob = self.bucket.blob(strBlobName)

        try:
            blob.delete()
            return True
        except NotFound:
            return False

    async def exists(self, strBlobName: str) -> bool:
        """Check if blob exists in Google Cloud Storage."""
        blob = self.bucket.blob(strBlobName)
        return blob.exists()

    async def list_blobs(
        self, optPrefix: Optional[str] = None, intLimit: int = 1000
    ) -> AsyncIterator[dict[str, any]]:
        """List blobs in Google Cloud Storage."""
        listBlobs = list(self.client.list_blobs(self.strBucketName, prefix=optPrefix, max_results=intLimit))

        for blob in listBlobs:
            yield {
                "name": blob.name,
                "size": blob.size,
                "created": blob.time_created,
                "modified": blob.updated,
                "metadata": blob.metadata or {},
            }

    async def get_metadata(self, strBlobName: str) -> dict[str, str]:
        """Get blob metadata from Google Cloud Storage."""
        blob = self.bucket.blob(strBlobName)
        blob.reload()
        return blob.metadata or {}

    async def set_metadata(self, strBlobName: str, dictMetadata: dict[str, str]) -> bool:
        """Set blob metadata in Google Cloud Storage."""
        from google.cloud.exceptions import NotFound

        blob = self.bucket.blob(strBlobName)

        try:
            blob.metadata = dictMetadata
            blob.patch()
            return True
        except NotFound:
            return False