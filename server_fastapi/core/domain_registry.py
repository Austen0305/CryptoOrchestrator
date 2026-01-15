"""
Domain Registry (2026 Best Practice)
Centralized dependency injection and service discovery for Domain-Driven Design.
Ensures strict separation of concerns and facilitates testing via mock injection.
"""

import logging
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

class DomainRegistry:
    _instance: "DomainRegistry | None" = None
    _services: dict[type[Any], Any] = {}
    _factories: dict[type[Any], Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, interface: type[T], implementation: T) -> None:
        """Register a singleton service implementation."""
        logger.debug(f"Registering service: {interface.__name__}")
        self._services[interface] = implementation

    def register_factory(self, interface: type[T], factory: Any) -> None:
        """Register a factory function for a service."""
        logger.debug(f"Registering factory for: {interface.__name__}")
        self._factories[interface] = factory

    def resolve(self, interface: type[T]) -> T:
        """Resolve a service implementation."""
        if interface in self._services:
            return self._services[interface]
        
        if interface in self._factories:
            # Create instance from factory
            instance = self._factories[interface]()
            # Cache it if it's treated as a singleton by the factory
            return instance

        raise ValueError(f"Service not registered: {interface.__name__}")

    def clear(self) -> None:
        """Clear all registrations (primarily for unit tests)."""
        self._services.clear()
        self._factories.clear()

# Global registry instance
domain_registry = DomainRegistry()
