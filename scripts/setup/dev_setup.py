#!/usr/bin/env python3
"""
Development Environment Setup Script
Automates common development setup tasks
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"▶ Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        sys.exit(1)
    return result


def check_requirements():
    """Check if required tools are installed"""
    print("🔍 Checking requirements...")
    
    requirements = {
        "python": ("python", "--version"),
        "node": ("node", "--version"),
        "npm": ("npm", "--version"),
        "git": ("git", "--version"),
    }
    
    missing = []
    for name, (cmd, flag) in requirements.items():
        try:
            result = run_command(f"{cmd} {flag}", check=False)
            if result.returncode == 0:
                print(f"  ✅ {name}: {result.stdout.strip()}")
            else:
                missing.append(name)
        except FileNotFoundError:
            missing.append(name)
    
    if missing:
        print(f"❌ Missing requirements: {', '.join(missing)}")
        print("Please install them before continuing.")
        sys.exit(1)
    
    print("✅ All requirements met!\n")


def setup_python_env():
    """Setup Python virtual environment"""
    print("🐍 Setting up Python environment...")
    
    venv_path = Path(".venv")
    if venv_path.exists():
        print("  ℹ Virtual environment already exists")
    else:
        print("  Creating virtual environment...")
        run_command("python -m venv .venv")
        print("  ✅ Virtual environment created")
    
    # Determine activation script based on OS
    if sys.platform == "win32":
        pip = ".venv\\Scripts\\pip.exe"
        python = ".venv\\Scripts\\python.exe"
    else:
        pip = ".venv/bin/pip"
        python = ".venv/bin/python"
    
    print("  Installing Python dependencies...")
    run_command(f"{pip} install --upgrade pip")
    run_command(f"{pip} install -r requirements.txt")
    print("  ✅ Python dependencies installed\n")


def setup_node_env():
    """Setup Node.js environment"""
    print("📦 Setting up Node.js environment...")
    
    if Path("node_modules").exists():
        print("  ℹ node_modules already exists, skipping install")
    else:
        print("  Installing Node.js dependencies...")
        run_command("npm install")
        print("  ✅ Node.js dependencies installed\n")


def setup_env_file():
    """Setup .env file from template"""
    print("⚙️  Setting up environment file...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("  ℹ .env file already exists")
    elif env_example.exists():
        print("  Creating .env from template...")
        shutil.copy(env_example, env_file)
        print("  ✅ .env file created (please update with your values)")
    else:
        print("  ⚠ .env.example not found, skipping")
    
    print()


def setup_git_hooks():
    """Setup Git hooks"""
    print("🔧 Setting up Git hooks...")
    
    try:
        run_command("npm run prepare", check=False)
        print("  ✅ Git hooks configured\n")
    except:
        print("  ⚠ Git hooks setup skipped\n")


def setup_database():
    """Setup database"""
    print("🗄️  Setting up database...")
    
    # Check if database exists
    db_path = Path("cryptoorchestrator.db")
    if db_path.exists():
        print("  ℹ Database already exists")
    else:
        print("  Database will be created on first run")
    
    # Run migrations
    print("  Running database migrations...")
    if sys.platform == "win32":
        python = ".venv\\Scripts\\python.exe"
    else:
        python = ".venv/bin/python"
    
    run_command(f"{python} -m alembic upgrade head", check=False)
    print("  ✅ Database setup complete\n")


def print_next_steps():
    """Print next steps for the developer"""
    print("=" * 60)
    print("✅ Development environment setup complete!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("\n1. Update .env file with your configuration:")
    print("   - Set JWT_SECRET_KEY")
    print("   - Configure database URL (if not using SQLite)")
    print("   - Add API keys for exchanges, Stripe, etc.")
    
    print("\n2. Activate virtual environment:")
    if sys.platform == "win32":
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    
    print("\n3. Start the development server:")
    print("   npm run dev:fastapi")
    
    print("\n4. In another terminal, start the frontend:")
    print("   cd client && npm run dev")
    
    print("\n5. Access the application:")
    print("   - API: http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Frontend: http://localhost:5173")
    
    print("\n📚 Documentation:")
    print("   - README.md - Project overview")
    print("   - COMMANDS.md - Command reference")
    print("   - docs/ - Additional documentation")
    print("\n" + "=" * 60)


def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 CryptoOrchestrator Development Setup")
    print("=" * 60)
    print()
    
    check_requirements()
    setup_python_env()
    setup_node_env()
    setup_env_file()
    setup_git_hooks()
    setup_database()
    print_next_steps()


if __name__ == "__main__":
    main()

