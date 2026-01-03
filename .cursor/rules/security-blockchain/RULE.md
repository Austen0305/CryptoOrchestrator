---
description: Security and blockchain-specific development rules for CryptoOrchestrator
globs: ["server_fastapi/services/blockchain/**/*", "server_fastapi/routes/**/*", "client/src/services/**/*"]
alwaysApply: true
---

# Security & Blockchain Development Rules

## Critical Security Rules

### Private Key Management

**⚠️ NEVER:**
- Store private keys in code, database, or environment variables
- Log private keys or seed phrases
- Commit private keys to version control
- Hardcode wallet addresses or keys

**✅ ALWAYS:**
- Use AWS KMS, HashiCorp Vault, or hardware security modules (HSM)
- Store only key IDs or references in the database
- Retrieve keys at runtime, never cache
- Use encryption at rest and in transit

```python
# ✅ Good: Use key management service
from server_fastapi.services.blockchain.key_management import KeyManager

async def execute_trade(wallet_id: int):
    # Retrieve key reference only
    wallet = await get_wallet(wallet_id)
    private_key = await key_manager.get_private_key(wallet.key_reference)
    # Use key, never store in memory longer than needed
    # Clear from memory after use

# ❌ Bad: Hardcoded or stored key
PRIVATE_KEY = "0x..."  # NEVER DO THIS
```

### Sensitive Data Logging

**⚠️ NEVER LOG:**
- Private keys or seed phrases
- API keys or secrets
- Passwords or authentication tokens
- Full credit card numbers (only last 4 digits if needed)
- Personal identification information (PII)

**✅ GOOD LOGGING:**
```python
# ✅ Good: Log references only
logger.info("API key accessed", extra={"key_id": key_id, "user_id": user_id})

# ✅ Good: Mask sensitive data
logger.info("Transaction processed", extra={
    "wallet_address": mask_address(address),  # Shows only first/last chars
    "amount": amount,
})

# ❌ Bad: Logging sensitive data
logger.info(f"API key: {api_key}")  # NEVER DO THIS
logger.debug(f"Private key used: {private_key}")  # NEVER DO THIS
```

## Authentication & Authorization

### JWT Token Handling
```python
# ✅ Good: Validate tokens on every request
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(
    token: str = Depends(security),
) -> dict:
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user_id, **payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Two-Factor Authentication
```python
# ✅ Good: Require 2FA for sensitive operations
async def withdraw_funds(
    current_user: dict = Depends(get_current_user),
    two_fa_code: str = None,
):
    if not verify_2fa(current_user["id"], two_fa_code):
        raise HTTPException(
            status_code=403,
            detail="2FA verification required for withdrawals",
        )
    # Process withdrawal
```

## Input Validation

### Backend Validation
```python
from pydantic import BaseModel, validator, Field
from typing import Optional

class TradeRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Trade amount must be positive")
    token_address: str = Field(..., min_length=42, max_length=42)
    
    @validator('token_address')
    def validate_ethereum_address(cls, v):
        if not v.startswith('0x'):
            raise ValueError('Invalid Ethereum address format')
        if len(v) != 42:
            raise ValueError('Ethereum address must be 42 characters')
        return v.lower()  # Normalize to lowercase
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > MAX_TRADE_AMOUNT:
            raise ValueError(f'Amount exceeds maximum of {MAX_TRADE_AMOUNT}')
        return v
```

### Frontend Validation
```typescript
import { z } from 'zod';

const tradeSchema = z.object({
  amount: z.number().positive('Amount must be positive'),
  tokenAddress: z.string()
    .regex(/^0x[a-fA-F0-9]{40}$/, 'Invalid Ethereum address')
    .transform((addr) => addr.toLowerCase()), // Normalize
});

