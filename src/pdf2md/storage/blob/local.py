"""Local filesystem blob storage provider."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from pdf2md.storage.base import BlobStorageProvider


class LocalBlobStorage(BlobStorageProvider):
    """
    Local filesystem implementation of blob storage.
    
    Used for development, testing, and as final fallback.
    """

    def __init__(self, strBasePath: str = "data/blobs"):
        """
        Initialize local blob storage.
        
        Args:
            strBasePath: Base directory for blob storage
        """
        self.strBasePath: str = strBasePath
        Path(strBasePath).mkdir(parents=True, exist_ok=True)

    def _get_blob_path(self, strBlobName: str) -> Path:
        """Get full filesystem path for blob."""
        return Path(self.strBasePath) / strBlobName

    def _get_metadata_path(self, strBlobName: str) -> Path:
        """Get path to metadata file."""
        return Path(self.strBasePath) / f"{strBlobName}.meta"

    async def upload(
        self,
        strBlobName: str,
        bytesData: bytes,
        strContentType: str = "application/octet-stream",
        optMetadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Upload blob to local filesystem."""
        pathBlob = self._get_blob_path(strBlobName)
        pathBlob.parent.mkdir(parents=True, exist_ok=True)

        # Write blob data
        pathBlob.write_bytes(bytesData)

        # Write metadata
        dictFullMetadata = {
            "content_type": strContentType,
            "created": datetime.now().isoformat(),
            **(optMetadata or {}),
        }

        pathMeta = self._get_metadata_path(strBlobName)
        strMetadata = "\n".join(f"{k}={v}" for k, v in dictFullMetadata.items())
        pathMeta.write_text(strMetadata, encoding="utf-8")

        return f"file://{pathBlob.absolute()}"

    async def download(self, strBlobName: str) -> bytes:
        """Download blob from local filesystem."""
        pathBlob = self._get_blob_path(strBlobName)

        if not pathBlob.exists():
            raise FileNotFoundError(f"Blob not found: {strBlobName}")

        return pathBlob.read_bytes()

    async def delete(self, strBlobName: str) -> bool:
        """Delete blob from local filesystem."""
        pathBlob = self._get_blob_path(strBlobName)
        pathMeta = self._get_metadata_path(strBlobName)

        boolDeleted = False

        if pathBlob.exists():
            pathBlob.unlink()
            boolDeleted = True

        if pathMeta.exists():
            pathMeta.unlink()

        return boolDeleted

    async def exists(self, strBlobName: str) -> bool:
        """Check if blob exists in local filesystem."""
        pathBlob = self._get_blob_path(strBlobName)
        return pathBlob.exists()

    async def list_blobs(
        self, optPrefix: Optional[str] = None, intLimit: int = 1000
    ) -> AsyncIterator[dict[str, Any]]:
        """List blobs in local filesystem."""
        pathBase = Path(self.strBasePath)
        strPattern = f"{optPrefix}*" if optPrefix else "*"

        intCount = 0
        for pathBlob in pathBase.glob(strPattern):
            if intCount >= intLimit:
                break

            if pathBlob.is_file() and not pathBlob.name.endswith(".meta"):
                statBlob = pathBlob.stat()
                dictMetadata = await self.get_metadata(pathBlob.name)

                yield {
                    "name": pathBlob.name,
                    "size": statBlob.st_size,
                    "created": datetime.fromtimestamp(statBlob.st_ctime),
                    "modified": datetime.fromtimestamp(statBlob.st_mtime),
                    "metadata": dictMetadata,
                }

                intCount += 1

    async def get_metadata(self, strBlobName: str) -> dict[str, str]:
        """Get blob metadata from local filesystem."""
        pathMeta = self._get_metadata_path(strBlobName)

        if not pathMeta.exists():
            return {}

        dictMetadata: dict[str, str] = {}
        strContent = pathMeta.read_text(encoding="utf-8")

        for strLine in strContent.strip().split("\n"):
            if "=" in strLine:
                strKey, strValue = strLine.split("=", 1)
                dictMetadata[strKey] = strValue

        return dictMetadata

    async def set_metadata(self, strBlobName: str, dictMetadata: dict[str, str]) -> bool:
        """Set blob metadata in local filesystem."""
        pathBlob = self._get_blob_path(strBlobName)

        if not pathBlob.exists():
            return False

        pathMeta = self._get_metadata_path(strBlobName)
        strMetadata = "\n".join(f"{k}={v}" for k, v in dictMetadata.items())
        pathMeta.write_text(strMetadata, encoding="utf-8")

        return True
