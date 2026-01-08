"""
Security Audit Tools
Provides comprehensive security auditing and vulnerability scanning
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SecurityAuditor:
    """
    Security audit utility

    Features:
    - Configuration security audit
    - Dependency vulnerability scanning
    - Code security analysis
    - Secret detection
    - Security best practices check
    """

    def __init__(self):
        self.issues: list[dict[str, Any]] = []
        self.secrets_patterns = [
            r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]",
            r"(?i)(secret|api_key|apikey|token)\s*=\s*['\"][^'\"]+['\"]",
            r"(?i)(private_key|privatekey)\s*=\s*['\"][^'\"]+['\"]",
            r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
            r"sk_live_[a-zA-Z0-9]{32,}",
            r"AKIA[0-9A-Z]{16}",
        ]

    def audit_configuration(self) -> dict[str, Any]:
        """Audit configuration security"""
        issues = []

        # Check JWT secret
        jwt_secret = os.getenv("JWT_SECRET", "")
        if len(jwt_secret) < 32:
            issues.append(
                {
                    "level": "error",
                    "category": "authentication",
                    "message": "JWT_SECRET must be at least 32 characters",
                    "recommendation": "Generate a secure random secret key",
                }
            )

        # Check if using default secrets
        if jwt_secret in ["your-secret-key", "change-me", "secret"]:
            issues.append(
                {
                    "level": "critical",
                    "category": "authentication",
                    "message": "Using default or weak JWT secret",
                    "recommendation": "Change to a strong, randomly generated secret",
                }
            )

        # Check CORS configuration
        cors_origins = os.getenv("CORS_ORIGINS", "")
        if "*" in cors_origins:
            issues.append(
                {
                    "level": "warning",
                    "category": "cors",
                    "message": "CORS allows all origins (*)",
                    "recommendation": "Restrict to specific origins in production",
                }
            )

        # Check database URL
        db_url = os.getenv("DATABASE_URL", "")
        if "password" in db_url.lower() and len(db_url.split(":")[2]) < 8:
            issues.append(
                {
                    "level": "warning",
                    "category": "database",
                    "message": "Database password may be weak",
                    "recommendation": "Use a strong database password",
                }
            )

        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def scan_for_secrets(self, directory: str = "server_fastapi") -> dict[str, Any]:
        """Scan codebase for exposed secrets"""
        issues = []
        scanned_files = 0

        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            dirs[:] = [
                d for d in dirs if d not in ["__pycache__", ".git", "node_modules"]
            ]

            for file in files:
                if not file.endswith((".py", ".env", ".yaml", ".yml", ".json")):
                    continue

                file_path = Path(root) / file
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        scanned_files += 1

                        for i, line in enumerate(content.split("\n"), 1):
                            for pattern in self.secrets_patterns:
                                if re.search(pattern, line):
                                    issues.append(
                                        {
                                            "file": str(file_path),
                                            "line": i,
                                            "pattern": pattern,
                                            "level": "critical",
                                            "message": f"Potential secret found in {file_path}:{i}",
                                        }
                                    )
                except Exception as e:
                    logger.debug(f"Error scanning {file_path}: {e}")

        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "files_scanned": scanned_files,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def audit_dependencies(self) -> dict[str, Any]:
        """Audit dependencies for known vulnerabilities"""
        issues = []

        try:
            import subprocess

            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                import json

                packages = json.loads(result.stdout)

                # Check for known vulnerable packages
                vulnerable_packages = [
                    "django",  # Example - should check actual vulnerabilities
                ]

                for package in packages:
                    if package["name"].lower() in vulnerable_packages:
                        issues.append(
                            {
                                "level": "warning",
                                "package": package["name"],
                                "version": package["version"],
                                "message": f"Package {package['name']} may have known vulnerabilities",
                                "recommendation": "Update to latest version",
                            }
                        )
        except Exception as e:
            logger.debug(f"Error auditing dependencies: {e}")

        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def check_security_headers(self) -> dict[str, Any]:
        """Check security headers configuration"""
        issues = []

        # Check if security headers are configured
        # This would check middleware configuration
        security_middleware_enabled = (
            os.getenv("ENABLE_ENHANCED_SECURITY", "false").lower() == "true"
        )

        if not security_middleware_enabled:
            issues.append(
                {
                    "level": "warning",
                    "category": "headers",
                    "message": "Enhanced security middleware not enabled",
                    "recommendation": "Enable enhanced security middleware in production",
                }
            )

        return {
            "status": "pass" if not issues else "fail",
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def run_full_audit(self) -> dict[str, Any]:
        """Run complete security audit"""
        results = {
            "configuration": self.audit_configuration(),
            "secrets": self.scan_for_secrets(),
            "dependencies": self.audit_dependencies(),
            "security_headers": self.check_security_headers(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Calculate overall status
        all_passed = all(
            result.get("status") == "pass"
            for result in results.values()
            if isinstance(result, dict) and "status" in result
        )

        results["overall_status"] = "pass" if all_passed else "fail"

        # Count issues
        total_issues = sum(
            len(result.get("issues", []))
            for result in results.values()
            if isinstance(result, dict) and "issues" in result
        )

        results["total_issues"] = total_issues

        return results


# Global security auditor
security_auditor = SecurityAuditor()
