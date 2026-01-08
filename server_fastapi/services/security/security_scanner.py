"""
Automated security scanning service.
Integrates with OWASP ZAP, Bandit, and other security scanners.
"""

import json
import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Service for automated security scanning"""

    def __init__(self):
        self.scan_results: dict[str, Any] = {}

    async def run_bandit_scan(
        self, target_path: str = "server_fastapi"
    ) -> dict[str, Any]:
        """
        Run Bandit security scan on Python code.

        Returns:
            {
                "success": bool,
                "vulnerabilities": List[Dict],
                "summary": Dict
            }
        """
        try:
            # Run Bandit scan
            result = subprocess.run(
                [
                    "bandit",
                    "-r",
                    target_path,
                    "-f",
                    "json",
                    "-ll",  # Low and low (minimal output)
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                # Parse JSON output
                try:
                    bandit_data = json.loads(result.stdout)
                    vulnerabilities = bandit_data.get("results", [])

                    # Filter high/medium severity issues
                    high_severity = [
                        v
                        for v in vulnerabilities
                        if v.get("issue_severity") in ["HIGH", "MEDIUM"]
                    ]

                    return {
                        "success": True,
                        "vulnerabilities": high_severity,
                        "total_issues": len(vulnerabilities),
                        "high_severity_count": len(high_severity),
                        "summary": bandit_data.get("metrics", {}),
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "Failed to parse Bandit output",
                        "raw_output": result.stdout,
                    }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "exit_code": result.returncode,
                }

        except FileNotFoundError:
            logger.warning("Bandit not installed. Install with: pip install bandit")
            return {"success": False, "error": "Bandit not installed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Bandit scan timed out"}
        except Exception as e:
            logger.error(f"Bandit scan failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def run_dependency_scan(self) -> dict[str, Any]:
        """
        Scan dependencies for known vulnerabilities.
        Uses safety or pip-audit if available.
        """
        try:
            # Try pip-audit first (more comprehensive)
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                try:
                    audit_data = json.loads(result.stdout)
                    vulnerabilities = audit_data.get("vulnerabilities", [])

                    return {
                        "success": True,
                        "vulnerabilities": vulnerabilities,
                        "total_count": len(vulnerabilities),
                    }
                except json.JSONDecodeError:
                    # Try safety as fallback
                    return await self._run_safety_scan()
            else:
                return await self._run_safety_scan()

        except FileNotFoundError:
            # Fallback to safety
            return await self._run_safety_scan()
        except Exception as e:
            logger.error(f"Dependency scan failed: {e}")
            return {"success": False, "error": str(e)}

    async def _run_safety_scan(self) -> dict[str, Any]:
        """Run safety check for dependency vulnerabilities"""
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                try:
                    safety_data = json.loads(result.stdout)
                    return {
                        "success": True,
                        "vulnerabilities": safety_data,
                        "scanner": "safety",
                    }
                except json.JSONDecodeError:
                    # Safety may return empty if no vulnerabilities
                    return {"success": True, "vulnerabilities": [], "scanner": "safety"}
            else:
                # Safety returns non-zero if vulnerabilities found
                try:
                    safety_data = json.loads(result.stdout)
                    return {
                        "success": True,
                        "vulnerabilities": safety_data,
                        "scanner": "safety",
                    }
                except json.JSONDecodeError:
                    return {"success": False, "error": "Failed to parse safety output"}

        except FileNotFoundError:
            logger.warning("Safety not installed. Install with: pip install safety")
            return {"success": False, "error": "Safety not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_security_scan(self) -> dict[str, Any]:
        """Run comprehensive security scan"""
        results = {
            "bandit": await self.run_bandit_scan(),
            "dependencies": await self.run_dependency_scan(),
            "timestamp": str(datetime.now()),
        }

        # Calculate overall security score
        total_vulnerabilities = len(results["bandit"].get("vulnerabilities", [])) + len(
            results["dependencies"].get("vulnerabilities", [])
        )

        results["summary"] = {
            "total_vulnerabilities": total_vulnerabilities,
            "bandit_issues": results["bandit"].get("high_severity_count", 0),
            "dependency_issues": len(
                results["dependencies"].get("vulnerabilities", [])
            ),
            "security_score": (
                "high"
                if total_vulnerabilities == 0
                else "medium"
                if total_vulnerabilities < 5
                else "low"
            ),
        }

        return results


# Import datetime
from datetime import datetime
