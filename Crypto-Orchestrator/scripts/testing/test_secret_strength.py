#!/usr/bin/env python3
"""
Secret Strength Validation Test Script
Tests that secrets meet strength requirements (for production)
"""
import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_secret_strength():
    """Test secret strength validation"""
    try:
        # Temporarily disable auto-validation on import
        original_env = os.getenv("SKIP_ENV_VALIDATION", "false")
        os.environ["SKIP_ENV_VALIDATION"] = "true"
        
        from server_fastapi.config.env_validator import validate_secret_strength
        
        # Restore original value
        if original_env == "false":
            os.environ.pop("SKIP_ENV_VALIDATION", None)
        else:
            os.environ["SKIP_ENV_VALIDATION"] = original_env
        
        print("[INFO] Testing secret strength validation...")
        
        # Check if in production mode
        node_env = os.getenv("NODE_ENV", "development").lower()
        
        # Load .env file if it exists to check NODE_ENV
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            env_content = env_file.read_text(encoding='utf-8', errors='ignore')
            for line in env_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    if key.strip() == "NODE_ENV":
                        node_env = value.lower()
                        break
        
        is_production = node_env == "production"
        
        if not is_production:
            print("[INFO] Development mode detected - secret strength checks are informational")
            print("[INFO] Secrets will be strictly validated when NODE_ENV=production")
            print("[INFO] Checking secrets for informational purposes...\n")
        else:
            print("[INFO] Production mode detected - strictly validating secrets...\n")
        
        secrets_to_check = [
            ("JWT_SECRET", 32, "JWT token signing secret"),
            ("EXCHANGE_KEY_ENCRYPTION_KEY", 32, "Exchange API key encryption key"),
        ]
        
        all_valid = True
        for var_name, min_length, description in secrets_to_check:
            value = os.getenv(var_name)
            
            if not value:
                if is_production:
                    print(f"X {var_name}: MISSING ({description})")
                    print(f"  Required in production mode")
                    all_valid = False
                else:
                    print(f"⚠ {var_name}: Not set ({description})")
                    print(f"  Optional in development mode")
                continue
            
            # Test using validator (without triggering auto-validation)
            try:
                # Manually check length and weak values
                if len(value) < min_length:
                    if is_production:
                        print(f"X {var_name}: Too short ({len(value)} chars, minimum: {min_length})")
                        all_valid = False
                    else:
                        print(f"⚠ {var_name}: Short ({len(value)} chars, recommend: {min_length}+)")
                elif value.lower() in ["change-me", "secret", "password", "123456", 
                                      "your-secret-key-change-in-production",
                                      "dev-secret-change-me-in-production"]:
                    if is_production:
                        print(f"X {var_name}: Uses weak/default value")
                        all_valid = False
                    else:
                        print(f"⚠ {var_name}: Uses default value (change for production)")
                else:
                    print(f"✓ {var_name}: Valid ({len(value)} chars, {description})")
            except Exception as e:
                print(f"X {var_name}: Error during validation - {e}")
                all_valid = False
        
        if all_valid or not is_production:
            if is_production:
                print("\n✓ All secrets meet strength requirements")
            else:
                print("\n✓ Secret check completed (development mode)")
            return True
        else:
            print("\nX Some secrets failed validation")
            print("\nTo generate strong secrets:")
            print("  python -c 'import secrets; print(secrets.token_urlsafe(32))'")
            return False
            
    except Exception as e:
        print(f"X Secret validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_secret_strength()
    sys.exit(0 if success else 1)
