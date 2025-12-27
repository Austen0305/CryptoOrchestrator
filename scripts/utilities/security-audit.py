#!/usr/bin/env python3
"""
Security Audit Utility
Checks for common security issues and vulnerabilities
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class SecurityAuditor:
    """Audits code for security issues"""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []

    def check_file(self, file_path: Path):
        """Check a file for security issues"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Check for hardcoded secrets
            self._check_hardcoded_secrets(file_path, lines)
            
            # Check for SQL injection risks
            self._check_sql_injection(file_path, content)
            
            # Check for XSS risks
            self._check_xss_risks(file_path, content)
            
            # Check for insecure random
            self._check_insecure_random(file_path, content)
            
            # Check for weak cryptography
            self._check_weak_crypto(file_path, content)

        except Exception as e:
            logger.debug(f"Error checking {file_path}: {e}")

    def _check_hardcoded_secrets(self, file_path: Path, lines: List[str]):
        """Check for hardcoded secrets"""
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
            (r'private[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded private key"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, message in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if it's a comment or example
                    if not line.strip().startswith("#") and "example" not in line.lower() and "TODO" not in line:
                        self.issues.append({
                            "type": "error",
                            "category": "secrets",
                            "file": str(file_path.relative_to(project_root)),
                            "line": i,
                            "message": message,
                            "code": line.strip()[:80],
                        })

    def _check_sql_injection(self, file_path: Path, content: str):
        """Check for SQL injection risks"""
        # Check for raw SQL with string formatting
        if re.search(r'execute\s*\(\s*f["\']', content) or re.search(r'execute\s*\(\s*["\'].*%', content):
            self.issues.append({
                "type": "warning",
                "category": "sql_injection",
                "file": str(file_path.relative_to(project_root)),
                "message": "Potential SQL injection risk - use parameterized queries",
            })

    def _check_xss_risks(self, file_path: Path, content: str):
        """Check for XSS risks"""
        # Check for unescaped user input in HTML
        if "render_template" in content or "Response" in content:
            if re.search(r'\{[^}]*user[^}]*\}', content, re.IGNORECASE):
                self.issues.append({
                    "type": "info",
                    "category": "xss",
                    "file": str(file_path.relative_to(project_root)),
                    "message": "Verify user input is properly escaped in templates",
                })

    def _check_insecure_random(self, file_path: Path, content: str):
        """Check for insecure random number generation"""
        if "import random" in content and "secrets" not in content:
            if re.search(r'random\.(randint|choice|random)', content):
                self.issues.append({
                    "type": "warning",
                    "category": "crypto",
                    "file": str(file_path.relative_to(project_root)),
                    "message": "Use secrets module instead of random for cryptographic operations",
                })

    def _check_weak_crypto(self, file_path: Path, content: str):
        """Check for weak cryptography"""
        if "md5" in content.lower() or "sha1" in content.lower():
            if "hashlib" in content:
                self.issues.append({
                    "type": "warning",
                    "category": "crypto",
                    "file": str(file_path.relative_to(project_root)),
                    "message": "MD5 and SHA1 are weak - use SHA256 or better",
                })

    def check_routes_directory(self):
        """Check all route files"""
        logger.info("Checking route files for security issues...")

        routes_dir = project_root / "server_fastapi" / "routes"
        if routes_dir.exists():
            for route_file in routes_dir.glob("*.py"):
                if route_file.name != "__init__.py":
                    self.check_file(route_file)

    def check_services_directory(self):
        """Check all service files"""
        logger.info("Checking service files for security issues...")

        services_dir = project_root / "server_fastapi" / "services"
        if services_dir.exists():
            for service_file in services_dir.rglob("*.py"):
                if service_file.name != "__init__.py":
                    self.check_file(service_file)

    def print_report(self):
        """Print security audit report"""
        print("\n" + "=" * 80)
        print("SECURITY AUDIT REPORT")
        print("=" * 80 + "\n")

        if not self.issues:
            print("[SUCCESS] No security issues found!")
            return True

        by_category = {}
        for issue in self.issues:
            category = issue.get("category", "other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)

        for category, issues in by_category.items():
            print(f"{category.upper().replace('_', ' ')}:")
            print("-" * 80)
            for issue in issues[:10]:
                itype = issue.get("type", "info")
                file = issue.get("file", "unknown")
                line = issue.get("line", "")
                message = issue.get("message", "")
                code = issue.get("code", "")

                location = f"{file}:{line}" if line else file

                if itype == "error":
                    print(f"  [ERROR] {location}: {message}")
                elif itype == "warning":
                    print(f"  [WARNING] {location}: {message}")
                else:
                    print(f"  [INFO] {location}: {message}")

                if code:
                    print(f"    -> {code}")

            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")

            print()

        print("=" * 80)
        errors = sum(1 for i in self.issues if i.get("type") == "error")
        warnings = sum(1 for i in self.issues if i.get("type") == "warning")
        info = sum(1 for i in self.issues if i.get("type") == "info")

        print(f"\nSummary: {errors} errors, {warnings} warnings, {info} info messages")

        if errors == 0:
            print("\n[SUCCESS] No critical security issues found!")
        else:
            print("\n[ERROR] Critical security issues need attention!")

        return errors == 0

    def run_audit(self):
        """Run security audit"""
        logger.info("Starting security audit...")

        self.check_routes_directory()
        self.check_services_directory()

        return self.print_report()


def main():
    """Main entry point"""
    auditor = SecurityAuditor()
    success = auditor.run_audit()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

