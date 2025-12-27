#!/usr/bin/env python3
"""
Code Quality Checker
Checks code quality, style, and best practices
"""

import sys
import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class CodeQualityChecker:
    """Checks code quality and best practices"""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []

    def check_file(self, file_path: Path):
        """Check a single Python file for quality issues"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Check for common issues
            self._check_long_lines(file_path, lines)
            self._check_missing_docstrings(file_path, content)
            self._check_todo_comments(file_path, lines)
            self._check_error_handling(file_path, content)

        except Exception as e:
            logger.debug(f"Error checking {file_path}: {e}")

    def _check_long_lines(self, file_path: Path, lines: List[str]):
        """Check for lines that are too long"""
        for i, line in enumerate(lines, 1):
            if len(line) > 120:  # Common Python line length limit
                self.issues.append(
                    {
                        "type": "warning",
                        "category": "style",
                        "file": str(file_path.relative_to(project_root)),
                        "line": i,
                        "message": f"Line {i} exceeds 120 characters ({len(line)} chars)",
                    }
                )

    def _check_missing_docstrings(self, file_path: Path, content: str):
        """Check for missing docstrings in functions and classes"""
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        # Skip private methods and __init__ if class has docstring
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name.startswith("_") and node.name != "__init__":
                                continue
                        self.issues.append(
                            {
                                "type": "info",
                                "category": "documentation",
                                "file": str(file_path.relative_to(project_root)),
                                "line": node.lineno,
                                "message": f"{node.__class__.__name__} '{node.name}' missing docstring",
                            }
                        )
        except SyntaxError:
            # Skip files with syntax errors
            pass

    def _check_todo_comments(self, file_path: Path, lines: List[str]):
        """Check for TODO/FIXME comments"""
        for i, line in enumerate(lines, 1):
            if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line, re.IGNORECASE):
                self.issues.append(
                    {
                        "type": "info",
                        "category": "todo",
                        "file": str(file_path.relative_to(project_root)),
                        "line": i,
                        "message": f"TODO/FIXME found: {line.strip()[:80]}",
                    }
                )

    def _check_error_handling(self, file_path: Path, content: str):
        """Check for proper error handling"""
        # Check for bare except clauses
        if re.search(r"except\s*:", content):
            self.issues.append(
                {
                    "type": "warning",
                    "category": "error_handling",
                    "file": str(file_path.relative_to(project_root)),
                    "message": "Bare except clause found - should specify exception type",
                }
            )

    def check_routes_directory(self):
        """Check all route files"""
        logger.info("Checking route files...")

        routes_dir = project_root / "server_fastapi" / "routes"
        if not routes_dir.exists():
            return

        route_files = list(routes_dir.glob("*.py"))
        for route_file in route_files:
            if route_file.name != "__init__.py":
                self.check_file(route_file)

    def print_report(self):
        """Print code quality report"""
        print("\n" + "=" * 80)
        print("CODE QUALITY REPORT")
        print("=" * 80 + "\n")

        if not self.issues:
            print("[SUCCESS] No code quality issues found!")
            return True

        by_category = {}
        for issue in self.issues:
            category = issue.get("category", "other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(issue)

        for category, issues in by_category.items():
            print(f"\n{category.upper()}:")
            print("-" * 80)
            for issue in issues[:10]:  # Limit to first 10 per category
                itype = issue.get("type", "info")
                file = issue.get("file", "unknown")
                line = issue.get("line", "")
                message = issue.get("message", "")

                location = f"{file}:{line}" if line else file

                if itype == "error":
                    print(f"  [ERROR] {location}: {message}")
                elif itype == "warning":
                    print(f"  [WARNING] {location}: {message}")
                else:
                    print(f"  [INFO] {location}: {message}")

            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")

        print("\n" + "=" * 80)
        errors = sum(1 for i in self.issues if i.get("type") == "error")
        warnings = sum(1 for i in self.issues if i.get("type") == "warning")
        info = sum(1 for i in self.issues if i.get("type") == "info")

        print(f"\nSummary: {errors} errors, {warnings} warnings, {info} info messages")
        print(f"Total issues: {len(self.issues)}")

        if errors == 0:
            print("\n[SUCCESS] Code quality is good!")
        else:
            print("\n[WARNING] Some code quality issues found")

        return errors == 0

    def run_all_checks(self):
        """Run all code quality checks"""
        logger.info("Starting code quality check...")

        self.check_routes_directory()

        return self.print_report()


def main():
    """Main entry point"""
    checker = CodeQualityChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

