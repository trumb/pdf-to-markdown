"""Storage configuration from environment."""

from typing import Optional

from pydantic_settings import BaseSettings


class StorageConfig(BaseSettings):
    """Storage configuration from environment variables."""

    # Provider selection
    blob_storage_provider: str = "auto"  # auto, azure, gcs, s3, local
    document_storage_provider: str = "auto"  # auto, cosmos, firestore, dynamodb, postgresql, mongodb

    # Azure
    azure_storage_connection_string: Optional[str] = None
    azure_storage_container: str = "pdf2md"
    azure_cosmos_endpoint: Optional[str] = None
    azure_cosmos_key: Optional[str] = None
    azure_cosmos_database: str = "pdf2md"

    # Google Cloud
    google_application_credentials: Optional[str] = None
    gcs_bucket: str = "pdf2md"
    firestore_project: Optional[str] = None

    # AWS
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket: str = "pdf2md"
    dynamodb_table: str = "pdf2md"

    # PostgreSQL
    postgresql_url: Optional[str] = None

    # MongoDB
    mongodb_url: Optional[str] = None
    mongodb_database: str = "pdf2md"

    # Retry configuration
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    retry_timeout: int = 30

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"