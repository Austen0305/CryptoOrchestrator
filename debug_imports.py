import traceback
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

print("--- Testing trades.py ---")
try:
    from server_fastapi.routes import trades

    print("Success: trades.py loaded")
except Exception:
    traceback.print_exc()

print("\n--- Testing tax_reporting.py ---")
try:
    from server_fastapi.routes import tax_reporting

    print("Success: tax_reporting.py loaded")
except Exception:
    traceback.print_exc()
