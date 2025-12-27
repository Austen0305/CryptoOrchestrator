# Disaster Recovery Runbook

This document provides procedures for disaster recovery and business continuity for CryptoOrchestrator.

## Recovery Objectives

- **RTO (Recovery Time Objective)**: 1 hour
- **RPO (Recovery Point Objective)**: 15 minutes
- **MTTR (Mean Time To Recovery)**: 45 minutes

## Backup Strategy

### Database Backups

#### Automated Backups

- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 30 days local, 90 days in S3
- **Format**: Compressed PostgreSQL custom format or SQLite copy
- **Location**: Local `./backups/` directory + S3 bucket

#### Manual Backups

```bash
# Create backup
python scripts/backup_database.py \
  --database-url "$DATABASE_URL" \
  --backup-dir ./backups \
  --s3-bucket cryptoorchestrator-backups \
  --retention-days 30

# Verify backup
python scripts/backup_database.py --verify-only
```

#### Point-in-Time Recovery (PostgreSQL)

PostgreSQL supports point-in-time recovery (PITR) using WAL archiving:

1. **Enable WAL Archiving**:
   ```sql
   -- In postgresql.conf
   wal_level = replica
   archive_mode = on
   archive_command = 'aws s3 cp %p s3://cryptoorchestrator-backups/wal/%f'
   ```

2. **Restore to Point in Time**:
   ```bash
   # Restore base backup
   pg_restore -d cryptoorchestrator base_backup.dump
   
   # Replay WAL files up to target time
   pg_recovery_target_time = '2024-01-15 14:30:00'
   ```

### Redis Backups

- **AOF (Append-Only File)**: Enabled for durability
- **Snapshots**: Daily snapshots to S3
- **Retention**: 7 days

### Application Data

- **Models**: Stored in S3 with versioning
- **Logs**: Centralized logging (CloudWatch, ELK)
- **Configuration**: Version controlled in Git

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms**:
- Database connection errors
- Data integrity errors
- Application crashes

**Recovery Steps**:

