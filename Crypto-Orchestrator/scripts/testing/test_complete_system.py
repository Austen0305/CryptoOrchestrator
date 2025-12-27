#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete System Testing
Tests the entire setup system end-to-end
"""

import os
import sys
import subprocess
from pathlib import Path
import io

# Fix Windows encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent.parent


def test_complete_system():
    """Test the complete setup system"""
    print("🧪 Complete System Testing")
    print("=" * 60)
    print()
    
    os.chdir(project_root)
    
    results = []
    
    # Test 1: All scripts exist and are valid
    print("1️⃣ Testing Script Validity...")
    scripts = [
        "scripts/setup/create_env_file.py",
        "scripts/setup/init_database.py",
        "scripts/setup/verify_dependencies.py",
        "scripts/setup/complete_setup.py",
        "scripts/setup/health_check.py",
        "scripts/diagnostics/runtime_diagnostics.py",
        "scripts/verification/comprehensive_feature_verification.py",
    ]
    
    all_valid = True
    for script in scripts:
        script_path = project_root / script
        if script_path.exists():
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(script_path)],
                    capture_output=True,
                    timeout=5
                )
                if proc.returncode == 0:
                    print(f"  ✅ {script_path.name}")
                else:
                    print(f"  ❌ {script_path.name}: Syntax error")
                    all_valid = False
            except Exception as e:
                print(f"  ❌ {script_path.name}: {e}")
                all_valid = False
        else:
            print(f"  ❌ {script_path.name}: Not found")
            all_valid = False
    
    results.append(("Script Validity", all_valid))
    print()
    
    # Test 2: NPM scripts
    print("2️⃣ Testing NPM Scripts...")
    package_json = project_root / "package.json"
    if package_json.exists():
        import json
        with open(package_json, "r") as f:
            data = json.load(f)
        scripts_data = data.get("scripts", {})
        setup_scripts = [s for s in scripts_data.keys() if s.startswith("setup:")]
        print(f"  ✅ Found {len(setup_scripts)} setup scripts")
        results.append(("NPM Scripts", len(setup_scripts) >= 7))
    else:
        print("  ❌ package.json not found")
        results.append(("NPM Scripts", False))
    print()
    
    # Test 3: Documentation
    print("3️⃣ Testing Documentation...")
    docs = [
        "docs/COMPLETE_SETUP_GUIDE.md",
        "docs/DATABASE_SETUP.md",
        "docs/SERVICE_STARTUP.md",
        "docs/QUICK_REFERENCE_SETUP.md",
    ]
    all_docs = all((project_root / d).exists() for d in docs)
    print(f"  ✅ {sum(1 for d in docs if (project_root / d).exists())}/{len(docs)} docs present")
    results.append(("Documentation", all_docs))
    print()
    
    # Test 4: Python version compatibility
    print("4️⃣ Testing Python Version Compatibility...")
    version = sys.version_info
    is_compatible = version.major >= 3 and version.minor >= 11
    print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} (compatible: {is_compatible})")
    results.append(("Python Version", is_compatible))
    print()
    
    # Test 5: .env file
    print("5️⃣ Testing .env File...")
    env_file = project_root / ".env"
    env_exists = env_file.exists()
    print(f"  ✅ .env file: {'Exists' if env_exists else 'Missing'}")
    results.append((".env File", env_exists))
    print()
    
    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    print()
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print()
    
    if passed == total:
        print("✅ Complete system test passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(test_complete_system())