// Validate before sending to API
const result = tradeSchema.safeParse(formData);
if (!result.success) {
  // Handle validation errors
}
```

## Rate Limiting

### Implementation
```python
from fastapi import Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# ✅ Good: Apply rate limits to sensitive endpoints
@router.post("/api/wallets/withdraw")
@limiter.limit("10/hour")
async def withdraw(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    # Process withdrawal with rate limiting
    pass
```

### Redis-Based Rate Limiting
```python
# ✅ Good: Check Redis availability
from server_fastapi.services.cache import cache_service

if await cache_service.is_available():
    # Use Redis for rate limiting
    await check_rate_limit(user_id, endpoint)
else:
    # Fallback to in-memory rate limiting
    logger.warning("Redis unavailable, using in-memory rate limiting")
```

## Blockchain Security

### Ethereum Address Validation
```python
from eth_utils import is_address, to_checksum_address

# ✅ Good: Validate and checksum addresses
def validate_ethereum_address(address: str) -> str:
    if not is_address(address):
        raise ValueError("Invalid Ethereum address")
    return to_checksum_address(address)  # EIP-55 checksum
```

### Transaction Verification
```python
from web3 import Web3

# ✅ Good: Verify transaction before processing
async def verify_transaction(tx_hash: str, expected_amount: float) -> bool:
    try:
        tx = w3.eth.get_transaction_receipt(tx_hash)
        if tx.status != 1:  # 1 = success
            logger.warning(f"Transaction {tx_hash} failed")
            return False
        
        # Verify transaction details
        if tx.to != expected_address:
            logger.error(f"Transaction to wrong address: {tx.to}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error verifying transaction: {e}")
        return False
```

### DEX Trading Security

```python
# ✅ Good: Validate slippage and amounts
async def execute_dex_swap(
    sell_token: str,
    buy_token: str,
    amount: float,
    slippage_percentage: float,
    user_id: int,
):
    # Validate inputs
    if slippage_percentage > MAX_SLIPPAGE:
        raise ValueError(f"Slippage exceeds maximum of {MAX_SLIPPAGE}%")
    
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    # Verify user balance
    balance = await get_user_balance(user_id, sell_token)
    if balance < amount:
        raise ValueError("Insufficient balance")
    
    # Get quote from aggregator
    quote = await get_dex_quote(sell_token, buy_token, amount)
    
    # Validate quote
    if quote.min_amount_out < expected_amount * (1 - slippage_percentage):
        raise ValueError("Quote does not meet slippage requirements")
    
    # Execute swap with idempotency
    swap_id = generate_idempotency_key(user_id, sell_token, buy_token, amount)
    return await execute_swap(quote, swap_id)
```

## Database Security

### SQL Injection Prevention
```python
# ✅ Good: Use SQLAlchemy ORM (parameterized queries)
from sqlalchemy import select

query = select(Bot).where(Bot.user_id == user_id)  # Safe
result = await db.execute(query)

# ❌ Bad: String concatenation (NEVER DO THIS)
query = f"SELECT * FROM bots WHERE user_id = {user_id}"  # Vulnerable!
```

### Password Hashing
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Good: Hash passwords before storing
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# ✅ Good: Verify passwords
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

## API Security

### CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Never use ["*"] in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### HTTPS Enforcement
```python
# ✅ Good: Enforce HTTPS in production
if ENVIRONMENT == "production":
    @app.middleware("http")
    async def force_https(request: Request, call_next):
        if request.url.scheme != "https":
            return Response("HTTPS required", status_code=403)
        return await call_next(request)
```

## Frontend Security

### XSS Prevention
```typescript
// ✅ Good: Sanitize user input
import DOMPurify from 'dompurify';

function SafeHTML({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}

// ❌ Bad: Directly rendering user input
function UnsafeHTML({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;  // Vulnerable!
}
```

### Secure Token Storage
```typescript
// ✅ Good: Store tokens securely
// Use httpOnly cookies when possible, or localStorage with encryption
// Always clear tokens on logout

function logout() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('refresh_token');
  // Clear any cached data
  queryClient.clear();
}
```

## Wallet Security

### Multi-Signature Wallets
```python
# ✅ Good: Support multi-sig wallets
async def execute_multi_sig_transaction(
    wallet_id: int,
    transaction_data: dict,
    signatures: list[str],
) -> dict:
    wallet = await get_wallet(wallet_id)
    
    if wallet.type != "multisig":
        raise ValueError("Wallet is not a multi-signature wallet")
    
    # Verify signatures
    required_signatures = wallet.threshold
    if len(signatures) < required_signatures:
        raise ValueError(f"Required {required_signatures} signatures")
    
    # Verify each signature
    for signature in signatures:
        if not verify_signature(signature, transaction_data, wallet):
            raise ValueError("Invalid signature")
    
    # Execute transaction
    return await submit_transaction(transaction_data, signatures)
```

## Audit Logging

```python
# ✅ Good: Log all sensitive operations
async def log_sensitive_operation(
    operation: str,
    user_id: int,
    details: dict,
):
    audit_log = {
        "operation": operation,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details,  # Never include sensitive data
        "ip_address": request.client.host,
    }
    await save_audit_log(audit_log)
```

## Compliance

### GDPR Compliance
- Implement right to be forgotten
- Allow data export
- Minimize data collection
- Obtain explicit consent

### Financial Regulations
- Implement KYC/AML checks
- Maintain transaction records
- Report suspicious activity
- Implement withdrawal limits

## Best Practices Summary

1. **Never store private keys** - Use key management services
2. **Never log sensitive data** - Log references only
3. **Always validate inputs** - Use Pydantic/Zod schemas
4. **Always verify permissions** - Check user permissions before operations
5. **Use rate limiting** - Protect against abuse
6. **Implement 2FA** - For sensitive operations
7. **Use HTTPS** - Enforce in production
8. **Audit logging** - Log all sensitive operations
9. **Regular security audits** - Review code for vulnerabilities
10. **Stay updated** - Keep dependencies updated for security patches
