import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add root to sys.path
sys.path.insert(0, os.getcwd())

# Set env vars for testing
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-dev-key-must-be-very-long-to-be-secure"
os.environ["EXCHANGE_KEY_ENCRYPTION_KEY"] = "test-32-byte-key-0123456789abcdef"

try:
    print("Importing app...")
    from server_fastapi.main import app

    print("App imported successfully.")

    print("Creating TestClient...")
    with TestClient(app) as client:
        print("TestClient created.")

        print("Calling /health...")
        response = client.get("/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("SUCCESS: Backend is healthy.")
        else:
            print("FAILURE: Health check failed.")
            sys.exit(1)

except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"RUNTIME ERROR: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
