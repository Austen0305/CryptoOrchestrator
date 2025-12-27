#!/usr/bin/env python3
"""
Performance Analyzer
Analyzes application performance and provides optimization recommendations
"""

import sys
import os
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Analyzes application performance and provides recommendations"""

    def __init__(self):
        self.findings: List[Dict[str, Any]] = []

    def analyze_imports(self):
        """Analyze import performance"""
        logger.info("Analyzing imports...")

        try:
            start_time = time.time()
            from server_fastapi.main import app
            import_time = time.time() - start_time

            if import_time > 5.0:
                self.findings.append(
                    {
                        "type": "warning",
                        "category": "imports",
                        "message": f"Slow application import: {import_time:.2f}s",
                        "recommendation": "Consider lazy loading heavy dependencies",
                    }
                )
            else:
                self.findings.append(
                    {
                        "type": "info",
                        "category": "imports",
                        "message": f"Application imports in {import_time:.2f}s",
                    }
                )
        except Exception as e:
            self.findings.append(
                {
                    "type": "error",
                    "category": "imports",
                    "message": f"Failed to import application: {e}",
                }
            )

    def analyze_routes(self):
        """Analyze route registration"""
        logger.info("Analyzing routes...")

        try:
            from server_fastapi.main import app

            routes = [r for r in app.routes if hasattr(r, "path")]
            route_count = len(routes)

            # Check for duplicate routes
            route_paths = {}
            duplicates = []
            for route in routes:
                path = getattr(route, "path", None)
                method = getattr(route, "methods", None)
                if path and method:
                    key = f"{list(method)[0] if method else 'GET'} {path}"
                    if key in route_paths:
                        duplicates.append(key)
                    else:
                        route_paths[key] = route

            if duplicates:
                self.findings.append(
                    {
                        "type": "warning",
                        "category": "routes",
                        "message": f"Found {len(duplicates)} duplicate routes",
                        "details": duplicates[:5],
                    }
                )
            else:
                self.findings.append(
                    {
                        "type": "info",
                        "category": "routes",
                        "message": f"{route_count} routes registered successfully",
                    }
                )

            # Check route complexity
            api_routes = [r for r in routes if hasattr(r, "path") and r.path.startswith("/api")]
            if len(api_routes) > 500:
                self.findings.append(
                    {
                        "type": "info",
                        "category": "routes",
                        "message": f"Large number of API routes: {len(api_routes)}",
                        "recommendation": "Consider route organization and versioning",
                    }
                )

        except Exception as e:
            self.findings.append(
                {
                    "type": "error",
                    "category": "routes",
                    "message": f"Failed to analyze routes: {e}",
                }
            )

    def analyze_caching(self):
        """Analyze caching configuration"""
        logger.info("Analyzing caching...")

        try:
            # Check Redis availability
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            if redis_url and redis_url != "redis://localhost:6379/0":
                self.findings.append(
                    {
                        "type": "info",
                        "category": "caching",
                        "message": "Redis configured",
                    }
                )
            else:
                self.findings.append(
                    {
                        "type": "warning",
                        "category": "caching",
                        "message": "Redis not configured, using in-memory cache",
                        "recommendation": "Configure Redis for production for better performance",
                    }
                )
        except Exception as e:
            self.findings.append(
                {
                    "type": "error",
                    "category": "caching",
                    "message": f"Failed to analyze caching: {e}",
                }
            )

    def analyze_database(self):
        """Analyze database configuration"""
        logger.info("Analyzing database...")

        try:
            database_url = os.getenv("DATABASE_URL", "")
            if not database_url:
                self.findings.append(
                    {
                        "type": "error",
                        "category": "database",
                        "message": "DATABASE_URL not configured",
                    }
                )
            elif "sqlite" in database_url.lower():
                self.findings.append(
                    {
                        "type": "warning",
                        "category": "database",
                        "message": "Using SQLite (development only)",
                        "recommendation": "Use PostgreSQL for production",
                    }
                )
            else:
                self.findings.append(
                    {
                        "type": "info",
                        "category": "database",
                        "message": "Database configured",
                    }
                )
        except Exception as e:
            self.findings.append(
                {
                    "type": "error",
                    "category": "database",
                    "message": f"Failed to analyze database: {e}",
                }
            )

    def print_report(self):
        """Print performance analysis report"""
        print("\n" + "=" * 80)
        print("PERFORMANCE ANALYSIS REPORT")
        print("=" * 80 + "\n")

        # Group findings by category
        by_category = {}
        for finding in self.findings:
            category = finding.get("category", "other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(finding)

        for category, findings in by_category.items():
            print(f"\n{category.upper()}:")
            print("-" * 80)
            for finding in findings:
                ftype = finding.get("type", "info")
                message = finding.get("message", "")
                recommendation = finding.get("recommendation")

                if ftype == "error":
                    print(f"  [ERROR] {message}")
                elif ftype == "warning":
                    print(f"  [WARNING] {message}")
                else:
                    print(f"  [INFO] {message}")

                if recommendation:
                    print(f"    -> Recommendation: {recommendation}")

                details = finding.get("details")
                if details:
                    print(f"    -> Details: {details}")

        print("\n" + "=" * 80)
        errors = sum(1 for f in self.findings if f.get("type") == "error")
        warnings = sum(1 for f in self.findings if f.get("type") == "warning")
        info = sum(1 for f in self.findings if f.get("type") == "info")

        print(f"\nSummary: {errors} errors, {warnings} warnings, {info} info messages")

        if errors == 0 and warnings == 0:
            print("\n[SUCCESS] No performance issues found!")
        elif errors == 0:
            print("\n[WARNING] Some optimizations recommended")
        else:
            print("\n[ERROR] Critical issues found")

        return errors == 0

    def run_all_checks(self):
        """Run all performance checks"""
        logger.info("Starting performance analysis...")

        self.analyze_imports()
        self.analyze_routes()
        self.analyze_caching()
        self.analyze_database()

        return self.print_report()


def main():
    """Main entry point"""
    analyzer = PerformanceAnalyzer()
    success = analyzer.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

