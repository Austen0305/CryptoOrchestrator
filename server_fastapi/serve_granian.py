import os
import sys

from granian import Granian
from granian.constants import Interfaces, Loops, ThreadModes

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def main():
    """
    Granian Enterprise Entry Point (2026).
    Replacing Uvicorn for production workloads.
    """
    # Configuration matches Research Plan:
    # 1. Interface: ASGI
    # 2. Loop: auto (uses uvloop if available)
    # 3. ThreadMode: Workers

    workers = int(os.getenv("WORKERS", "1"))
    port = int(os.getenv("PORT", "8000"))

    print(f"Starting Granian on port {port} with {workers} workers...")

    Granian(
        "server_fastapi.main:app",
        address="0.0.0.0",
        port=port,
        interface=Interfaces.ASGI,
        workers=workers,
        threads=1,  # GIL safety for Python-heavy apps
        threading_mode=ThreadModes.workers,
        loop=Loops.auto,
        log_access=True,
        log_level="info",
        # SSL config would go here if not behind Nginx/Ingress
    ).serve()


if __name__ == "__main__":
    main()
