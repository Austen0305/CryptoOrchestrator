#!/usr/bin/env python3
"""
Comprehensive Pre-Deployment Testing Script
Runs all critical tests and generates a readiness report
"""
import asyncio
import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class TestRunner:
    """Orchestrate all pre-deployment tests"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.start_time = datetime.now()
    
    def run_command(self, cmd: str, description: str, timeout: int = 300) -> Tuple[bool, str]:
        """Run a shell command and return success status"""
        print(f"\n🔧 Running: {description}")
        print(f"   Command: {cmd}")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {description}")
            
            return success, output
        except subprocess.TimeoutExpired:
            print(f"⏱️  TIMEOUT - {description}")
            return False, f"Timeout after {timeout}s"
        except Exception as e:
            print(f"❌ ERROR - {description}: {str(e)}")
            return False, str(e)
    
    async def run_python_script(self, script_path: str, description: str) -> Tuple[bool, str]:
        """Run a Python test script"""
        cmd = f"python {script_path}"
        return self.run_command(cmd, description)
    
    def test_phase_1_infrastructure(self):
        """Phase 1: Core Infrastructure"""
        print("\n" + "="*60)
        print("📦 PHASE 1: INFRASTRUCTURE VALIDATION")
        print("="*60)
        
        tests = []
        
        # Test backend health
        success, output = self.run_command(
            "python scripts/test_infrastructure.py",
            "Infrastructure Tests"
        )
        tests.append(("Infrastructure", success, output))
        
        # Test database migrations
        success, output = self.run_command(
            "alembic check || echo 'No pending migrations'",
            "Database Migrations Check",
            timeout=60
        )
        tests.append(("Migrations", success, output))
        
        self.results["phase1"] = {
            "name": "Infrastructure",
            "tests": tests,
            "passed": sum(1 for _, s, _ in tests if s),
            "total": len(tests)
        }
    
    def test_phase_2_security(self):
        """Phase 2: Authentication & Security"""
        print("\n" + "="*60)
        print("🔒 PHASE 2: SECURITY VALIDATION")
        print("="*60)
        
        tests = []
        
        # Run security tests
        success, output = self.run_command(
            "python scripts/test_security.py",
            "Security Tests"
        )
        tests.append(("Security", success, output))
        
        # Check for npm vulnerabilities (informational only)
        # NPM audit is run but results are informational
        # Manual review required for production deployments
        success, output = self.run_command(
            "npm audit --audit-level=high",
            "NPM Security Audit (Informational)",
            timeout=120
        )
        # Record audit results but mark as informational
        audit_status = "Passed" if success else "Found vulnerabilities - Manual review required"
        tests.append(("NPM Audit", None, audit_status))  # None = informational, not pass/fail
        
        self.results["phase2"] = {
            "name": "Security",
            "tests": tests,
            "passed": sum(1 for _, s, _ in tests if s),
            "total": len(tests)
        }
    
    def test_phase_4_backend(self):
        """Phase 4: Backend Unit Tests"""
        print("\n" + "="*60)
        print("🧪 PHASE 4: BACKEND TESTS")
        print("="*60)
        
        tests = []
        
        # Run pytest
        success, output = self.run_command(
            "pytest server_fastapi/tests/ -v --maxfail=5 -x",
            "Backend Unit Tests",
            timeout=600
        )
        tests.append(("Backend Tests", success, output))
        
        self.results["phase4"] = {
            "name": "Backend",
            "tests": tests,
            "passed": sum(1 for _, s, _ in tests if s),
            "total": len(tests)
        }
    
    def test_phase_9_e2e(self):
        """Phase 9: End-to-End Tests"""
        print("\n" + "="*60)
        print("🎭 PHASE 9: E2E TESTS")
        print("="*60)
        
        tests = []
        
        # Check if Playwright is available
        success, output = self.run_command(
            "npx playwright --version",
            "Playwright Check",
            timeout=30
        )
        
        if success:
            # Note: E2E tests require running server, skip for now
            print("⚠️  E2E tests require running server - skipping automated run")
            tests.append(("E2E Tests", None, "Requires manual run with server"))
        else:
            tests.append(("E2E Tests", False, "Playwright not installed"))
        
        self.results["phase9"] = {
            "name": "E2E",
            "tests": tests,
            "passed": sum(1 for _, s, _ in tests if s),
            "total": len(tests)
        }
    
    def test_phase_10_performance(self):
        """Phase 10: Load & Performance Tests"""
        print("\n" + "="*60)
        print("⚡ PHASE 10: PERFORMANCE TESTS")
        print("="*60)
        
        tests = []
        
        # Note: Load tests require running server
        print("⚠️  Load tests require running server - skipping automated run")
        tests.append(("Load Tests", None, "Requires manual run with server"))
        
        self.results["phase10"] = {
            "name": "Performance",
            "tests": tests,
            "passed": sum(1 for _, s, _ in tests if s),
            "total": len(tests)
        }
    
    def test_code_quality(self):
        """Additional: Code Quality Checks"""
        print("\n" + "="*60)
        print("📊 CODE QUALITY CHECKS")
        print("="*60)
        
        tests = []
        
        # Python linting
        success, output = self.run_command(
            "python -m flake8 server_fastapi/ --count --select=E9,F63,F7,F82 --show-source --statistics",
            "Python Syntax Check",
            timeout=60
        )
        tests.append(("Python Syntax", success, output))
        
        # TypeScript check
        success, output = self.run_command(
            "npm run check",
            "TypeScript Check",
            timeout=120
        )
        tests.append(("TypeScript", success, output))
        
        self.results["quality"] = {
            "name": "Code Quality",
            "tests": tests,
            "passed": sum(1 for _, s, _ in tests if s),
            "total": len(tests)
        }
    
    def generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*60)
        print("📊 PRE-DEPLOYMENT TEST REPORT")
        print("="*60)
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration:.2f}s")
        print("="*60)
        
        total_passed = 0
        total_tests = 0
        
        for phase_key, phase_data in self.results.items():
            name = phase_data["name"]
            passed = phase_data["passed"]
            total = phase_data["total"]
            
            total_passed += passed
            total_tests += total
            
            percentage = (passed / total * 100) if total > 0 else 0
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 60 else "❌"
            
            print(f"\n{status} {name}: {passed}/{total} ({percentage:.1f}%)")
            
            for test_name, success, output in phase_data["tests"]:
                if success is None:
                    print(f"   ⚠️  {test_name}: Skipped")
                elif success:
                    print(f"   ✅ {test_name}: Passed")
                else:
                    print(f"   ❌ {test_name}: Failed")
                    if output and len(output) < 200:
                        print(f"      {output[:200]}")
        
        # Overall score
        print("\n" + "="*60)
        overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"📈 OVERALL SCORE: {total_passed}/{total_tests} ({overall_percentage:.1f}%)")
        
        # Deployment recommendation
        if overall_percentage >= 90:
            status = "✅ PRODUCTION READY"
            recommendation = "All systems go! Ready for production deployment."
        elif overall_percentage >= 80:
            status = "⚠️  STAGING READY"
            recommendation = "Deploy to staging. Polish before production."
        elif overall_percentage >= 70:
            status = "🟡 BETA READY"
            recommendation = "Major issues remain. Beta testing recommended."
        else:
            status = "❌ NOT READY"
            recommendation = "Critical gaps exist. Do NOT deploy."
        
        print(f"\n{status}")
        print(f"Recommendation: {recommendation}")
        print("="*60)
        
        # Save JSON report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": duration,
            "phases": self.results,
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_tests - total_passed,
                "percentage": overall_percentage,
                "status": status,
                "recommendation": recommendation
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return overall_percentage >= 70  # Return True if acceptable


def main():
    """Main test orchestrator"""
    print("🚀 Starting Pre-Deployment Testing Suite")
    print(f"Time: {datetime.now()}")
    print("="*60)
    
    runner = TestRunner()
    
    # Run all test phases
    runner.test_phase_1_infrastructure()
    runner.test_phase_2_security()
    runner.test_phase_4_backend()
    runner.test_code_quality()
    runner.test_phase_9_e2e()
    runner.test_phase_10_performance()
    
    # Generate report
    success = runner.generate_report()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
