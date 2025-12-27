#!/usr/bin/env python3
"""
Comprehensive Startup Verification Script
Checks all critical components before starting the application
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


class VerificationResult:
    """Result of a verification check"""

    def __init__(self, name: str, passed: bool, message: str = "", details: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details


class StartupVerifier:
    """Verifies all critical components before startup"""

    def __init__(self):
        self.results: List[VerificationResult] = []
        self.project_root = project_root

    def add_result(self, result: VerificationResult):
        """Add a verification result"""
        self.results.append(result)

    def check_python_version(self) -> VerificationResult:
        """Check Python version"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            return VerificationResult(
                "Python Version",
                True,
                f"Python {version.major}.{version.minor}.{version.micro}",
            )
        else:
            return VerificationResult(
                "Python Version",
                False,
                f"Python {version.major}.{version.minor}.{version.micro}",
                "Python 3.11+ required",
            )

    def check_env_file(self) -> VerificationResult:
        """Check if .env file exists"""
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"

        if env_file.exists():
            return VerificationResult("Environment File", True, ".env file exists")
        elif env_example.exists():
            return VerificationResult(
                "Environment File",
                False,
                ".env file not found",
                f"Copy {env_example.name} to .env and configure it",
            )
        else:
            return VerificationResult(
                "Environment File",
                False,
                ".env file not found",
                "Create .env file with required configuration",
            )

    def check_dependencies(self) -> VerificationResult:
        """Check if critical dependencies are installed"""
        critical_deps = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "pydantic",
            "alembic",
        ]

        missing = []
        for dep in critical_deps:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)

        if not missing:
            return VerificationResult(
                "Python Dependencies", True, "All critical dependencies installed"
            )
        else:
            return VerificationResult(
                "Python Dependencies",
                False,
                f"Missing: {', '.join(missing)}",
                "Run: pip install -r requirements.txt",
            )

    def check_node_dependencies(self) -> VerificationResult:
        """Check if node_modules exists"""
        node_modules = self.project_root / "node_modules"
        package_json = self.project_root / "package.json"

        if not package_json.exists():
            return VerificationResult(
                "Node Dependencies",
                False,
                "package.json not found",
                "This is a Python/Node.js project",
            )

        if node_modules.exists() and any(node_modules.iterdir()):
            return VerificationResult(
                "Node Dependencies", True, "node_modules directory exists"
            )
        else:
            return VerificationResult(
                "Node Dependencies",
                False,
                "node_modules not found or empty",
                "Run: npm install --legacy-peer-deps",
            )

    def check_database_config(self) -> VerificationResult:
        """Check database configuration"""
        try:
            from dotenv import load_dotenv

            env_file = self.project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file)

            database_url = os.getenv("DATABASE_URL")
            if database_url:
                # Check if it's SQLite (development) or PostgreSQL
                if "sqlite" in database_url.lower():
                    db_path = database_url.split("///")[-1] if "///" in database_url else None
                    if db_path and os.path.exists(db_path):
                        return VerificationResult(
                            "Database Config",
                            True,
                            f"SQLite database configured: {db_path}",
                        )
                    else:
                        return VerificationResult(
                            "Database Config",
                            True,
                            "SQLite database configured (will be created on first run)",
                        )
                else:
                    return VerificationResult(
                        "Database Config",
                        True,
                        "PostgreSQL database configured",
                    )
            else:
                return VerificationResult(
                    "Database Config",
                    False,
                    "DATABASE_URL not set",
                    "Set DATABASE_URL in .env file",
                )
        except ImportError:
            return VerificationResult(
                "Database Config",
                False,
                "python-dotenv not installed",
                "Install: pip install python-dotenv",
            )

    def check_jwt_secret(self) -> VerificationResult:
        """Check if JWT secret is configured"""
        try:
            from dotenv import load_dotenv

            env_file = self.project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file)

            jwt_secret = os.getenv("JWT_SECRET")
            if jwt_secret:
                if len(jwt_secret) >= 32:
                    if jwt_secret != "your-secret-key-change-in-production-minimum-32-chars":
                        return VerificationResult(
                            "JWT Secret", True, "JWT secret configured"
                        )
                    else:
                        return VerificationResult(
                            "JWT Secret",
                            False,
                            "JWT secret is default value",
                            "Change JWT_SECRET in .env to a secure random value",
                        )
                else:
                    return VerificationResult(
                        "JWT Secret",
                        False,
                        "JWT secret too short",
                        "JWT_SECRET must be at least 32 characters",
                    )
            else:
                return VerificationResult(
                    "JWT Secret",
                    False,
                    "JWT_SECRET not set",
                    "Set JWT_SECRET in .env file",
                )
        except ImportError:
            return VerificationResult(
                "JWT Secret",
                False,
                "python-dotenv not installed",
                "Install: pip install python-dotenv",
            )

    async def check_database_connection(self) -> VerificationResult:
        """Check if database connection works"""
        try:
            from server_fastapi.database import get_db_session
            from sqlalchemy import text

            async with get_db_session() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()
                return VerificationResult(
                    "Database Connection", True, "Database connection successful"
                )
        except Exception as e:
            return VerificationResult(
                "Database Connection",
                False,
                f"Connection failed: {str(e)}",
                "Check DATABASE_URL and ensure database is running",
            )

    def check_imports(self) -> VerificationResult:
        """Check if critical modules can be imported"""
        critical_modules = [
            "server_fastapi.main",
            "server_fastapi.models",
            "server_fastapi.routes.auth",
        ]

        failed = []
        for module in critical_modules:
            try:
                __import__(module)
            except Exception as e:
                failed.append(f"{module}: {str(e)}")

        if not failed:
            return VerificationResult(
                "Module Imports", True, "All critical modules importable"
            )
        else:
            return VerificationResult(
                "Module Imports",
                False,
                f"Failed imports: {len(failed)}",
                "\n".join(failed[:5]),  # Show first 5 errors
            )

    def check_migrations(self) -> VerificationResult:
        """Check if migrations are up to date"""
        try:
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            from alembic.runtime.migration import MigrationContext
            from server_fastapi.database import get_db_session
            from sqlalchemy import text

            # Check if alembic.ini exists
            alembic_ini = self.project_root / "alembic.ini"
            if not alembic_ini.exists():
                return VerificationResult(
                    "Migrations",
                    False,
                    "alembic.ini not found",
                    "Alembic configuration missing",
                )

            # This is a simplified check - full migration check would require DB connection
            return VerificationResult(
                "Migrations",
                True,
                "Alembic configuration found",
                "Run 'alembic upgrade head' to apply migrations",
            )
        except Exception as e:
            return VerificationResult(
                "Migrations",
                False,
                f"Migration check failed: {str(e)}",
                "Ensure Alembic is installed and configured",
            )

    def check_logs_directory(self) -> VerificationResult:
        """Check if logs directory exists"""
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            return VerificationResult("Logs Directory", True, "logs directory exists")
        else:
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
                return VerificationResult(
                    "Logs Directory", True, "logs directory created"
                )
            except Exception as e:
                return VerificationResult(
                    "Logs Directory",
                    False,
                    f"Could not create logs directory: {str(e)}",
                )

    async def run_all_checks(self) -> Tuple[int, int]:
        """Run all verification checks"""
        print(f"{BOLD}{BLUE}Starting Startup Verification...{RESET}\n")

        # Synchronous checks
        checks = [
            self.check_python_version,
            self.check_env_file,
            self.check_dependencies,
            self.check_node_dependencies,
            self.check_database_config,
            self.check_jwt_secret,
            self.check_imports,
            self.check_migrations,
            self.check_logs_directory,
        ]

        for check in checks:
            result = check()
            self.add_result(result)

        # Async checks
        async_checks = [self.check_database_connection]

        for check in async_checks:
            result = await check()
            self.add_result(result)

        # Count results
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        return passed, total

    def print_results(self):
        """Print verification results"""
        import sys
        import io
        
        # Set UTF-8 encoding for Windows compatibility
        if sys.platform == 'win32':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        
        print(f"\n{BOLD}Verification Results:{RESET}\n")
        print("=" * 80)

        for result in self.results:
            # Use ASCII-safe characters for Windows
            status_symbol = "[PASS]" if result.passed else "[FAIL]"
            status = f"{GREEN}{status_symbol}{RESET}" if result.passed else f"{RED}{status_symbol}{RESET}"
            print(f"{status} {BOLD}{result.name}{RESET}")
            print(f"    {result.message}")
            if result.details:
                print(f"    {YELLOW}-> {result.details}{RESET}")
            print()

        print("=" * 80)
        passed, total = sum(1 for r in self.results if r.passed), len(self.results)
        percentage = (passed / total * 100) if total > 0 else 0

        if passed == total:
            print(f"\n{BOLD}{GREEN}All checks passed! ({passed}/{total}){RESET}\n")
        else:
            print(
                f"\n{BOLD}{YELLOW}Some checks failed ({passed}/{total} passed, {percentage:.1f}%){RESET}\n"
            )
            print(f"{YELLOW}Please fix the issues above before starting the application.{RESET}\n")

        return passed == total


async def main():
    """Main entry point"""
    verifier = StartupVerifier()
    passed, total = await verifier.run_all_checks()
    all_passed = verifier.print_results()

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())

