#!/usr/bin/env python3
"""
Test Coverage Analyzer
Analyzes test coverage and identifies untested code
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class TestCoverageAnalyzer:
    """Analyzes test coverage"""

    def __init__(self):
        self.coverage_data: Dict[str, Any] = {}
        self.untested_files: List[str] = []

    def run_coverage(self):
        """Run test coverage"""
        logger.info("Running test coverage...")

        try:
            result = subprocess.run(
                ["pytest", "server_fastapi/tests/", "--cov=server_fastapi", "--cov-report=term-missing", "--cov-report=json"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=project_root,
            )

            if result.returncode == 0:
                # Try to read coverage JSON
                coverage_file = project_root / "coverage.json"
                if coverage_file.exists():
                    import json
                    with open(coverage_file, "r") as f:
                        self.coverage_data = json.load(f)
                return True
            else:
                logger.warning("Test coverage run had issues")
                return False

        except subprocess.TimeoutExpired:
            logger.warning("Test coverage run timed out")
            return False
        except Exception as e:
            logger.warning(f"Could not run test coverage: {e}")
            return False

    def analyze_coverage(self):
        """Analyze coverage data"""
        if not self.coverage_data:
            logger.info("No coverage data available - run tests first")
            return

        files = self.coverage_data.get("files", {})
        
        for file_path, data in files.items():
            coverage = data.get("summary", {}).get("percent_covered", 0)
            if coverage < 80:  # Threshold
                self.untested_files.append({
                    "file": file_path,
                    "coverage": coverage,
                    "missing_lines": data.get("missing_lines", []),
                })

    def print_report(self):
        """Print coverage report"""
        print("\n" + "=" * 80)
        print("TEST COVERAGE REPORT")
        print("=" * 80 + "\n")

        if not self.coverage_data:
            print("[INFO] No coverage data available")
            print("Run: pytest server_fastapi/tests/ --cov=server_fastapi --cov-report=json")
            return True

        total = self.coverage_data.get("totals", {})
        percent = total.get("percent_covered", 0)

        print(f"Overall Coverage: {percent:.1f}%")
        print(f"Lines Covered: {total.get('covered_lines', 0)}")
        print(f"Lines Missing: {total.get('missing_lines', 0)}")
        print()

        if self.untested_files:
            print(f"FILES WITH LOW COVERAGE (<80%):")
            print("-" * 80)
            for item in self.untested_files[:20]:
                print(f"  {item['file']}: {item['coverage']:.1f}%")
                if item['missing_lines']:
                    missing = item['missing_lines'][:5]
                    print(f"    Missing lines: {missing}")
            if len(self.untested_files) > 20:
                print(f"  ... and {len(self.untested_files) - 20} more")
            print()

        print("=" * 80)

        if percent >= 80:
            print("\n[SUCCESS] Good test coverage!")
        else:
            print(f"\n[WARNING] Coverage below 80% - aim for 80%+")

        return percent >= 80

    def run_analysis(self):
        """Run coverage analysis"""
        logger.info("Starting test coverage analysis...")

        if self.run_coverage():
            self.analyze_coverage()

        return self.print_report()


def main():
    """Main entry point"""
    analyzer = TestCoverageAnalyzer()
    analyzer.run_analysis()
    sys.exit(0)


if __name__ == "__main__":
    main()

