#!/usr/bin/env python3
"""
Generate secure secrets for environment variables
"""
import secrets
import sys

def generate_jwt_secret():
    """Generate a secure JWT secret"""
    return secrets.token_urlsafe(32)

def generate_encryption_key():
    """Generate a secure encryption key (32 bytes)"""
    return secrets.token_urlsafe(32)

def main():
    print("🔐 Generating secure secrets...")
    print("")
    
    jwt_secret = generate_jwt_secret()
    encryption_key = generate_encryption_key()
    
    print("JWT_SECRET=" + jwt_secret)
    print("EXCHANGE_KEY_ENCRYPTION_KEY=" + encryption_key)
    print("")
    print("✅ Secrets generated successfully!")
    print("")
    print("Copy these values to your .env file:")
    print("  JWT_SECRET=" + jwt_secret)
    print("  EXCHANGE_KEY_ENCRYPTION_KEY=" + encryption_key)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
