#!/usr/bin/env python3
"""
Secrets Management Utility
Handles secret rotation, validation, and secure storage.
Supports AWS Secrets Manager, HashiCorp Vault, and local .env files.
"""

import os
import json
import secrets
import base64
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False


class SecretsManager:
    """Unified secrets management interface."""
    
    def __init__(
        self,
        provider: str = "local",
        aws_region: Optional[str] = None,
        vault_url: Optional[str] = None,
        vault_token: Optional[str] = None
    ):
        self.provider = provider
        self.aws_region = aws_region or os.getenv("AWS_REGION", "us-east-1")
        self.vault_url = vault_url or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        
        if provider == "aws" and AWS_AVAILABLE:
            self.client = boto3.client("secretsmanager", region_name=self.aws_region)
        elif provider == "vault" and VAULT_AVAILABLE:
            self.client = hvac.Client(url=self.vault_url, token=self.vault_token)
        else:
            self.client = None
    
    def generate_secret(self, length: int = 32) -> str:
        """Generate a cryptographically secure random secret."""
        return secrets.token_urlsafe(length)
    
    def generate_jwt_secret(self) -> str:
        """Generate JWT secret."""
        return self.generate_secret(64)
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret value."""
        if self.provider == "local":
            return os.getenv(key)
        elif self.provider == "aws" and self.client:
            try:
                response = self.client.get_secret_value(SecretId=key)
                return response["SecretString"]
            except ClientError as e:
                print(f"Error retrieving secret {key}: {e}")
                return None
        elif self.provider == "vault" and self.client:
            try:
                response = self.client.secrets.kv.v2.read_secret_version(path=key)
                return response["data"]["data"].get("value")
            except Exception as e:
                print(f"Error retrieving secret {key}: {e}")
                return None
        return None
    
    def set_secret(self, key: str, value: str, description: Optional[str] = None) -> bool:
        """Set secret value."""
        if self.provider == "local":
            # Update .env file
            env_file = Path(".env")
            if env_file.exists():
                content = env_file.read_text()
                lines = content.split("\n")
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                        updated = True
                        break
                if not updated:
                    lines.append(f"{key}={value}")
                env_file.write_text("\n".join(lines))
            else:
                env_file.write_text(f"{key}={value}\n")
            return True
        elif self.provider == "aws" and self.client:
            try:
                # Check if secret exists
                try:
                    self.client.describe_secret(SecretId=key)
                    # Update existing secret
                    self.client.put_secret_value(
                        SecretId=key,
                        SecretString=value
                    )
                except ClientError as e:
                    if e.response["Error"]["Code"] == "ResourceNotFoundException":
                        # Create new secret
                        self.client.create_secret(
                            Name=key,
                            SecretString=value,
                            Description=description or f"Secret for {key}"
                        )
                    else:
                        raise
                return True
            except ClientError as e:
                print(f"Error setting secret {key}: {e}")
                return False
        elif self.provider == "vault" and self.client:
            try:
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=key,
                    secret={"value": value}
                )
                return True
            except Exception as e:
                print(f"Error setting secret {key}: {e}")
                return False
        return False
    
    def rotate_secret(self, key: str) -> Optional[str]:
        """Rotate a secret and return the new value."""
        new_value = self.generate_secret()
        if self.set_secret(key, new_value, description=f"Rotated on {datetime.now().isoformat()}"):
            return new_value
        return None
    
    def rotate_jwt_secret(self) -> Optional[str]:
        """Rotate JWT secret."""
        return self.rotate_secret("JWT_SECRET")
    
    def rotate_all_secrets(self) -> Dict[str, bool]:
        """Rotate all secrets defined in secrets list."""
        secrets_to_rotate = [
            "JWT_SECRET",
            "DATABASE_URL",
            "REDIS_URL",
            "STRIPE_SECRET_KEY",
            "SENTRY_DSN",
        ]
        
        results = {}
        for secret_key in secrets_to_rotate:
            current = self.get_secret(secret_key)
            if current:
                new_value = self.rotate_secret(secret_key)
                results[secret_key] = new_value is not None
            else:
                results[secret_key] = False
        
        return results
    
    def validate_secrets(self, required_secrets: list) -> Dict[str, bool]:
        """Validate that all required secrets exist."""
        results = {}
        for secret_key in required_secrets:
            value = self.get_secret(secret_key)
            results[secret_key] = value is not None and len(value) > 0
        return results


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secrets management utility")
    parser.add_argument("action", choices=["get", "set", "rotate", "validate", "generate"])
    parser.add_argument("--key", help="Secret key")
    parser.add_argument("--value", help="Secret value (for set action)")
    parser.add_argument("--provider", choices=["local", "aws", "vault"], default="local")
    parser.add_argument("--all", action="store_true", help="Operate on all secrets")
    
    args = parser.parse_args()
    
    manager = SecretsManager(provider=args.provider)
    
    if args.action == "get":
        if args.key:
            value = manager.get_secret(args.key)
            if value:
                print(value)
            else:
                print(f"Secret {args.key} not found", file=sys.stderr)
                exit(1)
        else:
            print("--key required for get action", file=sys.stderr)
            exit(1)
    
    elif args.action == "set":
        if args.key and args.value:
            if manager.set_secret(args.key, args.value):
                print(f"✓ Set {args.key}")
            else:
                print(f"✗ Failed to set {args.key}", file=sys.stderr)
                exit(1)
        else:
            print("--key and --value required for set action", file=sys.stderr)
            exit(1)
    
    elif args.action == "rotate":
        if args.key:
            new_value = manager.rotate_secret(args.key)
            if new_value:
                print(f"✓ Rotated {args.key}: {new_value}")
            else:
                print(f"✗ Failed to rotate {args.key}", file=sys.stderr)
                exit(1)
        elif args.all:
            results = manager.rotate_all_secrets()
            for key, success in results.items():
                status = "✓" if success else "✗"
                print(f"{status} {key}")
        else:
            print("--key or --all required for rotate action", file=sys.stderr)
            exit(1)
    
    elif args.action == "validate":
        required = ["JWT_SECRET", "DATABASE_URL"]
        results = manager.validate_secrets(required)
        all_valid = all(results.values())
        for key, valid in results.items():
            status = "✓" if valid else "✗"
            print(f"{status} {key}")
        exit(0 if all_valid else 1)
    
    elif args.action == "generate":
        secret = manager.generate_secret()
        print(secret)


if __name__ == "__main__":
    import sys
    main()

