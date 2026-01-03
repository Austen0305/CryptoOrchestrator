# Database Restore

Restore the CryptoOrchestrator database from backup.

## ⚠️ Warning

**CRITICAL**: Restoring a database will **overwrite** the current database. Only restore if:
- Current database is corrupted
- You need to recover from a backup
- You're restoring to a different environment

## List Available Backups

Before restoring, list available backups:

```bash
python scripts/restore_database.py --list
```

This shows:
- Backup file names
- Backup dates
- Backup sizes
- Backup types (full/incremental)

## Restore from Backup

### Quick Restore

Restore from most recent backup:
```bash
python scripts/restore_database.py
```

### Restore Specific Backup

Restore from specific backup file:
```bash
python scripts/restore_database.py --backup-file backups/backup_2025-12-30_120000.sql
```

### Restore to Different Database

Restore to a different database (useful for testing):
```bash
python scripts/restore_database.py --database-url postgresql://user:pass@localhost:5432/test_db
```

## Restore Steps

### 1. Stop Services

**Important**: Stop all services before restoring:

```bash
# Stop backend
# Ctrl+C in terminal running FastAPI

# Or if using Docker
docker-compose down
```

### 2. Backup Current Database (Optional but Recommended)

Before restoring, backup current database:
```bash
python scripts/backup_database.py
```

### 3. Restore Database

```bash
python scripts/restore_database.py --backup-file <backup-file>
```

### 4. Verify Restore

```bash
# Check database health
python scripts/utilities/database-health.py

# Verify migrations
alembic current

# Check data
# Connect to database and verify data exists
```

### 5. Restart Services

```bash
# Start services
npm run start:all

# Or if using Docker
docker-compose up -d
```

## Restore Types

### Full Restore

Restores complete database:
```bash
python scripts/restore_database.py --full --backup-file <backup-file>
```

### Incremental Restore

Restores from incremental backup (requires base backup):
```bash
python scripts/restore_database.py --incremental --backup-file <backup-file>
```

## Environment-Specific Restores

### Development

```bash
# Restore to development database
python scripts/restore_database.py \
  --backup-file backups/production_backup.sql \
  --database-url sqlite+aiosqlite:///./crypto_orchestrator.db
```

### Staging

```bash
# Restore to staging database
python scripts/restore_database.py \
  --backup-file backups/production_backup.sql \
  --database-url $STAGING_DATABASE_URL
```

### Production

**⚠️ EXTREME CAUTION**: Only restore to production if absolutely necessary!

```bash
# 1. Backup current production database first!
python scripts/backup_database.py --output production_backup_before_restore.sql

# 2. Restore
python scripts/restore_database.py \
  --backup-file backups/backup_to_restore.sql \
  --database-url $PRODUCTION_DATABASE_URL

# 3. Verify immediately
python scripts/utilities/database-health.py
```

## Troubleshooting

### Restore Fails

1. **Check Backup File**: Verify backup file exists and is valid
2. **Check Database Connection**: Verify database URL is correct
3. **Check Permissions**: Verify database user has restore permissions
4. **Check Disk Space**: Verify sufficient disk space
5. **Check Logs**: Review restore script logs

### Data Missing After Restore

1. **Check Backup Date**: Verify backup contains expected data
2. **Check Restore Logs**: Review what was restored
3. **Verify Backup**: Check backup file integrity
4. **Check Database**: Connect and verify data manually

### Migration Issues After Restore

1. **Check Migration Status**: `alembic current`
2. **Run Migrations**: `alembic upgrade head`
3. **Check Migration History**: `alembic history`
4. **Resolve Conflicts**: May need to manually resolve migration conflicts

## Best Practices

1. **Always Backup Before Restore**: Backup current database first
2. **Test Restores**: Test restore procedure on staging first
3. **Verify Backups**: Regularly verify backup integrity
4. **Document Restores**: Document when and why you restored
5. **Monitor After Restore**: Monitor database closely after restore
6. **Have Rollback Plan**: Know how to rollback if restore fails

## Safety Checklist

Before restoring:
- [ ] Current database is backed up
- [ ] Backup file is verified
- [ ] Services are stopped
- [ ] Database connection is correct
- [ ] Sufficient disk space available
- [ ] Restore procedure is tested (on staging)
- [ ] Rollback plan is ready

## Summary

✅ **List Backups**: `python scripts/restore_database.py --list`  
✅ **Restore**: `python scripts/restore_database.py --backup-file <file>`  
✅ **Verify**: Check database health and data  
✅ **Restart**: Start services after restore

**Remember**: Database restores are destructive - always backup first and verify backups!
