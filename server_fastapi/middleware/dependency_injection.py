"""
Middleware Dependency Injection
Provides dependency injection utilities for middleware testing and configuration
"""

from typing import Optional, Callable, Any, Dict
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class MiddlewareDependency:
    """Dependency container for middleware components"""
    
    def __init__(self):
        self._dependencies: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
    
    def register(self, name: str, instance: Any):
        """Register a dependency instance"""
        self._dependencies[name] = instance
        logger.debug(f"Registered dependency: {name}")
    
    def register_factory(self, name: str, factory: Callable):
        """Register a dependency factory function"""
        self._factories[name] = factory
        logger.debug(f"Registered factory: {name}")
    
    def get(self, name: str, default: Any = None) -> Any:
        """Get a dependency by name"""
        if name in self._dependencies:
            return self._dependencies[name]
        
        if name in self._factories:
            instance = self._factories[name]()
            self._dependencies[name] = instance  # Cache the instance
            return instance
        
        if default is not None:
            return default
        
        raise ValueError(f"Dependency '{name}' not found")
    
    def clear(self):
        """Clear all dependencies (useful for testing)"""
        self._dependencies.clear()
        self._factories.clear()
    
    def has(self, name: str) -> bool:
        """Check if a dependency is registered"""
        return name in self._dependencies or name in self._factories


# Global dependency container
middleware_dependencies = MiddlewareDependency()


def inject_middleware_dependency(name: str, factory: Optional[Callable] = None):
    """
    Decorator to inject middleware dependencies
    
    Usage:
        @inject_middleware_dependency("cache_manager")
        def my_middleware(cache_manager=None):
            # Use cache_manager
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Inject dependency if not provided
            if name not in kwargs or kwargs[name] is None:
                try:
                    kwargs[name] = middleware_dependencies.get(name)
                except ValueError:
                    if factory:
                        kwargs[name] = factory()
                    else:
                        logger.warning(f"Dependency '{name}' not found for {func.__name__}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def provide_middleware_dependency(name: str):
    """
    Decorator to register a middleware dependency provider
    
    Usage:
        @provide_middleware_dependency("cache_manager")
        def create_cache_manager():
            return CacheManager()
    """
    def decorator(func: Callable) -> Callable:
        middleware_dependencies.register_factory(name, func)
        return func
    return decorator

