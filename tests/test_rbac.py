"""Tests for role-based access control."""

import pytest

from pdf2md.auth.models import Role, User
from pdf2md.auth.permissions import (
    Permission,
    check_permission,
    ROLE_PERMISSIONS,
)


@pytest.fixture
def admin_user():
    """Create admin user."""
    return User(
        strTokenId="admin-token",
        strUserId="admin-user",
        role=Role.ADMIN,
        intRateLimit=1000,
        boolIsActive=True,
        optExpiresAt=None,
    )


@pytest.fixture
def manager_user():
    """Create job_manager user."""
    return User(
        strTokenId="manager-token",
        strUserId="manager-user",
        role=Role.JOB_MANAGER,
        intRateLimit=500,
        boolIsActive=True,
        optExpiresAt=None,
    )


@pytest.fixture
def writer_user():
    """Create job_writer user."""
    return User(
        strTokenId="writer-token",
        strUserId="writer-user",
        role=Role.JOB_WRITER,
        intRateLimit=100,
        boolIsActive=True,
        optExpiresAt=None,
    )


@pytest.fixture
def reader_user():
    """Create job_reader user."""
    return User(
        strTokenId="reader-token",
        strUserId="reader-user",
        role=Role.JOB_READER,
        intRateLimit=50,
        boolIsActive=True,
        optExpiresAt=None,
    )


def test_admin_has_all_permissions(admin_user):
    """Test that admin has all permissions."""
    for permission in Permission:
        assert check_permission(admin_user, permission) is True


def test_admin_can_create_tokens(admin_user):
    """Test that admin can create tokens."""
    assert check_permission(admin_user, Permission.CREATE_TOKEN) is True
    assert check_permission(admin_user, Permission.CREATE_ADMIN_TOKEN) is True


def test_manager_can_view_all_jobs(manager_user):
    """Test that job_manager can view all jobs."""
    assert check_permission(manager_user, Permission.VIEW_ALL_JOBS) is True
    assert check_permission(manager_user, Permission.STOP_ALL_JOBS) is True
    assert check_permission(manager_user, Permission.THROTTLE_JOBS) is True


def test_manager_cannot_manage_tokens(manager_user):
    """Test that job_manager cannot manage tokens."""
    assert check_permission(manager_user, Permission.CREATE_TOKEN) is False
    assert check_permission(manager_user, Permission.REVOKE_TOKEN) is False


def test_writer_can_create_jobs(writer_user):
    """Test that job_writer can create jobs."""
    assert check_permission(writer_user, Permission.CREATE_JOB) is True
    assert check_permission(writer_user, Permission.VIEW_OWN_JOBS) is True
    assert check_permission(writer_user, Permission.STOP_OWN_JOBS) is True
    assert check_permission(writer_user, Permission.GRANT_JOB_ACCESS) is True


def test_writer_cannot_view_all_jobs(writer_user):
    """Test that job_writer cannot view all jobs."""
    assert check_permission(writer_user, Permission.VIEW_ALL_JOBS) is False
    assert check_permission(writer_user, Permission.STOP_ALL_JOBS) is False


def test_reader_can_only_view_jobs(reader_user):
    """Test that job_reader can only view their own jobs."""
    assert check_permission(reader_user, Permission.VIEW_OWN_JOBS) is True
    assert check_permission(reader_user, Permission.CREATE_JOB) is False
    assert check_permission(reader_user, Permission.STOP_OWN_JOBS) is False


def test_role_permissions_matrix_completeness():
    """Test that all roles are defined in permissions matrix."""
    for role in Role:
        assert role in ROLE_PERMISSIONS


def test_permission_hierarchy():
    """Test that admin has more permissions than other roles."""
    admin_perms = ROLE_PERMISSIONS[Role.ADMIN]
    manager_perms = ROLE_PERMISSIONS[Role.JOB_MANAGER]
    writer_perms = ROLE_PERMISSIONS[Role.JOB_WRITER]
    reader_perms = ROLE_PERMISSIONS[Role.JOB_READER]
    
    # Admin should have all permissions
    assert len(admin_perms) > len(manager_perms)
    assert len(admin_perms) > len(writer_perms)
    assert len(admin_perms) > len(reader_perms)
    
    # Manager should have more than writer
    assert len(manager_perms) > len(writer_perms)
    
    # Writer should have more than reader
    assert len(writer_perms) > len(reader_perms)