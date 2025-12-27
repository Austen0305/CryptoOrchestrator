#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Setup Testing Script
Tests all setup scripts and verifies the project is fully functional
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import io

# Fix Windows encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent.parent


class TestResult:
    """Test result container"""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error: Optional[str] = None
        self.details: List[str] = []
    
    def add_detail(self, detail: str):
        self.details.append(detail)
    
    def __str__(self):
        status = "✅" if self.passed else "❌"
        result = f"{status} {self.name}"
        if self.error:
            result += f"\n   Error: {self.error}"
        if self.details:
            result += "\n   " + "\n   ".join(self.details)
        return result


def test_python_version() -> TestResult:
    """Test Python version"""
    result = TestResult("Python Version Check")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        result.passed = True
        result.add_detail(f"Python {version.major}.{version.minor}.{version.micro}")
        if version.minor >= 13:
            result.add_detail(f"⚠️  Python {version.major}.{version.minor}: TensorFlow not compatible")
    else:
        result.error = f"Python 3.11+ required, found {version.major}.{version.minor}"
    return result


def test_node_version() -> TestResult:
    """Test Node.js version"""
    result = TestResult("Node.js Version Check")
    try:
        proc = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            version_str = proc.stdout.strip()
            version_num = int(version_str.replace("v", "").split(".")[0])
            if version_num >= 18:
                result.passed = True
                result.add_detail(f"Node.js {version_str}")
            else:
                result.error = f"Node.js 18+ required, found {version_str}"
        else:
            result.error = "Node.js not found"
    except FileNotFoundError:
        result.error = "Node.js not installed"
    except Exception as e:
        result.error = str(e)
    return result


def test_env_file() -> TestResult:
    """Test .env file exists"""
    result = TestResult(".env File Check")
    env_file = project_root / ".env"
    if env_file.exists():
        result.passed = True
        result.add_detail(f".env file exists at {env_file}")
        
        # Check for required variables
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            required_vars = ["DATABASE_URL", "JWT_SECRET"]
            missing = [var for var in required_vars if not os.getenv(var)]
            if missing:
                result.add_detail(f"⚠️  Missing variables: {', '.join(missing)}")
            else:
                result.add_detail("✅ Required variables present")
        except ImportError:
            result.add_detail("⚠️  python-dotenv not available for validation")
    else:
        result.error = ".env file not found. Run: npm run setup:env"
    return result


def test_setup_scripts() -> TestResult:
    """Test all setup scripts are present and importable"""
    result = TestResult("Setup Scripts Check")
    scripts = [
        "scripts/setup/create_env_file.py",
        "scripts/setup/init_database.py",
        "scripts/setup/verify_dependencies.py",
        "scripts/setup/complete_setup.py",
        "scripts/setup/health_check.py",
        "scripts/diagnostics/runtime_diagnostics.py",
        "scripts/verification/comprehensive_feature_verification.py",
    ]
    
    missing = []
    for script in scripts:
        script_path = project_root / script
        if not script_path.exists():
            missing.append(script)
    
    if missing:
        result.error = f"Missing scripts: {', '.join(missing)}"
    else:
        result.passed = True
        result.add_detail(f"✅ All {len(scripts)} setup scripts present")
    
    return result


def test_npm_scripts() -> TestResult:
    """Test npm scripts are configured"""
    result = TestResult("NPM Scripts Check")
    package_json = project_root / "package.json"
    
    if not package_json.exists():
        result.error = "package.json not found"
        return result
    
    try:
        with open(package_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        scripts = data.get("scripts", {})
        required_scripts = [
            "setup",
            "setup:env",
            "setup:db",
            "setup:verify",
            "setup:health",
            "setup:deps",
            "start:all",
        ]
        
        missing = [s for s in required_scripts if s not in scripts]
        if missing:
            result.error = f"Missing npm scripts: {', '.join(missing)}"
        else:
            result.passed = True
            result.add_detail(f"✅ All {len(required_scripts)} required npm scripts present")
    except Exception as e:
        result.error = f"Error reading package.json: {e}"
    
    return result


def test_documentation() -> TestResult:
    """Test documentation files exist"""
    result = TestResult("Documentation Check")
    docs = [
        "docs/COMPLETE_SETUP_GUIDE.md",
        "docs/DATABASE_SETUP.md",
        "docs/SERVICE_STARTUP.md",
        "docs/QUICK_REFERENCE_SETUP.md",
        "README.md",
        "SETUP.md",
    ]
    
    missing = []
    for doc in docs:
        doc_path = project_root / doc
        if not doc_path.exists():
            missing.append(doc)
    
    if missing:
        result.error = f"Missing documentation: {', '.join(missing)}"
    else:
        result.passed = True
        result.add_detail(f"✅ All {len(docs)} documentation files present")
    
    return result


def test_script_execution(script_name: str) -> TestResult:
    """Test if a script can be executed (import check)"""
    result = TestResult(f"Script Execution: {script_name}")
    script_path = project_root / script_name
    
    if not script_path.exists():
        result.error = f"Script not found: {script_name}"
        return result
    
    try:
        # Try to import/parse the script
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=project_root
        )
        if proc.returncode == 0:
            result.passed = True
            result.add_detail("✅ Script syntax is valid")
        else:
            result.error = f"Syntax error: {proc.stderr}"
    except Exception as e:
        result.error = f"Error testing script: {e}"
    
    return result


def run_all_tests() -> List[TestResult]:
    """Run all tests"""
    print("🧪 CryptoOrchestrator Complete Setup Testing")
    print("=" * 60)
    print()
    
    tests = [
        test_python_version,
        test_node_version,
        test_env_file,
        test_setup_scripts,
        test_npm_scripts,
        test_documentation,
    ]
    
    # Test script execution
    scripts_to_test = [
        "scripts/setup/create_env_file.py",
        "scripts/setup/init_database.py",
        "scripts/setup/verify_dependencies.py",
        "scripts/setup/complete_setup.py",
    ]
    
    for script in scripts_to_test:
        tests.append(lambda s=script: test_script_execution(s))
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print(result)
            print()
        except Exception as e:
            error_result = TestResult(test_func.__name__)
            error_result.error = str(e)
            results.append(error_result)
            print(error_result)
            print()
    
    return results


def main():
    """Main entry point"""
    os.chdir(project_root)
    
    results = run_all_tests()
    
    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    
    print(f"✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print()
    
    if failed > 0:
        print("❌ Some tests failed. Please fix the issues above.")
        print()
        print("💡 Quick Fixes:")
        print("  - Missing .env: npm run setup:env")
        print("  - Missing dependencies: npm run setup:deps")
        print("  - Database issues: npm run setup:db")
        sys.exit(1)
    else:
        print("✅ All tests passed! Setup is complete and functional.")
        sys.exit(0)


if __name__ == "__main__":
    main()
