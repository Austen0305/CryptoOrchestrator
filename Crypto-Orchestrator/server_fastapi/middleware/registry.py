"""
Middleware Registry
Handles dynamic loading and registration of middleware components
"""

import logging
import importlib
from typing import List, Optional, Type, Any
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from .config import MiddlewareConfig, middleware_manager

logger = logging.getLogger(__name__)


class MiddlewareRegistry:
    """Registry for managing middleware registration"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.registered: List[str] = []
        self.failed: List[str] = []
    
    def register_middleware(self, config: MiddlewareConfig) -> bool:
        """
        Register a middleware from configuration
        
        Returns:
            True if registration succeeded, False otherwise
        """
        try:
            # Import the module
            module = importlib.import_module(config.module_path)
            
            # Get the middleware class
            middleware_class: Type[BaseHTTPMiddleware] = getattr(
                module, config.class_name
            )
            
            # Register with FastAPI
            self.app.add_middleware(
                middleware_class,
                **config.kwargs
            )
            
            self.registered.append(config.name)
            logger.info(f"✓ Middleware '{config.name}' registered successfully")
            return True
            
        except ImportError as e:
            logger.warning(
                f"✗ Middleware '{config.name}' not available: {e}"
            )
            self.failed.append(config.name)
            return False
        except AttributeError as e:
            logger.warning(
                f"✗ Middleware '{config.name}' class '{config.class_name}' not found: {e}"
            )
            self.failed.append(config.name)
            return False
        except Exception as e:
            logger.error(
                f"✗ Failed to register middleware '{config.name}': {e}",
                exc_info=True
            )
            self.failed.append(config.name)
            return False
    
    def register_all(self, configs: List[MiddlewareConfig]) -> dict:
        """
        Register all middleware configurations
        
        Returns:
            Dictionary with registration statistics
        """
        stats = {
            "total": len(configs),
            "registered": 0,
            "failed": 0,
        }
        
        for config in configs:
            if self.register_middleware(config):
                stats["registered"] += 1
            else:
                stats["failed"] += 1
        
        logger.info(
            f"Middleware registration complete: "
            f"{stats['registered']}/{stats['total']} registered, "
            f"{stats['failed']} failed"
        )
        
        return stats
    
    def get_registration_summary(self) -> dict:
        """Get summary of registered middleware"""
        return {
            "registered": self.registered,
            "failed": self.failed,
            "total": len(self.registered) + len(self.failed),
        }

