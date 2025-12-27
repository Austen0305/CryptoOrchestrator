#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runtime Diagnostics Script
Detects common runtime issues and provides fixes
"""

import os
import sys
import io
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

# Fix Windows encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class DiagnosticIssue:
    """Represents a diagnostic issue"""
    def __init__(self, severity: str, category: str, message: str, fix: str):
        self.severity = severity  # "error", "warning", "info"
        self.category = category
        self.message = message
        self.fix = fix


class RuntimeDiagnostics:
    """Runtime diagnostics system"""
    
    def __init__(self):
        self.issues: List[DiagnosticIssue] = []
        self.project_root = Path(__file__).parent.parent.parent
    
    def check_env_file(self) -> bool:
        """Check if .env file exists"""
        env_file = self.project_root / ".env"
        if not env_file.exists():
            self.issues.append(DiagnosticIssue(
                severity="error",
                category="Environment",
                message=".env file not found",
                fix="Run: python scripts/setup/create_env_file.py"
            ))
            return False
        return True
    
    def check_database_connection(self) -> bool:
        """Check database connection"""
        try:
            sys.path.insert(0, str(self.project_root))
            from server_fastapi.database import get_db_context
            from sqlalchemy import text
            
            import asyncio
            async def test_db():
                async with get_db_context() as session:
                    await session.execute(text("SELECT 1"))
            
            asyncio.run(test_db())
            return True
        except Exception as e:
            self.issues.append(DiagnosticIssue(
                severity="error",
                category="Database",
                message=f"Database connection failed: {e}",
                fix="Check DATABASE_URL in .env file and ensure database is running"
            ))
            return False
    
    def check_migrations(self) -> bool:
        """Check if migrations are up to date"""
        try:
            from alembic.config import Config
            from alembic import command
            from alembic.runtime.migration import MigrationContext
            from sqlalchemy import create_engine
            
            alembic_ini = self.project_root / "alembic.ini"
            if not alembic_ini.exists():
                return True  # Skip if no Alembic config
            
            db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/app.db")
            sync_url = db_url.replace("sqlite+aiosqlite:///", "sqlite:///")
            sync_url = sync_url.replace("postgresql+asyncpg://", "postgresql://")
            
            engine = create_engine(sync_url)
            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()
                
                # Check if migrations need to be run
                cfg = Config(str(alembic_ini))
                cfg.set_main_option("sqlalchemy.url", sync_url)
                script = command.ScriptDirectory.from_config(cfg)
                head_rev = script.get_current_head()
                
                if current_rev != head_rev:
                    self.issues.append(DiagnosticIssue(
                        severity="warning",
                        category="Database",
                        message=f"Database migrations not up to date (current: {current_rev}, head: {head_rev})",
                        fix="Run: alembic upgrade head"
                    ))
                    return False
            return True
        except Exception:
            return True  # Skip if check fails
    
    def check_dependencies(self) -> bool:
        """Check if dependencies are installed"""
        critical_packages = ["fastapi", "uvicorn", "sqlalchemy", "httpx"]
        missing = []
        
        for package in critical_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            self.issues.append(DiagnosticIssue(
                severity="error",
                category="Dependencies",
                message=f"Missing packages: {', '.join(missing)}",
                fix="Run: pip install -r requirements.txt"
            ))
            return False
        return True
    
    def check_ports(self) -> bool:
        """Check if required ports are available"""
        import socket
        
        ports_to_check = [
            (8000, "Backend (FastAPI)"),
            (5173, "Frontend (Vite)"),
            (5432, "PostgreSQL"),
            (6379, "Redis"),
        ]
        
        conflicts = []
        for port, service in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is in use - might be our service or conflict
                # Check if it's actually our service by checking if it responds
                try:
                    import httpx
                    response = httpx.get(f"http://localhost:{port}/health", timeout=1)
                    if response.status_code < 500:
                        continue  # It's our service, that's OK
                except:
                    pass
                
                conflicts.append(f"{service} (port {port})")
        
        if conflicts:
            self.issues.append(DiagnosticIssue(
                severity="warning",
                category="Network",
                message=f"Port conflicts detected: {', '.join(conflicts)}",
                fix="Stop conflicting services or change ports in .env"
            ))
            return False
        return True
    
    def check_env_variables(self) -> bool:
        """Check critical environment variables"""
        required_vars = ["DATABASE_URL"]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            self.issues.append(DiagnosticIssue(
                severity="error",
                category="Environment",
                message=f"Missing required environment variables: {', '.join(missing)}",
                fix="Create .env file: python scripts/setup/create_env_file.py"
            ))
            return False
        
        # Check secret strength in production
        if os.getenv("NODE_ENV") == "production":
            jwt_secret = os.getenv("JWT_SECRET", "")
            if len(jwt_secret) < 32:
                self.issues.append(DiagnosticIssue(
                    severity="error",
                    category="Security",
                    message="JWT_SECRET is too short (minimum 32 characters)",
                    fix="Generate a strong secret: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                ))
                return False
        
        return True
    
    def run_all_checks(self) -> Dict[str, bool]:
        """Run all diagnostic checks"""
        print("🔍 Running Runtime Diagnostics...")
        print("=" * 60)
        
        results = {
            "env_file": self.check_env_file(),
            "env_variables": self.check_env_variables(),
            "dependencies": self.check_dependencies(),
            "import_errors": self.check_import_errors(),
            "database": self.check_database_connection(),
            "migrations": self.check_migrations(),
            "ports": self.check_ports(),
            "api_endpoints": self.check_api_endpoints(),
            "frontend_build": self.check_frontend_build(),
        }
        
        return results
    
    def print_report(self):
        """Print diagnostic report"""
        print("\n" + "=" * 60)
        print("📋 Diagnostic Report")
        print("-" * 60)
        
        if not self.issues:
            print("✅ No issues found!")
            return
        
        # Group by severity
        errors = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        info = [i for i in self.issues if i.severity == "info"]
        
        if errors:
            print("\n❌ Errors:")
            for issue in errors:
                print(f"  [{issue.category}] {issue.message}")
                print(f"     Fix: {issue.fix}")
        
        if warnings:
            print("\n⚠️  Warnings:")
            for issue in warnings:
                print(f"  [{issue.category}] {issue.message}")
                print(f"     Fix: {issue.fix}")
        
        if info:
            print("\nℹ️  Info:")
            for issue in info:
                print(f"  [{issue.category}] {issue.message}")
    
    def check_api_endpoints(self) -> bool:
        """Check if API endpoints are accessible"""
        try:
            import httpx
            base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            
            import asyncio
            async def test_endpoints():
                async with httpx.AsyncClient(timeout=5.0) as client:
                    try:
                        response = await client.get(f"{base_url}/health")
                        if response.status_code < 500:
                            return True
                    except:
                        pass
                    return False
            
            result = asyncio.run(test_endpoints())
            if not result:
                self.issues.append(DiagnosticIssue(
                    severity="warning",
                    category="API",
                    message="Backend API not accessible",
                    fix="Start backend: npm run dev:fastapi"
                ))
                return False
            return True
        except Exception:
            return True  # Skip if check fails
    
    def check_frontend_build(self) -> bool:
        """Check if frontend is built or dev server running"""
        frontend_dist = self.project_root / "client" / "dist"
        if not frontend_dist.exists():
            # Check if dev server might be running
            try:
                import httpx
                response = httpx.get("http://localhost:5173", timeout=2)
                if response.status_code < 500:
                    return True  # Dev server is running
            except:
                pass
            
            self.issues.append(DiagnosticIssue(
                severity="info",
                category="Frontend",
                message="Frontend not built (dev server may be running)",
                fix="Build frontend: npm run build, or start dev server: npm run dev"
            ))
        return True
    
    def check_import_errors(self) -> bool:
        """Check for import errors in critical modules"""
        critical_modules = [
            "server_fastapi.main",
            "server_fastapi.database",
            "server_fastapi.config.settings",
        ]
        
        failed = []
        for module in critical_modules:
            try:
                __import__(module)
            except Exception as e:
                failed.append(f"{module}: {e}")
        
        if failed:
            self.issues.append(DiagnosticIssue(
                severity="error",
                category="Dependencies",
                message=f"Import errors: {', '.join(failed)}",
                fix="Install dependencies: pip install -r requirements.txt"
            ))
            return False
        return True
    
    def auto_fix(self) -> bool:
        """Attempt to auto-fix common issues"""
        print("\n🔧 Attempting Auto-Fix...")
        print("-" * 60)
        
        fixed = 0
        
        for issue in self.issues:
            if issue.category == "Environment" and ".env file not found" in issue.message:
                try:
                    result = subprocess.run(
                        [sys.executable, "scripts/setup/create_env_file.py"],
                        cwd=self.project_root,
                        check=False
                    )
                    if result.returncode == 0:
                        print(f"  ✅ Fixed: Created .env file")
                        fixed += 1
                except Exception as e:
                    print(f"  ❌ Could not auto-fix: {e}")
            
            elif issue.category == "Database" and "migrations not up to date" in issue.message:
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "alembic", "upgrade", "head"],
                        cwd=self.project_root,
                        check=False
                    )
                    if result.returncode == 0:
                        print(f"  ✅ Fixed: Ran database migrations")
                        fixed += 1
                except Exception as e:
                    print(f"  ❌ Could not auto-fix: {e}")
        
        if fixed > 0:
            print(f"\n✅ Auto-fixed {fixed} issue(s)")
            return True
        
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Runtime diagnostics for CryptoOrchestrator")
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Attempt to auto-fix common issues"
    )
    
    args = parser.parse_args()
    
    diagnostics = RuntimeDiagnostics()
    diagnostics.run_all_checks()
    diagnostics.print_report()
    
    if args.auto_fix:
        diagnostics.auto_fix()
        # Re-run checks after fixes
        print("\n🔍 Re-running checks after fixes...")
        diagnostics.issues = []
        diagnostics.run_all_checks()
        diagnostics.print_report()
    
    # Exit with error code if errors found
    errors = [i for i in diagnostics.issues if i.severity == "error"]
    sys.exit(0 if len(errors) == 0 else 1)


if __name__ == "__main__":
    main()
