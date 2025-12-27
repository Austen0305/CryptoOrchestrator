"""
Portfolio Reconciliation Celery Tasks
Automatically reconcile portfolios after bot trades and on schedule
"""

import asyncio
import logging
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..celery_app import celery_app
from ..services.portfolio_reconciliation import PortfolioReconciliationService
from ..database import get_db_context

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.reconcile_user_portfolio", bind=True)
def reconcile_user_portfolio_task(self, user_id: str) -> Dict:
    """
    Reconcile a single user's portfolio after bot trades.
    This task is triggered automatically after bot trades complete.

    Args:
        user_id: User ID to reconcile

    Returns:
        Reconciliation result dictionary
    """

    async def reconcile():
        try:
            async with get_db_context() as db:
                service = PortfolioReconciliationService(db_session=db)
                result = await service.reconcile_portfolio(user_id)

                if result.get("status") == "discrepancies_found":
                    logger.warning(
                        f"Portfolio discrepancies found for user {user_id}: "
                        f"{result.get('discrepancy_count', 0)} discrepancies"
                    )
                else:
                    logger.info(
                        f"Portfolio reconciliation successful for user {user_id}"
                    )

                return result
        except Exception as e:
            logger.error(
                f"Portfolio reconciliation failed for user {user_id}: {e}",
                exc_info=True,
            )
            return {"user_id": user_id, "status": "error", "error": str(e)}

    return asyncio.run(reconcile())


@celery_app.task(name="tasks.reconcile_all_portfolios_batch")
def reconcile_all_portfolios_batch_task() -> Dict:
    """
    Reconcile all user portfolios in batch.
    This is the scheduled task that runs periodically.

    Returns:
        Summary of reconciliation results
    """

    async def reconcile_all():
        try:
            async with get_db_context() as db:
                service = PortfolioReconciliationService(db_session=db)
                results = await service.reconcile_all_portfolios()

                # Calculate summary statistics
                total = len(results)
                success = sum(1 for r in results if r.get("status") == "success")
                discrepancies = sum(
                    1 for r in results if r.get("status") == "discrepancies_found"
                )
                errors = sum(1 for r in results if r.get("status") == "error")

                logger.info(
                    f"Batch reconciliation complete: {success} success, "
                    f"{discrepancies} with discrepancies, {errors} errors"
                )

                return {
                    "status": "completed",
                    "total_portfolios": total,
                    "success": success,
                    "discrepancies": discrepancies,
                    "errors": errors,
                    "results": results,
                }
        except Exception as e:
            logger.error(f"Batch reconciliation failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    return asyncio.run(reconcile_all())


def trigger_reconciliation_after_trade(user_id: str) -> None:
    """
    Trigger portfolio reconciliation after a bot trade completes.
    This is called from bot_trading_service after successful trades.

    Args:
        user_id: User ID whose portfolio needs reconciliation
    """
    try:
        # Trigger async reconciliation task
        reconcile_user_portfolio_task.delay(user_id)
        logger.debug(f"Triggered portfolio reconciliation for user {user_id}")
    except Exception as e:
        logger.warning(
            f"Failed to trigger reconciliation for user {user_id}: {e}", exc_info=True
        )
