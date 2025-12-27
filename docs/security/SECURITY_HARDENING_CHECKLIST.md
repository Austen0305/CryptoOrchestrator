# Security Hardening Checklist

This checklist provides a comprehensive guide for hardening the CryptoOrchestrator platform for production deployment. Use this checklist before deploying to production and for regular security audits.

## 📋 Pre-Deployment Security Checklist

### ✅ TLS/HTTPS Configuration

#### TLS Termination
- [ ] **TLS 1.3 enabled** (minimum TLS 1.2)
  - Verify: `ssl_protocols TLSv1.2 TLSv1.3;` in nginx config
  - Location: `docs/DEPLOYMENT_GUIDE.md` (nginx configuration)
  - Status: ✅ Configured

- [ ] **Strong cipher suites only**
  - Verify: Modern cipher suites (ECDHE, AES-GCM)
  - Current: `ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384`
  - Recommendation: Use nginx's `ssl_ciphers HIGH:!aNULL:!MD5;` for automatic strong ciphers
  - Status: ⚠️ Review recommended

- [ ] **Perfect Forward Secrecy (PFS)**
  - Verify: ECDHE cipher suites enabled
  - Status: ✅ Enabled (ECDHE ciphers in use)

- [ ] **Certificate validation**
  - Verify: Valid SSL certificate from trusted CA (Let's Encrypt recommended)
  - Verify: Certificate not expired
  - Verify: Certificate includes all domains/subdomains
  - Auto-renewal: Configured with Certbot
  - Status: ⚠️ Verify in production

- [ ] **HTTP to HTTPS redirect**
  - Verify: All HTTP traffic redirects to HTTPS
  - Current: `return 301 https://$server_name$request_uri;`
  - Status: ✅ Configured

- [ ] **HSTS (HTTP Strict Transport Security)**
  - Verify: `Strict-Transport-Security` header set
  - Current: `max-age=31536000; includeSubDomains; preload`
  - Status: ✅ Configured
  - Note: Only enable `preload` after thorough testing

#### Certificate Management
- [ ] **Certificate auto-renewal configured**
  - Verify: Certbot cron job or systemd timer active
  - Command: `certbot renew --dry-run`
  - Status: ⚠️ Verify in production

- [ ] **Certificate monitoring**
  - Verify: Alerts configured for certificate expiration (30 days before)
  - Status: ⚠️ Configure monitoring

- [ ] **OCSP stapling enabled**
  - Verify: `ssl_stapling on;` in nginx config
  - Status: ⚠️ Add to nginx config

### ✅ Content Security Policy (CSP)

#### Current CSP Status
- **Location**: `server_fastapi/middleware/enhanced_security_headers.py`
- **Production CSP**: Includes `'unsafe-inline'` and `'unsafe-eval'` ⚠️

#### CSP Hardening Tasks
- [ ] **Remove `'unsafe-inline'` from script-src**
  - Current: `script-src 'self' 'unsafe-inline' 'unsafe-eval'`
  - Action: Use nonces or hashes for inline scripts
  - Priority: **HIGH** (XSS protection)
  - Status: ⚠️ Needs hardening

- [ ] **Remove `'unsafe-eval'` from script-src**
  - Current: Allows `eval()` and similar functions
  - Action: Remove eval usage, use strict mode
  - Priority: **HIGH** (XSS protection)
  - Status: ⚠️ Needs hardening

- [ ] **Tighten style-src**
  - Current: `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`
  - Action: Use nonces for inline styles or move to external stylesheets
  - Priority: **MEDIUM**
  - Status: ⚠️ Review

- [ ] **Review connect-src for production**
  - Current: Includes `ws://localhost:8000` (development only)
  - Action: Remove localhost URLs in production, use `wss://` only
  - Priority: **MEDIUM**
  - Status: ⚠️ Review

- [ ] **Add CSP reporting**
  - Action: Add `report-uri` or `report-to` directive
  - Example: `report-uri /api/csp-report;`
  - Priority: **MEDIUM**
  - Status: ⚠️ Not configured

#### Recommended Production CSP
```python
csp_directives = [
    "default-src 'self'",
    "script-src 'self' https://api.sentry.io",  # Remove unsafe-inline/eval
    "style-src 'self' https://fonts.googleapis.com",  # Remove unsafe-inline if possible
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https: blob:",
    "connect-src 'self' wss://yourdomain.com https://api.sentry.io",
    "frame-src 'none'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "upgrade-insecure-requests",
    "report-uri /api/csp-report",  # Add CSP reporting
]
```

### ✅ Dependency Scanning

#### Automated Scanning (Already Configured ✅)
- [ ] **Python dependency scanning**
  - Tools: Safety, pip-audit, Snyk
  - Location: `.github/workflows/security-scan.yml`
  - Frequency: Weekly + on PR
  - Status: ✅ Configured

- [ ] **Node.js dependency scanning**
  - Tools: npm audit, Snyk
  - Location: `.github/workflows/security-scan.yml`
  - Frequency: Weekly + on PR
  - Status: ✅ Configured

- [ ] **Code security scanning**
  - Tools: Bandit (Python), Semgrep, ESLint security plugin
  - Location: `.github/workflows/security-scan.yml`
  - Frequency: Weekly + on PR
  - Status: ✅ Configured

- [ ] **Container scanning**
  - Tools: Trivy, Docker Scout
  - Location: `.github/workflows/security-scan.yml`
  - Frequency: On container builds
  - Status: ✅ Configured

- [ ] **Secrets scanning**
  - Tools: Gitleaks, TruffleHog
  - Location: `.github/workflows/security-scan.yml`
  - Frequency: On every commit
  - Status: ✅ Configured

#### Manual Verification Tasks
- [ ] **Review security scan reports**
  - Action: Check GitHub Actions artifacts after each scan
  - Priority: **HIGH**
  - Frequency: Weekly

- [ ] **Fix high/critical vulnerabilities immediately**
  - Action: Create issues for all high/critical findings
  - SLA: Critical within 24 hours, High within 7 days
  - Status: ⚠️ Establish process

- [ ] **Update dependencies regularly**
  - Action: Review Dependabot PRs weekly
  - Priority: **MEDIUM**
  - Status: ✅ Dependabot configured

- [ ] **Verify no known CVEs in production**
  - Command: `safety check` and `npm audit`
  - Frequency: Before each deployment
  - Status: ⚠️ Add to deployment checklist

### ✅ Application Security

#### Authentication & Authorization
- [ ] **JWT secret rotated and strong**
  - Verify: `JWT_SECRET` is 64+ bytes, cryptographically random
  - Action: Use `scripts/rotate_secrets.py` to generate
  - Status: ✅ Script available

- [ ] **Password requirements enforced**
  - Verify: Minimum 12 characters, complexity requirements
  - Location: `server_fastapi/routes/auth.py`
  - Status: ✅ Implemented

- [ ] **2FA enabled for sensitive operations**
  - Verify: 2FA required for withdrawals, high-value trades
  - Status: ✅ Implemented

- [ ] **Session management secure**
  - Verify: Sessions expire appropriately
  - Verify: Secure cookie flags (HttpOnly, Secure, SameSite)
  - Status: ⚠️ Review cookie configuration

#### Input Validation
- [ ] **All inputs validated with Pydantic**
  - Verify: No raw input processing
  - Status: ✅ Implemented

- [ ] **SQL injection prevention**
  - Verify: All queries use ORM (SQLAlchemy) or parameterized queries
  - Status: ✅ Using SQLAlchemy ORM

- [ ] **XSS prevention**
  - Verify: User input sanitized before rendering
  - Verify: CSP headers configured
  - Status: ⚠️ CSP needs hardening (see above)

#### Secrets Management
- [ ] **No secrets in code**
  - Verify: All secrets in environment variables
  - Verify: `.env` files in `.gitignore`
  - Action: Run `gitleaks` and `trufflehog` scans
  - Status: ✅ Scanners configured

- [ ] **Secrets encrypted at rest**
  - Verify: API keys, private keys encrypted (AES-256)
  - Status: ✅ Implemented

- [ ] **Secret rotation policy**
  - Verify: Secrets rotated every 90 days
  - Action: Use `scripts/rotate_secrets.py`
  - Status: ✅ Script available

### ✅ Infrastructure Security

#### Network Security
- [ ] **Firewall configured**
  - Verify: Only necessary ports open (80, 443, 22)
  - Verify: Database and Redis not exposed publicly
  - Status: ⚠️ Verify in production

- [ ] **Rate limiting enabled**
  - Verify: Rate limiting active on all endpoints
  - Location: `server_fastapi/rate_limit_config.py`
  - Status: ✅ Implemented

- [ ] **DDoS protection**
  - Verify: CDN/proxy with DDoS protection (Cloudflare, AWS Shield)
  - Status: ⚠️ Configure if not using managed service

#### Database Security
- [ ] **Database encryption in transit**
  - Verify: PostgreSQL connections use SSL
  - Connection string: `postgresql+asyncpg://...?ssl=require`
  - Status: ⚠️ Verify connection string

- [ ] **Database encryption at rest**
  - Verify: Database files encrypted (LUKS, EBS encryption)
  - Status: ⚠️ Verify with infrastructure provider

- [ ] **Database access controls**
  - Verify: Least privilege principle (separate users for app/read-only)
  - Verify: No public access
  - Status: ⚠️ Review database users

- [ ] **Database backups encrypted**
  - Verify: Backup encryption enabled
  - Status: ✅ Configured (see `scripts/backup_database.py`)

#### Redis Security
- [ ] **Redis authentication enabled**
  - Verify: `requirepass` set in Redis config
  - Verify: `REDIS_URL` includes password
  - Status: ⚠️ Verify in production

- [ ] **Redis not exposed publicly**
  - Verify: Redis only accessible from application servers
  - Status: ⚠️ Verify network configuration

### ✅ Monitoring & Logging

#### Security Monitoring
- [ ] **Failed login attempt monitoring**
  - Verify: Alerts configured for multiple failed logins
  - Status: ⚠️ Configure alerts

- [ ] **Unusual activity detection**
  - Verify: Anomaly detection for trading patterns
  - Status: ✅ Implemented (fraud detection)

- [ ] **Security event logging**
  - Verify: All security events logged (auth failures, permission denials)
  - Status: ✅ Implemented

#### Log Management
- [ ] **Sensitive data not logged**
  - Verify: No passwords, API keys, private keys in logs
  - Location: `server_fastapi/middleware/log_sanitizer.py` (if exists)
  - Status: ⚠️ Verify log sanitization

- [ ] **Log retention policy**
  - Verify: Logs retained for compliance period (typically 90 days)
  - Status: ⚠️ Configure retention

- [ ] **Log access controls**
  - Verify: Logs only accessible to authorized personnel
  - Status: ⚠️ Review access

### ✅ Compliance & Auditing

#### Audit Logging
- [ ] **Comprehensive audit trail**
  - Verify: All critical operations logged (trades, withdrawals, config changes)
  - Status: ✅ Implemented (audit logger)

- [ ] **Audit log integrity**
  - Verify: Audit logs are append-only and tamper-proof
  - Status: ⚠️ Verify implementation

- [ ] **Audit log retention**
  - Verify: Audit logs retained per compliance requirements
  - Status: ⚠️ Configure retention

#### Compliance
- [ ] **GDPR compliance** (if applicable)
  - Verify: Data deletion, right to access implemented
  - Status: ⚠️ Review requirements

- [ ] **PCI-DSS compliance** (if processing payments)
  - Verify: Payment data handling compliant
  - Status: ⚠️ Review if using Stripe

- [ ] **SOC 2 compliance** (if applicable)
  - Verify: Security controls documented and tested
  - Status: ⚠️ Review requirements

## 🔍 Penetration Testing Schedule

### External Penetration Testing

#### Initial Penetration Test
- [ ] **Schedule initial penetration test**
  - **Timing**: Before production launch (recommended: 2-4 weeks before)
  - **Scope**: 
    - Application security (OWASP Top 10)
    - API security (authentication, authorization, input validation)
    - Infrastructure security (network, servers, databases)
    - Blockchain/DEX integration security (smart contract interactions, wallet security)
    - Social engineering (if applicable)
  - **Frequency**: Annually or after major architectural changes
  - **Recommended Providers**:
    - Independent security firms (e.g., Cure53, NCC Group)
    - Specialized crypto/DeFi security auditors (e.g., Trail of Bits, OpenZeppelin, Consensys Diligence)
    - Blockchain security specialists (e.g., Quantstamp, CertiK)
  - **Budget**: $5,000 - $50,000+ depending on scope
  - **Status**: ⚠️ **Schedule with security firm**
  - **Action Items**:
    1. Identify 2-3 potential security firms (prioritize crypto/DeFi specialists)
    2. Request quotes and scope proposals (include blockchain/DEX security)
    3. Schedule test 2-4 weeks before launch
    4. Allocate budget for remediation
    5. Document findings and remediation plan
    6. Schedule follow-up verification test after fixes

#### Vulnerability Assessment
- [ ] **Schedule quarterly vulnerability assessments**
  - **Timing**: Quarterly (every 3 months)
  - **Scope**: 
    - Automated scanning (OWASP ZAP, Burp Suite, Nessus)
    - Manual code review of new features
    - Configuration review
  - **Tools**: 
    - OWASP ZAP (free, automated)
    - Burp Suite Professional (commercial, comprehensive)
    - Nessus (infrastructure scanning)
  - **Status**: ⚠️ **Schedule first assessment**
  - **Action Items**:
    1. Set up automated scanning in CI/CD
    2. Schedule quarterly manual reviews
    3. Document findings and remediation

#### Bug Bounty Program (Optional)
- [ ] **Consider bug bounty program**
  - **Timing**: After initial security audit and production launch
  - **Platform Options**:
    - HackerOne (most popular, managed platform)
    - Bugcrowd (alternative managed platform)
    - Self-hosted (more control, more work)
  - **Scope**: 
    - Web application
    - API endpoints
    - Smart contracts (if applicable)
  - **Rewards**: $100 - $10,000+ depending on severity
  - **Status**: ⚠️ **Consider for production** (after initial audit)
  - **Action Items**:
    1. Research bug bounty platforms
    2. Define scope and rules
    3. Set reward structure
    4. Launch after initial audit complete

### Internal Security Testing
- [ ] **Regular security reviews**
  - Timing: Monthly
  - Scope: Code review, dependency updates, configuration review
  - Status: ⚠️ Establish process

- [ ] **Red team exercises**
  - Timing: Annually
  - Scope: Simulated attacks, incident response testing
  - Status: ⚠️ Schedule

## 📝 Security Configuration Review

### Nginx Security Configuration
Review and verify the following in nginx configuration:

```nginx
# ✅ TLS Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;  # ⚠️ Add this
ssl_stapling_verify on;  # ⚠️ Add this

# ✅ Security Headers (verify these are set)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# ⚠️ CSP should be set by application, not nginx
# But verify it's being set correctly
```

### FastAPI Security Configuration
Review `server_fastapi/middleware/enhanced_security_headers.py`:

- [ ] **Production CSP tightened** (remove unsafe-inline/eval)
- [ ] **Security headers verified**
- [ ] **CORS properly configured** (not wildcard in production)
- [ ] **Rate limiting active**

### Environment Variables Security
Review `.env` file (never commit to git):

- [ ] **All secrets are strong and unique**
- [ ] **No default/example values in production**
- [ ] **Secrets rotated regularly**
- [ ] **Environment-specific secrets** (dev/staging/prod separate)

## 🚨 Critical Security Issues to Address

### High Priority
1. **CSP Hardening** - Remove `'unsafe-inline'` and `'unsafe-eval'`
2. **Certificate Monitoring** - Set up expiration alerts
3. **Log Sanitization** - Ensure no secrets in logs
4. **Database SSL** - Verify all connections use SSL

### Medium Priority
1. **OCSP Stapling** - Add to nginx config
2. **CSP Reporting** - Add report-uri directive
3. **Session Cookie Security** - Verify HttpOnly, Secure, SameSite flags
4. **Redis Authentication** - Verify password protection

### Low Priority
1. **Security Headers Review** - Verify all headers are optimal
2. **CORS Configuration** - Review allowed origins
3. **Rate Limiting Tuning** - Adjust based on usage patterns

## 📅 Security Maintenance Schedule

### Daily
- [ ] Monitor security alerts and logs
- [ ] Review failed authentication attempts
- [ ] Check for unusual activity

### Weekly
- [ ] Review security scan reports (GitHub Actions)
- [ ] Update dependencies (review Dependabot PRs)
- [ ] Review access logs

### Monthly
- [ ] Security configuration review
- [ ] Dependency vulnerability assessment
- [ ] Access control review (user permissions)

### Quarterly
- [ ] Full security audit
- [ ] Penetration testing (if scheduled)
- [ ] Security training for team
- [ ] Incident response drill

### Annually
- [ ] External penetration test
- [ ] Security policy review
- [ ] Compliance audit (if applicable)
- [ ] Disaster recovery test

## 🔗 Related Documentation

- [Secret Rotation Guide](docs/SECRET_ROTATION_GUIDE.md)
- [Security Documentation](docs/SECURITY_DOCUMENTATION.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Redis Configuration](docs/REDIS_CONFIGURATION.md)
- [Security Scanning Workflow](.github/workflows/security-scan.yml)

## 📞 Security Contacts

- **Security Team**: [Add contact information]
- **Incident Response**: [Add contact information]
- **External Security Firm**: [Add if applicable]

## 📋 Quick Reference: Security Scanning Tools

### Automated Scanning (CI/CD)

All security scanning is automated in `.github/workflows/security-scan.yml`:

- **Python Dependencies**: Safety, pip-audit, Snyk
- **Node.js Dependencies**: npm audit, Snyk
- **Code Security**: Bandit (Python), Semgrep, ESLint security plugin
- **Container Security**: Trivy, Docker Scout
- **Secrets Scanning**: Gitleaks, TruffleHog

### Manual Scanning Commands

```bash
# Python dependency vulnerabilities
safety check
pip-audit

# Node.js dependency vulnerabilities
npm audit

# Code security (Python)
bandit -r server_fastapi/

# Secrets scanning
gitleaks detect --source . --verbose
trufflehog filesystem .

# Container scanning
trivy image cryptoorchestrator:latest
```

## ✅ Checklist Completion

**Last Updated**: 2025-01-XX
**Completed By**: [Name]
**Next Review Date**: [Date + 90 days]

---

**Note**: This checklist should be reviewed and updated regularly. Mark items as complete only after verification, not just implementation.

**Next Steps**:
1. Review all ⚠️ items and prioritize based on risk
2. Schedule initial penetration test 2-4 weeks before production launch
3. Set up automated security monitoring and alerts
4. Establish security incident response procedures
5. Document security contacts and escalation paths
