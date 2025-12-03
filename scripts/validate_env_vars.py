#!/usr/bin/env python3
"""
Environment Variables Validation Script

Validates all required environment variables are present and properly configured.
Checks .env file against .env.example and provides recommendations.

Usage:
    python scripts/validate_env_vars.py
    npm run validate:env
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
import re

# Color output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


class EnvValidator:
    # Critical variables required for basic operation
    CRITICAL_VARS = [
        "JWT_SECRET",
        "DATABASE_URL",
    ]
    
    # Recommended variables for production
    RECOMMENDED_VARS = [
        "NODE_ENV",
        "REDIS_URL",
        "ALLOWED_ORIGINS",
        "LOG_LEVEL",
    ]
    
    # Optional variables (feature-specific)
    OPTIONAL_VARS = [
        "STRIPE_SECRET_KEY",
        "KRAKEN_API_KEY",
        "BINANCE_API_KEY",
        "SENTRY_DSN",
    ]
    
    # Validation patterns
    PATTERNS = {
        "DATABASE_URL": r"^(postgresql|sqlite).*",
        "JWT_SECRET": r".{16,}",  # At least 16 characters
        "REDIS_URL": r"^redis://.*",
        "NODE_ENV": r"^(development|production|test)$",
    }
    
    def __init__(self):
        self.results = {
            "critical_missing": [],
            "recommended_missing": [],
            "insecure_defaults": [],
            "validation_errors": [],
            "warnings": [],
            "success": []
        }
    
    def load_env_example(self) -> Dict[str, str]:
        """Load variables from .env.example"""
        env_vars = {}
        try:
            with open(".env.example", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        except FileNotFoundError:
            print_error(".env.example not found")
        return env_vars
    
    def load_env_file(self) -> Dict[str, str]:
        """Load variables from .env file"""
        env_vars = {}
        try:
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        except FileNotFoundError:
            print_warning(".env file not found - using environment variables only")
        return env_vars
    
    def get_env_value(self, key: str, env_file: Dict[str, str]) -> Optional[str]:
        """Get environment variable value (from file or system env)"""
        return env_file.get(key) or os.getenv(key)
    
    def validate_critical_vars(self, env_file: Dict[str, str]) -> bool:
        """Validate critical environment variables"""
        print_info("Checking critical variables...")
        all_present = True
        
        for var in self.CRITICAL_VARS:
            value = self.get_env_value(var, env_file)
            if not value:
                print_error(f"  {var}: MISSING (CRITICAL)")
                self.results["critical_missing"].append(var)
                all_present = False
            elif value == env_file.get(var, ""):
                # Check if using default insecure value
                if "change-in-production" in value or "your-" in value:
                    print_warning(f"  {var}: Using default value (NOT PRODUCTION SAFE)")
                    self.results["insecure_defaults"].append(var)
                else:
                    print_success(f"  {var}: Configured")
                    self.results["success"].append(var)
            else:
                print_success(f"  {var}: Configured")
                self.results["success"].append(var)
        
        return all_present
    
    def validate_recommended_vars(self, env_file: Dict[str, str]):
        """Validate recommended environment variables"""
        print_info("\nChecking recommended variables...")
        
        for var in self.RECOMMENDED_VARS:
            value = self.get_env_value(var, env_file)
            if not value:
                print_warning(f"  {var}: Not set (recommended)")
                self.results["recommended_missing"].append(var)
            else:
                print_success(f"  {var}: {value}")
                self.results["success"].append(var)
    
    def validate_patterns(self, env_file: Dict[str, str]):
        """Validate environment variable patterns"""
        print_info("\nValidating variable formats...")
        
        for var, pattern in self.PATTERNS.items():
            value = self.get_env_value(var, env_file)
            if value:
                if not re.match(pattern, value):
                    print_error(f"  {var}: Invalid format")
                    self.results["validation_errors"].append(f"{var}: Invalid format (should match {pattern})")
                else:
                    print_success(f"  {var}: Valid format")
    
    def check_security_recommendations(self, env_file: Dict[str, str]):
        """Check security best practices"""
        print_info("\nSecurity recommendations...")
        
        # JWT_SECRET length check
        jwt_secret = self.get_env_value("JWT_SECRET", env_file)
        if jwt_secret:
            if len(jwt_secret) < 32:
                print_warning(f"  JWT_SECRET is short ({len(jwt_secret)} chars) - recommend 32+ chars")
                self.results["warnings"].append("JWT_SECRET should be at least 32 characters")
            elif len(jwt_secret) >= 64:
                print_success(f"  JWT_SECRET has strong length ({len(jwt_secret)} chars)")
            else:
                print_success(f"  JWT_SECRET has adequate length ({len(jwt_secret)} chars)")
        
        # NODE_ENV check
        node_env = self.get_env_value("NODE_ENV", env_file)
        if node_env == "production":
            print_info("  Production mode - performing additional checks...")
            
            # In production, should not have default values
            for var in self.CRITICAL_VARS:
                value = self.get_env_value(var, env_file)
                if value and ("change-in-production" in value or "your-" in value):
                    print_error(f"  {var}: Using default value in PRODUCTION")
                    self.results["validation_errors"].append(f"{var}: Default value in production")
        
        # CORS check
        allowed_origins = self.get_env_value("ALLOWED_ORIGINS", env_file)
        if allowed_origins:
            if "*" in allowed_origins:
                print_warning("  ALLOWED_ORIGINS contains wildcard (*) - security risk")
                self.results["warnings"].append("ALLOWED_ORIGINS should not use wildcard in production")
            else:
                print_success("  ALLOWED_ORIGINS properly configured")
    
    def create_env_from_example(self):
        """Create .env file from .env.example if it doesn't exist"""
        if not os.path.exists(".env"):
            print_info("\nCreating .env from .env.example...")
            try:
                with open(".env.example", "r") as src:
                    with open(".env", "w") as dst:
                        dst.write(src.read())
                print_success(".env file created from .env.example")
                print_warning("⚠ Remember to update the values in .env with your actual credentials!")
                return True
            except Exception as e:
                print_error(f"Failed to create .env: {str(e)}")
                return False
        return False
    
    def print_summary(self):
        """Print validation summary"""
        print_header("Validation Summary")
        
        critical_missing = len(self.results["critical_missing"])
        recommended_missing = len(self.results["recommended_missing"])
        insecure_defaults = len(self.results["insecure_defaults"])
        validation_errors = len(self.results["validation_errors"])
        warnings = len(self.results["warnings"])
        success_count = len(self.results["success"])
        
        print(f"Variables Configured: {success_count}")
        
        if critical_missing > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}Critical Missing: {critical_missing}{Colors.END}")
            for var in self.results["critical_missing"]:
                print(f"  - {var}")
        
        if recommended_missing > 0:
            print(f"\n{Colors.YELLOW}Recommended Missing: {recommended_missing}{Colors.END}")
            for var in self.results["recommended_missing"]:
                print(f"  - {var}")
        
        if insecure_defaults > 0:
            print(f"\n{Colors.YELLOW}Insecure Defaults: {insecure_defaults}{Colors.END}")
            for var in self.results["insecure_defaults"]:
                print(f"  - {var}")
        
        if validation_errors > 0:
            print(f"\n{Colors.RED}Validation Errors: {validation_errors}{Colors.END}")
            for error in self.results["validation_errors"]:
                print(f"  - {error}")
        
        if warnings > 0:
            print(f"\n{Colors.YELLOW}Warnings: {warnings}{Colors.END}")
            for warning in self.results["warnings"]:
                print(f"  - {warning}")
        
        # Overall status
        print()
        if critical_missing == 0 and validation_errors == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ Environment validation passed!{Colors.END}")
            if insecure_defaults > 0 or warnings > 0:
                print(f"{Colors.YELLOW}⚠ Review warnings before production deployment{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ Environment validation failed{Colors.END}")
            print("\nAction required:")
            print("1. Create/update .env file with required variables")
            print("2. Replace default values with actual credentials")
            print("3. Run this script again to validate")
            return False
    
    def run_validation(self) -> bool:
        """Run all validation checks"""
        print_header("Environment Variables Validation")
        
        # Create .env if it doesn't exist
        self.create_env_from_example()
        
        # Load environment files
        env_example = self.load_env_example()
        env_file = self.load_env_file()
        
        # Run validations
        critical_ok = self.validate_critical_vars(env_file)
        self.validate_recommended_vars(env_file)
        self.validate_patterns(env_file)
        self.check_security_recommendations(env_file)
        
        # Print summary
        return self.print_summary()


def main():
    """Main execution"""
    validator = EnvValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
