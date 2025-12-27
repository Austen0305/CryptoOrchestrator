# On-Call Procedures

Comprehensive guide for on-call engineers.

## On-Call Responsibilities

### Primary Responsibilities
- Monitor system health and alerts
- Respond to incidents within SLA
- Escalate critical issues
- Document incidents and resolutions

### Response Times
- **Critical (P0)**: < 15 minutes
- **High (P1)**: < 1 hour
- **Medium (P2)**: < 4 hours
- **Low (P3)**: < 24 hours

## Alert Channels

### Monitoring Dashboards
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Health Dashboard**: http://localhost:8000/api/health/detailed

### Notification Channels
- **Email**: Alerts sent to on-call email
- **SMS**: Critical alerts only
- **Slack/Discord**: Team notifications
- **PagerDuty/OpsGenie**: For critical incidents

## Common Alerts

### Database Alerts
- **Connection Pool Exhausted**: Check pool size, restart if needed
- **High Query Latency**: Optimize queries, check indexes
- **Replication Lag**: Check replica health, promote if needed

### Application Alerts
- **High Error Rate**: Check logs, identify root cause
- **High Response Time**: Check system resources, optimize
- **Memory Leak**: Restart application, investigate

### Security Alerts
- **Brute Force Attack**: Block IP, lock accounts
- **Suspicious Activity**: Review logs, investigate
- **Account Compromise**: Lock account, force password reset

## Incident Response Checklist

### Initial Response (0-5 minutes)
- [ ] Acknowledge alert
- [ ] Assess severity
- [ ] Check monitoring dashboards
- [ ] Review recent changes

### Investigation (5-30 minutes)
- [ ] Check error logs
- [ ] Review system metrics
- [ ] Identify root cause
- [ ] Determine impact scope

### Resolution (30+ minutes)
- [ ] Execute fix
- [ ] Verify resolution
- [ ] Monitor for stability
- [ ] Document incident

## Escalation Contacts

### Level 1: On-Call Engineer
- Primary responder
- Handles most incidents

### Level 2: Senior Engineer
- Escalate for complex issues
- Available 24/7 for critical incidents

### Level 3: Security Team
- Security incidents only
- Available for critical security issues

### Level 4: Management
- Business-critical incidents
- Extended outages

## Handoff Procedures

### End of Shift
- Review open incidents
- Document status
- Hand off to next on-call
- Update incident status

### Incident Handoff
- Brief next engineer
- Provide context
- Share investigation notes
- Set expectations

---

## Quick Reference

### Health Check
```bash
curl http://localhost:8000/healthz
```

### View Logs
```bash
tail -f logs/app.log
docker-compose logs -f backend
```

### Restart Services
```bash
docker-compose restart backend
sudo systemctl restart cryptoorchestrator
```

### Database Commands
```bash
psql -h localhost -U postgres -d cryptoorchestrator
SELECT * FROM pg_stat_activity;
```

---

**Last Updated**: December 12, 2025
