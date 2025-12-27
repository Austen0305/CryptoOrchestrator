"""
Marketplace Background Tasks
Celery tasks for marketplace operations:
- Daily metrics updates for signal providers
- Monthly payout calculations
- Performance alerts for underperforming providers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy import select, and_

from ..celery_app import celery_app
from ..database import get_db_context
from ..models.signal_provider import SignalProvider, CuratorStatus, Payout
from ..services.marketplace_service import MarketplaceService
from ..services.marketplace_verification_service import MarketplaceVerificationService

logger = logging.getLogger(__name__)


@celery_app.task(name="marketplace.update_all_provider_metrics", bind=True)
def update_all_provider_metrics_task(self) -> Dict:
    """
    Update performance metrics for all approved signal providers.
    Runs daily to keep metrics current.
    """
    async def update_metrics():
        try:
            logger.info("Starting daily metrics update for all signal providers")
            
            async with get_db_context() as session:
                # Get all approved signal providers
                result = await session.execute(
                    select(SignalProvider).where(
                        SignalProvider.curator_status == CuratorStatus.APPROVED.value
                    )
                )
                signal_providers = result.scalars().all()
                
                updated_count = 0
                failed_count = 0
                
                marketplace_service = MarketplaceService(session)
                
                for signal_provider in signal_providers:
                    try:
                        await marketplace_service.update_performance_metrics(signal_provider.id)
                        updated_count += 1
                        logger.debug(f"Updated metrics for signal provider {signal_provider.id}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(
                            f"Failed to update metrics for signal provider {signal_provider.id}: {e}",
                            exc_info=True
                        )
                        # Continue with next provider
                        continue
                
                logger.info(
                    f"Metrics update completed: {updated_count} updated, {failed_count} failed"
                )
                
                return {
                    "status": "completed",
                    "updated_count": updated_count,
                    "failed_count": failed_count,
                    "total_providers": len(signal_providers),
                }
        except Exception as e:
            logger.error(f"Error in update_all_provider_metrics_task: {e}", exc_info=True)
            raise
    
    return asyncio.run(update_metrics())


@celery_app.task(name="marketplace.calculate_monthly_payouts", bind=True)
def calculate_monthly_payouts_task(self) -> Dict:
    """
    Calculate and create monthly payouts for all signal providers.
    Runs on the 1st of each month for the previous month.
    """
    async def calculate_payouts():
        try:
            logger.info("Starting monthly payout calculation")
            
            async with get_db_context() as session:
                # Calculate period (previous month)
                now = datetime.utcnow()
                # First day of current month
                current_month_start = datetime(now.year, now.month, 1)
                # First day of previous month
                previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
                # Last day of previous month
                previous_month_end = current_month_start - timedelta(seconds=1)
                
                # Get all approved signal providers with active followers
                result = await session.execute(
                    select(SignalProvider).where(
                        and_(
                            SignalProvider.curator_status == CuratorStatus.APPROVED.value,
                            SignalProvider.is_public == True,
                        )
                    )
                )
                signal_providers = result.scalars().all()
                
                created_count = 0
                failed_count = 0
                total_payout_amount = 0.0
                
                marketplace_service = MarketplaceService(session)
                
                for signal_provider in signal_providers:
                    try:
                        # Check if payout already exists for this period
                        existing_result = await session.execute(
                            select(Payout).where(
                                and_(
                                    Payout.signal_provider_id == signal_provider.id,
                                    Payout.period_start >= previous_month_start,
                                    Payout.period_end <= previous_month_end,
                                )
                            )
                        )
                        existing_payout = existing_result.scalar_one_or_none()
                        
                        if existing_payout:
                            logger.debug(
                                f"Payout already exists for signal provider {signal_provider.id} for period {previous_month_start} to {previous_month_end}"
                            )
                            continue
                        
                        # Calculate payout
                        payout_data = await marketplace_service.calculate_payout(
                            signal_provider.id, previous_month_start, previous_month_end
                        )
                        
                        # Only create payout if there's revenue
                        if payout_data["total_revenue"] > 0:
                            payout = await marketplace_service.create_payout(
                                signal_provider.id, previous_month_start, previous_month_end
                            )
                            created_count += 1
                            total_payout_amount += payout["provider_payout"]
                            logger.info(
                                f"Created payout for signal provider {signal_provider.id}: ${payout['provider_payout']:.2f}"
                            )
                        else:
                            logger.debug(
                                f"No revenue for signal provider {signal_provider.id} in period {previous_month_start} to {previous_month_end}"
                            )
                            
                    except Exception as e:
                        failed_count += 1
                        logger.error(
                            f"Failed to create payout for signal provider {signal_provider.id}: {e}",
                            exc_info=True
                        )
                        # Continue with next provider
                        continue
                
                logger.info(
                    f"Monthly payout calculation completed: {created_count} payouts created, {failed_count} failed, total amount: ${total_payout_amount:.2f}"
                )
                
                return {
                    "status": "completed",
                    "created_count": created_count,
                    "failed_count": failed_count,
                    "total_payout_amount": total_payout_amount,
                    "period_start": previous_month_start.isoformat(),
                    "period_end": previous_month_end.isoformat(),
                }
        except Exception as e:
            logger.error(f"Error in calculate_monthly_payouts_task: {e}", exc_info=True)
            raise
    
    return asyncio.run(calculate_payouts())


@celery_app.task(name="marketplace.check_underperforming_providers", bind=True)
def check_underperforming_providers_task(self) -> Dict:
    """
    Check for underperforming signal providers and send alerts.
    Runs daily to monitor provider performance.
    """
    async def check_providers():
        try:
            logger.info("Checking for underperforming signal providers")
            
            async with get_db_context() as session:
                # Get all approved signal providers
                result = await session.execute(
                    select(SignalProvider).where(
                        SignalProvider.curator_status == CuratorStatus.APPROVED.value
                    )
                )
                signal_providers = result.scalars().all()
                
                underperforming_count = 0
                alerts_sent = 0
                
                # Thresholds for underperformance
                MIN_WIN_RATE = 0.4  # 40% win rate
                MAX_DRAWDOWN = 0.30  # 30% max drawdown
                MIN_SHARPE_RATIO = 0.5  # Sharpe ratio below 0.5
                MIN_TRADES = 10  # Need at least 10 trades to evaluate
                
                for signal_provider in signal_providers:
                    try:
                        # Skip if not enough trades
                        if signal_provider.total_trades < MIN_TRADES:
                            continue
                        
                        is_underperforming = False
                        reasons = []
                        
                        # Check win rate
                        if signal_provider.win_rate < MIN_WIN_RATE:
                            is_underperforming = True
                            reasons.append(f"Win rate {signal_provider.win_rate:.1%} below {MIN_WIN_RATE:.1%}")
                        
                        # Check max drawdown
                        if signal_provider.max_drawdown > MAX_DRAWDOWN * 100:  # Convert to percentage
                            is_underperforming = True
                            reasons.append(f"Max drawdown {signal_provider.max_drawdown:.1f}% above {MAX_DRAWDOWN * 100:.1f}%")
                        
                        # Check Sharpe ratio
                        if signal_provider.sharpe_ratio < MIN_SHARPE_RATIO:
                            is_underperforming = True
                            reasons.append(f"Sharpe ratio {signal_provider.sharpe_ratio:.2f} below {MIN_SHARPE_RATIO}")
                        
                        if is_underperforming:
                            underperforming_count += 1
                            
                            # Log alert
                            logger.warning(
                                f"Underperforming signal provider detected: {signal_provider.id} (User {signal_provider.user_id}) - {', '.join(reasons)}"
                            )
                            
                            # Send email notification to provider
                            try:
                                from ..services.marketplace_email_service import MarketplaceEmailService
                                from ..models.user import User
                                
                                user = await session.get(User, signal_provider.user_id)
                                if user and user.email:
                                    email_service = MarketplaceEmailService()
                                    metrics = {
                                        'win_rate': signal_provider.win_rate or 0.0,
                                        'sharpe_ratio': signal_provider.sharpe_ratio or 0.0,
                                        'max_drawdown': signal_provider.max_drawdown or 0.0,
                                        'total_trades': signal_provider.total_trades or 0,
                                    }
                                    await email_service.send_underperforming_alert_email(
                                        to_email=user.email,
                                        provider_name=user.username or user.email,
                                        reasons=reasons,
                                        metrics=metrics,
                                    )
                                    alerts_sent += 1
                            except Exception as e:
                                logger.error(f"Failed to send underperforming alert email: {e}", exc_info=True)
                            
                    except Exception as e:
                        logger.error(
                            f"Error checking signal provider {signal_provider.id}: {e}",
                            exc_info=True
                        )
                        continue
                
                logger.info(
                    f"Underperformance check completed: {underperforming_count} underperforming providers, {alerts_sent} alerts sent"
                )
                
                return {
                    "status": "completed",
                    "underperforming_count": underperforming_count,
                    "alerts_sent": alerts_sent,
                    "total_providers_checked": len(signal_providers),
                }
        except Exception as e:
            logger.error(f"Error in check_underperforming_providers_task: {e}", exc_info=True)
            raise
    
    return asyncio.run(check_providers())


@celery_app.task(name="marketplace.update_single_provider_metrics", bind=True)
def update_single_provider_metrics_task(self, signal_provider_id: int) -> Dict:
    """
    Update performance metrics for a single signal provider.
    Can be called on-demand or after trades are executed.
    """
    async def update_metrics():
        try:
            logger.info(f"Updating metrics for signal provider {signal_provider_id}")
            
            async with get_db_context() as session:
                marketplace_service = MarketplaceService(session)
                result = await marketplace_service.update_performance_metrics(signal_provider_id)
                
                logger.info(f"Metrics updated for signal provider {signal_provider_id}: {result}")
                
                return {
                    "status": "completed",
                    "signal_provider_id": signal_provider_id,
                    "metrics": result,
                }
        except Exception as e:
            logger.error(
                f"Error updating metrics for signal provider {signal_provider_id}: {e}",
                exc_info=True
            )
            raise
    
    return asyncio.run(update_metrics())


@celery_app.task(name="marketplace.check_analytics_thresholds", bind=True)
def check_analytics_thresholds_task(self) -> Dict:
    """
    Check all enabled analytics thresholds and trigger notifications if needed.
    Runs every 15 minutes to monitor marketplace analytics metrics.
    """
    async def check_thresholds():
        try:
            logger.info("Checking analytics thresholds")
            
            async with get_db_context() as session:
                from ..services.marketplace_threshold_service import MarketplaceThresholdService
                
                threshold_service = MarketplaceThresholdService(session)
                triggered_alerts = await threshold_service.check_all_thresholds()
                
                logger.info(
                    f"Analytics threshold check completed: {len(triggered_alerts)} thresholds triggered"
                )
                
                return {
                    "status": "completed",
                    "triggered_count": len(triggered_alerts),
                    "alerts": triggered_alerts,
                    "checked_at": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            logger.error(f"Error in check_analytics_thresholds_task: {e}", exc_info=True)
            raise
    
    return asyncio.run(check_thresholds())
