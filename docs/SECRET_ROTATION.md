# Secret Rotation Guide

This document outlines the process for rotating secrets in the CryptoOrchestrator platform.

---

## Overview

Secret rotation is a critical security practice that limits the impact of compromised credentials. This guide covers rotation procedures for all secrets used in the platform.

---

## 🔑 Secrets Requiring Rotation

### 1. JWT Secret (`JWT_SECRET`)

**Rotation Frequency**: Every 90 days or immediately if compromised

**Impact**: All users will need to re-authenticate after rotation

**Procedure**:

1. **Generate New Secret**:
   ```bash
   # Generate a secure 32+ character secret
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Update Environment Variable**:
   ```bash
   # Update .env.prod file
   JWT_SECRET=<new-secret>
   ```

3. **Deploy Update**:
   ```bash
   # Restart application to load new secret
   docker-compose restart api
   ```

4. **Verify**:
   - Test login functionality
   - Verify existing tokens are invalidated
   - Check logs for authentication errors

**Rollback**: Revert to previous secret if issues occur

---

### 2. Exchange Key Encryption Key (`EXCHANGE_KEY_ENCRYPTION_KEY`)

**Rotation Frequency**: Every 180 days or immediately if compromised

**Impact**: All encrypted exchange API keys must be re-encrypted

**Procedure**:

1. **Generate New Key** (32 bytes):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Re-encrypt All Exchange Keys**:
   ```python
   # Run migration script
   python server_fastapi/scripts/rotate_encryption_key.py
   ```

3. **Update Environment Variable**:
   ```bash
   EXCHANGE_KEY_ENCRYPTION_KEY=<new-key>
   ```

4. **Deploy and Verify**:
   - Restart application
   - Test exchange API connections
   - Verify keys are accessible

**Rollback**: Use previous key if re-encryption fails

---

### 3. Database Credentials

**Rotation Frequency**: Every 90 days

**Impact**: Temporary service interruption during rotation

**Procedure**:

1. **Create New Database User**:
   ```sql
   CREATE USER crypto_user_new WITH PASSWORD 'new-secure-password';
   GRANT ALL PRIVILEGES ON DATABASE cryptoorchestrator TO crypto_user_new;
   ```

2. **Update Connection String**:
   ```bash
   DATABASE_URL=postgresql+asyncpg://crypto_user_new:new-secure-password@host:5432/cryptoorchestrator
   ```

3. **Deploy Update**:
   - Update environment variable
   - Restart application
   - Verify database connectivity

4. **Cleanup** (after verification):
   ```sql
   DROP USER crypto_user_old;
   ```

---

### 4. Redis Credentials

**Rotation Frequency**: Every 90 days

**Impact**: Temporary cache loss (acceptable)

**Procedure**:

1. **Update Redis Password**:
   ```bash
   # In Redis configuration
   requirepass <new-password>
   ```

2. **Update Environment Variable**:
   ```bash
   REDIS_URL=redis://:new-password@host:6379/0
   ```

3. **Restart Services**:
   - Restart Redis
   - Restart application
   - Verify cache functionality

---

### 5. Stripe API Keys

**Rotation Frequency**: Every 90 days or if compromised

**Impact**: Payment processing interruption

**Procedure**:

1. **Generate New Keys in Stripe Dashboard**:
   - Log into Stripe Dashboard
   - Navigate to API Keys
   - Generate new secret key

2. **Update Environment Variables**:
   ```bash
   STRIPE_SECRET_KEY=sk_live_<new-key>
   STRIPE_PUBLISHABLE_KEY=pk_live_<new-key>
   ```

3. **Update Webhook Secret** (if changed):
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_<new-secret>
   ```

4. **Deploy and Test**:
   - Restart application
   - Test payment processing
   - Verify webhook delivery

---

## 🔄 Automated Rotation

### Setup Automated Rotation

1. **Create Rotation Script**:
   ```python
   # server_fastapi/scripts/rotate_secrets.py
   import os
   import secrets
   from datetime import datetime, timedelta
   
   def rotate_jwt_secret():
       """Rotate JWT secret"""
       new_secret = secrets.token_urlsafe(32)
       # Update environment variable
       # Restart application
       pass
   ```

2. **Schedule Rotation**:
   ```bash
   # Add to crontab or scheduled task
   0 2 1 * * /path/to/rotate_secrets.py --jwt-secret
   ```

3. **Monitor Rotation**:
   - Set up alerts for rotation failures
   - Log all rotation events
   - Track rotation history

---

## 📋 Rotation Checklist

### Pre-Rotation
- [ ] Review rotation schedule
- [ ] Generate new secrets
- [ ] Backup current secrets (encrypted)
- [ ] Notify team of upcoming rotation
- [ ] Schedule maintenance window (if needed)

### During Rotation
- [ ] Update environment variables
- [ ] Run migration scripts (if needed)
- [ ] Restart services
- [ ] Verify functionality
- [ ] Monitor error logs

### Post-Rotation
- [ ] Verify all services operational
- [ ] Test critical functionality
- [ ] Update documentation
- [ ] Archive old secrets (encrypted)
- [ ] Update rotation schedule

---

## 🚨 Emergency Rotation

If a secret is compromised:

1. **Immediate Actions**:
   - Rotate secret immediately
   - Revoke all active sessions/tokens
   - Review audit logs for unauthorized access
   - Notify affected users

2. **Investigation**:
   - Determine scope of compromise
   - Identify how secret was exposed
   - Review security controls
   - Document incident

3. **Remediation**:
   - Rotate all related secrets
   - Enhance security controls
   - Update procedures if needed
   - Conduct security review

---

## 📚 Related Documentation

- **Environment Variables**: `docs/ENV_VARIABLES.md`
- **Security Audit**: `docs/SECURITY_AUDIT.md`
- **Deployment Guide**: `PRODUCTION_DEPLOYMENT_CHECKLIST.md`

---

## 🔐 Secret Storage Best Practices

1. **Never commit secrets to git**
2. **Use environment variables for all secrets**
3. **Encrypt secrets at rest**
4. **Rotate secrets regularly**
5. **Use different secrets per environment**
6. **Limit access to secrets**
7. **Monitor secret access**
8. **Document all rotations**

---

## ✅ Conclusion

Regular secret rotation is essential for maintaining platform security. Follow this guide to ensure secure and smooth secret rotations.

**Remember**: Always test rotations in a staging environment first!

