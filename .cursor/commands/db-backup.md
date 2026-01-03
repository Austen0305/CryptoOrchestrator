# Database Backup

Backup the CryptoOrchestrator database.

## Quick Backup

Run automated backup script:
```bash
python scripts/backup_database.py
```

Or use npm script:
```bash
npm run db:backup
```

## Backup Options

### Full Backup
```bash
python scripts/backup_database.py --full
```

### Incremental Backup
```bash
python scripts/backup_database.py --incremental
```

### Scheduled Backups
```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts/utilities/schedule_backups.ps1

# Linux/Mac
bash scripts/utilities/schedule_backups.sh
```

## Backup Location

Backups are stored in:
- **Default**: `backups/` directory
- **Custom**: Specify with `--output` flag

## Verify Backup

After backup, verify it was created:
```bash
# List available backups
python scripts/restore_database.py --list
```

## Best Practices

1. **Regular Backups**: Run backups before major changes
2. **Before Migrations**: Always backup before running migrations
3. **Before Deployments**: Backup before deploying to production
4. **Test Restores**: Periodically test restore procedures
5. **Offsite Storage**: Store backups in separate location

## Troubleshooting

If backup fails:
1. Check database connection in `.env`
2. Verify backup directory exists and is writable
3. Check disk space availability
4. Review backup script logs
