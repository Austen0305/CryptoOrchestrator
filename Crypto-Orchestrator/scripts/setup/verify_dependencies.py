#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Verification Script
Verifies all required dependencies are installed and compatible
"""

import sys
import subprocess
import importlib
import io
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# Fix Windows encoding issues
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def check_python_version() -> Tuple[bool, str]:
    """Check Python version"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    # Check if Python 3.11+
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        return False, f"Python 3.11+ required, found {version_str}"
    
    # Warn about Python 3.13+ TensorFlow issues
    if version.major == 3 and version.minor >= 13:
        return True, f"Python {version_str} (⚠️  TensorFlow not compatible with Python 3.13+, ML features may not work)"
    
    return True, f"Python {version_str} ✅"


def check_node_version() -> Tuple[bool, str]:
    """Check Node.js version"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_str = result.stdout.strip()
            # Parse version (v18.0.0 -> 18)
            version_num = int(version_str.replace("v", "").split(".")[0])
            if version_num >= 18:
                return True, f"Node.js {version_str} ✅"
            return False, f"Node.js 18+ required, found {version_str}"
        return False, "Node.js not found"
    except FileNotFoundError:
        return False, "Node.js not installed"
    except Exception as e:
        return False, f"Error checking Node.js: {e}"


def check_python_package(package_name: str, import_name: Optional[str] = None) -> Tuple[bool, str]:
    """Check if Python package is installed"""
    import_name = import_name or package_name
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "unknown")
        return True, f"{package_name} {version} ✅"
    except ImportError:
        return False, f"{package_name} ❌ not installed"


def check_npm_package(package_name: str) -> Tuple[bool, str]:
    """Check if npm package is installed (in node_modules)"""
    try:
        node_modules = Path("node_modules") / package_name
        if node_modules.exists():
            # Try to get version from package.json
            pkg_json = node_modules / "package.json"
            if pkg_json.exists():
                import json
                with open(pkg_json, "r") as f:
                    pkg_data = json.load(f)
                    version = pkg_data.get("version", "installed")
                    return True, f"{package_name} {version} ✅"
            return True, f"{package_name} ✅ (installed)"
        return False, f"{package_name} ❌ not found in node_modules"
    except Exception as e:
        return False, f"{package_name} ❌ error checking: {e}"


def read_requirements() -> List[str]:
    """Read requirements.txt"""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        return []
    
    packages = []
    with open(requirements_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Parse package name (handle version constraints)
                package_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split("[")[0].strip()
                if package_name:
                    packages.append(package_name)
    return packages


def read_package_json() -> Dict[str, str]:
    """Read package.json dependencies"""
    package_json = Path("package.json")
    if not package_json.exists():
        return {}
    
    import json
    with open(package_json, "r") as f:
        data = json.load(f)
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        return {**deps, **dev_deps}


def verify_python_packages() -> Tuple[int, int]:
    """Verify Python packages"""
    print("\n📦 Verifying Python packages...")
    print("-" * 60)
    
    # Critical packages to check
    critical_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("alembic", "alembic"),
        ("pydantic", "pydantic"),
        ("httpx", "httpx"),
        ("redis", "redis"),
        ("celery", "celery"),
        ("web3", "web3"),
        ("pytest", "pytest"),
    ]
    
    passed = 0
    failed = 0
    
    for package_name, import_name in critical_packages:
        success, message = check_python_package(package_name, import_name)
        print(f"  {message}")
        if success:
            passed += 1
        else:
            failed += 1
    
    # Check optional packages
    optional_packages = [
        ("tensorflow", "tensorflow"),
        ("torch", "torch"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
    ]
    
    print("\n📦 Optional packages (ML/Data):")
    for package_name, import_name in optional_packages:
        success, message = check_python_package(package_name, import_name)
        if not success:
            message = message.replace("❌", "⚠️")
        print(f"  {message}")
        if success:
            passed += 1
    
    return passed, failed


def verify_npm_packages() -> Tuple[int, int]:
    """Verify npm packages"""
    print("\n📦 Verifying npm packages...")
    print("-" * 60)
    
    # Critical packages
    critical_packages = [
        "react",
        "react-dom",
        "@tanstack/react-query",
        "vite",
        "typescript",
        "@playwright/test",
    ]
    
    passed = 0
    failed = 0
    
    for package_name in critical_packages:
        success, message = check_npm_package(package_name)
        print(f"  {message}")
        if success:
            passed += 1
        else:
            failed += 1
    
    return passed, failed


def test_imports() -> Tuple[int, int]:
    """Test critical imports"""
    print("\n🧪 Testing critical imports...")
    print("-" * 60)
    
    imports_to_test = [
        ("fastapi", "FastAPI"),
        ("sqlalchemy", "create_engine"),
        ("pydantic", "BaseModel"),
        ("httpx", "AsyncClient"),
        ("web3", "Web3"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, item_name in imports_to_test:
        try:
            module = importlib.import_module(module_name)
            getattr(module, item_name)
            print(f"  ✅ {module_name}.{item_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {module_name}.{item_name}: {e}")
            failed += 1
    
    return passed, failed


def provide_installation_commands(failed_packages: List[str]) -> str:
    """Provide installation commands for missing packages"""
    if not failed_packages:
        return ""
    
    commands = [
        "\n📥 To install missing Python packages:",
        "  pip install -r requirements.txt",
        "",
        "📥 To install missing npm packages:",
        "  npm install",
        "",
    ]
    
    return "\n".join(commands)


def main():
    """Main entry point"""
    print("🔍 CryptoOrchestrator Dependency Verification")
    print("=" * 60)
    
    all_passed = True
    total_passed = 0
    total_failed = 0
    
    # Check Python version
    success, message = check_python_version()
    print(f"\n🐍 Python: {message}")
    if not success:
        all_passed = False
        total_failed += 1
    else:
        total_passed += 1
    
    # Check Node.js version
    success, message = check_node_version()
    print(f"📦 Node.js: {message}")
    if not success:
        all_passed = False
        total_failed += 1
    else:
        total_passed += 1
    
    # Verify Python packages
    py_passed, py_failed = verify_python_packages()
    total_passed += py_passed
    total_failed += py_failed
    if py_failed > 0:
        all_passed = False
    
    # Verify npm packages
    npm_passed, npm_failed = verify_npm_packages()
    total_passed += npm_passed
    total_failed += npm_failed
    if npm_failed > 0:
        all_passed = False
    
    # Test imports
    import_passed, import_failed = test_imports()
    total_passed += import_passed
    total_failed += import_failed
    if import_failed > 0:
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Summary: {total_passed} passed, {total_failed} failed")
    
    if all_passed:
        print("✅ All dependencies verified successfully!")
        return 0
    else:
        print("❌ Some dependencies are missing or incompatible")
        print(provide_installation_commands([]))
        return 1


if __name__ == "__main__":
    sys.exit(main())
