"""Storage provider factory with automatic fallback."""

import logging
from typing import Optional

from pdf2md.storage.base import BlobStorageProvider
from pdf2md.storage.blob.azure_blob import AzureBlobStorage
from pdf2md.storage.blob.gcs import GoogleCloudStorage
from pdf2md.storage.blob.local import LocalBlobStorage
from pdf2md.storage.blob.s3 import AWSS3Storage

logger = logging.getLogger(__name__)


class StorageFactory:
    """
    Factory for creating storage providers with automatic fallback.
    
    Priority order: Azure → GCS → S3 → Local
    """

    _blob_providers: dict[str, type[BlobStorageProvider]] = {
        "azure": AzureBlobStorage,
        "gcs": GoogleCloudStorage,
        "s3": AWSS3Storage,
        "local": LocalBlobStorage,
    }

    @classmethod
    def create_blob_storage(cls, optProvider: Optional[str] = None) -> BlobStorageProvider:
        """
        Create blob storage provider with automatic fallback.
        
        If provider is specified, attempt to create that provider.
        If provider is "auto" or None, try providers in priority order.
        
        Priority: Azure → GCS → S3 → Local
        
        Args:
            optProvider: Provider name ("azure", "gcs", "s3", "local", "auto", None)
            
        Returns:
            Configured blob storage provider
            
        Raises:
            RuntimeError: If no provider can be initialized
        """
        # If specific provider requested
        if optProvider and optProvider != "auto":
            if optProvider not in cls._blob_providers:
                raise ValueError(
                    f"Unknown blob storage provider: {optProvider}. "
                    f"Valid options: {', '.join(cls._blob_providers.keys())}"
                )

            try:
                provider = cls._blob_providers[optProvider]()
                logger.info(f"Blob storage provider: {optProvider}")
                return provider
            except Exception as e:
                raise RuntimeError(f"Failed to initialize {optProvider}: {e}")

        # Auto-detection: try providers in priority order
        listProviders = ["azure", "gcs", "s3", "local"]

        for strProviderName in listProviders:
            try:
                provider = cls._blob_providers[strProviderName]()
                logger.info(f"Blob storage provider (auto-detected): {strProviderName}")
                return provider
            except (ValueError, ImportError) as e:
                logger.debug(f"Skipping {strProviderName}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Failed to initialize {strProviderName}: {e}")
                continue

        raise RuntimeError(
            "No blob storage provider available. "
            "Please configure Azure, GCS, S3, or ensure local filesystem access."
        )

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Get list of available blob storage providers.
        
        Tests each provider to see if it can be initialized.
        
        Returns:
            List of available provider names
        """
        listAvailable: list[str] = []

        for strName, providerClass in cls._blob_providers.items():
            try:
                provider = providerClass()
                listAvailable.append(strName)
            except Exception:
                pass

        return listAvailable
