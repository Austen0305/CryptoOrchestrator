"""
Environment Variable Validation
Validates required environment variables on startup
"""

import os
import sys
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class EnvValidationError(Exception):
    """Raised when environment validation fails"""

    pass


def validate_required_vars(
    required_vars: List[str], exit_on_error: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate that required environment variables are set.

    Args:
        required_vars: List of required environment variable names
        exit_on_error: If True, exit application on validation failure

    Returns:
        Tuple of (is_valid, missing_vars)
    """
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing_vars.append(var)

    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)

        if exit_on_error:
            print(f"\n[ERROR] ERROR: {error_msg}", file=sys.stderr)
            print("\nPlease set the following environment variables:", file=sys.stderr)
            for var in missing_vars:
                print(f"  - {var}", file=sys.stderr)
            print("\nSee docs/ENV_VARIABLES.md for documentation.", file=sys.stderr)
            sys.exit(1)

        return False, missing_vars

    return True, []


def validate_secret_strength(
    var_name: str, min_length: int = 32, exit_on_error: bool = True
) -> bool:
    """
    Validate that a secret environment variable meets strength requirements.

    Args:
        var_name: Environment variable name
        min_length: Minimum length requirement
        exit_on_error: If True, exit application on validation failure

    Returns:
        True if valid, False otherwise
    """
    value = os.getenv(var_name)

    if not value:
        if exit_on_error:
            logger.error(f"Missing required secret: {var_name}")
            print(
                f"\n[ERROR] ERROR: Missing required secret: {var_name}", file=sys.stderr
            )
            sys.exit(1)
        return False

    if len(value) < min_length:
        error_msg = f"Secret {var_name} is too short (minimum {min_length} characters)"
        logger.error(error_msg)

        if exit_on_error:
            print(f"\n[ERROR] ERROR: {error_msg}", file=sys.stderr)
            print(f"Current length: {len(value)}", file=sys.stderr)
            sys.exit(1)

        return False

    # Check for common weak secrets
    weak_secrets = [
        "your-secret-key-change-in-production",
        "dev-secret-change-me-in-production",
        "change-me",
        "secret",
        "password",
        "123456",
    ]

    if value.lower() in weak_secrets:
        error_msg = f"Secret {var_name} uses a default/weak value. Please change it!"
        logger.error(error_msg)

        if exit_on_error:
            print(f"\n[ERROR] ERROR: {error_msg}", file=sys.stderr)
            sys.exit(1)

        return False

    return True


def validate_database_url(exit_on_error: bool = True) -> bool:
    """
    Validate DATABASE_URL format.

    Args:
        exit_on_error: If True, exit application on validation failure

    Returns:
        True if valid, False otherwise
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        if exit_on_error:
            logger.error("DATABASE_URL is required")
            print("\n[ERROR] ERROR: DATABASE_URL is required", file=sys.stderr)
            sys.exit(1)
        return False

    # Check for common mistakes
    if "localhost" in db_url and os.getenv("NODE_ENV") == "production":
        logger.warning(
            "DATABASE_URL uses localhost in production - this may be incorrect"
        )

    if "password" in db_url.lower() and "change" in db_url.lower():
        error_msg = "DATABASE_URL appears to contain placeholder password"
        logger.error(error_msg)

        if exit_on_error:
            print(f"\n[ERROR] ERROR: {error_msg}", file=sys.stderr)
            sys.exit(1)

        return False

    return True


def validate_dex_config(exit_on_error: bool = True) -> bool:
    """
    Validate DEX trading configuration.

    Args:
        exit_on_error: If True, exit application on validation failure

    Returns:
        True if valid, False otherwise
    """
    enable_dex = os.getenv("ENABLE_DEX_TRADING", "true").lower() == "true"

    if not enable_dex:
        logger.info("DEX trading is disabled, skipping DEX config validation")
        return True

    # Check if at least one DEX aggregator API key is configured
    zerox_key = os.getenv("ZEROX_API_KEY")
    okx_key = os.getenv("OKX_API_KEY")
    rubic_key = os.getenv("RUBIC_API_KEY")

    if not any([zerox_key, okx_key, rubic_key]):
        warning_msg = "DEX trading is enabled but no aggregator API keys are configured. At least one of ZEROX_API_KEY, OKX_API_KEY, or RUBIC_API_KEY should be set."
        logger.warning(warning_msg)

        if exit_on_error and os.getenv("NODE_ENV") == "production":
            print(f"\n[WARN]  WARNING: {warning_msg}", file=sys.stderr)
            print(
                "DEX trading may not work properly without API keys.", file=sys.stderr
            )
            # Don't exit, just warn - DEX trading can work with public endpoints

    return True


def validate_blockchain_rpc(exit_on_error: bool = True) -> bool:
    """
    Validate blockchain RPC URLs.

    Args:
        exit_on_error: If True, exit application on validation failure

    Returns:
        True if valid, False otherwise
    """
    enable_dex = os.getenv("ENABLE_DEX_TRADING", "true").lower() == "true"

    if not enable_dex:
        logger.info("DEX trading is disabled, skipping RPC validation")
        return True

    # Check if at least one RPC URL is configured
    rpc_urls = [
        os.getenv("ETHEREUM_RPC_URL"),
        os.getenv("BASE_RPC_URL"),
        os.getenv("ARBITRUM_RPC_URL"),
        os.getenv("POLYGON_RPC_URL"),
    ]

    if not any(rpc_urls):
        warning_msg = "No blockchain RPC URLs configured. DEX trading requires at least one RPC URL (ETHEREUM_RPC_URL, BASE_RPC_URL, etc.)"
        logger.warning(warning_msg)

        if exit_on_error and os.getenv("NODE_ENV") == "production":
            print(f"\n[WARN]  WARNING: {warning_msg}", file=sys.stderr)
            print("DEX trading will not work without RPC URLs.", file=sys.stderr)
            # Don't exit, just warn - public RPCs might be used as fallback

    return True


def validate_all(exit_on_error: bool = True) -> bool:
    """
    Validate all critical environment variables.

    Args:
        exit_on_error: If True, exit application on validation failure

    Returns:
        True if all validations pass, False otherwise
    """
    is_production = os.getenv("NODE_ENV") == "production"

    # Required variables (always)
    required_vars = ["DATABASE_URL"]

    # Production-only required variables
    if is_production:
        required_vars.extend(
            [
                "JWT_SECRET",
                "EXCHANGE_KEY_ENCRYPTION_KEY",
            ]
        )

    # Validate required variables
    is_valid, missing = validate_required_vars(required_vars, exit_on_error=False)
    if not is_valid:
        if exit_on_error:
            validate_required_vars(required_vars, exit_on_error=True)
        return False

    # Validate secret strength in production
    if is_production:
        if not validate_secret_strength(
            "JWT_SECRET", min_length=32, exit_on_error=False
        ):
            if exit_on_error:
                validate_secret_strength(
                    "JWT_SECRET", min_length=32, exit_on_error=True
                )
            return False

        if not validate_secret_strength(
            "EXCHANGE_KEY_ENCRYPTION_KEY", min_length=32, exit_on_error=False
        ):
            if exit_on_error:
                validate_secret_strength(
                    "EXCHANGE_KEY_ENCRYPTION_KEY", min_length=32, exit_on_error=True
                )
            return False

    # Validate database URL
    if not validate_database_url(exit_on_error=False):
        if exit_on_error:
            validate_database_url(exit_on_error=True)
        return False

    # Validate DEX configuration
    if not validate_dex_config(exit_on_error=False):
        if exit_on_error:
            validate_dex_config(exit_on_error=True)
        return False

    # Validate blockchain RPC URLs
    if not validate_blockchain_rpc(exit_on_error=False):
        if exit_on_error:
            validate_blockchain_rpc(exit_on_error=True)
        return False

    logger.info("[OK] Environment variable validation passed")
    return True


# Auto-validate on import in production
if os.getenv("NODE_ENV") == "production" and os.getenv("SKIP_ENV_VALIDATION") != "true":
    try:
        validate_all(exit_on_error=True)
    except SystemExit:
        raise
    except Exception as e:
        logger.warning(f"Environment validation failed: {e}")
