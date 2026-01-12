import importlib
import pkgutil
import logging
from pathlib import Path
from types import ModuleType
from fastapi import APIRouter, FastAPI

logger = logging.getLogger(__name__)


def auto_discover_routers(
    package_name: str, base_prefix: str = "/api"
) -> list[tuple[APIRouter, str, list[str]]]:
    """
    Automatically discover FastAPI routers in a package.

    Args:
        package_name: The dotted python package name to search (e.g., 'server_fastapi.routes')
        base_prefix: The base prefix for all routes (defaults to /api)

    Returns:
        List of tuples: (router_instance, url_prefix, tags_list)
    """
    discovered_routers = []

    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        logger.error(f"Could not import package {package_name}: {e}")
        return []

    # Get the directory of the package
    if not hasattr(package, "__path__"):
        logger.error(f"Package {package_name} has no __path__")
        return []

    package_path = list(package.__path__)[0]

    # Iterate through all modules in the package
    for _, module_name, _ in pkgutil.iter_modules([package_path]):
        full_module_name = f"{package_name}.{module_name}"

        try:
            mod = importlib.import_module(full_module_name)

            # Look for a 'router' attribute
            if hasattr(mod, "router") and isinstance(mod.router, APIRouter):
                # Determine properties
                router = mod.router

                # Default Strategy:
                # 1. Check for module-level override (ROUTER_PREFIX)
                # 2. If router prefix already starts with base_prefix (e.g. /api/health), mount at root ("") to avoid duplication
                # 3. If router has other prefix (e.g. /billing), mount at base_prefix (e.g. /api + /billing -> /api/billing)
                # 4. If router has no prefix, mount at base_prefix/module_name (e.g. /api/auth)

                module_override = getattr(mod, "ROUTER_PREFIX", None)

                if module_override is not None:
                    prefix = module_override
                elif router.prefix and router.prefix.startswith(base_prefix):
                    # Router specifically defines full path (e.g. /api/health)
                    # Mount at root to respect its absolute path
                    prefix = ""
                elif router.prefix:
                    # Router handles its own resource path relative to base (e.g. /billing -> /api/billing)
                    prefix = base_prefix
                else:
                    # Router needs a resource path derived from module name
                    prefix = f"{base_prefix}/{module_name}"

                # Check for module-level tags override
                tags = getattr(
                    mod, "ROUTER_TAGS", [module_name.replace("_", " ").title()]
                )

                discovered_routers.append((router, prefix, tags))
                logger.debug(f"Discovered router: {module_name} -> {prefix}")

        except Exception as e:
            logger.warning(f"Failed to load module {full_module_name}: {e}")
            continue

    return discovered_routers


def register_routers(app: FastAPI, package_name: str = "server_fastapi.routes"):
    """
    Main entry point to register all found routers to the app.
    """
    logger.info(f"Starting auto-discovery of routers in {package_name}...")
    routers = auto_discover_routers(package_name)

    count = 0
    for router, prefix, tags in routers:
        app.include_router(router, prefix=prefix, tags=tags)
        count += 1

    logger.info(f"Auto-discovery complete. Registered {count} routers.")
