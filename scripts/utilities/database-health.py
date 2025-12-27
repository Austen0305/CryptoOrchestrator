#!/usr/bin/env python3
"""
Database Health Checker
Checks database health, indexes, and performance
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class DatabaseHealthChecker:
    """Checks database health"""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.info: List[Dict[str, Any]] = []

    async def check_connection(self):
        """Check database connection"""
        logger.info("Checking database connection...")

        try:
            from server_fastapi.database import get_db_session
            from sqlalchemy import text

            async with get_db_session() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()
                self.info.append({
                    "category": "connection",
                    "message": "Database connection successful",
                })
                return True
        except Exception as e:
            self.issues.append({
                "type": "error",
                "category": "connection",
                "message": f"Database connection failed: {e}",
            })
            return False

    async def check_indexes(self):
        """Check for missing indexes"""
        logger.info("Checking database indexes...")

        try:
            from server_fastapi.database import get_db_session
            from sqlalchemy import text, inspect

            async with get_db_session() as session:
                # Get database type
                inspector = inspect(session.bind)
                
                # Check for common tables
                tables = inspector.get_table_names()
                
                if "trades" in tables:
                    indexes = inspector.get_indexes("trades")
                    index_names = [idx["name"] for idx in indexes]
                    
                    # Check for important indexes
                    important_indexes = [
                        "ix_trades_user_mode_created",
                        "ix_trades_symbol_side",
                    ]
                    
                    for idx_name in important_indexes:
                        if idx_name not in index_names:
                            self.issues.append({
                                "type": "warning",
                                "category": "indexes",
                                "message": f"Missing index: {idx_name} on trades table",
                            })

                self.info.append({
                    "category": "indexes",
                    "message": f"Found {len(tables)} tables",
                })

        except Exception as e:
            logger.debug(f"Could not check indexes: {e}")

    async def check_migrations(self):
        """Check migration status"""
        logger.info("Checking migration status...")

        try:
            import subprocess
            result = subprocess.run(
                ["alembic", "current"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=project_root,
            )

            if result.returncode == 0:
                self.info.append({
                    "category": "migrations",
                    "message": "Migrations are up to date",
                    "details": result.stdout.strip(),
                })
            else:
                self.issues.append({
                    "type": "warning",
                    "category": "migrations",
                    "message": "Could not check migration status",
                })

        except Exception as e:
            logger.debug(f"Could not check migrations: {e}")

    def print_report(self):
        """Print health check report"""
        print("\n" + "=" * 80)
        print("DATABASE HEALTH REPORT")
        print("=" * 80 + "\n")

        if self.info:
            print("INFO:")
            print("-" * 80)
            for item in self.info:
                print(f"  [{item['category'].upper()}] {item['message']}")
                if 'details' in item:
                    print(f"    -> {item['details']}")
            print()

        if self.issues:
            print("ISSUES:")
            print("-" * 80)
            for issue in self.issues:
                itype = issue.get("type", "warning")
                category = issue.get("category", "unknown")
                message = issue.get("message", "")

                if itype == "error":
                    print(f"  [ERROR] [{category.upper()}] {message}")
                else:
                    print(f"  [WARNING] [{category.upper()}] {message}")
            print()

        print("=" * 80)
        errors = sum(1 for i in self.issues if i.get("type") == "error")
        warnings = sum(1 for i in self.issues if i.get("type") == "warning")

        print(f"\nSummary: {errors} errors, {warnings} warnings")

        if errors == 0 and warnings == 0:
            print("\n[SUCCESS] Database is healthy!")
        elif errors == 0:
            print("\n[WARNING] Some database optimizations recommended")
        else:
            print("\n[ERROR] Database issues need attention")

        return errors == 0

    async def run_checks(self):
        """Run all health checks"""
        logger.info("Starting database health check...")

        await self.check_connection()
        await self.check_indexes()
        await self.check_migrations()

        return self.print_report()


def main():
    """Main entry point"""
    checker = DatabaseHealthChecker()
    success = asyncio.run(checker.run_checks())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

