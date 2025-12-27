"""
Lazy Middleware Loading
Loads middleware components on-demand to improve startup time
"""

import logging
import importlib
from typing import Dict, Optional, Type, Any, Callable
from functools import lru_cache
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LazyMiddlewareLoader:
    """
    Lazy loads middleware components to reduce startup time
    
    Only loads middleware when:
    1. First request that needs it
    2. Explicitly requested
    3. Health check endpoint
    """

    def __init__(self):
        self._loaded_middleware: Dict[str, Type[BaseHTTPMiddleware]] = {}
        self._middleware_configs: Dict[str, Dict[str, Any]] = {}
        self._load_stats = {
            "loaded": 0,
            "cached": 0,
            "errors": 0,
        }

    def register(
        self,
        name: str,
        module_path: str,
        class_name: str,
        enabled: bool = True,
        **kwargs
    ):
        """Register middleware for lazy loading"""
        self._middleware_configs[name] = {
            "module_path": module_path,
            "class_name": class_name,
            "enabled": enabled,
            "kwargs": kwargs,
        }

    @lru_cache(maxsize=50)
    def _load_middleware_class(self, module_path: str, class_name: str) -> Optional[Type[BaseHTTPMiddleware]]:
        """Load middleware class with caching"""
        try:
            module = importlib.import_module(module_path)
            middleware_class = getattr(module, class_name)
            
            if not issubclass(middleware_class, BaseHTTPMiddleware):
                logger.warning(f"{class_name} is not a BaseHTTPMiddleware subclass")
                return None
            
            self._load_stats["loaded"] += 1
            return middleware_class
        except ImportError as e:
            logger.debug(f"Middleware {module_path}.{class_name} not available: {e}")
            self._load_stats["errors"] += 1
            return None
        except AttributeError as e:
            logger.warning(f"Middleware class {class_name} not found in {module_path}: {e}")
            self._load_stats["errors"] += 1
            return None
        except Exception as e:
            logger.error(f"Error loading middleware {module_path}.{class_name}: {e}", exc_info=True)
            self._load_stats["errors"] += 1
            return None

    def load(self, name: str) -> Optional[Type[BaseHTTPMiddleware]]:
        """Load middleware by name"""
        if name in self._loaded_middleware:
            self._load_stats["cached"] += 1
            return self._loaded_middleware[name]
        
        if name not in self._middleware_configs:
            logger.warning(f"Middleware {name} not registered")
            return None
        
        config = self._middleware_configs[name]
        if not config["enabled"]:
            return None
        
        middleware_class = self._load_middleware_class(
            config["module_path"],
            config["class_name"]
        )
        
        if middleware_class:
            self._loaded_middleware[name] = middleware_class
        
        return middleware_class

    def preload_critical(self, app: FastAPI):
        """Preload critical middleware that's always needed"""
        critical_middleware = [
            "request_id",
            "security_headers",
            "structured_logging",
        ]
        
        for name in critical_middleware:
            if name in self._middleware_configs:
                middleware_class = self.load(name)
                if middleware_class:
                    try:
                        kwargs = self._middleware_configs[name].get("kwargs", {})
                        app.add_middleware(middleware_class, **kwargs)
                        logger.debug(f"Preloaded critical middleware: {name}")
                    except Exception as e:
                        logger.warning(f"Failed to preload {name}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get loading statistics"""
        return {
            **self._load_stats,
            "registered": len(self._middleware_configs),
            "loaded": len(self._loaded_middleware),
        }


# Global lazy loader instance
lazy_loader = LazyMiddlewareLoader()

