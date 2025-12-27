# Security Best Practices Guide

## Overview
This document outlines security best practices for the CryptoOrchestrator platform, focusing on real-money trading operations and user data protection.

## Authentication & Authorization

### JWT Tokens
- **Storage**: Tokens stored in localStorage (frontend) with automatic cleanup on 401
- **Validation**: All protected routes validate JWT tokens
- **Expiration**: Tokens expire after configured time (default: 24 hours)
- **Refresh**: Implement token refresh mechanism for long sessions

### 2FA (Two-Factor Authentication)
- **Required For**: Withdrawals, real money trades, account settings changes
- **Implementation**: TOTP-based (Google Authenticator, Authy)
- **Backup Codes**: Generate and securely store recovery codes
- **Enforcement**: Backend validates 2FA tokens before sensitive operations

### Session Management
- **Timeout**: Automatic session timeout after inactivity
- **Concurrent Sessions**: Monitor and limit concurrent sessions per user
- **Device Tracking**: Track devices for suspicious activity detection

## Input Validation

### Backend Validation
- **Pydantic Models**: All API inputs validated with Pydantic v2
- **Type Checking**: Strict type validation
- **Sanitization**: User inputs sanitized before logging
- **SQL Injection**: Prevented via SQLAlchemy ORM (parameterized queries)

### Frontend Validation
- **Zod Schemas**: Form validation with Zod
- **Real-time Validation**: Immediate feedback on input errors
- **Address Validation**: Ethereum address format validation
- **Amount Validation**: Positive numbers, minimums, maximums

## Rate Limiting

### Configuration
- **Per-Endpoint Limits**: Different limits for different endpoints
  - `/api/wallets/withdraw`: 10 requests/hour
  - `/api/dex/swap`: 20 requests/hour
  - `/api/wallets/refresh-balances`: 60 requests/hour
- **Tier-Based Scaling**: Limits scale with user subscription tier
- **Admin Bypass**: Admins bypass rate limits (still logged)

### Implementation
- **Storage**: Redis-based (with in-memory fallback)
- **Headers**: Rate limit info in all responses
- **Monitoring**: Rate limit violations logged and monitored

## IP Whitelisting

### When to Use
- **Withdrawals**: Highly recommended for real money withdrawals
- **Real Money Trades**: Recommended for custodial swaps
- **Account Changes**: Optional for sensitive account operations

### Management
- **UI**: Manage via Settings page (`/settings` → Security tab)
- **API**: Use `/api/security/whitelists/ip` endpoints
- **Validation**: IP addresses validated before storage
- **Notifications**: Users notified of whitelist violations

## Audit Logging

### What Gets Logged
- **Wallet Operations**: Create, deposit, withdraw, balance refresh, external wallet registration
- **DEX Trades**: Quotes, swaps, status updates
- **Security Events**: Rate limit violations, 2FA failures, IP whitelist violations
- **User Actions**: Login, logout, mode switches, settings changes

### Log Storage
- **Format**: JSON logs in `logs/audit/audit.log`
- **Retention**: 90 days default (configurable)
- **Export**: JSON or CSV export available
- **Search**: Filter by user, event type, date range

### Access Control
- **Users**: Can view their own audit logs
- **Admins**: Can view all audit logs
- **Export**: Requires authentication

## Error Handling

### Error Message Sanitization
- **Production**: Sensitive data removed (API keys, tokens, passwords, IPs, emails)
- **Development**: Full error details for debugging
- **Classification**: Errors classified as user_error, system_error, or security_error

### Error Rate Monitoring
- **Tracking**: Error rates tracked per endpoint
- **Alerting**: Alerts when error rate exceeds threshold (10 errors/minute)
- **Logging**: All errors logged with context (user_id, path, method)

## Transaction Security

### Transaction Monitoring
- **Tracking**: All transactions tracked (deposits, withdrawals, swaps)
- **Success Rates**: Monitor transaction success rates
- **Latency**: Track transaction confirmation times
- **Suspicious Patterns**: Detect unusual activity (high frequency, large amounts, high failure rate)

### Withdrawal Security
- **2FA Required**: All withdrawals require 2FA token
- **IP Whitelisting**: Recommended for withdrawals
- **Address Validation**: Ethereum address format validation
- **Amount Limits**: Minimum and maximum withdrawal amounts
- **Cooldown Periods**: Optional cooldown for new withdrawal addresses

## Wallet Security

### Custodial Wallets
- **Key Management**: Private keys encrypted at rest (implementation required)
- **Key Rotation**: Regular key rotation recommended
- **Multi-Signature**: Consider multi-sig for high-value wallets
- **Backup**: Secure backup of wallet keys

### Non-Custodial Wallets
- **User Control**: Users maintain full control of private keys
- **Validation**: Wallet addresses validated before registration
- **Verification**: Optional wallet verification process

## DEX Trading Security

### Quote Validation
- **Price Checks**: Validate quotes are within reasonable range
- **Slippage Protection**: Enforce maximum slippage tolerance
- **Liquidity Checks**: Verify sufficient liquidity before swaps

