#!/usr/bin/env python3
"""
Test Coverage Reporter
Generates coverage reports with trends and badges
"""
import subprocess
import json
import os
from datetime import datetime
from typing import Dict
import argparse


class CoverageReporter:
    """Generate and track test coverage"""
    
    def __init__(self):
        self.coverage_file = ".coverage"
        self.history_file = "coverage_history.json"
        self.badge_file = "coverage_badge.svg"
    
    def run_tests_with_coverage(self) -> bool:
        """Run tests and generate coverage"""
        print("🧪 Running tests with coverage...")
        
        try:
            result = subprocess.run(
                ["pytest", "server_fastapi/tests/", "-v", "--cov=server_fastapi", 
                 "--cov-report=html", "--cov-report=json", "--cov-report=term"],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            if result.returncode != 0:
                print("⚠️  Some tests failed, but coverage was generated")
            
            return os.path.exists("coverage.json")
        except Exception as e:
            print(f"❌ Error running tests: {str(e)}")
            return False
    
    def load_coverage_data(self) -> Dict:
        """Load coverage data from JSON"""
        if os.path.exists("coverage.json"):
            with open("coverage.json", 'r') as f:
                return json.load(f)
        return None
    
    def calculate_metrics(self, coverage_data: Dict) -> Dict:
        """Calculate coverage metrics"""
        totals = coverage_data.get('totals', {})
        
        return {
            'timestamp': datetime.now().isoformat(),
            'percent_covered': round(totals.get('percent_covered', 0), 2),
            'num_statements': totals.get('num_statements', 0),
            'covered_lines': totals.get('covered_lines', 0),
            'missing_lines': totals.get('missing_lines', 0),
            'num_branches': totals.get('num_branches', 0),
            'covered_branches': totals.get('covered_branches', 0),
            'missing_branches': totals.get('missing_branches', 0),
        }
    
    def save_to_history(self, metrics: Dict):
        """Save metrics to history"""
        history = []
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        
        history.append(metrics)
        
        # Keep last 50 runs
        history = history[-50:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"✅ Coverage saved to history: {self.history_file}")
    
    def generate_badge(self, coverage_pct: float):
        """Generate SVG coverage badge"""
        # Determine color based on coverage
        if coverage_pct >= 90:
            color = "brightgreen"
        elif coverage_pct >= 80:
            color = "green"
        elif coverage_pct >= 70:
            color = "yellowgreen"
        elif coverage_pct >= 60:
            color = "yellow"
        elif coverage_pct >= 50:
            color = "orange"
        else:
            color = "red"
        
        badge_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
    <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <mask id="a">
        <rect width="120" height="20" rx="3" fill="#fff"/>
    </mask>
    <g mask="url(#a)">
        <path fill="#555" d="M0 0h69v20H0z"/>
        <path fill="#{color}" d="M69 0h51v20H69z"/>
        <path fill="url(#b)" d="M0 0h120v20H0z"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
        <text x="34.5" y="15" fill="#010101" fill-opacity=".3">coverage</text>
        <text x="34.5" y="14">coverage</text>
        <text x="93.5" y="15" fill="#010101" fill-opacity=".3">{coverage_pct:.1f}%</text>
        <text x="93.5" y="14">{coverage_pct:.1f}%</text>
    </g>
</svg>'''
        
        with open(self.badge_file, 'w') as f:
            f.write(badge_svg)
        
        print(f"✅ Badge generated: {self.badge_file}")
    
    def analyze_trends(self):
        """Analyze coverage trends"""
        if not os.path.exists(self.history_file):
            print("⚠️  No history file found")
            return
        
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        
        if len(history) < 2:
            print("⚠️  Not enough history for trend analysis")
            return
        
        print("\n" + "=" * 60)
        print("📊 Coverage Trends")
        print("=" * 60)
        
        recent = history[-5:]
        
        print(f"\nLast {len(recent)} runs:")
        for i, entry in enumerate(recent, 1):
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
            print(f"   {i}. {timestamp}: {entry['percent_covered']}%")
        
        # Calculate trend
        if len(recent) >= 2:
            oldest = recent[0]['percent_covered']
            newest = recent[-1]['percent_covered']
            change = newest - oldest
            
            print(f"\n📈 Trend: {change:+.2f}% over last {len(recent)} runs")
            
            if change > 0:
                print("   ✅ Coverage is improving!")
            elif change < 0:
                print("   ⚠️  Coverage is decreasing")
            else:
                print("   ➡️  Coverage is stable")
        
        print("=" * 60)
    
    def check_threshold(self, coverage_pct: float, threshold: float = 80.0) -> bool:
        """Check if coverage meets threshold"""
        print(f"\n🎯 Coverage Threshold Check:")
        print(f"   Current: {coverage_pct:.2f}%")
        print(f"   Threshold: {threshold:.2f}%")
        
        if coverage_pct >= threshold:
            print(f"   ✅ PASS: Coverage meets threshold")
            return True
        else:
            print(f"   ❌ FAIL: Coverage below threshold")
            return False
    
    def generate_report(self, metrics: Dict):
        """Generate detailed report"""
        print("\n" + "=" * 60)
        print("📋 Coverage Report")
        print("=" * 60)
        print(f"Timestamp: {metrics['timestamp']}")
        print(f"\n📊 Overall Coverage: {metrics['percent_covered']:.2f}%")
        print(f"\n   Statements:")
        print(f"      Total: {metrics['num_statements']}")
        print(f"      Covered: {metrics['covered_lines']}")
        print(f"      Missing: {metrics['missing_lines']}")
        
        if metrics['num_branches'] > 0:
            branch_pct = (metrics['covered_branches'] / metrics['num_branches']) * 100
            print(f"\n   Branches:")
            print(f"      Total: {metrics['num_branches']}")
            print(f"      Covered: {metrics['covered_branches']}")
            print(f"      Missing: {metrics['missing_branches']}")
            print(f"      Coverage: {branch_pct:.2f}%")
        
        print("=" * 60)
        print(f"\n💡 HTML Report: htmlcov/index.html")
        print(f"   JSON Report: coverage.json")
        print(f"   Badge: {self.badge_file}")


def main():
    """Main CLI"""
    parser = argparse.ArgumentParser(description='Generate test coverage reports and badges')
    parser.add_argument('--run-tests', action='store_true', help='Run tests to generate coverage')
    parser.add_argument('--threshold', type=float, default=80.0, help='Minimum coverage threshold (default: 80.0)')
    parser.add_argument('--trends', action='store_true', help='Analyze coverage trends')
    parser.add_argument('--badge', action='store_true', help='Generate coverage badge')
    parser.add_argument('--fail-under', type=float, help='Exit with error if coverage below this value')
    
    args = parser.parse_args()
    
    reporter = CoverageReporter()
    
    # Run tests if requested
    if args.run_tests:
        if not reporter.run_tests_with_coverage():
            print("❌ Failed to generate coverage data")
            exit(1)
    
    # Load coverage data
    coverage_data = reporter.load_coverage_data()
    if not coverage_data:
        print("❌ No coverage data found. Run with --run-tests first.")
        exit(1)
    
    # Calculate metrics
    metrics = reporter.calculate_metrics(coverage_data)
    
    # Generate report
    reporter.generate_report(metrics)
    
    # Save to history
    reporter.save_to_history(metrics)
    
    # Generate badge if requested
    if args.badge:
        reporter.generate_badge(metrics['percent_covered'])
    
    # Analyze trends if requested
    if args.trends:
        reporter.analyze_trends()
    
    # Check threshold
    coverage_pct = metrics['percent_covered']
    threshold = args.fail_under if args.fail_under else args.threshold
    passed = reporter.check_threshold(coverage_pct, threshold)
    
    if args.fail_under and not passed:
        print(f"\n❌ Coverage {coverage_pct:.2f}% is below --fail-under threshold {args.fail_under}%")
        exit(1)
    
    print("\n✅ Coverage report complete!")


if __name__ == "__main__":
    main()
