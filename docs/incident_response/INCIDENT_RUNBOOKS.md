# Incident Response Runbooks

Step-by-step procedures for common incidents.

## Table of Contents

1. [Database Connection Failures](#database-connection-failures)
2. [High Error Rate](#high-error-rate)
3. [Security Incidents](#security-incidents)
4. [Performance Degradation](#performance-degradation)
5. [Data Corruption](#data-corruption)

---

## Database Connection Failures

### Symptoms
- Database connection errors in logs
- 500 errors on API endpoints
- Health check failures

### Immediate Actions

1. **Check Database Status**:
   ```bash
   curl http://localhost:8000/healthz
   psql -h localhost -U postgres -c "SELECT 1"
   ```

2. **Check Connection Pool**:
   - Review connection pool metrics
   - Check for connection leaks
   - Verify pool size settings

3. **Restart Database** (if needed):
   ```bash
   # PostgreSQL
   sudo systemctl restart postgresql
   # Or Docker
   docker-compose restart postgres
   ```

4. **Restart Application**:
   ```bash
   # Restart FastAPI
   sudo systemctl restart cryptoorchestrator
   # Or Docker
   docker-compose restart backend
   ```

### Verification
- Health check returns 200
- API endpoints respond normally
- No connection errors in logs

---

## High Error Rate

### Symptoms
- Error rate > 10 errors/minute
- Multiple 500 errors
- User complaints

### Immediate Actions

1. **Check Error Logs**:
   ```bash
   tail -f logs/error.log | grep ERROR
   ```

2. **Identify Error Pattern**:
   - Check most common errors
   - Identify affected endpoints
   - Check for recent deployments

3. **Check System Resources**:
   - CPU usage
   - Memory usage
   - Disk space
   - Database connections

4. **Rollback Recent Changes** (if applicable):
   ```bash
   git revert <commit-hash>
   docker-compose up -d --build
   ```

5. **Scale Resources** (if needed):
   - Increase instance size
   - Add more workers
   - Scale database

### Verification
- Error rate returns to normal
- No new errors in logs
- System stability restored

---

## Security Incidents

### Brute Force Attack

**Symptoms**: Multiple failed login attempts from same IP

**Actions**:
1. Block IP address automatically (via security monitoring)
2. Lock affected user accounts
3. Review security logs
4. Notify security team

**Script**:
```bash
python scripts/incident_response/automated_response.py \
  --incident-type brute_force_attempt \
  --severity high \
  --ip-address <IP>
```

### Account Compromise

**Symptoms**: Login from multiple IPs, unusual activity

**Actions**:
1. Lock user account immediately
2. Force password reset
3. Revoke all sessions
4. Review account activity
5. Notify user

**Script**:
```bash
python scripts/incident_response/automated_response.py \
  --incident-type account_compromise \
  --severity critical \
  --user-id <USER_ID>
```

### DDoS Attack

**Symptoms**: High request rate, service degradation

**Actions**:
1. Enable rate limiting
2. Block malicious IPs
3. Scale resources if needed
4. Contact DDoS protection provider
5. Monitor attack patterns

---

## Performance Degradation

### Symptoms
- Slow API responses
- High latency (p95 > 2s)
- Timeout errors

### Immediate Actions

1. **Check System Metrics**:
   - CPU usage
   - Memory usage
   - Database query times
   - Cache hit rates

2. **Check Database Performance**:
   ```sql
   SELECT * FROM pg_stat_activity WHERE state = 'active';
   EXPLAIN ANALYZE <slow_query>;
   ```

3. **Check Cache Performance**:
   - Redis connection
   - Cache hit rates
   - Cache size

4. **Optimize Queries**:
   - Add missing indexes
   - Optimize slow queries
   - Enable query caching

5. **Scale Resources**:
   - Add more application instances
   - Scale database
   - Increase cache size

### Verification
- API latency returns to normal
- No timeout errors
- System resources stable

---

## Data Corruption

### Symptoms
- Data inconsistency errors
- Unexpected application behavior
- Database integrity errors

### Immediate Actions

1. **Stop Affected Services**:
   ```bash
   # Stop application to prevent further corruption
   docker-compose stop backend
   ```

2. **Assess Corruption Scope**:
   - Identify affected tables
   - Determine time of corruption
   - Check backup availability

3. **Restore from Backup**:
   ```bash
   python scripts/backup_database.py restore --backup-path <backup_file>
   ```

4. **Verify Data Integrity**:
   - Run data validation
   - Check critical data
   - Verify application functionality

5. **Restart Services**:
   ```bash
   docker-compose start backend
   ```

### Verification
- Data integrity verified
- Application functioning normally
- No data loss

---

## Escalation Procedures

### Severity Levels

- **Critical**: Immediate response required (< 15 minutes)
- **High**: Response within 1 hour
- **Medium**: Response within 4 hours
- **Low**: Response within 24 hours

### Escalation Path

1. **Level 1**: Automated response (scripts)
2. **Level 2**: On-call engineer
3. **Level 3**: Security team / Management
4. **Level 4**: External support

---

## Post-Incident Procedures

1. **Document Incident**:
   - Timeline of events
   - Root cause analysis
   - Actions taken
   - Resolution time

2. **Post-Mortem Meeting** (within 48 hours):
   - Review incident
   - Identify improvements
   - Update procedures
   - Assign action items

3. **Update Runbooks**:
   - Incorporate lessons learned
   - Improve procedures
   - Update documentation

---

## Additional Resources

- [Disaster Recovery Plan](../DISASTER_RECOVERY_PLAN.md)
- [Security Documentation](../security/SECURITY_DOCUMENTATION.md)
- [Monitoring Dashboard](/api/health/detailed)
