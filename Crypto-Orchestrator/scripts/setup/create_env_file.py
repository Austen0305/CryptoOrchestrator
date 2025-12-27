#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Environment File Creation Script
Creates .env file with all required variables and secure defaults
"""

import os
import secrets
import sys
import io
from pathlib import Path
from typing import Dict, Optional

# Fix Windows encoding issues
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def generate_secure_secret(length: int = 64) -> str:
    """Generate a secure random secret using secrets module"""
    return secrets.token_urlsafe(length)


def generate_32_byte_key() -> str:
    """Generate a 32-byte encryption key"""
    return secrets.token_urlsafe(32)


def read_existing_env() -> Dict[str, str]:
    """Read existing .env file if it exists"""
    env_file = Path(".env")
    existing = {}
    
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    existing[key.strip()] = value.strip()
    
    return existing


def create_env_file(overwrite: bool = False, interactive: bool = False) -> bool:
    """Create .env file with all required variables"""
    env_file = Path(".env")
    existing = read_existing_env() if env_file.exists() else {}
    
    if env_file.exists() and not overwrite:
        # Check if running non-interactively (stdin is not a TTY)
        import sys
        try:
            is_interactive = sys.stdin.isatty()
        except (AttributeError, OSError):
            # stdin might not be available, assume non-interactive
            is_interactive = False
        
        if not is_interactive:
            # Running non-interactively (e.g., from setup script), skip creation
            print(f"✅ .env file already exists at {env_file.absolute()}, skipping creation")
            return True
        
        # Interactive mode: prompt user
        print(f"⚠️  .env file already exists at {env_file.absolute()}")
        try:
            response = input("Overwrite? (y/N): ").strip().lower()
            if response != "y":
                print("❌ Aborted. Use --overwrite flag to force overwrite.")
                return False
        except (EOFError, KeyboardInterrupt):
            # Handle case where stdin is closed or interrupted
            print("❌ Aborted. Use --overwrite flag to force overwrite.")
            return False
    
    print("🔐 Generating secure secrets...")
    
    # Generate secure secrets
    jwt_secret = existing.get("JWT_SECRET") or generate_secure_secret(64)
    enc_key = existing.get("EXCHANGE_KEY_ENCRYPTION_KEY") or generate_32_byte_key()
    
    # Environment variables with defaults for development
    env_vars = {
        # Application
        "NODE_ENV": existing.get("NODE_ENV", "development"),
        "PORT": existing.get("PORT", "8000"),
        "HOST": existing.get("HOST", "0.0.0.0"),
        "API_VERSION": existing.get("API_VERSION", "1.0.0"),
        "LOG_LEVEL": existing.get("LOG_LEVEL", "DEBUG"),
        "LOG_FORMAT": existing.get("LOG_FORMAT", "text"),
        
        # Database (SQLite for development)
        "DATABASE_URL": existing.get("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db"),
        "DB_POOL_SIZE": existing.get("DB_POOL_SIZE", "30"),
        "DB_MAX_OVERFLOW": existing.get("DB_MAX_OVERFLOW", "20"),
        "DB_POOL_TIMEOUT": existing.get("DB_POOL_TIMEOUT", "60"),
        "DB_POOL_RECYCLE": existing.get("DB_POOL_RECYCLE", "3600"),
        
        # Redis (optional for development)
        "REDIS_URL": existing.get("REDIS_URL", "redis://localhost:6379/0"),
        "REDIS_POOL_SIZE": existing.get("REDIS_POOL_SIZE", "10"),
        
        # Security (generated secrets)
        "JWT_SECRET": jwt_secret,
        "JWT_ALGORITHM": existing.get("JWT_ALGORITHM", "HS256"),
        "JWT_EXPIRATION_HOURS": existing.get("JWT_EXPIRATION_HOURS", "24"),
        "EXCHANGE_KEY_ENCRYPTION_KEY": enc_key,
        
        # CORS
        "ALLOWED_ORIGINS": existing.get(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://localhost:8000"
        ),
        
        # Trading
        "DEFAULT_TRADING_MODE": existing.get("DEFAULT_TRADING_MODE", "paper"),
        "ENABLE_MOCK_DATA": existing.get("ENABLE_MOCK_DATA", "true"),
        "PRODUCTION_MODE": existing.get("PRODUCTION_MODE", "false"),
        "EXCHANGE_TIMEOUT": existing.get("EXCHANGE_TIMEOUT", "30"),
        "EXCHANGE_RETRY_ATTEMPTS": existing.get("EXCHANGE_RETRY_ATTEMPTS", "3"),
        
        # Cache
        "CACHE_TTL": existing.get("CACHE_TTL", "300"),
        "CACHE_MAX_SIZE": existing.get("CACHE_MAX_SIZE", "1000"),
        
        # WebSocket
        "WS_PING_INTERVAL": existing.get("WS_PING_INTERVAL", "20"),
        "WS_PING_TIMEOUT": existing.get("WS_PING_TIMEOUT", "10"),
        "WS_MAX_MESSAGE_SIZE": existing.get("WS_MAX_MESSAGE_SIZE", "1048576"),
        
        # Celery
        "CELERY_BROKER_URL": existing.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        "CELERY_RESULT_BACKEND": existing.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
        
        # Feature Flags
        "ENABLE_2FA": existing.get("ENABLE_2FA", "true"),
        "ENABLE_KYC": existing.get("ENABLE_KYC", "true"),
        "ENABLE_COLD_STORAGE": existing.get("ENABLE_COLD_STORAGE", "true"),
        "ENABLE_STAKING": existing.get("ENABLE_STAKING", "true"),
        "ENABLE_COPY_TRADING": existing.get("ENABLE_COPY_TRADING", "true"),
        "ENABLE_DEX_TRADING": existing.get("ENABLE_DEX_TRADING", "true"),
        "ENABLE_WITHDRAWAL_WHITELIST": existing.get("ENABLE_WITHDRAWAL_WHITELIST", "true"),
        
        # DEX Trading (optional - can be added later)
        # "ZEROX_API_KEY": "",
        # "OKX_API_KEY": "",
        # "OKX_SECRET_KEY": "",
        # "OKX_PASSPHRASE": "",
        # "RUBIC_API_KEY": "",
        
        # Blockchain RPC (optional - can be added later)
        # "ETHEREUM_RPC_URL": "",
        # "BASE_RPC_URL": "",
        # "ARBITRUM_RPC_URL": "",
        # "POLYGON_RPC_URL": "",
        # "OPTIMISM_RPC_URL": "",
        # "AVALANCHE_RPC_URL": "",
        # "BNB_CHAIN_RPC_URL": "",
        # "RPC_PROVIDER_TYPE": "public",
        # "RPC_API_KEY": "",
        
        # Stripe (optional)
        # "STRIPE_SECRET_KEY": "",
        # "STRIPE_PUBLISHABLE_KEY": "",
        # "STRIPE_WEBHOOK_SECRET": "",
        
        # Email (optional)
        # "SMTP_HOST": "",
        # "SMTP_PORT": "587",
        # "SMTP_USER": "",
        # "SMTP_PASSWORD": "",
        # "SMTP_FROM": "",
        # "EMAIL_ENABLED": "false",
        
        # Monitoring (optional)
        # "SENTRY_DSN": "",
        # "ENABLE_SENTRY": "false",
        # "ENABLE_PROMETHEUS": "true",
    }
    
    # Interactive mode: prompt for optional values
    if interactive:
        print("\n📝 Optional Configuration (press Enter to skip):")
        
        # DEX Trading
        if not existing.get("ZEROX_API_KEY"):
            zerox = input("ZEROX_API_KEY (optional): ").strip()
            if zerox:
                env_vars["ZEROX_API_KEY"] = zerox
        
        # Blockchain RPC
        if not existing.get("ETHEREUM_RPC_URL"):
            eth_rpc = input("ETHEREUM_RPC_URL (optional): ").strip()
            if eth_rpc:
                env_vars["ETHEREUM_RPC_URL"] = eth_rpc
        
        # Stripe
        if not existing.get("STRIPE_SECRET_KEY"):
            stripe_key = input("STRIPE_SECRET_KEY (optional): ").strip()
            if stripe_key:
                env_vars["STRIPE_SECRET_KEY"] = stripe_key
    
    # Build .env file content
    content = [
        "# CryptoOrchestrator Environment Configuration",
        "# Generated automatically - DO NOT COMMIT TO GIT",
        "# This file contains sensitive information",
        "",
        "# ==========================================",
        "# Application Configuration",
        "# ==========================================",
        f"NODE_ENV={env_vars['NODE_ENV']}",
        f"PORT={env_vars['PORT']}",
        f"HOST={env_vars['HOST']}",
        f"API_VERSION={env_vars['API_VERSION']}",
        f"LOG_LEVEL={env_vars['LOG_LEVEL']}",
        f"LOG_FORMAT={env_vars['LOG_FORMAT']}",
        "",
        "# ==========================================",
        "# Database Configuration",
        "# ==========================================",
        f"DATABASE_URL={env_vars['DATABASE_URL']}",
        f"DB_POOL_SIZE={env_vars['DB_POOL_SIZE']}",
        f"DB_MAX_OVERFLOW={env_vars['DB_MAX_OVERFLOW']}",
        f"DB_POOL_TIMEOUT={env_vars['DB_POOL_TIMEOUT']}",
        f"DB_POOL_RECYCLE={env_vars['DB_POOL_RECYCLE']}",
        "",
        "# ==========================================",
        "# Redis Configuration (Optional)",
        "# ==========================================",
        f"REDIS_URL={env_vars['REDIS_URL']}",
        f"REDIS_POOL_SIZE={env_vars['REDIS_POOL_SIZE']}",
        "",
        "# ==========================================",
        "# Security Secrets (Generated Securely)",
        "# ==========================================",
        f"JWT_SECRET={env_vars['JWT_SECRET']}",
        f"JWT_ALGORITHM={env_vars['JWT_ALGORITHM']}",
        f"JWT_EXPIRATION_HOURS={env_vars['JWT_EXPIRATION_HOURS']}",
        f"EXCHANGE_KEY_ENCRYPTION_KEY={env_vars['EXCHANGE_KEY_ENCRYPTION_KEY']}",
        "",
        "# ==========================================",
        "# CORS Configuration",
        "# ==========================================",
        f"ALLOWED_ORIGINS={env_vars['ALLOWED_ORIGINS']}",
        "",
        "# ==========================================",
        "# Trading Configuration",
        "# ==========================================",
        f"DEFAULT_TRADING_MODE={env_vars['DEFAULT_TRADING_MODE']}",
        f"ENABLE_MOCK_DATA={env_vars['ENABLE_MOCK_DATA']}",
        f"PRODUCTION_MODE={env_vars['PRODUCTION_MODE']}",
        f"EXCHANGE_TIMEOUT={env_vars['EXCHANGE_TIMEOUT']}",
        f"EXCHANGE_RETRY_ATTEMPTS={env_vars['EXCHANGE_RETRY_ATTEMPTS']}",
        "",
        "# ==========================================",
        "# Cache Configuration",
        "# ==========================================",
        f"CACHE_TTL={env_vars['CACHE_TTL']}",
        f"CACHE_MAX_SIZE={env_vars['CACHE_MAX_SIZE']}",
        "",
        "# ==========================================",
        "# WebSocket Configuration",
        "# ==========================================",
        f"WS_PING_INTERVAL={env_vars['WS_PING_INTERVAL']}",
        f"WS_PING_TIMEOUT={env_vars['WS_PING_TIMEOUT']}",
        f"WS_MAX_MESSAGE_SIZE={env_vars['WS_MAX_MESSAGE_SIZE']}",
        "",
        "# ==========================================",
        "# Celery Configuration",
        "# ==========================================",
        f"CELERY_BROKER_URL={env_vars['CELERY_BROKER_URL']}",
        f"CELERY_RESULT_BACKEND={env_vars['CELERY_RESULT_BACKEND']}",
        "",
        "# ==========================================",
        "# Feature Flags",
        "# ==========================================",
        f"ENABLE_2FA={env_vars['ENABLE_2FA']}",
        f"ENABLE_KYC={env_vars['ENABLE_KYC']}",
        f"ENABLE_COLD_STORAGE={env_vars['ENABLE_COLD_STORAGE']}",
        f"ENABLE_STAKING={env_vars['ENABLE_STAKING']}",
        f"ENABLE_COPY_TRADING={env_vars['ENABLE_COPY_TRADING']}",
        f"ENABLE_DEX_TRADING={env_vars['ENABLE_DEX_TRADING']}",
        f"ENABLE_WITHDRAWAL_WHITELIST={env_vars['ENABLE_WITHDRAWAL_WHITELIST']}",
        "",
        "# ==========================================",
        "# DEX Trading Configuration (Optional)",
        "# ==========================================",
        "# ZEROX_API_KEY=",
        "# OKX_API_KEY=",
        "# OKX_SECRET_KEY=",
        "# OKX_PASSPHRASE=",
        "# RUBIC_API_KEY=",
        "",
        "# ==========================================",
        "# Blockchain RPC URLs (Optional)",
        "# ==========================================",
        "# ETHEREUM_RPC_URL=",
        "# BASE_RPC_URL=",
        "# ARBITRUM_RPC_URL=",
        "# POLYGON_RPC_URL=",
        "# OPTIMISM_RPC_URL=",
        "# AVALANCHE_RPC_URL=",
        "# BNB_CHAIN_RPC_URL=",
        "# RPC_PROVIDER_TYPE=public",
        "# RPC_API_KEY=",
        "",
        "# ==========================================",
        "# Stripe Configuration (Optional)",
        "# ==========================================",
        "# STRIPE_SECRET_KEY=",
        "# STRIPE_PUBLISHABLE_KEY=",
        "# STRIPE_WEBHOOK_SECRET=",
        "",
        "# ==========================================",
        "# Email Configuration (Optional)",
        "# ==========================================",
        "# SMTP_HOST=",
        "# SMTP_PORT=587",
        "# SMTP_USER=",
        "# SMTP_PASSWORD=",
        "# SMTP_FROM=",
        "# EMAIL_ENABLED=false",
        "",
        "# ==========================================",
        "# Monitoring Configuration (Optional)",
        "# ==========================================",
        "# SENTRY_DSN=",
        "# ENABLE_SENTRY=false",
        "# ENABLE_PROMETHEUS=true",
        "",
        "# ==========================================",
        "# IMPORTANT SECURITY NOTES",
        "# ==========================================",
        "# ⚠️  NEVER commit this file to git!",
        "# ⚠️  Keep JWT_SECRET and EXCHANGE_KEY_ENCRYPTION_KEY secure!",
        "# ⚠️  Change all secrets in production!",
        "# ⚠️  Use strong secrets (32+ characters) in production!",
        "",
    ]
    
    # Add any optional values that were set
    optional_keys = [
        "ZEROX_API_KEY", "OKX_API_KEY", "OKX_SECRET_KEY", "OKX_PASSPHRASE", "RUBIC_API_KEY",
        "ETHEREUM_RPC_URL", "BASE_RPC_URL", "ARBITRUM_RPC_URL", "POLYGON_RPC_URL",
        "OPTIMISM_RPC_URL", "AVALANCHE_RPC_URL", "BNB_CHAIN_RPC_URL", "RPC_API_KEY",
        "STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY", "STRIPE_WEBHOOK_SECRET",
        "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM",
        "SENTRY_DSN"
    ]
    
    for key in optional_keys:
        if key in env_vars and env_vars[key]:
            # Find where to insert in content
            for i, line in enumerate(content):
                if f"# {key}=" in line or key in line:
                    content[i] = f"{key}={env_vars[key]}"
                    break
    
    # Write .env file
    try:
        env_file.write_text("\n".join(content), encoding="utf-8")
        print(f"✅ Created .env file at {env_file.absolute()}")
        print(f"✅ Generated secure JWT_SECRET (length: {len(jwt_secret)})")
        print(f"✅ Generated secure EXCHANGE_KEY_ENCRYPTION_KEY (length: {len(enc_key)})")
        print("⚠️  IMPORTANT: Keep these secrets secure and never commit .env to git!")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create .env file for CryptoOrchestrator")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing .env file without prompting"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for optional configuration values"
    )
    
    args = parser.parse_args()
    
    success = create_env_file(overwrite=args.overwrite, interactive=args.interactive)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
