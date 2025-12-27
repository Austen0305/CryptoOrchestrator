#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Project Setup Script
One-command setup for CryptoOrchestrator
"""

import os
import sys
import asyncio
import io
import subprocess
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def print_step(step_num: int, total: int, message: str):
    """Print setup step"""
    print(f"\n[{step_num}/{total}] {message}")
    print("-" * 60)


def check_system_requirements() -> bool:
    """Check system requirements"""
    print("🔍 Checking System Requirements...")
    
    # Check Python
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    
    # Check Node.js
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_str = result.stdout.strip()
            version_num = int(version_str.replace("v", "").split(".")[0])
            if version_num >= 18:
                print(f"✅ Node.js {version_str}")
            else:
                print(f"❌ Node.js 18+ required, found {version_str}")
                return False
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not installed")
        return False
    
    return True


def create_env_file() -> bool:
    """Create .env file"""
    try:
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        
        # If .env exists, skip creation (preserve existing configuration)
        if env_file.exists():
            print("✅ .env file already exists, skipping creation")
            print("   (To recreate, delete .env and run setup again)")
            return True
        
        # Create .env file non-interactively (no prompts)
        # Use --overwrite flag and redirect stdin to avoid prompts
        result = subprocess.run(
            [sys.executable, "scripts/setup/create_env_file.py", "--overwrite"],
            cwd=project_root,
            check=False,
            stdin=subprocess.DEVNULL,  # Prevent any input prompts
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if result.stdout:
                print(result.stdout)
            return True
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            print(f"❌ Failed to create .env file: {error_msg}")
            return False
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def install_python_dependencies() -> bool:
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    project_root = Path(__file__).parent.parent.parent
    
    # Check if we're in a virtual environment
    import sys
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if not in_venv:
        # Check if .venv exists and suggest activation
        venv_python = project_root / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / "python.exe" if sys.platform == "win32" else "python"
        if (project_root / ".venv").exists():
            print("  ⚠️  Virtual environment (.venv) detected but not activated")
            print("  💡 Activate it with: .venv\\Scripts\\Activate.ps1 (Windows) or source .venv/bin/activate (Linux/Mac)")
            print("  📦 Installing to current Python environment...")
    
    # Check Python version for TensorFlow compatibility
    version = sys.version_info
    # TensorFlow not compatible with Python 3.13+ (including 3.14)
    is_python_313_plus = version.major == 3 and version.minor >= 13
    
    if is_python_313_plus:
        version_str = f"{version.major}.{version.minor}"
        print(f"⚠️  Python {version_str} detected - TensorFlow not compatible, installing without TensorFlow...")
        # Create temporary requirements without TensorFlow
        requirements_file = project_root / "requirements.txt"
        temp_requirements = project_root / "requirements_temp.txt"
        
        try:
            with open(requirements_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Filter out TensorFlow and related dependencies
            filtered_lines = []
            skip_next = False
            for line in lines:
                stripped = line.strip()
                # Skip TensorFlow line
                if "tensorflow" in stripped.lower() and not stripped.startswith("#"):
                    print(f"  ⏭️  Skipping: {stripped}")
                    continue
                # Skip numpy pin if it's TensorFlow-related
                if "numpy" in stripped.lower() and "<2.0.0" in stripped and not stripped.startswith("#"):
                    # Keep numpy but allow newer versions for Python 3.13
                    filtered_lines.append("numpy>=1.24.3\n")
                    continue
                filtered_lines.append(line)
            
            with open(temp_requirements, "w", encoding="utf-8") as f:
                f.writelines(filtered_lines)
            
            # Install with temporary requirements
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(temp_requirements)],
                cwd=project_root,
                check=False
            )
            
            # Clean up temp file (ensure it's deleted even if installation fails)
            cleanup_success = False
            try:
                if temp_requirements.exists():
                    temp_requirements.unlink()
                    cleanup_success = True
            except Exception as cleanup_error:
                # Log but don't fail on cleanup errors
                print(f"  ⚠️  Warning: Could not clean up temp file: {cleanup_error}")
            
            # Final cleanup attempt if first one failed
            if not cleanup_success and temp_requirements.exists():
                try:
                    import time
                    time.sleep(0.1)  # Brief delay for file system
                    if temp_requirements.exists():
                        temp_requirements.unlink()
                except:
                    pass  # Ignore final cleanup errors
            
            if result.returncode == 0:
                version_str = f"{version.major}.{version.minor}"
                print(f"✅ Python dependencies installed (TensorFlow skipped for Python {version_str})")
                print(f"   ⚠️  ML features requiring TensorFlow will not work on Python {version_str}")
                return True
            else:
                print(f"❌ Failed to install Python dependencies: {result.returncode}")
                return False
        except Exception as e:
            print(f"❌ Error creating temporary requirements: {e}")
            # Ensure temp file is cleaned up even on error
            try:
                if temp_requirements.exists():
                    temp_requirements.unlink()
            except:
                pass
            # Fall back to regular installation
            pass
    
    # Regular installation for Python 3.11-3.12
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=project_root,
            check=False
        )
        if result.returncode == 0:
            print("✅ Python dependencies installed")
            return True
        else:
            print(f"❌ Failed to install Python dependencies (exit code: {result.returncode})")
            print("   Try installing manually: pip install -r requirements.txt")
            return False
    except Exception as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False


def install_node_dependencies() -> bool:
    """Install Node.js dependencies"""
    print("📦 Installing Node.js dependencies...")
    try:
        subprocess.run(
            ["npm", "install", "--legacy-peer-deps"],
            cwd=Path(__file__).parent.parent.parent,
            check=True
        )
        print("✅ Node.js dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Node.js dependencies: {e}")
        return False


async def initialize_database() -> bool:
    """Initialize database"""
    try:
        from scripts.setup.init_database import init_database as init_db
        return await init_db(
            create_db=True,
            run_migrations_flag=True,
            verify=True,
            seed_data=False
        )
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def verify_dependencies() -> bool:
    """Verify dependencies"""
    try:
        result = subprocess.run(
            [sys.executable, "scripts/setup/verify_dependencies.py"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Dependency verification failed: {e}")
        return False


async def run_complete_setup() -> bool:
    """Run complete setup"""
    print("🚀 CryptoOrchestrator Complete Setup")
    print("=" * 60)
    
    steps = [
        ("Checking system requirements", check_system_requirements),
        ("Creating .env file", create_env_file),
        ("Installing Python dependencies", install_python_dependencies),
        ("Installing Node.js dependencies", install_node_dependencies),
        ("Initializing database", initialize_database),
        ("Verifying dependencies", verify_dependencies),
    ]
    
    for i, (step_name, step_func) in enumerate(steps, 1):
        print_step(i, len(steps), step_name)
        try:
            if asyncio.iscoroutinefunction(step_func):
                success = await step_func()
            elif callable(step_func):
                success = step_func()
            else:
                success = False
                print(f"❌ Invalid step function for: {step_name}")
            
            if not success:
                print(f"\n❌ Setup failed at step: {step_name}")
                return False
        except Exception as e:
            print(f"\n❌ Setup failed at step {step_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 60)
    print("✅ Complete setup finished successfully!")
    print("\n📋 Next Steps:")
    print("  1. Review .env file and configure any optional settings")
    print("  2. Start services: npm run start:all")
    print("  3. Verify setup: npm run setup:health")
    print("  4. Run feature verification: npm run setup:verify")
    print("\n💡 Quick Commands:")
    print("  - Health check: npm run setup:health")
    print("  - Feature verification: npm run setup:verify")
    print("  - Runtime diagnostics: python scripts/diagnostics/runtime_diagnostics.py --auto-fix")
    print("  - Start all services: npm run start:all")
    
    return True


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    try:
        success = asyncio.run(run_complete_setup())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
