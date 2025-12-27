#!/usr/bin/env python3
"""
Database Migrations Validation Script
Tests alembic migrations for upgrade/downgrade functionality
"""

import sys
import subprocess
import json
from datetime import datetime

class MigrationValidator:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
    
    def run_command(self, command, description):
        """Run a shell command and capture output"""
        print(f"
▶ {description}...")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            success = result.returncode == 0
            print(f"  {'✓' if success else '✗'} {description}")
            return {
                'test': description,
                'command': command,
                'status': 'passed' if success else 'failed',
                'output': result.stdout[:500] if success else result.stderr[:500],
                'exit_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            print(f"  ✗ {description} (timeout)")
            return {
                'test': description,
                'command': command,
                'status': 'timeout',
                'output': 'Command timed out after 30 seconds'
            }
        except Exception as e:
            print(f"  ✗ {description} (error: {e})")
            return {
                'test': description,
                'command': command,
                'status': 'error',
                'output': str(e)
            }
    
    def test_alembic_current(self):
        """Test getting current migration version"""
        result = self.run_command(
            'alembic current',
            'Get current migration version'
        )
        self.results['tests'].append(result)
        return result['status'] == 'passed'
    
    def test_alembic_heads(self):
        """Test getting migration heads"""
        result = self.run_command(
            'alembic heads',
            'Get migration heads'
        )
        self.results['tests'].append(result)
        return result['status'] == 'passed'
    
    def test_alembic_upgrade_head(self):
        """Test upgrading to head"""
        result = self.run_command(
            'alembic upgrade head',
            'Upgrade to latest migration'
        )
        self.results['tests'].append(result)
        return result['status'] == 'passed'
    
    def test_alembic_downgrade_one(self):
        """Test downgrading one version"""
        result = self.run_command(
            'alembic downgrade -1',
            'Downgrade one migration'
        )
        self.results['tests'].append(result)
        return result['status'] == 'passed'
    
    def test_alembic_upgrade_again(self):
        """Test upgrading again after downgrade"""
        result = self.run_command(
            'alembic upgrade head',
            'Upgrade to head again'
        )
        self.results['tests'].append(result)
        return result['status'] == 'passed'
    
    def test_alembic_history(self):
        """Test getting migration history"""
        result = self.run_command(
            'alembic history',
            'Get migration history'
        )
        self.results['tests'].append(result)
        return result['status'] == 'passed'
    
    def run_all_tests(self):
        """Run all migration validation tests"""
        print("
" + "="*60)
        print("DATABASE MIGRATIONS VALIDATION")
        print("="*60)
        
        tests = [
            self.test_alembic_current,
            self.test_alembic_heads,
            self.test_alembic_history,
            self.test_alembic_upgrade_head,
            self.test_alembic_downgrade_one,
            self.test_alembic_upgrade_again,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        # Summary
        self.results['summary'] = {
            'total': len(tests),
            'passed': passed,
            'failed': failed,
            'pass_rate': round((passed / len(tests)) * 100, 1) if len(tests) > 0 else 0
        }
        
        print("
" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total Tests:   {self.results['summary']['total']}")
        print(f"Passed:        {self.results['summary']['passed']}")
        print(f"Failed:        {self.results['summary']['failed']}")
        print(f"Pass Rate:     {self.results['summary']['pass_rate']}%")
        
        if failed == 0:
        else:
            print(f"
✗ {failed} migration test(s) failed")
        
        # Save results
        with open('migration_validation_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"
Results saved to: migration_validation_results.json")
        
        return failed == 0

def main():
    validator = MigrationValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
