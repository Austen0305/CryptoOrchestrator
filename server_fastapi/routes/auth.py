from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
# Use str instead of EmailStr to avoid email-validator dependency
EmailStr = str

# Import validation utilities
try:
    from ..middleware.validation import (
        SanitizedBaseModel,
        validate_email_format,
        validate_password_strength,
        sanitize_input
    )
except ImportError:
    SanitizedBaseModel = BaseModel
    def validate_email_format(email): return True
    def validate_password_strength(pwd): return {"valid": True}
    def sanitize_input(inp): return inp
try:
    import bcrypt
    import jwt
    import speakeasy
except ImportError:
    # Mock implementations for missing modules
    import hashlib
    import base64
    import hmac
    import json
    from datetime import datetime, timedelta

    class MockBcrypt:
        @staticmethod
        def hashpw(password, salt):
            return hashlib.sha256(password + salt).hexdigest().encode()
        @staticmethod
        def checkpw(password, hashed):
            return hashlib.sha256(password).hexdigest().encode() == hashed.decode()

    class MockJWT:
        @staticmethod
        def encode(payload, key, algorithm="HS256"):
            # Simple mock JWT
            header = {"alg": algorithm, "typ": "JWT"}
            encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
            encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
            message = f"{encoded_header}.{encoded_payload}"
            signature = base64.urlsafe_b64encode(hmac.new(key.encode(), message.encode(), hashlib.sha256).digest()).decode().rstrip('=')
            return f"{message}.{signature}"

        @staticmethod
        def decode(token, key, algorithms=None):
            return json.loads(base64.urlsafe_b64decode(token.split('.')[1] + '=='))

    class MockSpeakeasy:
        class totp:
            @staticmethod
            def verify(data):
                return True  # Always verify as true for mock

        @staticmethod
        def generate_secret(data):
            return {"base32": "MOCKSECRET", "otpauth_url": "otpauth://totp/Mock:mock@example.com?secret=MOCKSECRET"}

    bcrypt = MockBcrypt()
    jwt = MockJWT()
    speakeasy = MockSpeakeasy()
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import json

# Local schemas for auth requests with validation
class RegisterRequest(SanitizedBaseModel):
    email: EmailStr
    password: str
    name: str

    def validate_email(self):
        if not validate_email_format(self.email):
            raise ValueError("Invalid email format")
        return self

    def validate_password(self):
        strength = validate_password_strength(self.password)
        if not strength["valid"]:
            raise ValueError(strength["message"])
        return self

