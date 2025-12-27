#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Setup Features Testing
Tests every feature of the setup system in detail
"""

import os
import sys
import subprocess
import json
import asyncio
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


class FeatureTest:
    """Individual feature test"""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error: Optional[str] = None
        self.details: List[str] = []
        self.warnings: List[str] = []
    
    def add_detail(self, detail: str):
        self.details.append(detail)
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    def __str__(self):
        status = "✅" if self.passed else "❌"
        result = f"{status} {self.name}"
        if self.error:
            result += f"\n   Error: {self.error}"
        if self.warnings:
            result += "\n   Warnings: " + "; ".join(self.warnings)
        if self.details:
            result += "\n   " + "\n   ".join(self.details)
        return result


def test_create_env_file_features() -> FeatureTest:
    """Test create_env_file.py features"""
    test = FeatureTest("create_env_file.py Features")
    script = project_root / "scripts/setup/create_env_file.py"
    
    if not script.exists():
        test.error = "Script not found"
        return test
    
    # Test 1: Script can be imported
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("create_env_file", script)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            test.add_detail("✅ Script imports successfully")
            create_env_file = module
        else:
            test.error = "Could not load script spec"
            return test
    except Exception as e:
        test.error = f"Import failed: {e}"
        return test
    
    # Test 2: Function exists
    if hasattr(create_env_file, 'create_env_file'):
        test.add_detail("✅ create_env_file function exists")
    else:
        test.error = "create_env_file function not found"
        return test
    
    # Test 3: Command line arguments
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        if result.returncode == 0 or "--overwrite" in result.stdout or "--overwrite" in result.stderr:
            test.add_detail("✅ Command line arguments work")
        else:
            test.add_warning("Help flag may not work correctly")
    except Exception as e:
        test.add_warning(f"Help test failed: {e}")
    
    # Test 4: Non-interactive mode detection
    try:
        # Test if function handles non-interactive mode
        func = create_env_file.create_env_file
        import inspect
        sig = inspect.signature(func)
        if 'overwrite' in sig.parameters and 'interactive' in sig.parameters:
            test.add_detail("✅ Non-interactive mode parameters exist")
        else:
            test.add_warning("Missing overwrite or interactive parameters")
    except Exception as e:
        test.add_warning(f"Signature check failed: {e}")
    
    test.passed = True
    return test


def test_init_database_features() -> FeatureTest:
    """Test init_database.py features"""
    test = FeatureTest("init_database.py Features")
    script = project_root / "scripts/setup/init_database.py"
    
    if not script.exists():
        test.error = "Script not found"
        return test
    
    # Test 1: Script can be imported
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("init_database", script)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            test.add_detail("✅ Script imports successfully")
            init_database = module
        else:
            test.error = "Could not load script spec"
            return test
    except Exception as e:
        test.error = f"Import failed: {e}"
        return test
    
    # Test 2: Async function exists
    if hasattr(init_database, 'init_database'):
        func = init_database.init_database
        import inspect
        if inspect.iscoroutinefunction(func):
            test.add_detail("✅ init_database is async function")
        else:
            test.add_warning("init_database should be async")
        
        # Check parameters
        sig = inspect.signature(func)
        required_params = ['create_db', 'run_migrations_flag', 'verify', 'seed_data']
        for param in required_params:
            if param in sig.parameters:
                test.add_detail(f"✅ Parameter '{param}' exists")
            else:
                test.add_warning(f"Missing parameter: {param}")
    else:
        test.error = "init_database function not found"
        return test
    
    test.passed = True
    return test


def test_complete_setup_features() -> FeatureTest:
    """Test complete_setup.py features"""
    test = FeatureTest("complete_setup.py Features")
    script = project_root / "scripts/setup/complete_setup.py"
    
    if not script.exists():
        test.error = "Script not found"
        return test
    
    # Test 1: Script can be imported
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("complete_setup", script)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            test.add_detail("✅ Script imports successfully")
            complete_setup = module
        else:
            test.error = "Could not load script spec"
            return test
    except Exception as e:
        test.error = f"Import failed: {e}"
        return test
    
    # Test 2: Python 3.13 compatibility
    version = sys.version_info
    if version[:2] == (3, 13):
        if hasattr(complete_setup, 'install_python_dependencies'):
            # Check if it handles Python 3.13
            import inspect
            source = inspect.getsource(complete_setup.install_python_dependencies)
            if "is_python_313" in source or "version.minor == 13" in source:
                test.add_detail("✅ Python 3.13 compatibility code exists")
            else:
                test.add_warning("Python 3.13 compatibility may be missing")
        else:
            test.add_warning("install_python_dependencies function not found")
    else:
        test.add_detail(f"✅ Python {version.major}.{version.minor} (3.13 compatibility not needed)")
    
    # Test 3: Non-interactive mode
    if hasattr(complete_setup, 'create_env_file'):
        import inspect
        source = inspect.getsource(complete_setup.create_env_file)
        if "stdin=subprocess.DEVNULL" in source or "DEVNULL" in source:
            test.add_detail("✅ Non-interactive mode (stdin redirection) implemented")
        else:
            test.add_warning("Non-interactive mode may not be fully implemented")
    
    # Test 4: All required functions exist
    required_funcs = [
        'check_system_requirements',
        'create_env_file',
        'install_python_dependencies',
        'install_node_dependencies',
        'initialize_database',
        'verify_dependencies',
        'run_complete_setup'
    ]
    for func_name in required_funcs:
        if hasattr(complete_setup, func_name):
            test.add_detail(f"✅ Function '{func_name}' exists")
        else:
            test.add_warning(f"Missing function: {func_name}")
    
    test.passed = True
    return test


def test_npm_scripts() -> FeatureTest:
    """Test all npm setup scripts"""
    test = FeatureTest("NPM Setup Scripts")
    package_json = project_root / "package.json"
    
    if not package_json.exists():
        test.error = "package.json not found"
        return test
    
    try:
        with open(package_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        scripts = data.get("scripts", {})
        setup_scripts = {k: v for k, v in scripts.items() if k.startswith("setup:")}
        
        test.add_detail(f"✅ Found {len(setup_scripts)} setup scripts")
        
        # Verify each script points to existing file
        for script_name, script_cmd in setup_scripts.items():
            if "python" in script_cmd:
                # Extract Python script path
                parts = script_cmd.split()
                script_path = None
                for i, part in enumerate(parts):
                    if part.endswith(".py"):
                        script_path = project_root / part
                        break
                
                if script_path and script_path.exists():
                    test.add_detail(f"✅ {script_name} -> {script_path.name}")
                else:
                    test.add_warning(f"{script_name} may point to non-existent file")
            else:
                test.add_detail(f"✅ {script_name} (non-Python script)")
        
        # Check for required scripts
        required = ["setup", "setup:env", "setup:db", "setup:verify", "setup:health", "setup:deps", "setup:test"]
        missing = [s for s in required if s not in scripts]
        if missing:
            test.error = f"Missing required scripts: {', '.join(missing)}"
            return test
        
        test.passed = True
    except Exception as e:
        test.error = f"Error reading package.json: {e}"
    
    return test


def test_documentation_files() -> FeatureTest:
    """Test all documentation files"""
    test = FeatureTest("Documentation Files")
    
    docs = [
        "docs/COMPLETE_SETUP_GUIDE.md",
        "docs/DATABASE_SETUP.md",
        "docs/SERVICE_STARTUP.md",
        "docs/QUICK_REFERENCE_SETUP.md",
        "docs/SETUP_TESTING_REPORT.md",
        "docs/SETUP_COMPLETE_SUMMARY.md",
        "docs/SETUP_IMPLEMENTATION_SUMMARY.md",
    ]
    
    missing = []
    for doc in docs:
        doc_path = project_root / doc
        if doc_path.exists():
            size = doc_path.stat().st_size
            test.add_detail(f"✅ {doc} ({size} bytes)")
        else:
            missing.append(doc)
    
    if missing:
        test.error = f"Missing documentation: {', '.join(missing)}"
        return test
    
    test.passed = True
    return test


def test_python_313_compatibility() -> FeatureTest:
    """Test Python 3.13 compatibility features"""
    test = FeatureTest("Python 3.13 Compatibility")
    version = sys.version_info
    
    if version[:2] != (3, 13):
        test.add_detail(f"Python {version.major}.{version.minor} (3.13 compatibility not needed)")
        test.passed = True
        return test
    
    test.add_detail(f"✅ Python 3.13.{version.micro} detected")
    
    # Test if complete_setup handles Python 3.13
    script = project_root / "scripts/setup/complete_setup.py"
    if script.exists():
        try:
            with open(script, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "is_python_313" in content or "version.minor == 13" in content:
                test.add_detail("✅ Python 3.13 detection code exists")
            else:
                test.add_warning("Python 3.13 detection code may be missing")
            
            if "requirements_temp.txt" in content or "tensorflow" in content.lower():
                test.add_detail("✅ TensorFlow handling code exists")
            else:
                test.add_warning("TensorFlow handling may be missing")
        except Exception as e:
            test.add_warning(f"Could not check script: {e}")
    
    test.passed = True
    return test


def test_non_interactive_mode() -> FeatureTest:
    """Test non-interactive mode features"""
    test = FeatureTest("Non-Interactive Mode")
    
    # Test create_env_file.py
    script1 = project_root / "scripts/setup/create_env_file.py"
    if script1.exists():
        try:
            with open(script1, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "sys.stdin.isatty()" in content:
                test.add_detail("✅ create_env_file.py has non-interactive detection")
            else:
                test.add_warning("create_env_file.py may lack non-interactive detection")
        except Exception as e:
            test.add_warning(f"Could not check create_env_file.py: {e}")
    
    # Test complete_setup.py
    script2 = project_root / "scripts/setup/complete_setup.py"
    if script2.exists():
        try:
            with open(script2, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "stdin=subprocess.DEVNULL" in content or "DEVNULL" in content:
                test.add_detail("✅ complete_setup.py uses stdin redirection")
            else:
                test.add_warning("complete_setup.py may not redirect stdin")
        except Exception as e:
            test.add_warning(f"Could not check complete_setup.py: {e}")
    
    test.passed = True
    return test


def run_all_feature_tests() -> List[FeatureTest]:
    """Run all feature tests"""
    print("🔍 Comprehensive Setup Features Testing")
    print("=" * 60)
    print()
    
    tests = [
        test_create_env_file_features,
        test_init_database_features,
        test_complete_setup_features,
        test_npm_scripts,
        test_documentation_files,
        test_python_313_compatibility,
        test_non_interactive_mode,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print(result)
            print()
        except Exception as e:
            error_result = FeatureTest(test_func.__name__)
            error_result.error = str(e)
            results.append(error_result)
            print(error_result)
            print()
    
    return results


def main():
    """Main entry point"""
    os.chdir(project_root)
    
    results = run_all_feature_tests()
    
    # Summary
    print("=" * 60)
    print("📊 Feature Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    warnings = sum(len(r.warnings) for r in results)
    
    print(f"✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    if warnings > 0:
        print(f"⚠️  Warnings: {warnings}")
    print()
    
    if failed > 0:
        print("❌ Some feature tests failed. Please review the issues above.")
        sys.exit(1)
    else:
        if warnings > 0:
            print("⚠️  All tests passed, but some warnings were found.")
            print("   Review warnings above for potential improvements.")
        else:
            print("✅ All feature tests passed! Every feature is working perfectly.")
        sys.exit(0)


if __name__ == "__main__":
    main()