### Swap Execution
- **Transaction Validation**: Validate transaction hashes
- **Status Monitoring**: Track swap status until confirmation
- **Error Handling**: Handle failed swaps gracefully
- **Fee Verification**: Verify fees are calculated correctly

## API Security

### CORS Configuration
- **Origins**: Whitelist specific origins (no wildcards in production)
- **Credentials**: Allow credentials for authenticated requests
- **Headers**: Allow necessary headers (Authorization, Content-Type)

### Security Headers
- **CSP**: Content Security Policy headers
- **XSS Protection**: X-XSS-Protection header
- **Frame Options**: X-Frame-Options header
- **Content Type**: Prevent MIME sniffing

### Request Validation
- **Size Limits**: Limit request body sizes
- **Content Type**: Validate Content-Type headers
- **Parameter Validation**: Validate all query parameters

## Data Protection

### Secrets Management
- **Environment Variables**: Store secrets in `.env.prod` (never commit)
- **Encryption**: Encrypt sensitive data at rest (API keys, private keys)
- **Rotation**: Regularly rotate API keys and tokens
- **Access Control**: Limit access to secrets

### Logging
- **Never Log Secrets**: API keys, passwords, tokens, private keys
- **Sanitization**: Use LogSanitizer middleware
- **Context**: Include user_id, path, method in logs (not sensitive data)

### Database Security
- **Connection Encryption**: Use TLS for database connections
- **Access Control**: Limit database access to application servers
- **Backups**: Encrypt database backups
- **PII**: Encrypt personally identifiable information

## Monitoring & Alerting

### Security Monitoring
- **Audit Logs**: Monitor for suspicious patterns
- **Error Rates**: Alert on high error rates
- **Rate Limit Violations**: Alert on repeated violations
- **Failed Logins**: Alert on brute force attempts

### Transaction Monitoring
- **Success Rates**: Monitor transaction success rates
- **Latency**: Alert on high transaction latency
- **Suspicious Patterns**: Detect unusual transaction patterns
- **Volume**: Monitor transaction volumes

### System Monitoring
- **Health Checks**: Monitor system health
- **Resource Usage**: Alert on high CPU/memory usage
- **Dependency Health**: Monitor blockchain RPC and DEX aggregator health

## Incident Response

### Security Incidents
1. **Identify**: Detect security incident (audit logs, monitoring)
2. **Contain**: Isolate affected systems/users
3. **Investigate**: Review audit logs, transaction history
4. **Remediate**: Fix vulnerabilities, revoke access
5. **Notify**: Notify affected users (if required)
6. **Document**: Document incident and response

### Data Breach Response
1. **Assess**: Determine scope of breach
2. **Contain**: Stop breach, secure systems
3. **Notify**: Notify users and authorities (if required)
4. **Remediate**: Fix vulnerabilities, enhance security
5. **Review**: Post-incident review and improvements

## Compliance

### Regulatory Requirements
- **KYC/AML**: Implement if required by jurisdiction
- **Data Protection**: GDPR compliance (if applicable)
- **Financial Regulations**: Comply with local financial regulations
- **Reporting**: Maintain audit logs for compliance

### Best Practices
- **Privacy Policy**: Clear privacy policy
- **Terms of Service**: Comprehensive terms of service
- **Data Retention**: Define data retention policies
- **User Rights**: Respect user data rights (access, deletion)

## Development Security

### Code Security
- **Dependencies**: Regularly update dependencies
- **Vulnerability Scanning**: Scan for known vulnerabilities
- **Code Review**: Security-focused code reviews
- **Static Analysis**: Use static analysis tools

### Testing
- **Security Tests**: Test security features
- **Penetration Testing**: Regular penetration testing
- **Load Testing**: Test security under load
- **Fuzz Testing**: Test with invalid inputs

## Deployment Security

### Production Checklist
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] IP whitelisting configured (if needed)
- [ ] Audit logging enabled
- [ ] Error sanitization enabled
- [ ] Secrets properly configured
- [ ] Database encryption enabled
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery tested

### Environment Variables
- [ ] All secrets in environment variables
- [ ] No secrets in code or config files
- [ ] Environment variables validated on startup
- [ ] Production secrets different from development

## Regular Security Tasks

### Weekly
- Review audit logs for suspicious activity
- Check error rates and patterns
- Review rate limit violations
- Monitor transaction success rates

### Monthly
- Review and update dependencies
- Security vulnerability scanning
- Review and update security policies
- Test backup and recovery procedures

### Quarterly
- Security audit
- Penetration testing
- Review and update security documentation
- Security training for team

## Resources

- [Security Audit Checklist](SECURITY_AUDIT_CHECKLIST.md)
- [API Documentation](api.md)
- [Architecture Guide](architecture.md)
- [Test Coverage Report](TEST_COVERAGE_REPORT.md)

## Support

For security concerns or incidents:
- **Email**: security@cryptoorchestrator.com
- **Emergency**: Follow incident response procedures
- **Reporting**: Report vulnerabilities responsibly
