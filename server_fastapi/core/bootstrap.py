"""
Bootstrap (2026 Best Practice)
Coordinates the initialization of the application's domain services.
"""

import logging

from ..services.security.local_vault import LocalEnvVault
from ..services.security.signing_service import SigningService
from ..services.security.vault_interface import AbstractVault
from .domain_registry import domain_registry

logger = logging.getLogger(__name__)


def bootstrap_domain_services():
    """Register all core domain services."""
    logger.info("Initializing Domain Services...")

    # 1. Security & Key Management

    # Core Orchestration
    from ..services.trading_orchestrator import trading_orchestrator

    domain_registry.register(Any, trading_orchestrator)
    # In production, this would be a HashiCorpVault() instance
    local_vault = LocalEnvVault()
    domain_registry.register(AbstractVault, local_vault)

    # 2. Signing Service
    from ..services.security.signing_service import signing_service

    domain_registry.register(SigningService, signing_service)

    # 3. Risk Engine (Implementation pending - placeholder registration)
    from ..services.advanced_risk_manager import AdvancedRiskManager

    domain_registry.register(
        Any, AdvancedRiskManager()
    )  # Use proper interface type later

    logger.info("Domain Services registered successfully.")
