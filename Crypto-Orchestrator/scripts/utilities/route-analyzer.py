#!/usr/bin/env python3
"""
Route Analyzer
Analyzes routes for common issues, duplicates, and optimization opportunities
"""

import sys
import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class RouteAnalyzer:
    """Analyzes routes for issues and optimizations"""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.routes: Dict[str, List[str]] = defaultdict(list)
        self.missing_error_handling: List[str] = []
        self.missing_caching: List[str] = []
        self.missing_pagination: List[str] = []

    def analyze_route_file(self, file_path: Path):
        """Analyze a single route file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                logger.debug(f"Could not parse {file_path}")
                return

            # Find route definitions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._analyze_function(node, file_path, content)

        except Exception as e:
            logger.debug(f"Error analyzing {file_path}: {e}")

    def _analyze_function(self, node: ast.FunctionDef, file_path: Path, content: str):
        """Analyze a function for route patterns"""
        # Check if it's a route handler (has decorators)
        decorators = [d.id if isinstance(d, ast.Name) else None for d in node.decorator_list]
        
        if any(d in ["router.get", "router.post", "router.put", "router.delete", "router.patch"] for d in decorators if d):
            # Extract route path from decorator
            route_path = self._extract_route_path(node.decorator_list, content)
            method = self._extract_method(node.decorator_list)
            
            if route_path and method:
                key = f"{method} {route_path}"
                self.routes[key].append(f"{file_path.name}:{node.lineno}")

            # Check for error handling
            if not self._has_error_handling(node):
                self.missing_error_handling.append(
                    f"{file_path.name}:{node.name}:{node.lineno}"
                )

            # Check for caching (if it's a GET endpoint)
            if method == "GET" and "@cached" not in content.split("\n")[node.lineno - 10:node.lineno]:
                # Check if it returns a list
                if self._returns_list(node):
                    self.missing_caching.append(
                        f"{file_path.name}:{node.name}:{node.lineno}"
                    )

            # Check for pagination (if it returns a list)
            if self._returns_list(node) and "page" not in content.split("\n")[node.lineno - 5:node.lineno + 20].lower():
                self.missing_pagination.append(
                    f"{file_path.name}:{node.name}:{node.lineno}"
                )

    def _extract_route_path(self, decorators: List[ast.expr], content: str) -> str:
        """Extract route path from decorator"""
        for decorator in decorators:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ["get", "post", "put", "delete", "patch"]:
                        if decorator.args:
                            if isinstance(decorator.args[0], ast.Constant):
                                return decorator.args[0].value
        return ""

    def _extract_method(self, decorators: List[ast.expr]) -> str:
        """Extract HTTP method from decorator"""
        for decorator in decorators:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    method = decorator.func.attr.upper()
                    if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        return method
        return ""

    def _has_error_handling(self, node: ast.FunctionDef) -> bool:
        """Check if function has error handling"""
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                return True
        return False

    def _returns_list(self, node: ast.FunctionDef) -> bool:
        """Check if function likely returns a list"""
        # Simple heuristic: check for List in return type annotation
        if node.returns:
            if isinstance(node.returns, ast.Subscript):
                if isinstance(node.returns.value, ast.Name):
                    if node.returns.value.id == "List":
                        return True
        return False

    def analyze_routes_directory(self):
        """Analyze all route files"""
        logger.info("Analyzing route files...")

        routes_dir = project_root / "server_fastapi" / "routes"
        if not routes_dir.exists():
            return

        route_files = list(routes_dir.glob("*.py"))
        for route_file in route_files:
            if route_file.name != "__init__.py":
                self.analyze_route_file(route_file)

    def print_report(self):
        """Print analysis report"""
        print("\n" + "=" * 80)
        print("ROUTE ANALYSIS REPORT")
        print("=" * 80 + "\n")

        # Duplicate routes
        duplicates = {k: v for k, v in self.routes.items() if len(v) > 1}
        if duplicates:
            print(f"DUPLICATE ROUTES ({len(duplicates)}):")
            print("-" * 80)
            for route, locations in list(duplicates.items())[:10]:
                print(f"  {route}")
                for loc in locations:
                    print(f"    -> {loc}")
            if len(duplicates) > 10:
                print(f"  ... and {len(duplicates) - 10} more")
            print()

        # Missing error handling
        if self.missing_error_handling:
            print(f"MISSING ERROR HANDLING ({len(self.missing_error_handling)}):")
            print("-" * 80)
            for item in self.missing_error_handling[:10]:
                print(f"  {item}")
            if len(self.missing_error_handling) > 10:
                print(f"  ... and {len(self.missing_error_handling) - 10} more")
            print()

        # Missing caching
        if self.missing_caching:
            print(f"MISSING CACHING ({len(self.missing_caching)}):")
            print("-" * 80)
            for item in self.missing_caching[:10]:
                print(f"  {item}")
            if len(self.missing_caching) > 10:
                print(f"  ... and {len(self.missing_caching) - 10} more")
            print()

        # Missing pagination
        if self.missing_pagination:
            print(f"MISSING PAGINATION ({len(self.missing_pagination)}):")
            print("-" * 80)
            for item in self.missing_pagination[:10]:
                print(f"  {item}")
            if len(self.missing_pagination) > 10:
                print(f"  ... and {len(self.missing_pagination) - 10} more")
            print()

        print("=" * 80)
        print(f"\nSummary:")
        print(f"  Duplicate routes: {len(duplicates)}")
        print(f"  Missing error handling: {len(self.missing_error_handling)}")
        print(f"  Missing caching: {len(self.missing_caching)}")
        print(f"  Missing pagination: {len(self.missing_pagination)}")

        return len(duplicates) == 0 and len(self.missing_error_handling) == 0

    def run_analysis(self):
        """Run route analysis"""
        logger.info("Starting route analysis...")

        self.analyze_routes_directory()

        return self.print_report()


def main():
    """Main entry point"""
    analyzer = RouteAnalyzer()
    analyzer.run_analysis()
    sys.exit(0)


if __name__ == "__main__":
    main()

