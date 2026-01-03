# Security Audit

Run comprehensive security audit for CryptoOrchestrator.

## Quick Security Audit

Run all security checks:
```bash
npm run audit:security
```

This runs:
- npm security audit
- Python package security check (safety)
- Security best practices verification

## Individual Security Checks

### npm Security Audit

```bash
npm audit
```

**Fix vulnerabilities**:
```bash
npm audit fix
```

**Fix with breaking changes**:
```bash
npm audit fix --force
```

### Python Security Check

```bash
# Using safety (if installed)
safety check

# Or check requirements
pip-audit -r requirements.txt
```

### Security Testing

```bash
# Run security tests
npm run test:security

# Comprehensive security tests
npm run test:security:comprehensive
```

## Security Checklist

### Code Security

- [ ] No hardcoded secrets or API keys
- [ ] No private keys in code or database
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (using ORM)
- [ ] XSS prevention (sanitizing user input)
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Authentication required for sensitive endpoints

### Dependencies

- [ ] All dependencies up to date
- [ ] No known vulnerabilities
- [ ] Security patches applied
- [ ] Unused dependencies removed

### Configuration

- [ ] Environment variables for all secrets
- [ ] Strong JWT secrets (64+ characters)
- [ ] HTTPS enforced in production
- [ ] CORS properly configured
- [ ] Security headers set
- [ ] Database not publicly accessible

### Infrastructure

- [ ] Firewall rules configured
- [ ] Database access restricted
- [ ] API keys rotated regularly
- [ ] Logging doesn't expose sensitive data
- [ ] Backups encrypted
- [ ] Access controls in place

## Security Best Practices

### Private Key Management

**✅ Good**:
- Use AWS KMS, HashiCorp Vault, or HSM
- Store only key IDs in database
- Retrieve keys at runtime
- Clear keys from memory after use

**❌ Bad**:
- Storing private keys in code
- Storing private keys in database
- Logging private keys
- Committing keys to git

### Input Validation

**✅ Good**:
```python
# Backend: Use Pydantic
class TradeRequest(BaseModel):
    amount: float = Field(..., gt=0)
    token_address: str = Field(..., regex=r'^0x[a-fA-F0-9]{40}$')
```

```typescript
// Frontend: Use Zod
const tradeSchema = z.object({
  amount: z.number().positive(),
  tokenAddress: z.string().regex(/^0x[a-fA-F0-9]{40}$/),
});
```

**❌ Bad**:
- Trusting user input
- No validation
- Weak validation

### Authentication

- ✅ JWT tokens validated on every request
- ✅ 2FA required for sensitive operations
- ✅ Session management secure
- ✅ Password hashing (bcrypt)
- ✅ Account lockout after failed attempts

## Security Audit Report

After running audit, review:

1. **Vulnerability List**: All found vulnerabilities
2. **Severity Levels**: Critical, High, Medium, Low
3. **Affected Packages**: Which packages have issues
4. **Fix Recommendations**: How to fix each issue
5. **Update Path**: How to update vulnerable packages

## Fixing Security Issues

### npm Vulnerabilities

```bash
# Fix automatically (safe)
npm audit fix

# Review and fix manually
npm audit
# Then update specific packages
npm update <package-name>
```

### Python Vulnerabilities

```bash
# Update vulnerable packages
pip install --upgrade <package-name>

# Or update requirements.txt and reinstall
pip install -r requirements.txt --upgrade
```

### Code Security Issues

1. **Review**: Identify security issues
2. **Fix**: Apply security fixes
3. **Test**: Verify fixes don't break functionality
4. **Document**: Document security improvements

## Regular Security Audits

### Schedule

- **Weekly**: Quick dependency check
- **Monthly**: Full security audit
- **Before Release**: Comprehensive audit
- **After Incidents**: Immediate audit

### Automation

```bash
# Add to CI/CD pipeline
npm run audit:security
```

## Security Resources

- **[Security Rules](../../.cursor/rules/security-blockchain.mdc)** - Project security rules
- **[Security Documentation](../../docs/security/)** - Security guides
- **[Security Testing](../../scripts/security/)** - Security test scripts

## Summary

✅ **Quick Audit**: `npm run audit:security`  
✅ **npm Audit**: `npm audit`  
✅ **Python Audit**: `safety check` or `pip-audit`  
✅ **Security Tests**: `npm run test:security`  
✅ **Fix Issues**: Follow recommendations

**Remember**: Security is critical - address vulnerabilities immediately!
