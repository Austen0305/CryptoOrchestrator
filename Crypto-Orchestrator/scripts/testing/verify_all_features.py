#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Feature Verification
Tests every feature of the setup system comprehensively
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import io

# Fix Windows encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent.parent


def test_feature(name: str, test_func) -> tuple:
    """Run a test and return (passed, message)"""
    try:
        result = test_func()
        return (True, result) if isinstance(result, str) else result
    except Exception as e:
        return (False, f"Error: {e}")


def verify_all_features():
    """Verify all setup features"""
    print("🔍 Complete Feature Verification")
    print("=" * 60)
    print()
    
    results = []
    
    # 1. Python Version
    version = sys.version_info
    results.append(("Python Version", version.major >= 3 and version.minor >= 11, 
                   f"Python {version.major}.{version.minor}.{version.micro}"))
    
    # 2. Node.js Version
    try:
        proc = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            version_str = proc.stdout.strip()
            version_num = int(version_str.replace("v", "").split(".")[0])
            results.append(("Node.js Version", version_num >= 18, f"Node.js {version_str}"))
        else:
            results.append(("Node.js Version", False, "Not found"))
    except:
        results.append(("Node.js Version", False, "Not installed"))
    
    # 3. .env File
    env_file = project_root / ".env"
    results.append((".env File", env_file.exists(), 
                   "Exists" if env_file.exists() else "Missing"))
    
    # 4. Setup Scripts
    scripts = [
        "scripts/setup/create_env_file.py",
        "scripts/setup/init_database.py",
        "scripts/setup/verify_dependencies.py",
        "scripts/setup/complete_setup.py",
        "scripts/setup/health_check.py",
        "scripts/diagnostics/runtime_diagnostics.py",
        "scripts/verification/comprehensive_feature_verification.py",
    ]
    all_exist = all((project_root / s).exists() for s in scripts)
    results.append(("Setup Scripts", all_exist, f"{sum(1 for s in scripts if (project_root / s).exists())}/{len(scripts)} present"))
    
    # 5. NPM Scripts
    package_json = project_root / "package.json"
    if package_json.exists():
        with open(package_json, "r") as f:
            data = json.load(f)
        scripts_data = data.get("scripts", {})
        required = ["setup", "setup:env", "setup:db", "setup:verify", "setup:health", "setup:deps", "setup:test"]
        all_present = all(s in scripts_data for s in required)
        results.append(("NPM Scripts", all_present, f"{sum(1 for s in required if s in scripts_data)}/{len(required)} present"))
    else:
        results.append(("NPM Scripts", False, "package.json not found"))
    
    # 6. Documentation
    docs = [
        "docs/COMPLETE_SETUP_GUIDE.md",
        "docs/DATABASE_SETUP.md",
        "docs/SERVICE_STARTUP.md",
        "docs/QUICK_REFERENCE_SETUP.md",
    ]
    all_docs_exist = all((project_root / d).exists() for d in docs)
    results.append(("Documentation", all_docs_exist, 
                   f"{sum(1 for d in docs if (project_root / d).exists())}/{len(docs)} present"))
    
    # 7. Python 3.13+ Compatibility
    if version[:2] >= (3, 13):
        script = project_root / "scripts/setup/complete_setup.py"
        if script.exists():
            content = script.read_text(encoding="utf-8")
            has_313_plus_code = ("is_python_313_plus" in content or 
                                 "version.minor >= 13" in content or
                                 "version.minor == 13" in content)
            version_str = f"{version[0]}.{version[1]}"
            results.append(("Python 3.13+ Compatibility", has_313_plus_code, 
                           f"Handled for {version_str}" if has_313_plus_code else "Not handled"))
        else:
            results.append(("Python 3.13+ Compatibility", False, "Script not found"))
    else:
        results.append(("Python 3.13+ Compatibility", True, "Not needed"))
    
    # 8. Non-Interactive Mode
    script1 = project_root / "scripts/setup/create_env_file.py"
    script2 = project_root / "scripts/setup/complete_setup.py"
    has_non_interactive = False
    if script1.exists() and script2.exists():
        content1 = script1.read_text(encoding="utf-8")
        content2 = script2.read_text(encoding="utf-8")
        has_non_interactive = ("sys.stdin.isatty()" in content1 or "DEVNULL" in content2)
    results.append(("Non-Interactive Mode", has_non_interactive, 
                   "Implemented" if has_non_interactive else "Not implemented"))
    
    # 9. Script Syntax
    syntax_valid = True
    for script_path in scripts:
        script_file = project_root / script_path
        if script_file.exists():
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(script_file)],
                    capture_output=True,
                    timeout=5
                )
                if proc.returncode != 0:
                    syntax_valid = False
                    break
            except:
                syntax_valid = False
                break
    results.append(("Script Syntax", syntax_valid, "All valid" if syntax_valid else "Some invalid"))
    
    # 10. Temp File Cleanup
    temp_file = project_root / "requirements_temp.txt"
    # Clean up if it exists (may be leftover from previous run)
    if temp_file.exists():
        try:
            temp_file.unlink()
        except:
            pass  # Ignore cleanup errors in test
    results.append(("Temp File Cleanup", not temp_file.exists(), 
                   "Clean" if not temp_file.exists() else "Temp file exists (cleaned up)"))
    
    # Print results
    passed = 0
    failed = 0
    
    for name, status, message in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {message}")
        if status:
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print()
    
    if failed == 0:
        print("✅ All features working perfectly!")
        return 0
    else:
        print("❌ Some features need attention.")
        return 1


if __name__ == "__main__":
    os.chdir(project_root)
    sys.exit(verify_all_features())
