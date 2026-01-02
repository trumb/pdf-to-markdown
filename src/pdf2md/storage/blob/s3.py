"""AWS S3 storage provider."""

import logging
import os
from datetime import datetime
from typing import Any, AsyncIterator, Optional

from pdf2md.storage.base import BlobStorageProvider

logger = logging.getLogger(__name__)


class AWSS3Storage(BlobStorageProvider):
    """AWS S3 implementation."""

    def __init__(self) -> None:
        """Initialize AWS S3 client."""
        strAccessKeyId = os.getenv("AWS_ACCESS_KEY_ID")
        strSecretAccessKey = os.getenv("AWS_SECRET_ACCESS_KEY")

        if not strAccessKeyId or not strSecretAccessKey:
            raise ValueError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set")

        self.strBucketName: str = os.getenv("S3_BUCKET", "pdf2md")
        self.strRegion: str = os.getenv("AWS_REGION", "us-east-1")

        # Import here to allow optional dependency
        try:
            import boto3

            self.client = boto3.client(
                "s3",
                aws_access_key_id=strAccessKeyId,
                aws_secret_access_key=strSecretAccessKey,
                region_name=self.strRegion,
            )
        except ImportError:
            raise ImportError("boto3 not installed. Install with: pip install boto3")

        logger.info(f"AWS S3 initialized: bucket={self.strBucketName}, region={self.strRegion}")

    async def upload(
        self,
        strBlobName: str,
        bytesData: bytes,
        strContentType: str = "application/octet-stream",
        optMetadata: Optional[dict[str, str]] = None,
    ) -> str:
        """Upload blob to S3."""
        dictExtraArgs = {"ContentType": strContentType, "Metadata": optMetadata or {}}

        self.client.put_object(
            Bucket=self.strBucketName, Key=strBlobName, Body=bytesData, **dictExtraArgs
        )

        return f"https://{self.strBucketName}.s3.{self.strRegion}.amazonaws.com/{strBlobName}"

    async def download(self, strBlobName: str) -> bytes:
        """Download blob from S3."""
        from botocore.exceptions import ClientError

        try:
            response = self.client.get_object(Bucket=self.strBucketName, Key=strBlobName)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"Blob not found: {strBlobName}")
            raise

    async def delete(self, strBlobName: str) -> bool:
        """Delete blob from S3."""
        from botocore.exceptions import ClientError

        try:
            self.client.delete_object(Bucket=self.strBucketName, Key=strBlobName)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return False
            raise

    async def exists(self, strBlobName: str) -> bool:
        """Check if blob exists in S3."""
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.strBucketName, Key=strBlobName)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def list_blobs(
        self, optPrefix: Optional[str] = None, intLimit: int = 1000
    ) -> AsyncIterator[dict[str, Any]]:
        """List blobs in S3."""
        dictParams = {"Bucket": self.strBucketName, "MaxKeys": intLimit}

        if optPrefix:
            dictParams["Prefix"] = optPrefix

        response = self.client.list_objects_v2(**dictParams)

        for dictObj in response.get("Contents", []):
            yield {
                "name": dictObj["Key"],
                "size": dictObj["Size"],
                "created": dictObj["LastModified"],
                "modified": dictObj["LastModified"],
                "metadata": {},  # Metadata requires separate HEAD request
            }

    async def get_metadata(self, strBlobName: str) -> dict[str, str]:
        """Get blob metadata from S3."""
        from botocore.exceptions import ClientError

        try:
            response = self.client.head_object(Bucket=self.strBucketName, Key=strBlobName)
            return response.get("Metadata", {})
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"Blob not found: {strBlobName}")
            raise

    async def set_metadata(self, strBlobName: str, dictMetadata: dict[str, str]) -> bool:
        """Set blob metadata in S3."""
        from botocore.exceptions import ClientError

        try:
            # S3 requires copying the object to update metadata
            self.client.copy_object(
                Bucket=self.strBucketName,
                Key=strBlobName,
                CopySource={"Bucket": self.strBucketName, "Key": strBlobName},
                Metadata=dictMetadata,
                MetadataDirective="REPLACE",
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return False
            raise
