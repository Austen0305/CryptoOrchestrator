from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import hashlib
import jwt


JWT_SECRET = "dev-minimal-secret"
JWT_ALG = "HS256"


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    password_hash: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_email_verified: bool = False
    role: str = "user"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    user: User
    message: Optional[str] = None


app = FastAPI(title="Minimal Auth Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_users_by_email: Dict[str, User] = {}
_next_id = 1


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _generate_token(user: User) -> str:
    payload = {
        "id": user.id,
        "email": user.email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


@app.get("/health")
async def health():
    return {"status": "ok", "users": len(_users_by_email)}


@app.post("/api/auth/register", response_model=TokenResponse)
async def minimal_register(payload: RegisterRequest):
    global _next_id
    email_lower = payload.email.lower()
    if email_lower in _users_by_email:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        id=_next_id,
        email=email_lower,
        username=payload.username,
        password_hash=_hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    _users_by_email[email_lower] = user
    _next_id += 1

    token = _generate_token(user)
    return TokenResponse(access_token=token, refresh_token=None, user=user, message="Registered via minimal auth server")


@app.post("/api/auth/login", response_model=TokenResponse)
async def minimal_login(payload: LoginRequest):
    email_lower = payload.email.lower()
    user = _users_by_email.get(email_lower)
    if not user or user.password_hash != _hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _generate_token(user)
    return TokenResponse(access_token=token, refresh_token=None, user=user, message="Logged in via minimal auth server")


