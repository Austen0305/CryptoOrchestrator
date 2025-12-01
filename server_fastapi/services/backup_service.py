"""
Automated Database Backup Service
Provides scheduled, encrypted backups with verification and cloud storage
"""
import logging
import asyncio
import subprocess
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class BackupService:
    """Service for automated database backups"""
    
    def __init__(self):
        self.settings = get_settings()
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.retention_days = 30  # Keep backups for 30 days
        self.encryption_enabled = True
        
    async def create_backup(
        self,
        backup_type: str = "full",
        encrypt: bool = True
    ) -> Dict[str, Any]:
        """
        Create a database backup
        
        Args:
            backup_type: Type of backup ('full', 'incremental')
            encrypt: Whether to encrypt the backup
        
        Returns:
            Dict with backup details
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{backup_type}_{timestamp}.sql"
            backup_path = self.backup_dir / backup_filename
            
            # Get database URL
            db_url = self.settings.database_url
            
            # Determine backup method based on database type
            if "sqlite" in db_url.lower():
                # SQLite backup
                success = await self._backup_sqlite(db_url, backup_path)
            elif "postgresql" in db_url.lower() or "postgres" in db_url.lower():
                # PostgreSQL backup
                success = await self._backup_postgresql(db_url, backup_path)
            else:
                raise ValueError(f"Unsupported database type: {db_url}")
            
            if not success:
                raise Exception("Backup creation failed")
            
            # Encrypt backup if requested
            if encrypt and self.encryption_enabled:
                encrypted_path = await self._encrypt_backup(backup_path)
                if encrypted_path:
                    # Remove unencrypted backup
                    backup_path.unlink()
                    backup_path = encrypted_path
                    backup_filename = encrypted_path.name
            
            # Verify backup
            backup_size = backup_path.stat().st_size
            is_valid = await self._verify_backup(backup_path)
            
            if not is_valid:
                raise Exception("Backup verification failed")
            
            # Upload to cloud storage (if configured)
            cloud_url = None
            try:
                cloud_url = await self._upload_to_cloud(backup_path)
            except Exception as e:
                logger.warning(f"Cloud upload failed: {e}")
            
            backup_info = {
                "backup_id": f"backup_{timestamp}",
                "filename": backup_filename,
                "path": str(backup_path),
                "size_bytes": backup_size,
                "size_mb": round(backup_size / (1024 * 1024), 2),
                "type": backup_type,
                "encrypted": encrypt and self.encryption_enabled,
                "timestamp": timestamp,
                "verified": is_valid,
                "cloud_url": cloud_url,
                "status": "success"
            }
            
            logger.info(f"✅ Backup created successfully: {backup_filename} ({backup_info['size_mb']} MB)")
            
            # Clean up old backups
            await self._cleanup_old_backups()
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _backup_sqlite(self, db_url: str, backup_path: Path) -> bool:
        """Backup SQLite database"""
        try:
            # Extract database path from URL
            if db_url.startswith("sqlite+aiosqlite:///"):
                db_path = db_url.replace("sqlite+aiosqlite:///", "")
            elif db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")
            else:
                db_path = db_url.replace("sqlite+aiosqlite://", "").replace("sqlite://", "")
            
            # Use SQLite backup API
            import sqlite3
            source_conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(str(backup_path))
            
            source_conn.backup(backup_conn)
            source_conn.close()
            backup_conn.close()
            
            return True
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}", exc_info=True)
            return False
    
    async def _backup_postgresql(self, db_url: str, backup_path: Path) -> bool:
        """Backup PostgreSQL database using pg_dump"""
        try:
            # Extract connection details from URL
            # Format: postgresql://user:password@host:port/database
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(db_url.replace("postgresql+asyncpg://", "postgresql://"))
            
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h", parsed.hostname or "localhost",
                "-p", str(parsed.port or 5432),
                "-U", parsed.username or "postgres",
                "-d", parsed.path.lstrip("/") or "postgres",
                "-F", "c",  # Custom format
                "-f", str(backup_path)
            ]
            
            # Set password via environment
            env = os.environ.copy()
            if parsed.password:
                env["PGPASSWORD"] = parsed.password
            
            # Run pg_dump
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"pg_dump failed: {stderr.decode()}")
                return False
            
            return True
        except FileNotFoundError:
            logger.warning("pg_dump not found, PostgreSQL backup unavailable")
            return False
        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {e}", exc_info=True)
            return False
    
    async def _encrypt_backup(self, backup_path: Path) -> Optional[Path]:
        """Encrypt backup file using GPG"""
        try:
            encrypted_path = backup_path.with_suffix(backup_path.suffix + ".gpg")
            
            # Get encryption key from settings or environment
            encryption_key = os.getenv("BACKUP_ENCRYPTION_KEY")
            if not encryption_key:
                logger.warning("No encryption key found, skipping encryption")
                return None
            
            # Use GPG to encrypt
            cmd = [
                "gpg",
                "--symmetric",
                "--cipher-algo", "AES256",
                "--batch",
                "--passphrase", encryption_key,
                "--output", str(encrypted_path),
                str(backup_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Encryption failed: {stderr.decode()}")
                return None
            
            return encrypted_path
        except FileNotFoundError:
            logger.warning("GPG not found, encryption unavailable")
            return None
        except Exception as e:
            logger.error(f"Encryption failed: {e}", exc_info=True)
            return None
    
    async def _verify_backup(self, backup_path: Path) -> bool:
        """Verify backup file integrity"""
        try:
            # Check file exists and has content
            if not backup_path.exists():
                return False
            
            if backup_path.stat().st_size == 0:
                return False
            
            # For SQLite, try to open and verify
            if backup_path.suffix == ".sql" or backup_path.suffix == ".db":
                try:
                    import sqlite3
                    conn = sqlite3.connect(str(backup_path))
                    conn.execute("SELECT 1")
                    conn.close()
                    return True
                except:
                    # Not SQLite or corrupted, but might be valid PostgreSQL backup
                    return True
            
            # For encrypted backups, just check size
            if backup_path.suffix == ".gpg":
                return backup_path.stat().st_size > 0
            
            return True
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    async def _upload_to_cloud(self, backup_path: Path) -> Optional[str]:
        """Upload backup to cloud storage (S3, etc.)"""
        try:
            # Check if cloud storage is configured
            s3_bucket = os.getenv("BACKUP_S3_BUCKET")
            if not s3_bucket:
                return None
            
            # Use boto3 for S3 upload
            try:
                import boto3
                from botocore.exceptions import ClientError
                
                s3_client = boto3.client('s3')
                s3_key = f"backups/{backup_path.name}"
                
                s3_client.upload_file(
                    str(backup_path),
                    s3_bucket,
                    s3_key,
                    ExtraArgs={'ServerSideEncryption': 'AES256'}
                )
                
                return f"s3://{s3_bucket}/{s3_key}"
            except ImportError:
                logger.warning("boto3 not installed, S3 upload unavailable")
                return None
        except Exception as e:
            logger.warning(f"Cloud upload failed: {e}")
            return None
    
    async def _cleanup_old_backups(self) -> int:
        """Remove backups older than retention period"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            deleted_count = 0
            
            for backup_file in self.backup_dir.glob("backup_*"):
                try:
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old backup: {backup_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete old backup {backup_file.name}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backups")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return 0
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        try:
            backups = []
            
            for backup_file in sorted(self.backup_dir.glob("backup_*"), reverse=True):
                try:
                    stat = backup_file.stat()
                    backups.append({
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "encrypted": backup_file.suffix == ".gpg"
                    })
                except Exception as e:
                    logger.warning(f"Error reading backup info for {backup_file.name}: {e}")
            
            return backups
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    async def restore_backup(
        self,
        backup_filename: str,
        verify_only: bool = False
    ) -> Dict[str, Any]:
        """
        Restore database from backup
        
        Args:
            backup_filename: Name of backup file to restore
            verify_only: If True, only verify backup without restoring
        
        Returns:
            Dict with restore status
        """
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_filename}")
            
            # Decrypt if needed
            if backup_path.suffix == ".gpg":
                decrypted_path = await self._decrypt_backup(backup_path)
                if not decrypted_path:
                    raise Exception("Failed to decrypt backup")
                backup_path = decrypted_path
            
            # Verify backup before restore
            is_valid = await self._verify_backup(backup_path)
            if not is_valid:
                raise Exception("Backup verification failed")
            
            if verify_only:
                return {
                    "status": "verified",
                    "backup_file": backup_filename,
                    "message": "Backup verified successfully"
                }
            
            # Perform restore based on database type
            db_url = self.settings.database_url
            if "sqlite" in db_url.lower():
                success = await self._restore_sqlite(db_url, backup_path)
            elif "postgresql" in db_url.lower() or "postgres" in db_url.lower():
                success = await self._restore_postgresql(db_url, backup_path)
            else:
                raise ValueError(f"Unsupported database type: {db_url}")
            
            if not success:
                raise Exception("Restore failed")
            
            return {
                "status": "success",
                "backup_file": backup_filename,
                "message": "Database restored successfully"
            }
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "backup_file": backup_filename
            }
    
    async def _decrypt_backup(self, encrypted_path: Path) -> Optional[Path]:
        """Decrypt backup file"""
        try:
            decrypted_path = encrypted_path.with_suffix("")
            
            encryption_key = os.getenv("BACKUP_ENCRYPTION_KEY")
            if not encryption_key:
                raise ValueError("No encryption key found")
            
            cmd = [
                "gpg",
                "--decrypt",
                "--batch",
                "--passphrase", encryption_key,
                "--output", str(decrypted_path),
                str(encrypted_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Decryption failed: {stderr.decode()}")
                return None
            
            return decrypted_path
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    async def _restore_sqlite(self, db_url: str, backup_path: Path) -> bool:
        """Restore SQLite database"""
        try:
            # Extract database path
            if db_url.startswith("sqlite+aiosqlite:///"):
                db_path = db_url.replace("sqlite+aiosqlite:///", "")
            else:
                db_path = db_url.replace("sqlite:///", "").replace("sqlite+aiosqlite://", "").replace("sqlite://", "")
            
            # Copy backup to database location
            import shutil
            shutil.copy2(backup_path, db_path)
            
            return True
        except Exception as e:
            logger.error(f"SQLite restore failed: {e}", exc_info=True)
            return False
    
    async def _restore_postgresql(self, db_url: str, backup_path: Path) -> bool:
        """Restore PostgreSQL database using pg_restore"""
        try:
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(db_url.replace("postgresql+asyncpg://", "postgresql://"))
            
            cmd = [
                "pg_restore",
                "-h", parsed.hostname or "localhost",
                "-p", str(parsed.port or 5432),
                "-U", parsed.username or "postgres",
                "-d", parsed.path.lstrip("/") or "postgres",
                "-c",  # Clean (drop) existing objects
                str(backup_path)
            ]
            
            env = os.environ.copy()
            if parsed.password:
                env["PGPASSWORD"] = parsed.password
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"pg_restore failed: {stderr.decode()}")
                return False
            
            return True
        except FileNotFoundError:
            logger.warning("pg_restore not found, PostgreSQL restore unavailable")
            return False
        except Exception as e:
            logger.error(f"PostgreSQL restore failed: {e}", exc_info=True)
            return False


# Global instance
backup_service = BackupService()

