"""
Startup Configuration Validation
Validates all configuration and dependencies on application startup
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class StartupValidator:
    """
    Validates configuration and dependencies on startup

    Features:
    - Environment variable validation
    - Database connectivity check
    - Redis connectivity check
    - External service checks
    - Configuration validation
    - Dependency verification
    """

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks: list[dict[str, Any]] = []

    def validate_environment(self) -> tuple[bool, list[str]]:
        """Validate environment variables"""
        errors = []
        warnings = []

        # Required environment variables
        required_vars = {
            "DATABASE_URL": "Database connection URL",
            "JWT_SECRET": "JWT secret key (must be at least 32 characters)",
        }

        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                errors.append(
                    f"Missing required environment variable: {var} ({description})"
                )
            elif var == "JWT_SECRET" and len(value) < 32:
                errors.append("JWT_SECRET must be at least 32 characters")

        # Optional but recommended
        recommended_vars = {
            "REDIS_URL": "Redis connection URL (recommended for caching)",
            "SENTRY_DSN": "Sentry DSN for error tracking (recommended for production)",
        }

        for var, description in recommended_vars.items():
            if not os.getenv(var):
                warnings.append(
                    f"Missing recommended environment variable: {var} ({description})"
                )

        return len(errors) == 0, errors + warnings

    async def validate_database(self) -> tuple[bool, str]:
        """Validate database connectivity"""
        try:
            from sqlalchemy import text

            from ..database.session import get_db_context

            async with get_db_context() as session:
                await session.execute(text("SELECT 1"))
            return True, "Database connection successful"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    async def validate_redis(self) -> tuple[bool, str]:
        """Validate Redis connectivity"""
        redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        if not redis_enabled:
            return True, "Redis not enabled (skipped)"

        try:
            import redis.asyncio as redis

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            client = redis.from_url(redis_url)
            await client.ping()
            await client.close()
            return True, "Redis connection successful"
        except ImportError:
            return True, "Redis not installed (optional)"
        except Exception as e:
            return False, f"Redis connection failed: {str(e)}"

    async def validate_external_services(self) -> list[dict[str, Any]]:
        """Validate external service connectivity"""
        results = []

        # Check Sentry (if configured)
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            try:
                # Basic validation - check if DSN format is valid
                if sentry_dsn.startswith("https://"):
                    results.append(
                        {
                            "service": "Sentry",
                            "status": "configured",
                            "message": "Sentry DSN configured",
                        }
                    )
                else:
                    results.append(
                        {
                            "service": "Sentry",
                            "status": "error",
                            "message": "Invalid Sentry DSN format",
                        }
                    )
            except Exception as e:
                results.append(
                    {
                        "service": "Sentry",
                        "status": "error",
                        "message": f"Sentry validation failed: {str(e)}",
                    }
                )

        return results

    async def validate_all(self) -> dict[str, Any]:
        """Run all validation checks"""
        self.errors = []
        self.warnings = []
        self.checks = []

        # Environment validation
        env_valid, env_issues = self.validate_environment()
        if not env_valid:
            self.errors.extend(
                [issue for issue in env_issues if "Missing required" in issue]
            )
            self.warnings.extend(
                [issue for issue in env_issues if "Missing recommended" in issue]
            )

        self.checks.append(
            {
                "check": "Environment Variables",
                "status": "pass" if env_valid else "fail",
                "issues": env_issues,
            }
        )

        # Database validation
        db_valid, db_message = await self.validate_database()
        if not db_valid:
            self.errors.append(db_message)

        self.checks.append(
            {
                "check": "Database",
                "status": "pass" if db_valid else "fail",
                "message": db_message,
            }
        )

        # Redis validation
        redis_valid, redis_message = await self.validate_redis()
        if not redis_valid:
            self.warnings.append(redis_message)

        self.checks.append(
            {
                "check": "Redis",
                "status": "pass" if redis_valid else "warning",
                "message": redis_message,
            }
        )

        # External services
        external_results = await self.validate_external_services()
        self.checks.extend(external_results)

        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def log_results(self, results: dict[str, Any]):
        """Log validation results"""
        if results["valid"]:
            logger.info("Startup validation passed")
        else:
            logger.error("Startup validation failed")
            for error in results["errors"]:
                logger.error(f"  ERROR: {error}")

        if results["warnings"]:
            logger.warning("Startup validation warnings:")
            for warning in results["warnings"]:
                logger.warning(f"  WARNING: {warning}")

        for check in results["checks"]:
            status = check["status"]
            if status == "pass":
                logger.info(f"  ✓ {check['check']}: {check.get('message', 'OK')}")
            elif status == "warning":
                logger.warning(
                    f"  ⚠ {check['check']}: {check.get('message', 'WARNING')}"
                )
            else:
                logger.error(f"  ✗ {check['check']}: {check.get('message', 'FAILED')}")


# Global validator instance
startup_validator = StartupValidator()
