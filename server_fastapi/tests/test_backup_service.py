"""
Tests for Backup Service
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from server_fastapi.services.backup_service import BackupService


class TestBackupService:
    """Tests for BackupService"""

    def test_backup_service_initialization(self):
        """Test backup service initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BackupService(
                db_url="sqlite:///./test.db",
                backup_dir=tmpdir,
            )
            
            assert service.backup_dir == Path(tmpdir)
            assert service.retention_days == 7

    def test_list_backups_empty(self):
        """Test listing backups when none exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BackupService(
                db_url="sqlite:///./test.db",
                backup_dir=tmpdir,
            )
            
            backups = service.list_backups()
            assert backups == []

    def test_calculate_checksum(self):
        """Test checksum calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BackupService(
                db_url="sqlite:///./test.db",
                backup_dir=tmpdir,
            )
            
            # Create test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")
            
            checksum = service._calculate_checksum(test_file)
            assert len(checksum) == 64  # SHA-256 hex length
            assert isinstance(checksum, str)

    def test_compress_backup(self):
        """Test backup compression"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BackupService(
                db_url="sqlite:///./test.db",
                backup_dir=tmpdir,
            )
            
            # Create test backup file
            backup_file = Path(tmpdir) / "backup.sql"
            backup_file.write_text("test backup content" * 100)
            original_size = backup_file.stat().st_size
            
            # Compress
            compressed = service._compress_backup(backup_file)
            
            assert compressed.suffix == ".gz"
            assert compressed.exists()
            assert compressed.stat().st_size < original_size

    def test_verify_backup(self):
        """Test backup verification"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BackupService(
                db_url="sqlite:///./test.db",
                backup_dir=tmpdir,
            )
            
            # Create test backup
            backup_file = Path(tmpdir) / "backup.sql"
            backup_file.write_text("test content")
            
            checksum = service._calculate_checksum(backup_file)
            
            # Verify
            is_valid = service.verify_backup(str(backup_file), checksum)
            assert is_valid is True
            
            # Verify with wrong checksum
            is_valid = service.verify_backup(str(backup_file), "wrong_checksum")
            assert is_valid is False

    def test_cleanup_old_backups(self):
        """Test cleanup of old backups"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BackupService(
                db_url="sqlite:///./test.db",
                backup_dir=tmpdir,
                retention_days=7,
            )
            
            # Create old backup file
            old_backup = Path(tmpdir) / "backup_daily_old.sql"
            old_backup.write_text("old backup")
            # Set modification time to 10 days ago
            import time
            old_time = time.time() - (10 * 24 * 60 * 60)
            os.utime(old_backup, (old_time, old_time))
            
            # Create recent backup
            recent_backup = Path(tmpdir) / "backup_daily_recent.sql"
            recent_backup.write_text("recent backup")
            
            # Cleanup
            stats = service.cleanup_old_backups()
            
            # Old backup should be deleted
            assert not old_backup.exists()
            # Recent backup should remain
            assert recent_backup.exists()
            assert stats["deleted_daily"] >= 1
