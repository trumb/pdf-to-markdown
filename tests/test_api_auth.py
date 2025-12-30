"""Tests for API authentication and authorization."""

import pytest
from httpx import AsyncClient

from pdf2md.api.main import create_app
from pdf2md.auth.models import Role
from pdf2md.auth.token_manager import TokenManager
from pdf2md.database import Database


@pytest.fixture
async def database():
    """Create test database."""
    db = Database(":memory:")
    await db.connect()
    yield db
    await db.disconnect()


@pytest.fixture
async def app(database):
    """Create test app."""
    app = create_app()
    app.state.database = database
    return app


@pytest.fixture
async def admin_token(database):
    """Create admin token."""
    token_manager = TokenManager(database)
    _, token = await token_manager.create_token("admin-test", Role.ADMIN, optExpiresDays=1)
    return token


@pytest.fixture
async def writer_token(database):
    """Create job_writer token."""
    token_manager = TokenManager(database)
    _, token = await token_manager.create_token("writer-test", Role.JOB_WRITER, optExpiresDays=1)
    return token


@pytest.mark.asyncio
async def test_health_endpoint_no_auth(app):
    """Test health endpoint doesn't require auth."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_invalid_token_rejected(app):
    """Test that invalid tokens are rejected."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/jobs",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_create_tokens(app, admin_token):
    """Test that admin can create tokens."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/tokens",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "user_id": "new-writer",
                "role": "job_writer",
                "expires_days": 30
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "new-writer"
        assert data["role"] == "job_writer"


@pytest.mark.asyncio
async def test_writer_cannot_create_tokens(app, writer_token):
    """Test that job_writer cannot create tokens."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/tokens",
            headers={"Authorization": f"Bearer {writer_token}"},
            json={
                "user_id": "new-writer",
                "role": "job_writer",
                "expires_days": 30
            }
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_cannot_create_admin_token_via_api(app, admin_token):
    """Test that admin tokens cannot be created via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/tokens",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "user_id": "new-admin",
                "role": "admin",
                "expires_days": 365
            }
        )
        assert response.status_code == 403
        assert "CLI" in response.json()["detail"]