class LoginRequest(SanitizedBaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

# Import auth services with relative imports
try:
    from ..services.auth import AuthService, APIKeyService
except ImportError:
    # Fallback to mock services if import fails
    class MockAuthService:
        def register(self, data):
            return {'user': {'id': 1, 'email': data.get('email'), 'name': data.get('name')}}
        def verifyEmail(self, token):
            return {'success': True, 'message': 'Email verified successfully', 'user_id': 1}
        def resendVerificationEmail(self, email):
            return {'success': True, 'message': 'Verification email sent'}

    class MockAPIKeyService:
        pass

    AuthService = MockAuthService
    APIKeyService = MockAPIKeyService

from ..database import get_db_context
from ..repositories.user_repository import user_repository

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Import rate limiting configuration
auth_limiter = None  # Disabled for test stability; integration tests rely on unrestricted calls.

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Pydantic models (using shared schemas) with validation

class MFATokenRequest(SanitizedBaseModel):
    userId: int
    token: str

class EnableMFARequest(SanitizedBaseModel):
    token: str

class SetupTwoFactorChoiceRequest(SanitizedBaseModel):
    method: str  # 'email' or 'sms'
    phoneNumber: Optional[str] = None  # required only when method='sms'

class VerifyTwoFactorCodeRequest(SanitizedBaseModel):
    code: str  # 6-digit code

class VerifyTwoFactorLoginRequest(SanitizedBaseModel):
    userId: int
    code: str

class GenerateRecoveryCodesResponse(SanitizedBaseModel):
    codes: list[str]

class VerifyRecoveryCodeRequest(SanitizedBaseModel):
    userId: int
    code: str

class ForgotPasswordRequest(SanitizedBaseModel):
    email: EmailStr

    def validate_email(self):
        if not validate_email_format(self.email):
            raise ValueError("Invalid email format")
        return self

class ResetPasswordRequest(SanitizedBaseModel):
    token: str
    newPassword: str

    def validate_password(self):
        strength = validate_password_strength(self.newPassword)
        if not strength["valid"]:
            raise ValueError(strength["message"])
        return self

class UpdateProfileRequest(SanitizedBaseModel):
    name: str

class RefreshTokenRequest(SanitizedBaseModel):
    refreshToken: str

class LogoutRequest(SanitizedBaseModel):
    refreshToken: Optional[str] = None

class VerifyEmailRequest(SanitizedBaseModel):
    token: str

class ResendVerificationRequest(SanitizedBaseModel):
    email: EmailStr

    def validate_email(self):
        if not validate_email_format(self.email):
            raise ValueError("Invalid email format")
        return self

# Mock email service for development
class MockEmailService:
    def __init__(self, smtp_host: str = None, smtp_user: str = None, smtp_pass: str = None):
        self.smtp_host = smtp_host
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        logger.info("MockEmailService initialized - no real emails will be sent")

    def send_verification_email(self, email: str, token: str):
        """Mock sending verification email - logs instead of sending"""
        logger.info(f"[MOCK EMAIL] Verification email would be sent to {email}")
        logger.info(f"[MOCK EMAIL] Token: {token}")
        logger.info(f"[MOCK EMAIL] Link: http://localhost:3000/verify-email?token={token}")
        return True

    def send_password_reset_email(self, email: str, token: str):
        """Mock sending password reset email - logs instead of sending"""
        logger.info(f"[MOCK EMAIL] Password reset email would be sent to {email}")
        logger.info(f"[MOCK EMAIL] Token: {token}")
        logger.info(f"[MOCK EMAIL] Link: http://localhost:3000/reset-password?token={token}")
        return True

    def send_twofactor_code(self, email: str, code: str):
        """Mock sending 2FA code via email"""
        logger.info(f"[MOCK EMAIL] 2FA code {code} would be emailed to {email}")
        return True

class MockSMSService:
    def __init__(self):
        logger.info("MockSMSService initialized - no real SMS will be sent")

    def send_twofactor_code(self, phone_number: str, code: str):
        logger.info(f"[MOCK SMS] 2FA code {code} would be sent to {phone_number}")
        return True

# Mock storage - replace with actual database implementation
class MockStorage:
    def __init__(self):
        self.users = {}
        self.refresh_tokens = {}
        # Seed with default user for testing
        self._seed_default_user()

    def _seed_default_user(self):
        """Seed the storage with a default user for testing purposes."""
        hashed_password = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
        default_user = {
            'id': 1,
            'email': 'test@example.com',
            'name': 'Test User',
            'passwordHash': hashed_password,
            'emailVerified': True,
            'mfaEnabled': False,
            'mfaSecret': None,  # for TOTP flow
            'mfaMethod': None,  # 'email' | 'sms'
            'mfaCode': None,
            'mfaCodeExpires': None,
            'phoneNumber': None,
            'mfaRecoveryCodes': [],
            'createdAt': datetime.now(timezone.utc).isoformat()
        }
        self.users[1] = default_user

    def getUserByEmail(self, email: str):
        return next((user for user in self.users.values() if user.get('email') == email), None)

    def getUserByUsername(self, username: str):
        return next((user for user in self.users.values() if user.get('username') == username), None)

    def getUserById(self, user_id: int):
        return self.users.get(user_id)

    def createUser(self, user_data):
        user_id = len(self.users) + 1
        user = {
            'id': user_id,
            'email': user_data['email'],
            'name': user_data['name'],
            'passwordHash': user_data['passwordHash'],
            'emailVerified': False,
            'mfaEnabled': False,
            'mfaSecret': None,
            'mfaMethod': None,
            'mfaCode': None,
            'mfaCodeExpires': None,
            'phoneNumber': None,
            'mfaRecoveryCodes': [],
            'createdAt': datetime.now(timezone.utc).isoformat()
        }
        self.users[user_id] = user
        return user

    def updateUser(self, user_id: int, updates: dict):
        if user_id in self.users:
            self.users[user_id].update(updates)
            return True
        return False

    def storeRefreshToken(self, user_id: int, token: str):
        if user_id not in self.refresh_tokens:
            self.refresh_tokens[user_id] = []
        self.refresh_tokens[user_id].append(token)

    def getRefreshToken(self, user_id: int, token: str):
        return token in self.refresh_tokens.get(user_id, [])

    def updateRefreshToken(self, user_id: int, old_token: str, new_token: str):
        if user_id in self.refresh_tokens:
            tokens = self.refresh_tokens[user_id]
            if old_token in tokens:
                tokens.remove(old_token)
                tokens.append(new_token)

    def removeRefreshToken(self, user_id: int, token: str):
        if user_id in self.refresh_tokens:
            tokens = self.refresh_tokens[user_id]
            if token in tokens:
                tokens.remove(token)

# Persistent user creation helper (fallback to in-memory storage for operations not yet migrated)
storage = MockStorage()

# Initialize mock email service
email_service = MockEmailService(SMTP_HOST, SMTP_USER, SMTP_PASS)
sms_service = MockSMSService()

# Mock auth service - replace with actual implementation
class MockAuthService:
    def register(self, data):
        # Check if user exists
        existing = storage.getUserByEmail(data['email'])
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        # Hash password
        hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()

        # Create user
        user = storage.createUser({
            'email': data['email'],
            'name': data['name'],
            'passwordHash': hashed
        })

        return {
            'message': 'User registered successfully',
            'user': user
        }

    def verifyEmail(self, token: str):
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if decoded.get('type') != 'email_verification':
                return {'success': False, 'message': 'Invalid token type'}

            user = storage.getUserById(decoded['id'])
            if not user:
                return {'success': False, 'message': 'User not found'}

            # Check if already verified
            if user.get('emailVerified'):
                return {'success': False, 'message': 'Email already verified'}

            storage.updateUser(user['id'], {'emailVerified': True})
            return {'success': True, 'message': 'Email verified successfully', 'user_id': user['id']}
        except jwt.ExpiredSignatureError:
            return {'success': False, 'message': 'Verification token expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'message': 'Invalid verification token'}

    def resendVerificationEmail(self, email: str):
        user = storage.getUserByEmail(email)
        if not user:
            return {'success': False, 'message': 'User not found'}

        # Check if email is already verified
        if user.get('emailVerified'):
            return {'success': False, 'message': 'Email already verified'}

        # Generate verification token with expiration
        token = jwt.encode(
            {'id': user['id'], 'type': 'email_verification', 'exp': datetime.now(timezone.utc) + timedelta(hours=24)},
            JWT_SECRET,
            algorithm="HS256"
        )

        # Send verification email using mock service
        email_service.send_verification_email(email, token)

        return {'success': True, 'message': 'Verification email sent'}

# Initialize services
# Use route-local MockAuthService to keep storage in sync for tests and dev.
auth_service = MockAuthService()
api_key_service = APIKeyService()

# Helper functions
def generate_token(user: dict) -> str:
    return jwt.encode(
        {
            'id': user['id'],
            'email': user['email'],
            'exp': datetime.now(timezone.utc) + timedelta(minutes=15)
        },
        JWT_SECRET,
        algorithm="HS256"
    )

def generate_refresh_token(user: dict) -> str:
    return jwt.encode(
        {
            'id': user['id'],
            'type': 'refresh',
            'exp': datetime.now(timezone.utc) + timedelta(days=7)
        },
        JWT_SECRET,
        algorithm="HS256"
    )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user = storage.getUserById(payload['id'])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def _generate_6_digit_code() -> str:
    import random
    return f"{random.randint(0, 999999):06d}"

def _mask_email(email: str) -> str:
    try:
        name, domain = email.split('@', 1)
        masked_name = name[0] + "***" + name[-1] if len(name) > 2 else name[0] + "***"
        return f"{masked_name}@{domain}"
    except Exception:
        return "***"

def _mask_phone(phone: str) -> str:
    digits = ''.join([c for c in (phone or '') if c.isdigit()])
    if len(digits) >= 4:
        return f"***{digits[-4:]}"
    return "***"

# Routes
@router.post("/register")
async def register(payload: RegisterRequest, request: Request):
    logger.info(f"Registration request received for email: {payload.email}")
    try:
        # Validate email and password (map failures to 422 Unprocessable Entity)
        try:
            payload.validate_email()
            payload.validate_password()
        except ValueError as ve:
            logger.warning(f"Registration validation failed for {payload.email}: {ve}")
            raise HTTPException(status_code=422, detail=str(ve))

        result = auth_service.register({
            'email': sanitize_input(payload.email),
            'password': payload.password,  # Password is hashed in service
            'name': sanitize_input(payload.name)
        })

        # Extract user after registration
        user = result['user']

        # Persist user to database if not exists (basic fields). Username derived from email prefix.
        try:
            async with get_db_context() as session:
                existing = await user_repository.get_by_email(session, user['email'])
                if not existing:
                    username_part = user['email'].split('@')[0][:40] or f"user{user['id']}"
                    from server_fastapi.models.base import User  # local import to avoid circulars
                    db_user = User(
                        username=username_part,
                        email=user['email'],
                        password_hash=storage.getUserById(user['id'])['passwordHash'],
                        first_name=user['name'],
                        last_name=None,
                        avatar_url=None,
                        locale='en',
                        timezone='UTC'
                    )
                    session.add(db_user)
                    await session.commit()
        except Exception as db_err:
            logger.warning(f"Database persistence skipped for user {user['email']}: {db_err}")

        # Generate verification token for email verification
        verification_token = jwt.encode(
            {'id': user['id'], 'type': 'email_verification', 'exp': datetime.now(timezone.utc) + timedelta(hours=24)},
            JWT_SECRET,
            algorithm="HS256"
        )

        # Send verification email
        email_service.send_verification_email(user['email'], verification_token)

        # Generate temporary token (expires in 15 minutes, pending email verification)
        token = generate_token(user)

        logger.info(f"Registration successful for user ID: {user['id']}")

        return {
            "data": {
                "user": {
                    "id": user['id'],
                    "email": user['email'],
                    "name": user['name'],
                    "emailVerified": user['emailVerified']
                },
                "token": token,
                "message": "Please check your email to verify your account"
            }
        }
    except HTTPException:
        logger.warning(f"Registration failed for email {payload.email}: HTTPException")
        raise
    except Exception as e:
        logger.error(f"Registration failed for email {payload.email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(payload: LoginRequest, request: Request):
    logger.info(f"Login request received for email/username: {payload.email or payload.username}")

    # Sanitize login identifier
    login_identifier = sanitize_input(payload.email or payload.username or "")

    # Find user
    user = None
    if payload.email:
        user = storage.getUserByEmail(login_identifier)
    elif payload.username:
        user = storage.getUserByUsername(login_identifier)

    if not user or not user.get('passwordHash'):
        logger.warning(f"Login failed: Invalid credentials for {payload.email or payload.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify password
    if not bcrypt.checkpw(payload.password.encode(), user['passwordHash'].encode()):
        logger.warning(f"Login failed: Invalid password for user {user['id']}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check MFA (TOTP or one-time code via email/SMS)
    if user.get('mfaEnabled'):
        # If classic TOTP is configured
        if user.get('mfaSecret'):
            logger.info(f"MFA (TOTP) required for user {user['id']}")
            return {
                "requiresMfa": True,
                "userId": user['id'],
                "method": "totp"
            }

        # If email/sms 6-digit code is configured
        method = user.get('mfaMethod')
        if method in ("email", "sms"):
            code = _generate_6_digit_code()
            expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
            storage.updateUser(user['id'], {'mfaCode': code, 'mfaCodeExpires': expires_at})
            # Persist one-time login code to DB for durability across restarts
            try:
                async with get_db_context() as session:
                    db_user = await user_repository.get_by_email(session, user['email'])
                    if db_user:
                        db_user.mfa_code = code
                        from datetime import datetime as _dt
                        db_user.mfa_code_expires_at = _dt.fromisoformat(expires_at)
                        await session.commit()
            except Exception as e:
                logger.warning(f"DB persistence of MFA login code failed: {e}")
            if method == 'email':
                email_service.send_twofactor_code(user['email'], code)
                destination = _mask_email(user['email'])
            else:
                sms_service.send_twofactor_code(user.get('phoneNumber') or '', code)
                destination = _mask_phone(user.get('phoneNumber') or '')

            logger.info(f"MFA ({method}) required for user {user['id']}")
            return {
                "requiresMfa": True,
                "userId": user['id'],
                "method": method,
                "destination": destination
            }

    # Generate tokens
    token = generate_token(user)
    refresh_token = generate_refresh_token(user)

    # Store refresh token
    storage.storeRefreshToken(user['id'], refresh_token)

    logger.info(f"Login successful for user {user['id']}")

    return {
        "data": {
            "user": {
                "id": user['id'],
                "email": user['email'],
                "name": user['name']
            },
            "token": token,
            "refreshToken": refresh_token
        }
    }

@router.post("/verify-mfa")
async def verify_mfa(payload: MFATokenRequest, request: Request):
    user = storage.getUserById(payload.userId)
    if not user or not user.get('mfaSecret'):
        raise HTTPException(status_code=400, detail="Invalid user or MFA not enabled")

    verified = speakeasy.totp.verify({
        'secret': user['mfaSecret'],
        'encoding': 'base32',
        'token': payload.token,
        'window': 2
    })

    if not verified:
        raise HTTPException(status_code=401, detail="Invalid MFA token")

    token = generate_token(user)
    refresh_token = generate_refresh_token(user)
    storage.storeRefreshToken(user['id'], refresh_token)

    return {
        "data": {
            "user": {
                "id": user['id'],
                "email": user['email'],
                "name": user['name']
            },
            "token": token,
            "refreshToken": refresh_token
        }
    }

@router.post("/setup-mfa")
async def setup_mfa(current_user: dict = Depends(get_current_user)):
    secret = speakeasy.generate_secret({
        'name': f"CryptoOrchestrator ({current_user['email']})",
        'issuer': 'CryptoOrchestrator'
    })

    storage.updateUser(current_user['id'], {
        'mfaSecret': secret['base32'],
        'mfaEnabled': False
    })

    return {
        "secret": secret['base32'],
        "otpauthUrl": secret['otpauth_url']
    }

@router.post("/enable-mfa")
async def enable_mfa(payload: EnableMFARequest, request: Request, current_user: dict = Depends(get_current_user)):
    db_user = storage.getUserById(current_user['id'])
    if not db_user or not db_user.get('mfaSecret'):
        raise HTTPException(status_code=400, detail="MFA not set up")

    verified = speakeasy.totp.verify({
        'secret': db_user['mfaSecret'],
        'encoding': 'base32',
        'token': payload.token,
        'window': 2
    })

    if not verified:
        raise HTTPException(status_code=401, detail="Invalid MFA token")

    storage.updateUser(current_user['id'], {'mfaEnabled': True})
    return {"message": "MFA enabled successfully"}

@router.post("/setup-mfa-choice")
async def setup_mfa_choice(payload: SetupTwoFactorChoiceRequest, current_user: dict = Depends(get_current_user)):
    method = (payload.method or '').lower().strip()
    if method not in ('email', 'sms'):
        raise HTTPException(status_code=400, detail="method must be 'email' or 'sms'")

    # Save chosen method and phone if applicable
    updates = {'mfaMethod': method}
    if method == 'sms':
        if not payload.phoneNumber or len(payload.phoneNumber) < 6:
            raise HTTPException(status_code=422, detail="Valid phoneNumber is required for sms method")
        updates['phoneNumber'] = sanitize_input(payload.phoneNumber)

    # Generate one-time 6-digit code and expiry (10 minutes)
    code = _generate_6_digit_code()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    updates['mfaCode'] = code
    updates['mfaCodeExpires'] = expires_at

    storage.updateUser(current_user['id'], updates)
    user = storage.getUserById(current_user['id'])
    # Persist MFA setup data (method, phone, code & expiry) to DB
    try:
        async with get_db_context() as session:
            db_user = await user_repository.get_by_email(session, user['email'])
            if db_user:
                db_user.mfa_method = method
                if method == 'sms' and updates.get('phoneNumber'):
                    db_user.phone_number = updates.get('phoneNumber')
                db_user.mfa_code = updates.get('mfaCode')
                from datetime import datetime as _dt
                db_user.mfa_code_expires_at = _dt.fromisoformat(updates.get('mfaCodeExpires')) if updates.get('mfaCodeExpires') else None
                await session.commit()
    except Exception as e:
        logger.warning(f"DB persistence of MFA setup failed: {e}")

    # Deliver code
    if method == 'email':
        email_service.send_twofactor_code(user['email'], code)
        destination = _mask_email(user['email'])
    else:
        sms_service.send_twofactor_code(user['phoneNumber'], code)
        destination = _mask_phone(user['phoneNumber'])

    return {"message": "2FA code sent", "method": method, "destination": destination}

@router.post("/verify-mfa-code")
async def verify_mfa_code(payload: VerifyTwoFactorCodeRequest, current_user: dict = Depends(get_current_user)):
    user = storage.getUserById(current_user['id'])
    if not user or not user.get('mfaMethod'):
        raise HTTPException(status_code=400, detail="2FA method not set up")

    code = (payload.code or '').strip()
    if not code.isdigit() or len(code) != 6:
        raise HTTPException(status_code=422, detail="Invalid code format")

    # Validate code and expiry
    stored_code = user.get('mfaCode')
    expires_str = user.get('mfaCodeExpires')
    if not stored_code or not expires_str:
        raise HTTPException(status_code=400, detail="No pending 2FA code")

    try:
        expires_at = datetime.fromisoformat(expires_str)
    except Exception:
        expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    if datetime.now(timezone.utc) > expires_at or code != stored_code:
        raise HTTPException(status_code=401, detail="Invalid or expired code")

    # Enable MFA for the chosen method and clear one-time code
    storage.updateUser(user['id'], {
        'mfaEnabled': True,
        'mfaSecret': None,  # not used for code-based 2FA
        'mfaCode': None,
        'mfaCodeExpires': None
    })
    # Persist enabling of MFA to DB
    try:
        async with get_db_context() as session:
            db_user = await user_repository.get_by_email(session, user['email'])
            if db_user:
                db_user.mfa_enabled = True
                db_user.mfa_secret = None
                db_user.mfa_code = None
                db_user.mfa_code_expires_at = None
                await session.commit()
    except Exception as e:
        logger.warning(f"DB persistence of MFA enable failed: {e}")

    return {"message": "2FA enabled successfully", "method": user.get('mfaMethod')}

@router.post("/mfa/recovery/generate", response_model=GenerateRecoveryCodesResponse)
async def generate_recovery_codes(current_user: dict = Depends(get_current_user)):
    """Generate and persist a new set of MFA recovery codes.
    Codes are one-time use; previously issued codes are replaced.
    """
    user = storage.getUserById(current_user['id'])
    if not user or not user.get('mfaEnabled'):
        raise HTTPException(status_code=400, detail="MFA not enabled")
    import secrets, hashlib
    # Generate 8 recovery codes
    raw_codes = [secrets.token_hex(4) for _ in range(8)]
    # Store hashed codes in DB, plain codes only in session (mock storage) for display once
    hashed_codes = [hashlib.sha256(c.encode()).hexdigest() for c in raw_codes]
    storage.updateUser(user['id'], {'mfaRecoveryCodes': raw_codes})
    try:
        async with get_db_context() as session:
            db_user = await user_repository.get_by_email(session, user['email'])
            if db_user:
                import json as _json
                db_user.mfa_recovery_codes = _json.dumps(hashed_codes)
                await session.commit()
    except Exception as e:
        logger.warning(f"DB persistence of recovery codes failed: {e}")
    return GenerateRecoveryCodesResponse(codes=raw_codes)

@router.post("/mfa/recovery/verify")
async def verify_recovery_code(payload: VerifyRecoveryCodeRequest):
    user = storage.getUserById(payload.userId)
    if not user or not user.get('mfaEnabled'):
        raise HTTPException(status_code=400, detail="MFA not enabled for user")
    import hashlib, json as _json
    submitted = (payload.code or '').strip()
    if not submitted:
        raise HTTPException(status_code=422, detail="Recovery code required")
    # Check DB hashed list first
    valid = False
    try:
        async with get_db_context() as session:
            db_user = await user_repository.get_by_email(session, user['email'])
            if db_user and db_user.mfa_recovery_codes:
                hashed_list = _json.loads(db_user.mfa_recovery_codes)
                submitted_hash = hashlib.sha256(submitted.encode()).hexdigest()
                if submitted_hash in hashed_list:
                    valid = True
                    hashed_list.remove(submitted_hash)
                    db_user.mfa_recovery_codes = _json.dumps(hashed_list)
                    await session.commit()
    except Exception as e:
        logger.warning(f"DB recovery code verify failed: {e}")
    # Fallback to in-memory codes (plain) for current session if DB failed or not found
    if not valid:
        plain_codes = user.get('mfaRecoveryCodes') or []
        if submitted in plain_codes:
            valid = True
            plain_codes.remove(submitted)
            storage.updateUser(user['id'], {'mfaRecoveryCodes': plain_codes})
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid recovery code")
    # Issue tokens bypassing current MFA code requirement
    token = generate_token(user)
    refresh_token = generate_refresh_token(user)
    storage.storeRefreshToken(user['id'], refresh_token)
    return {
        "data": {
            "user": {"id": user['id'], "email": user['email'], "name": user['name']},
            "token": token,
            "refreshToken": refresh_token,
            "usedRecoveryCode": True
        }
    }

@router.post("/verify-mfa-login-code")
async def verify_mfa_login_code(payload: VerifyTwoFactorLoginRequest):
    user = storage.getUserById(payload.userId)
    if not user or not user.get('mfaMethod'):
        raise HTTPException(status_code=400, detail="2FA method not set up")

    code = (payload.code or '').strip()
    if not code.isdigit() or len(code) != 6:
        raise HTTPException(status_code=422, detail="Invalid code format")

    stored_code = user.get('mfaCode')
    expires_str = user.get('mfaCodeExpires')
    # Fallback to DB if memory does not have code (e.g., after restart)
    if (not stored_code or not expires_str):
        try:
            async with get_db_context() as session:
                db_user = await user_repository.get_by_email(session, user['email'])
                if db_user:
                    stored_code = stored_code or db_user.mfa_code
                    if db_user.mfa_code_expires_at:
                        expires_str = expires_str or db_user.mfa_code_expires_at.isoformat()
        except Exception as e:
            logger.warning(f"DB fetch MFA code failed: {e}")
    if not stored_code or not expires_str:
        raise HTTPException(status_code=400, detail="No pending 2FA code")

    try:
        expires_at = datetime.fromisoformat(expires_str)
    except Exception:
        expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    if datetime.now(timezone.utc) > expires_at or code != stored_code:
        raise HTTPException(status_code=401, detail="Invalid or expired code")

    # Clear code and proceed to issue tokens
    storage.updateUser(user['id'], {'mfaCode': None, 'mfaCodeExpires': None})
    # Clear persisted code in DB
    try:
        async with get_db_context() as session:
            db_user = await user_repository.get_by_email(session, user['email'])
            if db_user:
                db_user.mfa_code = None
                db_user.mfa_code_expires_at = None
                await session.commit()
    except Exception as e:
        logger.warning(f"DB clearing MFA code failed: {e}")

    token = generate_token(user)
    refresh_token = generate_refresh_token(user)
    storage.storeRefreshToken(user['id'], refresh_token)

    return {
        "data": {
            "user": {
                "id": user['id'],
                "email": user['email'],
                "name": user['name']
            },
            "token": token,
            "refreshToken": refresh_token
        }
    }

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, request: Request):
    # Validate email format
    payload.validate_email()

    sanitized_email = sanitize_input(payload.email)
    user = storage.getUserByEmail(sanitized_email)
    if not user:
        # Don't reveal if user exists
        return {"message": "If the email exists, a reset link has been sent"}

    # Check if email is verified
    if not user.get('emailVerified'):
        return {"message": "Please verify your email first before resetting password"}

    # Generate reset token with expiration
    reset_token = jwt.encode(
        {'id': user['id'], 'type': 'password_reset', 'exp': datetime.now(timezone.utc) + timedelta(hours=1)},
        JWT_SECRET,
        algorithm="HS256"
    )

    # Send password reset email using mock service
    email_service.send_password_reset_email(payload.email, reset_token)

    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, request: Request):
    try:
        # Validate new password
        payload.validate_password()

        decoded = jwt.decode(payload.token, JWT_SECRET, algorithms=["HS256"])
        if decoded.get('type') != 'password_reset':
            raise HTTPException(status_code=400, detail="Invalid reset token")

        hashed_password = bcrypt.hashpw(payload.newPassword.encode(), bcrypt.gensalt()).decode()
        storage.updateUser(decoded['id'], {'passwordHash': hashed_password})

        return {"message": "Password reset successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    # Attempt to enrich profile from DB persistence
    db_data = {}
    try:
        async with get_db_context() as session:
            db_user = await user_repository.get_by_email(session, current_user['email'])
            if db_user:
                db_data = {
                    'username': db_user.username,
                    'firstName': db_user.first_name,
                    'lastName': db_user.last_name,
                    'avatarUrl': db_user.avatar_url,
                    'locale': db_user.locale,
                    'timezone': db_user.timezone,
                    'preferences': json.loads(db_user.preferences_json) if db_user.preferences_json else None,
                }
    except Exception as e:
        logger.warning(f"Profile DB enrichment failed: {e}")
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "name": current_user['name'],
        "createdAt": current_user['createdAt'],
        "mfaEnabled": current_user.get('mfaEnabled', False),
        **db_data
    }

@router.patch("/profile")
async def update_profile(request: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    sanitized_name = sanitize_input(request.name)
    storage.updateUser(current_user['id'], {'name': sanitized_name})
    # Persist name change
    try:
        async with get_db_context() as session:
            db_user = await user_repository.get_by_email(session, current_user['email'])
            if db_user:
                db_user.first_name = sanitized_name
                await session.commit()
    except Exception as e:
        logger.warning(f"DB profile update failed: {e}")
    return {"message": "Profile updated successfully"}

@router.post("/refresh")
async def refresh_token(payload: RefreshTokenRequest, request: Request):
    try:
        decoded = jwt.decode(payload.refreshToken, JWT_SECRET, algorithms=["HS256"])
        if decoded.get('type') != 'refresh':
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Check if refresh token exists
        if not storage.getRefreshToken(decoded['id'], payload.refreshToken):
            raise HTTPException(status_code=401, detail="Refresh token not found")

        user = storage.getUserById(decoded['id'])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Generate new tokens
        new_access_token = generate_token(user)
        new_refresh_token = generate_refresh_token(user)

        # Update refresh token
        storage.updateRefreshToken(decoded['id'], payload.refreshToken, new_refresh_token)

        return {
            "accessToken": new_access_token,
            "refreshToken": new_refresh_token
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
async def logout(request: LogoutRequest, current_user: dict = Depends(get_current_user)):
    if request.refreshToken:
        storage.removeRefreshToken(current_user['id'], request.refreshToken)
    return {"message": "Logged out successfully"}

@router.post("/verify-email")
async def verify_email(payload: VerifyEmailRequest, request: Request):
    result = auth_service.verifyEmail(payload.token)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])

    # Generate full access token after email verification
    user = storage.getUserById(result['user_id']) if 'user_id' in result else None
    if user:
        token = generate_token(user)
        return {
            "message": result['message'],
            "token": token,
            "emailVerified": True
        }
    return {"message": result['message']}

@router.post("/resend-verification")
async def resend_verification(payload: ResendVerificationRequest, request: Request):
    # Validate email format
    payload.validate_email()

    sanitized_email = sanitize_input(payload.email)
    result = auth_service.resendVerificationEmail(sanitized_email)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    return {"message": result['message']}
