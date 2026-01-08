"""
Deposit Monitor Celery Worker
Background task to monitor blockchain for deposits
"""

import logging

from celery import shared_task

from ..services.blockchain.deposit_monitor import get_deposit_monitor

logger = logging.getLogger(__name__)


@shared_task(name="monitor_deposits")
def monitor_deposits_task(chain_id: Optional[int] = None):
    """
    Celery task to monitor deposits on blockchain

    Args:
        chain_id: Optional specific chain ID to monitor (if None, monitors all chains)
    """
    try:
        monitor = get_deposit_monitor()

        # Get database session
        # Note: In production, you'd use a proper async context manager
        # For Celery, you might need to use sync database operations
        # or run this in an async context

        # For now, this is a placeholder that shows the structure
        # In production, you'd need to properly handle async database sessions in Celery
        logger.info(f"Deposit monitoring task started for chain {chain_id or 'all'}")

        # Note: Proper async database session handling in Celery requires additional setup
        # Future enhancement: Use asyncio.run() or sync database adapter for Celery workers

        return {"status": "completed", "chain_id": chain_id}

    except Exception as e:
        logger.error(f"Error in deposit monitoring task: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@shared_task(name="monitor_all_deposits")
def monitor_all_deposits_task():
    """Monitor deposits on all supported chains"""
    return monitor_deposits_task(chain_id=None)
