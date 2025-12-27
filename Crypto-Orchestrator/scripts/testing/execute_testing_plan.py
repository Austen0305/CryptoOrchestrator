#!/usr/bin/env python3
"""
Automated Testing Plan Execution Script
Executes the comprehensive testing plan from TestingPlan.md systematically
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestingPlanExecutor:
    """Execute testing plan phases systematically"""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {
            "started_at": datetime.now().isoformat(),
            "phases": {},
            "summary": {
                "total_phases": 15,
                "completed_phases": 0,
                "failed_tasks": [],
                "warnings": []
            }
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command: str, check: bool = False) -> Tuple[bool, str]:
        """Run shell command and return success status and output"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            success = result.returncode == 0
            output = result.stdout + result.stderr
            return success, output
        except Exception as e:
            return False, str(e)
    
    def phase_1_environment_setup(self) -> Dict:
        """Phase 1.1: Environment Setup & Validation"""
        self.log("Starting Phase 1.1: Environment Setup & Validation")
        results = {
            "tasks": {},
            "status": "in_progress"
        }
        
        # Task 1: Validate environment
        self.log("Task 1: Validating environment variables...")
        success, output = self.run_command("npm run validate:env")
        results["tasks"]["validate_env"] = {
            "success": success,
            "output": output[:500] if len(output) > 500 else output
        }
        
        # Task 2: Database setup
        self.log("Task 2: Verifying database setup...")
        success, output = self.run_command("npm run setup:db")
        results["tasks"]["database_setup"] = {
            "success": success,
            "output": output[:500] if len(output) > 500 else output
        }
        
        # Task 3: Service health (requires services running)
        self.log("Task 3: Checking service health (may require services)...")
        success, output = self.run_command("npm run setup:health")
        results["tasks"]["health_check"] = {
            "success": success,
            "output": output[:500] if len(output) > 500 else output,
            "note": "May require services to be running"
        }
        
        # Task 4: Dependency verification
        self.log("Task 4: Verifying dependencies...")
        success, output = self.run_command("npm list --depth=0")
        results["tasks"]["dependencies"] = {
            "success": success,
            "output": output[:500] if len(output) > 500 else output
        }
        
        all_success = all(task.get("success", False) for task in results["tasks"].values())
        results["status"] = "completed" if all_success else "partial"
        
        return results
    
    def phase_1_test_infrastructure(self) -> Dict:
        """Phase 1.2: Test Infrastructure Verification"""
        self.log("Starting Phase 1.2: Test Infrastructure Verification")
        results = {
            "tasks": {},
            "status": "in_progress"
        }
        
        # Task 1: Backend test framework
        self.log("Task 1: Verifying backend test framework...")
        success, output = self.run_command("npm test -- --collect-only")
        results["tasks"]["backend_tests"] = {
            "success": success,
            "output": output[:500] if len(output) > 500 else output
        }
        
        # Task 2: Frontend test framework
        self.log("Task 2: Verifying frontend test framework...")
        success, output = self.run_command("npm run test:frontend -- --run --reporter=verbose")
        results["tasks"]["frontend_tests"] = {
            "success": success,
            "output": output[:500] if len(output) > 500 else output
        }
        
        # Task 3: E2E test framework (check if Playwright installed)
        self.log("Task 3: Verifying E2E test framework...")
        success, output = self.run_command("npx playwright --version")
        results["tasks"]["e2e_tests"] = {
            "success": success,
            "output": output[:500] if len(output) > 500 else output
        }
        
        all_success = all(task.get("success", False) for task in results["tasks"].values())
        results["status"] = "completed" if all_success else "partial"
        
        return results
    
    def execute_phase_1(self) -> Dict:
        """Execute Phase 1: Foundation & Infrastructure"""
        self.log("=" * 60)
        self.log("PHASE 1: Foundation & Infrastructure Testing")
        self.log("=" * 60)
        
        phase_results = {
            "1.1_environment": self.phase_1_environment_setup(),
            "1.2_test_infrastructure": self.phase_1_test_infrastructure()
        }
        
        return phase_results
    
    def save_results(self):
        """Save test results to file"""
        results_file = self.project_root / "test-results" / "testing-plan-execution.json"
        results_file.parent.mkdir(exist_ok=True)
        
        self.results["completed_at"] = datetime.now().isoformat()
        
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        self.log(f"Results saved to {results_file}")
    
    def run(self):
        """Execute testing plan"""
        try:
            # Phase 1
            phase_1_results = self.execute_phase_1()
            self.results["phases"]["phase_1"] = phase_1_results
            
            # Save results
            self.save_results()
            
            # Print summary
            self.log("=" * 60)
            self.log("TESTING PLAN EXECUTION SUMMARY")
            self.log("=" * 60)
            self.log(f"Phase 1 Status: {phase_1_results.get('1.1_environment', {}).get('status', 'unknown')}")
            
        except Exception as e:
            self.log(f"Error executing testing plan: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    executor = TestingPlanExecutor()
    executor.run()

