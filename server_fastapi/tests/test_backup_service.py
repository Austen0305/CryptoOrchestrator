"""
Tests for Backup Service
"""
import pytest
import asyncio
from pathlib import Path
from decimal import Decimal

from server_fastapi.services.backup_service import backup_service


@pytest.mark.asyncio
async def test_backup_service_initialization():
    """Test backup service initializes correctly"""
    assert backup_service is not None
    assert backup_service.backup_dir.exists() or backup_service.backup_dir.parent.exists()


@pytest.mark.asyncio
async def test_list_backups():
    """Test listing backups"""
    backups = await backup_service.list_backups()
    assert isinstance(backups, list)


@pytest.mark.asyncio
async def test_backup_status():
    """Test backup status endpoint"""
    # This would test the backup status functionality
    # For now, just verify service is accessible
    assert backup_service.retention_days == 30
    assert backup_service.encryption_enabled is True

