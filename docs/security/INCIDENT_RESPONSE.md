# Incident Response Guide

This guide outlines procedures for responding to incidents in the CryptoOrchestrator platform, including crash reports, security events, and system failures.

## Overview

The platform integrates with Sentry for error tracking and Electron crash reporting. All critical errors are automatically forwarded to incident management systems when thresholds are exceeded.

## Incident Classification

### Severity Levels

1. **Critical (P0)**: System down, data loss, security breach
   - Response time: Immediate
   - Escalation: On-call engineer + security team

2. **High (P1)**: Major feature broken, significant performance degradation
   - Response time: 15 minutes
   - Escalation: On-call engineer

3. **Medium (P2)**: Minor feature broken, moderate performance issues
   - Response time: 1 hour
   - Escalation: Engineering team

4. **Low (P3)**: Cosmetic issues, minor bugs
   - Response time: 4 hours
   - Escalation: Next business day

## Incident Sources

### Sentry Events

Sentry automatically captures:
- Backend exceptions (FastAPI)
- Frontend JavaScript errors
- Database query errors
- External API failures

**Configuration**: Set `SENTRY_DSN` environment variable

### Electron Crash Reports

Electron automatically reports:
- Main process crashes
- Renderer process crashes
- Unhandled exceptions
- Native module crashes

**Configuration**: Set `SENTRY_DSN` or `ELECTRON_SENTRY_DSN` environment variable

### Manual Reports

Users can report issues via:
- Support tickets
- GitHub issues
- Email support

## Incident Detection

### Automated Detection

1. **Sentry Alerts**: Configured in Sentry dashboard
   - Error rate spikes
   - New error types
   - Performance degradation

2. **Crash Report Triage**: `server_fastapi/services/monitoring/crash_report_triage.py`
   - Automatically forwards critical crashes to incident management
   - Severity-based routing
   - Deduplication

3. **Health Checks**: `/healthz` endpoint
   - Database connectivity
   - Redis availability
   - External API status

### Manual Detection

- User reports
- Monitoring dashboards
- Log analysis

## Incident Response Workflow

### Step 1: Acknowledge

1. **Receive alert** from Sentry, PagerDuty, or monitoring system
2. **Acknowledge incident** in incident management system
3. **Assess severity** based on impact and user count

### Step 2: Investigate

1. **Review Sentry event**:
   - Error message and stack trace
   - User context and tags
   - Breadcrumbs and timeline
   - Affected users count

2. **Check logs**:
   - Application logs: `logs/fastapi.log`
   - Electron logs: `logs/electron.log`
   - System logs: `logs/system.log`

3. **Reproduce issue**:
   - Test in staging environment
   - Verify with affected users
   - Check recent deployments

### Step 3: Mitigate

1. **Immediate actions**:
   - Rollback deployment if recent
   - Disable affected feature
   - Increase resource limits
   - Restart services

2. **Temporary fixes**:
   - Add error handling
   - Increase timeouts
   - Add circuit breakers
   - Enable fallback mechanisms

### Step 4: Resolve

1. **Root cause analysis**:
   - Identify underlying issue
   - Document findings
   - Create fix plan

2. **Implement fix**:
   - Code changes
   - Configuration updates
   - Database migrations
   - Infrastructure changes

3. **Verify resolution**:
   - Test in staging
   - Monitor production
   - Confirm with users

### Step 5: Post-Incident

1. **Document incident**:
   - Incident report
   - Root cause analysis
   - Timeline of events
   - Actions taken

2. **Follow-up actions**:
   - Prevent recurrence
   - Update monitoring
   - Improve alerting
   - Update runbooks

## Integration with Incident Management

### PagerDuty Integration

**Configuration**: Set `PAGERDUTY_INTEGRATION_KEY` environment variable

**Automatic Forwarding**:
- Critical crashes (P0) → Immediate escalation
- High severity errors (P1) → 15-minute response
- Medium severity (P2) → 1-hour response

### OpsGenie Integration

**Configuration**: Set `OPSGENIE_API_KEY` environment variable

**Automatic Forwarding**:
- Similar to PagerDuty
- Configurable escalation policies

### Custom Integration

The crash report triage service (`crash_report_triage.py`) can be extended to integrate with:
- Slack
- Microsoft Teams
- Email
- Custom webhooks

## Crash Report Endpoints

### Electron Crash Reports

**Endpoint**: `POST /api/crash-reports/electron`

**Payload**:
```json
{
  "process_type": "main",
  "version": "1.0.0",
  "platform": "win32",
  "crash_report": "{...}",
  "timestamp": "2025-01-15T10:30:00Z",
  "environment": "production"
}
```

### Sentry Webhook

**Endpoint**: `POST /api/crash-reports/sentry`

**Payload**: Sentry webhook event format

## Monitoring and Alerting

### Key Metrics

1. **Error Rate**: Errors per minute
2. **Crash Rate**: Crashes per hour
3. **Response Time**: API response times
4. **Availability**: Uptime percentage

### Alert Thresholds

- **Error Rate**: > 10 errors/minute for 5 minutes
- **Crash Rate**: > 1 crash/hour
- **Response Time**: P95 > 2 seconds
- **Availability**: < 99.9%

## Runbooks

### Common Incidents

#### Database Connection Failures

1. Check database health: `curl http://localhost:8000/healthz`
2. Verify connection pool settings
3. Check database logs
4. Restart database if needed
5. Restart application

#### Redis Connection Failures

1. Check Redis health
2. Verify Redis URL configuration
3. Check Redis logs
4. Restart Redis if needed
5. Application will fallback to in-memory cache

#### DEX Aggregator Outages

1. Check circuit breaker status: `/api/dex/aggregator-status`
2. Verify aggregator API status
3. Check fallback aggregators
4. Manually reset circuit breakers if needed

#### High Error Rate

1. Check Sentry dashboard for error patterns
2. Review recent deployments
3. Check for dependency issues
4. Rollback if recent deployment
5. Increase monitoring

## Communication

### Internal Communication

- **Slack**: #incidents channel
- **Email**: incidents@yourdomain.com
- **PagerDuty**: Automatic escalation

### External Communication

- **Status Page**: Update status page
- **User Notifications**: Email affected users
- **Public Updates**: Twitter, blog post (if major)

## Prevention

### Best Practices

1. **Comprehensive Testing**: Unit, integration, E2E tests
2. **Staging Deployment**: Always test in staging first
3. **Gradual Rollout**: Use feature flags for new features
4. **Monitoring**: Set up alerts before incidents occur
5. **Documentation**: Keep runbooks up to date

### Post-Incident Actions

1. **Root Cause Analysis**: Document what went wrong
2. **Prevention Measures**: Implement safeguards
3. **Process Improvements**: Update procedures
4. **Team Training**: Share learnings

## Related Documentation

- [Security Audit Checklist](SECURITY_AUDIT_CHECKLIST.md)
- [Disaster Recovery Guide](DISASTER_RECOVERY.md)
- [Production Setup Guide](PRODUCTION_SETUP.md)
- [Monitoring Setup](MONITORING_SETUP.md)
