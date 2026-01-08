"""
Celery Tasks for Transaction Batcher
Periodically flushes pending batches to execute swaps
"""

import logging

from celery import shared_task

from ..services.blockchain.transaction_batcher import get_transaction_batcher

logger = logging.getLogger(__name__)


@shared_task(name="transaction_batcher.flush_pending_batches")
def flush_pending_batches(chain_id: int = None):
    """
    Flush all pending transaction batches.
    Runs periodically to execute queued swaps.

    Args:
        chain_id: Specific chain to flush, or None for all chains
    """
    try:
        batcher = get_transaction_batcher()
        result = batcher.flush_pending(chain_id=chain_id)

        logger.info(
            f"Flushed transaction batches: {result}",
            extra={"chain_id": chain_id, "result": result},
        )

        return result
    except Exception as e:
        logger.error(
            f"Failed to flush transaction batches: {e}",
            exc_info=True,
            extra={"chain_id": chain_id},
        )
        raise


@shared_task(name="transaction_batcher.get_pending_count")
def get_pending_batch_count(chain_id: int = None):
    """
    Get count of pending swaps in batches.
    Useful for monitoring and metrics.

    Args:
        chain_id: Specific chain, or None for all chains

    Returns:
        Count of pending swaps
    """
    try:
        batcher = get_transaction_batcher()
        count = batcher.get_pending_count(chain_id=chain_id)
        return {"pending_count": count, "chain_id": chain_id}
    except Exception as e:
        logger.error(f"Failed to get pending batch count: {e}", exc_info=True)
        return {"pending_count": 0, "error": str(e)}