1. **Immediate Actions**:
   ```bash
   # Stop application
   kubectl scale deployment backend --replicas=0
   
   # Verify corruption
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **Restore from Backup**:
   ```bash
   # List available backups
   python scripts/restore_database.py --list
   
   # Restore latest backup
   python scripts/restore_database.py \
     --database-url "$DATABASE_URL" \
     --latest \
     --drop-existing \
     --confirm
   ```

3. **Verify Restoration**:
   ```bash
   # Check database integrity
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM bots;"
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM trades;"
   ```

4. **Restart Application**:
   ```bash
   kubectl scale deployment backend --replicas=3
   ```

5. **Monitor**:
   - Check application logs
   - Verify API endpoints
   - Monitor error rates

**Estimated Recovery Time**: 30-45 minutes

### Scenario 2: Complete Infrastructure Loss

**Symptoms**:
- All services unavailable
- Infrastructure provider outage
- Region-wide failure

**Recovery Steps**:

1. **Assess Situation**:
   - Determine scope of outage
   - Check backup availability
   - Estimate recovery time

2. **Provision New Infrastructure**:
   ```bash
   # Using Terraform
   cd terraform/aws
   terraform apply
   
   # Or using Kubernetes
   kubectl apply -f k8s/
   ```

3. **Restore Database**:
   ```bash
   # Download latest backup from S3
   aws s3 cp s3://cryptoorchestrator-backups/database-backups/latest.sql.gz ./backups/
   
   # Restore database
   python scripts/restore_database.py \
     --database-url "$DATABASE_URL" \
     --backup-file ./backups/latest.sql.gz \
     --confirm
   ```

4. **Restore Redis**:
   ```bash
   # Download Redis snapshot
   aws s3 cp s3://cryptoorchestrator-backups/redis/latest.rdb ./redis.rdb
   
   # Restore to Redis
   kubectl cp ./redis.rdb redis-0:/data/dump.rdb
   kubectl exec redis-0 -- redis-cli CONFIG SET dir /data
   kubectl exec redis-0 -- redis-cli CONFIG SET dbfilename dump.rdb
   ```

5. **Deploy Application**:
   ```bash
   kubectl apply -f k8s/backend-deployment.yaml
   kubectl apply -f k8s/frontend-deployment.yaml
   ```

6. **Update DNS**:
   - Point DNS records to new infrastructure
   - Wait for DNS propagation (5-15 minutes)

7. **Verify Services**:
   ```bash
   # Health checks
   curl https://api.cryptoorchestrator.com/health
   curl https://app.cryptoorchestrator.com/
   ```

**Estimated Recovery Time**: 1-2 hours

### Scenario 3: Data Loss (Accidental Deletion)

**Symptoms**:
- Missing data in database
- User reports missing records
- Audit logs show deletion

**Recovery Steps**:

1. **Stop Further Damage**:
   ```bash
   # Scale down application
   kubectl scale deployment backend --replicas=0
   ```

2. **Identify Last Good State**:
   ```bash
   # List backups with timestamps
   python scripts/restore_database.py --list
   
   # Find backup before deletion
   # Restore to that point
   ```

3. **Point-in-Time Recovery**:
   ```bash
   # Restore to specific time (PostgreSQL)
   python scripts/restore_database.py \
     --database-url "$DATABASE_URL" \
     --backup-file backup_before_deletion.sql.gz \
     --drop-existing \
     --confirm
   ```

4. **Verify Data**:
   ```bash
   # Check critical tables
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM trades WHERE created_at > '2024-01-15';"
   ```

5. **Restart Application**:
   ```bash
   kubectl scale deployment backend --replicas=3
   ```

**Estimated Recovery Time**: 30-60 minutes

### Scenario 4: Security Breach

**Symptoms**:
- Unauthorized access detected
- Suspicious activity in logs
- Data exfiltration alerts

**Recovery Steps**:

1. **Immediate Containment**:
   ```bash
   # Isolate affected systems
   kubectl scale deployment backend --replicas=0
   
   # Revoke compromised credentials
   # Update secrets in Kubernetes
   kubectl delete secret cryptoorchestrator-secrets
   kubectl apply -f k8s/secrets.yaml  # With new credentials
   ```

2. **Assess Damage**:
   - Review audit logs
   - Check for data modification
   - Identify compromised accounts

3. **Restore from Clean Backup**:
   ```bash
   # Restore database from before breach
   python scripts/restore_database.py \
     --backup-file backup_before_breach.sql.gz \
     --drop-existing \
     --confirm
   ```

4. **Rotate All Secrets**:
   - Database passwords
   - JWT secrets
   - API keys
   - Encryption keys

5. **Patch Vulnerabilities**:
   - Update application code
   - Apply security patches
   - Review access controls

6. **Restart Services**:
   ```bash
   kubectl apply -f k8s/
   ```

7. **Notify Stakeholders**:
   - Internal team
   - Affected users (if required)
   - Regulatory bodies (if required)

**Estimated Recovery Time**: 2-4 hours

## Backup Verification

### Daily Verification

```bash
# Automated verification script
python scripts/backup_database.py --verify-only
```

### Weekly Full Test

1. **Create Test Environment**:
   ```bash
   # Provision test cluster
   kubectl create namespace cryptoorchestrator-test
   ```

2. **Restore Backup**:
   ```bash
   python scripts/restore_database.py \
     --database-url "postgresql://test:test@test-db:5432/test" \
     --latest \
     --confirm
   ```

3. **Run Smoke Tests**:
   ```bash
   pytest tests/test_backup_restore.py
   ```

4. **Verify Data Integrity**:
   ```bash
   # Check record counts
   # Verify relationships
   # Test critical queries
   ```

## Backup Retention Policy

| Backup Type | Local Retention | S3 Retention | Purpose |
|------------|----------------|--------------|---------|
| Daily | 7 days | 30 days | Quick recovery |
| Weekly | 30 days | 90 days | Medium-term recovery |
| Monthly | N/A | 1 year | Long-term archive |
| Point-in-Time | N/A | 7 days | Precise recovery |

## Monitoring & Alerting

### Backup Monitoring

- **Success Rate**: Alert if backup fails 2 consecutive times
- **Backup Size**: Alert if size changes >20% from baseline
- **Backup Age**: Alert if no backup in last 26 hours

### Recovery Testing

- **Monthly**: Full disaster recovery drill
- **Quarterly**: Cross-region recovery test
- **Annually**: Complete infrastructure rebuild test

## Communication Plan

### Internal

- **On-Call Engineer**: Immediate notification
- **Engineering Team**: Within 15 minutes
- **Management**: Within 30 minutes

### External

- **Users**: If downtime >1 hour
- **Stakeholders**: If data loss or security breach
- **Regulatory**: If required by compliance

## Post-Recovery Actions

1. **Root Cause Analysis**:
   - Document incident
   - Identify root cause
   - Create action items

2. **Improvements**:
   - Update procedures
   - Enhance monitoring
   - Improve backups

3. **Documentation**:
   - Update runbook
   - Share lessons learned
   - Train team

## Emergency Contacts

- **On-Call Engineer**: [Phone/Email]
- **Database Admin**: [Phone/Email]
- **Infrastructure Team**: [Phone/Email]
- **Security Team**: [Phone/Email]

## Recovery Checklist

- [ ] Assess situation and scope
- [ ] Notify team and stakeholders
- [ ] Stop further damage
- [ ] Identify recovery point
- [ ] Provision infrastructure (if needed)
- [ ] Restore database
- [ ] Restore Redis cache
- [ ] Deploy application
- [ ] Update DNS (if needed)
- [ ] Verify services
- [ ] Monitor for issues
- [ ] Document incident
- [ ] Post-mortem review

## Testing Schedule

- **Weekly**: Backup verification
- **Monthly**: Restore test in staging
- **Quarterly**: Full DR drill
- **Annually**: Complete infrastructure rebuild

## Additional Resources

- [Backup Scripts](../scripts/backup_database.py)
- [Restore Scripts](../scripts/restore_database.py)
- [Infrastructure Guide](./INFRASTRUCTURE.md)
- [Monitoring Setup](./MONITORING.md)
