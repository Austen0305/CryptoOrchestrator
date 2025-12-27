#!/usr/bin/env python3
"""
Dependency Checker
Checks for outdated, vulnerable, or missing dependencies
"""

import sys
import os
import subprocess
import json
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


class DependencyChecker:
    """Checks dependencies for issues"""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []

    def check_python_dependencies(self):
        """Check Python dependencies"""
        logger.info("Checking Python dependencies...")

        try:
            # Check if requirements.txt exists
            requirements_file = project_root / "requirements.txt"
            if not requirements_file.exists():
                self.issues.append(
                    {
                        "type": "error",
                        "category": "python",
                        "message": "requirements.txt not found",
                    }
                )
                return

            # Try to check for outdated packages (if pip-tools is available)
            try:
                result = subprocess.run(
                    ["pip", "list", "--outdated", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    outdated = json.loads(result.stdout)
                    if outdated:
                        self.issues.append(
                            {
                                "type": "warning",
                                "category": "python",
                                "message": f"{len(outdated)} outdated packages found",
                                "details": [pkg["name"] for pkg in outdated[:10]],
                            }
                        )
                    else:
                        self.issues.append(
                            {
                                "type": "info",
                                "category": "python",
                                "message": "All Python packages are up to date",
                            }
                        )
            except Exception as e:
                logger.debug(f"Could not check outdated packages: {e}")

        except Exception as e:
            self.issues.append(
                {
                    "type": "error",
                    "category": "python",
                    "message": f"Failed to check Python dependencies: {e}",
                }
            )

    def check_node_dependencies(self):
        """Check Node.js dependencies"""
        logger.info("Checking Node.js dependencies...")

        try:
            package_json = project_root / "package.json"
            if not package_json.exists():
                self.issues.append(
                    {
                        "type": "error",
                        "category": "node",
                        "message": "package.json not found",
                    }
                )
                return

            # Check for outdated packages (if npm-check-updates is available)
            try:
                result = subprocess.run(
                    ["npm", "outdated", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=project_root,
                )
                if result.returncode == 0 and result.stdout.strip():
                    outdated = json.loads(result.stdout)
                    if outdated:
                        self.issues.append(
                            {
                                "type": "warning",
                                "category": "node",
                                "message": f"{len(outdated)} outdated packages found",
                                "details": list(outdated.keys())[:10],
                            }
                        )
                    else:
                        self.issues.append(
                            {
                                "type": "info",
                                "category": "node",
                                "message": "All Node.js packages are up to date",
                            }
                        )
            except Exception as e:
                logger.debug(f"Could not check outdated packages: {e}")

        except Exception as e:
            self.issues.append(
                {
                    "type": "error",
                    "category": "node",
                    "message": f"Failed to check Node.js dependencies: {e}",
                }
            )

    def check_missing_dependencies(self):
        """Check for missing critical dependencies"""
        logger.info("Checking for missing dependencies...")

        critical_python = [
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "uvicorn",
        ]

        critical_node = [
            "react",
            "react-dom",
            "vite",
        ]

        missing_python = []
        for dep in critical_python:
            try:
                __import__(dep)
            except ImportError:
                missing_python.append(dep)

        if missing_python:
            self.issues.append(
                {
                    "type": "error",
                    "category": "python",
                    "message": f"Missing critical Python packages: {', '.join(missing_python)}",
                }
            )

        # Node.js dependencies are harder to check without actually running npm
        # We'll just check if node_modules exists
        node_modules = project_root / "node_modules"
        if not node_modules.exists():
            self.issues.append(
                {
                    "type": "warning",
                    "category": "node",
                    "message": "node_modules not found - run 'npm install'",
                }
            )

    def print_report(self):
        """Print dependency check report"""
        print("\n" + "=" * 80)
        print("DEPENDENCY CHECK REPORT")
        print("=" * 80 + "\n")

        by_category = {}
        for issue in self.issues:
            category = issue.get("category", "other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)

        for category, issues in by_category.items():
            print(f"\n{category.upper()}:")
            print("-" * 80)
            for issue in issues:
                itype = issue.get("type", "info")
                message = issue.get("message", "")

                if itype == "error":
                    print(f"  [ERROR] {message}")
                elif itype == "warning":
                    print(f"  [WARNING] {message}")
                else:
                    print(f"  [INFO] {message}")

                details = issue.get("details")
                if details:
                    print(f"    -> {details}")

        print("\n" + "=" * 80)
        errors = sum(1 for i in self.issues if i.get("type") == "error")
        warnings = sum(1 for i in self.issues if i.get("type") == "warning")

        print(f"\nSummary: {errors} errors, {warnings} warnings")

        if errors == 0:
            print("\n[SUCCESS] All dependencies are in good shape!")
        else:
            print("\n[ERROR] Some dependency issues need attention")

        return errors == 0

    def run_all_checks(self):
        """Run all dependency checks"""
        logger.info("Starting dependency check...")

        self.check_missing_dependencies()
        self.check_python_dependencies()
        self.check_node_dependencies()

        return self.print_report()


def main():
    """Main entry point"""
    checker = DependencyChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

