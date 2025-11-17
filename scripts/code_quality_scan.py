#!/usr/bin/env python3
"""
Code Quality Scanning Utility
Integrates Snyk, SonarQube, Bandit, and other code quality tools.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse


class CodeQualityScanner:
    """Unified code quality scanning interface."""
    
    def __init__(self):
        self.results = {
            "snyk": None,
            "bandit": None,
            "safety": None,
            "npm_audit": None,
        }
    
    def run_snyk(self, severity_threshold: str = "high") -> Dict[str, Any]:
        """Run Snyk security scan."""
        results = {
            "status": "skipped",
            "issues": [],
            "summary": {}
        }
        
        # Check if Snyk CLI is available
        try:
            result = subprocess.run(
                ["snyk", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return results
        except (FileNotFoundError, subprocess.TimeoutExpired):
            results["message"] = "Snyk CLI not installed. Install with: npm install -g snyk"
            return results
        
        # Check if SNYK_TOKEN is set
        if not os.getenv("SNYK_TOKEN"):
            results["message"] = "SNYK_TOKEN not set. Set environment variable or run: snyk auth"
            return results
        
        try:
            # Scan Python dependencies
            result = subprocess.run(
                ["snyk", "test", "--severity-threshold", severity_threshold, "--json"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                results["status"] = "ok"
                results["summary"]["python"] = "No issues found"
            else:
                try:
                    data = json.loads(result.stdout)
                    results["status"] = "issues_found"
                    results["issues"] = data.get("vulnerabilities", [])
                    results["summary"]["python"] = f"{len(results['issues'])} issues found"
                except json.JSONDecodeError:
                    results["status"] = "error"
                    results["message"] = result.stderr or "Unknown error"
        except subprocess.TimeoutExpired:
            results["status"] = "timeout"
            results["message"] = "Snyk scan timed out"
        except Exception as e:
            results["status"] = "error"
            results["message"] = str(e)
        
        self.results["snyk"] = results
        return results
    
    def run_bandit(self) -> Dict[str, Any]:
        """Run Bandit security scan for Python."""
        results = {
            "status": "skipped",
            "issues": [],
            "summary": {}
        }
        
        try:
            result = subprocess.run(
                ["bandit", "-r", "server_fastapi", "-f", "json", "-ll"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    results["status"] = "ok" if not data.get("results") else "issues_found"
                    results["issues"] = data.get("results", [])
                    results["summary"]["total"] = len(results["issues"])
                    results["summary"]["high"] = len([i for i in results["issues"] if i.get("issue_severity") == "HIGH"])
                    results["summary"]["medium"] = len([i for i in results["issues"] if i.get("issue_severity") == "MEDIUM"])
                    results["summary"]["low"] = len([i for i in results["issues"] if i.get("issue_severity") == "LOW"])
                except json.JSONDecodeError:
                    results["status"] = "error"
                    results["message"] = "Failed to parse Bandit output"
            else:
                results["status"] = "error"
                results["message"] = result.stderr or "Bandit scan failed"
        except FileNotFoundError:
            results["message"] = "Bandit not installed. Install with: pip install bandit"
        except subprocess.TimeoutExpired:
            results["status"] = "timeout"
            results["message"] = "Bandit scan timed out"
        except Exception as e:
            results["status"] = "error"
            results["message"] = str(e)
        
        self.results["bandit"] = results
        return results
    
    def run_safety(self) -> Dict[str, Any]:
        """Run Safety check for Python dependencies."""
        results = {
            "status": "skipped",
            "issues": [],
            "summary": {}
        }
        
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                results["status"] = "ok"
                results["summary"]["python"] = "No known vulnerabilities"
            else:
                try:
                    data = json.loads(result.stdout)
                    results["status"] = "issues_found"
                    results["issues"] = data if isinstance(data, list) else []
                    results["summary"]["total"] = len(results["issues"])
                except json.JSONDecodeError:
                    results["status"] = "error"
                    results["message"] = "Failed to parse Safety output"
        except FileNotFoundError:
            results["message"] = "Safety not installed. Install with: pip install safety"
        except subprocess.TimeoutExpired:
            results["status"] = "timeout"
            results["message"] = "Safety check timed out"
        except Exception as e:
            results["status"] = "error"
            results["message"] = str(e)
        
        self.results["safety"] = results
        return results
    
    def run_npm_audit(self) -> Dict[str, Any]:
        """Run npm audit for Node.js dependencies."""
        results = {
            "status": "skipped",
            "issues": [],
            "summary": {}
        }
        
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # npm audit returns exit code 1 if vulnerabilities found, but still valid JSON
            try:
                data = json.loads(result.stdout)
                vulnerabilities = data.get("vulnerabilities", {})
                
                if not vulnerabilities:
                    results["status"] = "ok"
                    results["summary"]["npm"] = "No vulnerabilities found"
                else:
                    results["status"] = "issues_found"
                    results["issues"] = list(vulnerabilities.values())
                    
                    # Count by severity
                    critical = sum(1 for v in vulnerabilities.values() if v.get("severity") == "critical")
                    high = sum(1 for v in vulnerabilities.values() if v.get("severity") == "high")
                    moderate = sum(1 for v in vulnerabilities.values() if v.get("severity") == "moderate")
                    low = sum(1 for v in vulnerabilities.values() if v.get("severity") == "low")
                    
                    results["summary"]["total"] = len(vulnerabilities)
                    results["summary"]["critical"] = critical
                    results["summary"]["high"] = high
                    results["summary"]["moderate"] = moderate
                    results["summary"]["low"] = low
            except json.JSONDecodeError:
                results["status"] = "error"
                results["message"] = "Failed to parse npm audit output"
        except FileNotFoundError:
            results["message"] = "npm not installed"
        except subprocess.TimeoutExpired:
            results["status"] = "timeout"
            results["message"] = "npm audit timed out"
        except Exception as e:
            results["status"] = "error"
            results["message"] = str(e)
        
        self.results["npm_audit"] = results
        return results
    
    def run_all(self, severity_threshold: str = "high") -> Dict[str, Any]:
        """Run all code quality scans."""
        print("🔍 Running code quality scans...")
        
        print("\n📦 Running npm audit...")
        self.run_npm_audit()
        
        print("🐍 Running Safety check...")
        self.run_safety()
        
        print("🔒 Running Bandit scan...")
        self.run_bandit()
        
        print("🛡️  Running Snyk scan...")
        self.run_snyk(severity_threshold)
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all scan results."""
        summary = {
            "total_issues": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "status": "ok"
        }
        
        for tool, result in self.results.items():
            if result and result.get("status") == "issues_found":
                summary["status"] = "issues_found"
                tool_summary = result.get("summary", {})
                summary["total_issues"] += tool_summary.get("total", len(result.get("issues", [])))
                summary["critical_issues"] += tool_summary.get("critical", 0)
                summary["high_issues"] += tool_summary.get("high", 0)
        
        return summary


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Code quality scanning utility")
    parser.add_argument("tool", nargs="?", choices=["snyk", "bandit", "safety", "npm", "all"], default="all")
    parser.add_argument("--severity", choices=["low", "medium", "high", "critical"], default="high")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    scanner = CodeQualityScanner()
    
    if args.tool == "all":
        results = scanner.run_all(severity_threshold=args.severity)
    elif args.tool == "snyk":
        results = {"snyk": scanner.run_snyk(args.severity)}
    elif args.tool == "bandit":
        results = {"bandit": scanner.run_bandit()}
    elif args.tool == "safety":
        results = {"safety": scanner.run_safety()}
    elif args.tool == "npm":
        results = {"npm_audit": scanner.run_npm_audit()}
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        summary = scanner.get_summary()
        print("\n📊 Summary:")
        print(f"Status: {summary['status']}")
        print(f"Total Issues: {summary['total_issues']}")
        print(f"Critical Issues: {summary['critical_issues']}")
        print(f"High Issues: {summary['high_issues']}")
    
    sys.exit(0 if summary["status"] == "ok" else 1)


if __name__ == "__main__":
    main()

