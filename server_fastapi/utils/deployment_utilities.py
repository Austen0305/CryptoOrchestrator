"""
Deployment Utilities
Provides utilities for deployment, health checks, and rollback
"""

import logging
import os
import subprocess
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class DeploymentManager:
    """
    Deployment management utility
    
    Features:
    - Health check validation
    - Deployment verification
    - Rollback support
    - Version tracking
    - Configuration validation
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.deployment_history: List[Dict[str, Any]] = []

    async def health_check(self, timeout: int = 10) -> Dict[str, Any]:
        """Perform health check"""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return {
                    "status": "healthy",
                    "response": response.json(),
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def verify_deployment(self) -> Dict[str, Any]:
        """Verify deployment is working correctly"""
        checks = {
            "health": await self.health_check(),
            "api": await self._check_api(),
            "database": await self._check_database(),
            "redis": await self._check_redis(),
        }

        all_healthy = all(
            check.get("status") == "healthy" for check in checks.values()
        )

        return {
            "status": "success" if all_healthy else "failed",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _check_api(self) -> Dict[str, Any]:
        """Check API endpoints"""
        try:
            async with httpx.AsyncClient() as client:
                # Check docs endpoint
                response = await client.get(f"{self.base_url}/docs")
                if response.status_code == 200:
                    return {"status": "healthy", "message": "API accessible"}
                else:
                    return {"status": "unhealthy", "message": f"API returned {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health/database")
                if response.status_code == 200:
                    return {"status": "healthy", "message": "Database accessible"}
                else:
                    return {"status": "unhealthy", "message": "Database check failed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health/redis")
                if response.status_code == 200:
                    return {"status": "healthy", "message": "Redis accessible"}
                else:
                    return {"status": "degraded", "message": "Redis not available (optional)"}
        except Exception:
            return {"status": "degraded", "message": "Redis not available (optional)"}

    def record_deployment(
        self,
        version: str,
        environment: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Record deployment"""
        deployment = {
            "version": version,
            "environment": environment,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        self.deployment_history.append(deployment)

        # Save to file
        history_file = Path("deployment_history.json")
        with open(history_file, "w") as f:
            json.dump(self.deployment_history, f, indent=2)

        logger.info(f"Deployment recorded: {version} to {environment} - {status}")

    def get_deployment_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get deployment history"""
        return self.deployment_history[-limit:]


class EnvironmentValidator:
    """Validates deployment environment"""

    @staticmethod
    def validate_production() -> Dict[str, Any]:
        """Validate production environment"""
        errors = []
        warnings = []

        # Required environment variables
        required = [
            "DATABASE_URL",
            "JWT_SECRET",
            "NODE_ENV",
        ]

        for var in required:
            if not os.getenv(var):
                errors.append(f"Missing required environment variable: {var}")

        # Security checks
        jwt_secret = os.getenv("JWT_SECRET", "")
        if len(jwt_secret) < 32:
            errors.append("JWT_SECRET must be at least 32 characters")

        if os.getenv("NODE_ENV") != "production":
            warnings.append("NODE_ENV is not set to 'production'")

        # Recommended
        if not os.getenv("SENTRY_DSN"):
            warnings.append("SENTRY_DSN not set (recommended for production)")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


def create_deployment_package(output_dir: str = "deploy"):
    """Create deployment package"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Copy necessary files
    files_to_copy = [
        "server_fastapi",
        "requirements.txt",
        ".env.example",
        "docker-compose.yml",
        "Dockerfile",
    ]

    for file_path in files_to_copy:
        src = Path(file_path)
        if src.exists():
            if src.is_dir():
                # Copy directory
                import shutil
                dst = output_path / src.name
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                # Copy file
                import shutil
                shutil.copy2(src, output_path / src.name)

    logger.info(f"Deployment package created: {output_dir}")


# Global instances
deployment_manager = DeploymentManager()
environment_validator = EnvironmentValidator()

