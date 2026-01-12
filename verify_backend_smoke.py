import sys
import os
import asyncio

# Ensure project root is in path
sys.path.insert(0, os.getcwd())

try:
    from server_fastapi.main import app
except ImportError as e:
    print(f"CRITICAL: Failed to import FastAPI app: {e}")
    sys.exit(1)


def verify_routers():
    print("Verifying router registration...")
    # List of expected critical endpoints (paths)
    expected_paths = [
        "/api/auth/login",
        "/api/kyc/submit",
        "/api/wallet/balance",
        "/api/marketplace/strategies",
        "/health",
    ]

    registered_routes = set()
    for route in app.routes:
        if hasattr(route, "path"):
            registered_routes.add(route.path)

    print(f"Total registered routes: {len(registered_routes)}")

    missing = []
    for expected in expected_paths:
        if expected not in registered_routes:
            # Try fuzzy match (FastAPI stores /api/auth/login as /api/auth/login)
            missing.append(expected)

    if missing:
        print(f"FAILED: The following critical routes are missing: {missing}")
        print("This indicates that the router loading logic in main.py is broken.")
        sys.exit(1)

    print("SUCCESS: All critical routers verified.")
    sys.exit(0)


if __name__ == "__main__":
    verify_routers()
