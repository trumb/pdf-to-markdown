"""Abstract base classes for storage providers."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator, Optional


class BlobStorageProvider(ABC):
    """Abstract base for blob storage providers."""

    @abstractmethod
    async def upload(
        self,
        strBlobName: str,
        bytesData: bytes,
        strContentType: str = "application/octet-stream",
        optMetadata: Optional[dict[str, str]] = None,
    ) -> str:
        """
        Upload blob and return URL.
        
        Args:
            strBlobName: Blob name/path
            bytesData: Blob data
            strContentType: MIME type
            optMetadata: Optional metadata dict
            
        Returns:
            URL to uploaded blob
        """
        pass

    @abstractmethod
    async def download(self, strBlobName: str) -> bytes:
        """
        Download blob data.
        
        Args:
            strBlobName: Blob name/path
            
        Returns:
            Blob data bytes
            
        Raises:
            FileNotFoundError: If blob not found
        """
        pass

    @abstractmethod
    async def delete(self, strBlobName: str) -> bool:
        """
        Delete blob.
        
        Args:
            strBlobName: Blob name/path
            
        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, strBlobName: str) -> bool:
        """
        Check if blob exists.
        
        Args:
            strBlobName: Blob name/path
            
        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def list_blobs(
        self, optPrefix: Optional[str] = None, intLimit: int = 1000
    ) -> AsyncIterator[dict[str, any]]:
        """
        List blobs with metadata.
        
        Args:
            optPrefix: Optional prefix filter
            intLimit: Maximum number of blobs
            
        Yields:
            Dict with blob metadata (name, size, created, modified, metadata)
        """
        pass

    @abstractmethod
    async def get_metadata(self, strBlobName: str) -> dict[str, str]:
        """
        Get blob metadata.
        
        Args:
            strBlobName: Blob name/path
            
        Returns:
            Metadata dict
        """
        pass

    @abstractmethod
    async def set_metadata(self, strBlobName: str, dictMetadata: dict[str, str]) -> bool:
        """
        Set blob metadata.
        
        Args:
            strBlobName: Blob name/path
            dictMetadata: Metadata dict
            
        Returns:
            True if successful
        """
        pass


class DocumentStorageProvider(ABC):
    """Abstract base for document storage providers."""

    @abstractmethod
    async def insert(self, strCollection: str, dictDocument: dict[str, any]) -> str:
        """
        Insert document and return ID.
        
        Args:
            strCollection: Collection/table name
            dictDocument: Document data
            
        Returns:
            Document ID
        """
        pass

    @abstractmethod
    async def get(self, strCollection: str, strDocId: str) -> Optional[dict[str, any]]:
        """
        Get document by ID.
        
        Args:
            strCollection: Collection/table name
            strDocId: Document ID
            
        Returns:
            Document dict or None if not found
        """
        pass

    @abstractmethod
    async def update(
        self, strCollection: str, strDocId: str, dictUpdates: dict[str, any]
    ) -> bool:
        """
        Update document.
        
        Args:
            strCollection: Collection/table name
            strDocId: Document ID
            dictUpdates: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        pass

    @abstractmethod
    async def delete(self, strCollection: str, strDocId: str) -> bool:
        """
        Delete document.
        
        Args:
            strCollection: Collection/table name
            strDocId: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def query(
        self,
        strCollection: str,
        dictFilters: dict[str, any],
        intLimit: int = 100,
        intOffset: int = 0,
    ) -> list[dict[str, any]]:
        """
        Query documents with filters.
        
        Args:
            strCollection: Collection/table name
            dictFilters: Filter criteria
            intLimit: Maximum documents to return
            intOffset: Offset for pagination
            
        Returns:
            List of matching documents
        """
        pass