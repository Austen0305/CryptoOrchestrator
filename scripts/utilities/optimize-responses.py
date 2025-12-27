#!/usr/bin/env python3
"""
Response Optimizer
Analyzes API responses and suggests optimizations
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import ast
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class ResponseOptimizer:
    """Analyzes and optimizes API responses"""

    def __init__(self):
        self.suggestions: List[Dict[str, Any]] = []

    def analyze_route(self, file_path: Path):
        """Analyze a route file for response optimization opportunities"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for missing caching
            if "@router.get" in content or "@router.post" in content:
                if "@cached" not in content and "@cache_query_result" not in content:
                    # Count list endpoints
                    if re.search(r"List\[|list\(|\.all\(\)", content):
                        self.suggestions.append(
                            {
                                "type": "optimization",
                                "file": str(file_path.relative_to(project_root)),
                                "message": "Consider adding @cached decorator for list endpoints",
                            }
                        )

            # Check for missing pagination
            if "List[" in content and "page" not in content.lower():
                self.suggestions.append(
                    {
                        "type": "optimization",
                        "file": str(file_path.relative_to(project_root)),
                        "message": "Consider adding pagination for list endpoints",
                    }
                )

        except Exception as e:
            logger.debug(f"Error analyzing {file_path}: {e}")

    def analyze_routes_directory(self):
        """Analyze all route files"""
        logger.info("Analyzing route files for optimization opportunities...")

        routes_dir = project_root / "server_fastapi" / "routes"
        if not routes_dir.exists():
            return

        route_files = list(routes_dir.glob("*.py"))
        for route_file in route_files:
            if route_file.name != "__init__.py":
                self.analyze_route(route_file)

    def print_report(self):
        """Print optimization report"""
        print("\n" + "=" * 80)
        print("RESPONSE OPTIMIZATION REPORT")
        print("=" * 80 + "\n")

        if not self.suggestions:
            print("[SUCCESS] No optimization opportunities found!")
            return True

        print(f"Found {len(self.suggestions)} optimization opportunities:\n")

        for suggestion in self.suggestions[:20]:  # Limit to first 20
            file = suggestion.get("file", "unknown")
            message = suggestion.get("message", "")

            print(f"  [OPTIMIZATION] {file}")
            print(f"    -> {message}\n")

        if len(self.suggestions) > 20:
            print(f"  ... and {len(self.suggestions) - 20} more\n")

        print("=" * 80)
        print(f"\nTotal suggestions: {len(self.suggestions)}")
        print("\n[INFO] These are suggestions - evaluate each one based on your needs")

        return True

    def run_analysis(self):
        """Run response optimization analysis"""
        logger.info("Starting response optimization analysis...")

        self.analyze_routes_directory()

        return self.print_report()


def main():
    """Main entry point"""
    optimizer = ResponseOptimizer()
    optimizer.run_analysis()
    sys.exit(0)


if __name__ == "__main__":
    main()

