#!/usr/bin/env python3
"""
Security Audit Script
Runs comprehensive security checks and generates audit report.

Usage:
    python scripts/security/security_audit.py
    python scripts/security/security_audit.py --check dependency
    python scripts/security/security_audit.py --check code
    python scripts/security/security_audit.py --check secrets
"""

import subprocess
import sys
import json
import argparse
import io
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        # If reconfiguration fails, continue without it
        pass

project_root = Path(__file__).parent.parent.parent


class SecurityAuditor:
    """Runs security audits and generates reports."""
    
    def __init__(self):
        self.results: Dict[str, any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "summary": {"passed": 0, "failed": 0, "warnings": 0, "total": 0}
        }
        self.report_file = project_root / "test-results" / f"security_audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        self.report_file.parent.mkdir(exist_ok=True)
    
    def check_dependencies(self) -> Dict[str, any]:
        """Check for dependency vulnerabilities."""
        print("\n[CHECK] Checking Dependencies...")
        result = {
            "check": "dependencies",
            "status": "unknown",
            "issues": [],
            "warnings": []
        }
        
        # Python dependencies
        try:
            print("  [INFO] Checking Python dependencies (safety)...")
            safety_result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if safety_result.returncode == 0:
                result["status"] = "passed"
                result["issues"].append("No Python vulnerabilities found")
                print("    [OK] No Python vulnerabilities found")
            else:
                result["status"] = "failed"
                try:
                    safety_data = json.loads(safety_result.stdout)
                    for vuln in safety_data:
                        result["issues"].append(f"{vuln.get('package', 'unknown')}: {vuln.get('vulnerability', 'unknown')}")
                        print(f"    [FAIL] {vuln.get('package', 'unknown')}: {vuln.get('vulnerability', 'unknown')}")
                except:
                    result["issues"].append("Safety check found vulnerabilities (see output)")
                    print("    [FAIL] Safety check found vulnerabilities")
        except FileNotFoundError:
            result["warnings"].append("safety not installed (pip install safety)")
            print("    [WARN] safety not installed")
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Error running safety: {e}")
            print(f"    [FAIL] Error: {e}")
        
        # Node dependencies
        try:
            print("  [INFO] Checking Node dependencies (npm audit)...")
            npm_result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            try:
                npm_data = json.loads(npm_result.stdout)
                vulnerabilities = npm_data.get("vulnerabilities", {})
                
                if not vulnerabilities:
                    result["status"] = "passed" if result["status"] != "failed" else "failed"
                    result["issues"].append("No Node vulnerabilities found")
                    print("    [OK] No Node vulnerabilities found")
                else:
                    result["status"] = "failed"
                    count = len(vulnerabilities)
                    result["issues"].append(f"{count} Node vulnerabilities found")
                    print(f"    [FAIL] {count} Node vulnerabilities found")
            except:
                if npm_result.returncode == 0:
                    result["status"] = "passed" if result["status"] != "failed" else "failed"
                    print("    [OK] npm audit passed")
                else:
                    result["status"] = "failed"
                    print("    [FAIL] npm audit found issues")
        except Exception as e:
            result["warnings"].append(f"Error running npm audit: {e}")
            print(f"    [WARN] Error: {e}")
        
        return result
    
    def check_code_security(self) -> Dict[str, any]:
        """Check code for security issues."""
        print("\n[CHECK] Checking Code Security...")
        result = {
            "check": "code",
            "status": "unknown",
            "issues": [],
            "warnings": []
        }
        
        # Bandit (Python security linter)
        try:
            print("  [INFO] Running Bandit (Python security)...")
            bandit_result = subprocess.run(
                ["bandit", "-r", "server_fastapi", "-f", "json"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            try:
                bandit_data = json.loads(bandit_result.stdout)
                issues = bandit_data.get("results", [])
                
                if not issues:
                    result["status"] = "passed"
                    result["issues"].append("No Python security issues found")
                    print("    [OK] No Python security issues found")
                else:
                    result["status"] = "failed"
                    high_severity = [i for i in issues if i.get("issue_severity") == "HIGH"]
                    medium_severity = [i for i in issues if i.get("issue_severity") == "MEDIUM"]
                    
                    result["issues"].append(f"{len(high_severity)} high, {len(medium_severity)} medium severity issues")
                    print(f"    [FAIL] {len(high_severity)} high, {len(medium_severity)} medium severity issues")
            except:
                if bandit_result.returncode == 0:
                    result["status"] = "passed"
                    print("    [OK] Bandit check passed")
                else:
                    result["status"] = "failed"
                    print("    [FAIL] Bandit found issues")
        except FileNotFoundError:
            result["warnings"].append("bandit not installed (pip install bandit)")
            print("    [WARN] bandit not installed")
        except Exception as e:
            result["warnings"].append(f"Error running bandit: {e}")
            print(f"    [WARN] Error: {e}")
        
        return result
    
    def check_secrets(self) -> Dict[str, any]:
        """Check for exposed secrets."""
        print("\n[CHECK] Checking for Exposed Secrets...")
        result = {
            "check": "secrets",
            "status": "unknown",
            "issues": [],
            "warnings": []
        }
        
        # Gitleaks
        try:
            print("  [INFO] Running Gitleaks...")
            gitleaks_result = subprocess.run(
                ["gitleaks", "detect", "--source", str(project_root), "--report-path", str(self.report_file.parent / "gitleaks_report.json")],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            
            if gitleaks_result.returncode == 0:
                result["status"] = "passed"
                result["issues"].append("No secrets detected")
                print("    [OK] No secrets detected")
            else:
                result["status"] = "failed"
                result["issues"].append("Secrets detected (check gitleaks_report.json)")
                print("    [FAIL] Secrets detected")
        except FileNotFoundError:
            result["warnings"].append("gitleaks not installed")
            print("    [WARN] gitleaks not installed")
        except Exception as e:
            result["warnings"].append(f"Error running gitleaks: {e}")
            print(f"    [WARN] Error: {e}")
        
        return result
    
    def run_all_checks(self, check_filter: Optional[str] = None):
        """Run all security checks."""
        print("\n[SECURITY] Security Audit")
        print("=" * 60)
        
        checks = {
            "dependency": self.check_dependencies,
            "code": self.check_code_security,
            "secrets": self.check_secrets,
        }
        
        if check_filter:
            if check_filter not in checks:
                print(f"[ERROR] Unknown check: {check_filter}")
                print(f"Available checks: {', '.join(checks.keys())}")
                return
            checks = {check_filter: checks[check_filter]}
        
        for check_name, check_func in checks.items():
            try:
                result = check_func()
                self.results["checks"][check_name] = result
                
                if result["status"] == "passed":
                    self.results["summary"]["passed"] += 1
                elif result["status"] == "failed":
                    self.results["summary"]["failed"] += 1
                else:
                    self.results["summary"]["warnings"] += 1
                
                self.results["summary"]["total"] += 1
            except Exception as e:
                # Sanitize error message to remove emojis for Windows compatibility
                error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
                print(f"[ERROR] Check {check_name} crashed: {error_msg}")
                self.results["checks"][check_name] = {"error": str(e)}
        
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print audit summary."""
        print("\n" + "=" * 60)
        print("[SUMMARY] Security Audit Summary")
        print("=" * 60)
        summary = self.results["summary"]
        
        print(f"[OK] Passed: {summary['passed']}")
        print(f"[FAIL] Failed: {summary['failed']}")
        print(f"[WARN] Warnings: {summary['warnings']}")
        print(f"[INFO] Total: {summary['total']}")
        
        if summary["failed"] > 0:
            print("\n[WARN] Security issues found. Review the results above.")
        else:
            print("\n[SUCCESS] All security checks passed!")
    
    def save_results(self):
        """Save audit results."""
        with open(self.report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n[SAVED] Results saved to: {self.report_file}")


def main():
    parser = argparse.ArgumentParser(description="Security Audit Script")
    parser.add_argument(
        "--check",
        choices=["dependency", "code", "secrets"],
        help="Run specific check only"
    )
    
    args = parser.parse_args()
    
    auditor = SecurityAuditor()
    auditor.run_all_checks(check_filter=args.check)


if __name__ == "__main__":
    main()
