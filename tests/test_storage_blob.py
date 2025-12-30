"""Tests for blob storage providers."""

import pytest

from pdf2md.storage.blob.local import LocalBlobStorage
from pdf2md.storage.factory import StorageFactory


@pytest.fixture
async def local_storage():
    """Create local storage for testing."""
    return LocalBlobStorage("test_data/blobs")


@pytest.mark.asyncio
async def test_blob_upload_download(local_storage):
    """Test blob upload and download."""
    bytesData = b"Hello, PDF2MD!"
    strUrl = await local_storage.upload("test.txt", bytesData)

    assert strUrl.startswith("file://")

    bytesDownloaded = await local_storage.download("test.txt")
    assert bytesDownloaded == bytesData


@pytest.mark.asyncio
async def test_blob_exists(local_storage):
    """Test blob existence check."""
    await local_storage.upload("exists.txt", b"data")

    assert await local_storage.exists("exists.txt") is True
    assert await local_storage.exists("not-exists.txt") is False


@pytest.mark.asyncio
async def test_blob_delete(local_storage):
    """Test blob deletion."""
    await local_storage.upload("delete-me.txt", b"data")

    assert await local_storage.exists("delete-me.txt") is True
    assert await local_storage.delete("delete-me.txt") is True
    assert await local_storage.exists("delete-me.txt") is False


@pytest.mark.asyncio
async def test_blob_metadata(local_storage):
    """Test blob metadata operations."""
    dictMetadata = {"key1": "value1", "key2": "value2"}
    await local_storage.upload("meta.txt", b"data", optMetadata=dictMetadata)

    dictRetrieved = await local_storage.get_metadata("meta.txt")
    assert dictRetrieved["key1"] == "value1"
    assert dictRetrieved["key2"] == "value2"

    # Update metadata
    await local_storage.set_metadata("meta.txt", {"key3": "value3"})
    dictUpdated = await local_storage.get_metadata("meta.txt")
    assert dictUpdated["key3"] == "value3"


@pytest.mark.asyncio
async def test_blob_lifecycle(local_storage):
    """Test complete blob lifecycle."""
    strBlobName = "lifecycle.txt"
    bytesData = b"Lifecycle test"

    # Upload
    strUrl = await local_storage.upload(strBlobName, bytesData)
    assert strUrl

    # Exists
    assert await local_storage.exists(strBlobName)

    # Download
    bytesDownloaded = await local_storage.download(strBlobName)
    assert bytesDownloaded == bytesData

    # Delete
    assert await local_storage.delete(strBlobName)
    assert not await local_storage.exists(strBlobName)


@pytest.mark.asyncio
async def test_storage_factory_fallback():
    """Test storage factory fallback to local."""
    storage = StorageFactory.create_blob_storage()
    assert isinstance(storage, LocalBlobStorage)


@pytest.mark.asyncio
async def test_storage_factory_explicit_provider():
    """Test storage factory with explicit provider."""
    storage = StorageFactory.create_blob_storage("local")
    assert isinstance(storage, LocalBlobStorage)


@pytest.mark.asyncio
async def test_storage_factory_invalid_provider():
    """Test storage factory with invalid provider."""
    with pytest.raises(ValueError, match="Unknown blob storage provider"):
        StorageFactory.create_blob_storage("invalid")


@pytest.mark.asyncio
async def test_download_nonexistent_blob(local_storage):
    """Test downloading non-existent blob raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        await local_storage.download("nonexistent.txt")