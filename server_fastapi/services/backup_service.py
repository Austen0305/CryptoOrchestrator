"""
Backup Service
Automated database backups and point-in-time recovery
"""

import logging
import subprocess
import gzip
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


class BackupService:
    """
    Service for managing database backups
    
    Features:
    - Automated database backups
    - Backup compression
    - Backup verification
    - Retention policy management
    - Point-in-time recovery support
    """
    
    def __init__(
        self,
        db_url: str,
        backup_dir: str = "./backups",
        retention_days: int = 7,
        retention_weeks: int = 4,
        retention_months: int = 12,
        secondary_storage: Optional[str] = None,  # Cloud storage path
    ):
        """
        Initialize backup service
        
        Args:
            db_url: Database URL
            backup_dir: Backup directory path
            retention_days: Days to keep daily backups
            retention_weeks: Weeks to keep weekly backups
            retention_months: Months to keep monthly backups
        """
        self.db_url = db_url
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.retention_weeks = retention_weeks
        self.retention_months = retention_months
        self.secondary_storage = secondary_storage  # Optional cloud storage
    
    def create_backup(
        self,
        backup_type: str = "full",
        compress: bool = True,
    ) -> Dict[str, Any]:
        """
        Create database backup
        
        Args:
            backup_type: Backup type ("full", "incremental")
            compress: Whether to compress backup
        
        Returns:
            Backup metadata
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{backup_type}_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Determine database type and create backup
            if "postgresql" in self.db_url or "postgres" in self.db_url:
                # PostgreSQL backup
                backup_path = self._backup_postgresql(backup_path)
            elif "sqlite" in self.db_url:
                # SQLite backup
                backup_path = self._backup_sqlite(backup_path)
            else:
                raise ValueError(f"Unsupported database type: {self.db_url}")
            
            # Compress if requested
            if compress:
                backup_path = self._compress_backup(backup_path)
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Get file size
            file_size = backup_path.stat().st_size
            
            # Replicate to secondary storage if configured
            secondary_path = None
            if self.secondary_storage:
                try:
                    secondary_path = self._replicate_to_secondary(backup_path)
                    logger.info(f"Backup replicated to secondary storage: {secondary_path}")
                except Exception as e:
                    logger.warning(f"Failed to replicate to secondary storage: {e}")

            backup_metadata = {
                "backup_id": f"{backup_type}_{timestamp}",
                "backup_type": backup_type,
                "file_path": str(backup_path),
                "secondary_path": secondary_path,
                "file_size": file_size,
                "checksum": checksum,
                "created_at": datetime.utcnow().isoformat(),
                "compressed": compress,
            }
            
            logger.info(f"Backup created: {backup_path} ({file_size} bytes)")
            
            return backup_metadata
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}", exc_info=True)
            raise
    
    def _backup_postgresql(self, backup_path: Path) -> Path:
        """Create PostgreSQL backup using pg_dump"""
        # Extract connection details from URL
        # Format: postgresql://user:password@host:port/database
        import re
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", self.db_url)
        if not match:
            raise ValueError("Invalid PostgreSQL URL format")
        
        user, password, host, port, database = match.groups()
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        # Run pg_dump
        cmd = [
            "pg_dump",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", database,
            "-F", "c",  # Custom format
            "-f", str(backup_path),
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr}")
        
        return backup_path
    
    def _backup_sqlite(self, backup_path: Path) -> Path:
        """Create SQLite backup"""
        # Extract database path from URL
        # Format: sqlite:///path/to/database.db
        db_path = self.db_url.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        # Copy database file
        import shutil
        shutil.copy2(db_path, backup_path)
        
        return backup_path
    
    def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup file"""
        compressed_path = backup_path.with_suffix(backup_path.suffix + ".gz")
        
        with open(backup_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                f_out.writelines(f_in)
        
        # Remove original
        backup_path.unlink()
        
        return compressed_path
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of backup file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def verify_backup(
        self,
        backup_path: str,
        expected_checksum: Optional[str] = None,
    ) -> bool:
        """
        Verify backup integrity
        
        Args:
            backup_path: Path to backup file
            expected_checksum: Expected checksum (optional)
        
        Returns:
            True if backup is valid
        """
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        # Verify checksum if provided
        if expected_checksum:
            actual_checksum = self._calculate_checksum(backup_file)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {backup_path}")
                return False
        
        # Try to decompress and verify structure (for compressed backups)
        if backup_file.suffix == ".gz":
            try:
                with gzip.open(backup_file, "rb") as f:
                    # Try to read first few bytes
                    f.read(1024)
            except Exception as e:
                logger.error(f"Failed to decompress backup: {e}")
                return False
        
        logger.info(f"Backup verified: {backup_path}")
        return True
    
    def list_backups(
        self,
        backup_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all backups
        
        Args:
            backup_type: Filter by backup type
        
        Returns:
            List of backup metadata
        """
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.sql*"):
            try:
                stat = backup_file.stat()
                backups.append({
                    "file_path": str(backup_file),
                    "file_size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "compressed": backup_file.suffix == ".gz",
                })
            except Exception as e:
                logger.warning(f"Failed to get metadata for {backup_file}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self) -> Dict[str, int]:
        """
        Clean up old backups based on retention policy
        
        Returns:
            Dictionary with cleanup statistics
        """
        now = datetime.utcnow()
        deleted_daily = 0
        deleted_weekly = 0
        deleted_monthly = 0
        
        for backup_file in self.backup_dir.glob("backup_*.sql*"):
            try:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                age = now - file_time
                
                # Determine backup type from filename
                if "daily" in backup_file.name or age.days < 7:
                    if age.days > self.retention_days:
                        backup_file.unlink()
                        deleted_daily += 1
                elif "weekly" in backup_file.name or (age.days >= 7 and age.days < 30):
                    if age.days > (self.retention_weeks * 7):
                        backup_file.unlink()
                        deleted_weekly += 1
                elif "monthly" in backup_file.name or age.days >= 30:
                    if age.days > (self.retention_months * 30):
                        backup_file.unlink()
                        deleted_monthly += 1
                        
            except Exception as e:
                logger.warning(f"Failed to process {backup_file}: {e}")
        
        logger.info(
            f"Backup cleanup completed: {deleted_daily} daily, "
            f"{deleted_weekly} weekly, {deleted_monthly} monthly backups deleted"
        )
        
        return {
            "deleted_daily": deleted_daily,
            "deleted_weekly": deleted_weekly,
            "deleted_monthly": deleted_monthly,
        }
    
    def _replicate_to_secondary(self, backup_path: Path) -> Optional[str]:
        """
        Replicate backup to secondary storage location
        
        Args:
            backup_path: Path to backup file
        
        Returns:
            Secondary storage path if successful, None otherwise
        """
        if not self.secondary_storage:
            return None
        
        try:
            # For cloud storage, would use boto3 (S3) or backblaze SDK
            # For now, support local secondary directory
            secondary_dir = Path(self.secondary_storage)
            secondary_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy backup to secondary location
            import shutil
            secondary_path = secondary_dir / backup_path.name
            shutil.copy2(backup_path, secondary_path)
            
            logger.info(f"Backup replicated to secondary: {secondary_path}")
            return str(secondary_path)
            
        except Exception as e:
            logger.error(f"Failed to replicate backup: {e}", exc_info=True)
            return None
    
    def restore_backup(
        self,
        backup_path: str,
        verify: bool = True,
    ) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
            verify: Whether to verify backup before restoring
        
        Returns:
            True if restore successful
        """
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Verify backup if requested
        if verify:
            if not self.verify_backup(backup_path):
                raise ValueError("Backup verification failed")
        
        try:
            # Decompress if needed
            if backup_file.suffix == ".gz":
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".sql") as tmp:
                    with gzip.open(backup_file, "rb") as f_in:
                        tmp.write(f_in.read())
                    restore_path = tmp.name
            else:
                restore_path = str(backup_file)
            
            # Restore based on database type
            if "postgresql" in self.db_url:
                self._restore_postgresql(restore_path)
            elif "sqlite" in self.db_url:
                self._restore_sqlite(restore_path)
            else:
                raise ValueError(f"Unsupported database type: {self.db_url}")
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}", exc_info=True)
            raise
    
    def _restore_postgresql(self, backup_path: str) -> None:
        """Restore PostgreSQL database"""
        import re
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", self.db_url)
        if not match:
            raise ValueError("Invalid PostgreSQL URL format")
        
        user, password, host, port, database = match.groups()
        
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        cmd = [
            "pg_restore",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", database,
            "-c",  # Clean (drop) before restore
            backup_path,
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"pg_restore failed: {result.stderr}")
    
    def _restore_sqlite(self, backup_path: str) -> None:
        """Restore SQLite database"""
        db_path = self.db_url.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
        
        import shutil
        shutil.copy2(backup_path, db_path)
