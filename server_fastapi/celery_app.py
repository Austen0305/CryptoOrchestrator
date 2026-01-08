"""
Background Task Queue with Celery
For long-running tasks like backtesting, data analysis, etc.
Enhanced with prioritization, batching, rate limiting, and monitoring.
"""

import logging
import os

from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Initialize rate limiter with default limits
try:
    from .utils.task_rate_limiter import get_task_rate_limiter

    rate_limiter = get_task_rate_limiter()

    # Set default rate limits for common tasks
    rate_limiter.set_rate_limit(
        "tasks.update_market_data", max_calls=60, time_window_seconds=60
    )  # 60/min
    rate_limiter.set_rate_limit(
        "tasks.calculate_portfolio_metrics", max_calls=12, time_window_seconds=60
    )  # 12/min
    rate_limiter.set_rate_limit(
        "tasks.run_backtest", max_calls=10, time_window_seconds=3600
    )  # 10/hour
    rate_limiter.set_rate_limit(
        "tasks.train_ml_model", max_calls=5, time_window_seconds=3600
    )  # 5/hour

    logger.info("Task rate limits configured")
except Exception as e:
    logger.warning(f"Failed to configure rate limits: {e}")

# Initialize Celery
celery_app = Celery(
    "cryptoorchestrator",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
)

# Import bot worker tasks
try:
    from .workers.bot_worker import check_subscriptions, execute_bot, stop_bot

    celery_app.conf.beat_schedule.update(
        {
            "check-subscriptions": {
                "task": "bot_worker.check_subscriptions",
                "schedule": 3600.0,  # Every hour
            },
        }
    )
except ImportError:
    logger.warning("Bot worker tasks not available")

# Import competitive trading bot worker tasks
try:
    from .workers.trading_bots_worker import (
        process_dca_orders,
        process_grid_cycles,
        process_infinity_grids,
        process_trailing_bots,
        update_futures_pnl,
    )

    logger.info("[OK] Competitive trading bot worker tasks loaded")
except ImportError as e:
    logger.warning(f"Competitive trading bot worker tasks not available: {e}")

# Import transaction batcher tasks
try:
    from .celery_tasks.transaction_batcher_tasks import (
        flush_pending_batches,
        get_pending_batch_count,
    )

    logger.info("[OK] Transaction batcher tasks loaded")
except ImportError as e:
    logger.warning(f"Transaction batcher tasks not available: {e}")

# Import portfolio reconciliation tasks
try:
    from .tasks.portfolio_reconciliation import (
        reconcile_all_portfolios_batch_task,
        reconcile_user_portfolio_task,
    )

    logger.info("[OK] Portfolio reconciliation tasks loaded")
except ImportError as e:
    logger.warning(f"Portfolio reconciliation tasks not available: {e}")

# Configuration with task prioritization, monitoring, and enhanced features
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes warning
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Task prioritization queues
    task_routes={
        "workers.bot_worker.*": {"queue": "high_priority"},
        "workers.trading_bots_worker.*": {"queue": "high_priority"},
        "tasks.run_backtest": {"queue": "medium_priority"},
        "tasks.update_market_data": {"queue": "low_priority"},
        "tasks.cleanup_old_data": {"queue": "low_priority"},
    },
    # Queue configuration
    task_default_queue="default",
    task_default_exchange="tasks",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    # Task result caching
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    # Task monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Task result backend settings
    result_backend_always_retry=True,
    result_backend_max_retries=10,
    # Task acknowledgment settings
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    # Task compression
    task_compression="gzip",  # Compress large task payloads
    result_compression="gzip",  # Compress large results
)

# Periodic tasks
# Import security tasks
try:
    from .tasks.security_tasks import (
        cleanup_old_security_events_task,
        monitor_security_events_task,
        verify_audit_log_integrity_task,
    )

    logger.info("[OK] Security tasks loaded")
except ImportError as e:
    logger.warning(f"Security tasks not available: {e}")

# Import marketplace tasks
try:
    from .tasks.marketplace_tasks import (
        calculate_monthly_payouts_task,
        check_underperforming_providers_task,
        flag_suspicious_providers_task,
        update_all_provider_metrics_task,
        update_single_provider_metrics_task,
        verify_all_providers_task,
    )

    logger.info("[OK] Marketplace tasks loaded")
except ImportError as e:
    logger.warning(f"Marketplace tasks not available: {e}")

celery_app.conf.beat_schedule = {
    # Transaction batching - flush pending batches every 30 seconds
    "flush-transaction-batches": {
        "task": "transaction_batcher.flush_pending_batches",
        "schedule": 30.0,  # Every 30 seconds
    },
    "cleanup-old-data": {
        "task": "tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "update-market-data": {
        "task": "tasks.update_market_data",
        "schedule": 60.0,  # Every minute
    },
    "calculate-portfolio-metrics": {
        "task": "tasks.calculate_portfolio_metrics",
        "schedule": 300.0,  # Every 5 minutes
    },
    "check-system-health": {
        "task": "tasks.check_system_health",
        "schedule": 120.0,  # Every 2 minutes
    },
    "reconcile-portfolios": {
        "task": "tasks.reconcile_portfolios",
        "schedule": 3600.0,  # Every hour
    },
    "portfolio-reconciliation": {
        "task": "tasks.reconcile_all_portfolios",
        "schedule": 1800.0,  # Every 30 minutes
    },
    "reconcile-all-portfolios-batch": {
        "task": "tasks.reconcile_all_portfolios_batch",
        "schedule": 3600.0,  # Every hour
    },
    "check-alert-escalations": {
        "task": "tasks.check_alert_escalations",
        "schedule": 60.0,  # Every minute
    },
    # Backup tasks
    "daily-backup": {
        "task": "backups.create_daily_backup",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "cleanup-backups": {
        "task": "backups.cleanup_old_backups",
        "schedule": crontab(hour=3, minute=0),  # 3 AM daily
    },
    "distribute-staking-rewards": {
        "task": "tasks.distribute_staking_rewards",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight UTC
    },
    # Security tasks
    "verify-audit-log-integrity": {
        "task": "security.verify_audit_log_integrity",
        "schedule": 3600.0,  # Every hour
    },
    "monitor-security-events": {
        "task": "security.monitor_security_events",
        "schedule": 900.0,  # Every 15 minutes
    },
    "cleanup-old-security-events": {
        "task": "security.cleanup_old_security_events",
        "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    # Marketplace tasks
    "check-analytics-thresholds": {
        "task": "marketplace.check_analytics_thresholds",
        "schedule": 900.0,  # Every 15 minutes
    },
    "update-all-provider-metrics": {
        "task": "marketplace.update_all_provider_metrics",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM UTC
    },
    "calculate-monthly-payouts": {
        "task": "marketplace.calculate_monthly_payouts",
        "schedule": crontab(
            day_of_month=1, hour=2, minute=0
        ),  # 1st of each month at 2 AM UTC
    },
    "check-underperforming-providers": {
        "task": "marketplace.check_underperforming_providers",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    "verify-all-providers": {
        "task": "marketplace.verify_all_providers",
        "schedule": crontab(
            day_of_week=0, hour=5, minute=0
        ),  # Weekly on Sunday at 5 AM UTC
    },
    "flag-suspicious-providers": {
        "task": "marketplace.flag_suspicious_providers",
        "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM UTC
    },
}


@celery_app.task(name="tasks.run_backtest")
def run_backtest_task(bot_id: str, start_date: str, end_date: str):
    """
    Run backtesting in background
    Usage: run_backtest_task.delay('bot_123', '2024-01-01', '2024-12-31')
    """
    from server_fastapi.services.backtesting_service import BacktestingService

    service = BacktestingService()
    result = service.run_backtest(bot_id, start_date, end_date)
    return result


@celery_app.task(name="tasks.train_ml_model")
def train_ml_model_task(model_type: str, data_path: str):
    """
    Train ML model in background
    Usage: train_ml_model_task.delay('lstm', '/data/btc_history.csv')
    """
    from server_fastapi.services.ml_training_service import MLTrainingService

    service = MLTrainingService()
    result = service.train_model(model_type, data_path)
    return result


@celery_app.task(name="tasks.update_market_data")
def update_market_data():
    """Update market data from exchanges"""
    from server_fastapi.services.market_data_service import MarketDataService

    service = MarketDataService()
    result = service.fetch_latest_data()
    return {"status": "success", "pairs_updated": len(result)}


@celery_app.task(name="tasks.calculate_portfolio_metrics")
def calculate_portfolio_metrics():
    """Calculate portfolio performance metrics"""
    from server_fastapi.services.portfolio_service import PortfolioService

    service = PortfolioService()
    result = service.calculate_all_metrics()
    return {"status": "success", "portfolios_processed": len(result)}


@celery_app.task(name="tasks.cleanup_old_data")
def cleanup_old_data():
    """Clean up old logs, cache, and temporary data"""
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=30)

    # Cleanup logic here
    return {"status": "success", "cutoff_date": cutoff_date.isoformat()}


@celery_app.task(name="tasks.check_system_health")
def check_system_health():
    """Check system health and send alerts if needed"""
    import asyncio

    from server_fastapi.routes.health_advanced import health_checker

    # Run async health check
    health = asyncio.run(health_checker.check_all())

    if health.status == "unhealthy":
        # Send alert
        from server_fastapi.services.performance_monitoring import Alert, AlertSeverity
        from server_fastapi.services.performance_monitoring import (
            performance_monitor as system_performance_monitor,
        )

        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            component="system_health",
            message=f"System unhealthy: {len([c for c in health.components if c.status == 'unhealthy'])} components down",
        )
        asyncio.run(system_performance_monitor.alert_callback(alert))

    return {"status": health.status}


@celery_app.task(name="tasks.send_trading_report")
def send_trading_report(user_id: str, period: str = "daily"):
    """
    Generate and send trading performance report
    Usage: send_trading_report.delay('user_123', 'weekly')
    """
    from server_fastapi.services.reporting_service import ReportingService

    service = ReportingService()
    report = service.generate_report(user_id, period)

    # Send via email/notification
    return {"status": "success", "report_id": report.id}


@celery_app.task(name="tasks.process_large_dataset")
def process_large_dataset(dataset_id: str):
    """
    Process large datasets asynchronously
    """
    # Heavy data processing here
    return {"status": "success", "dataset_id": dataset_id}


@celery_app.task(name="tasks.check_alert_escalations")
def check_alert_escalations():
    """
    Check and escalate unacknowledged alerts.
    Runs periodically to ensure alerts are escalated appropriately.
    """
    import asyncio

    from server_fastapi.services.alerting.alerting_service import get_alerting_service

    async def check_escalations():
        try:
            service = get_alerting_service()
            await service.check_escalations()
            logger.info("Alert escalation check completed")
            return {"status": "success", "escalations_checked": True}
        except Exception as e:
            logger.error(f"Error checking alert escalations: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    return asyncio.run(check_escalations())


@celery_app.task(name="tasks.reconcile_all_portfolios")
def reconcile_all_portfolios():
    """
    Reconcile all user portfolios with trade history.
    Runs periodically to keep portfolio, trades, and analytics in sync.
    """
    import asyncio

    from sqlalchemy import select

    from server_fastapi.database import get_db_context
    from server_fastapi.models.user import User
    from server_fastapi.services.portfolio_reconciliation import (
        PortfolioReconciliationService,
    )

    async def reconcile_all():
        async with get_db_context() as db:
            # Get all users
            result = await db.execute(select(User.id))
            user_ids = [row[0] for row in result.all()]

            reconciled = 0
            discrepancies_found = 0

            for user_id in user_ids:
                try:
                    service = PortfolioReconciliationService(db_session=db)
                    result = await service.reconcile_portfolio(str(user_id))

                    if result.get("status") == "discrepancies_found":
                        discrepancies_found += 1
                        logger.warning(
                            f"Portfolio discrepancies found for user {user_id}: {result.get('discrepancies', [])}"
                        )

                    reconciled += 1
                except Exception as e:
                    logger.error(
                        f"Failed to reconcile portfolio for user {user_id}: {e}",
                        exc_info=True,
                    )

            return {
                "status": "success",
                "users_reconciled": reconciled,
                "discrepancies_found": discrepancies_found,
            }

    return asyncio.run(reconcile_all())


@celery_app.task(bind=True, name="tasks.long_running_task")
def long_running_task(self, iterations: int = 100):
    """
    Example of a long-running task with progress updates
    """
    for i in range(iterations):
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i,
                "total": iterations,
                "status": f"Processing {i}/{iterations}",
            },
        )

        # Do work here
        import time

        time.sleep(0.1)

    return {"status": "completed", "result": "Success!"}


@celery_app.task(name="tasks.reconcile_portfolios")
def reconcile_portfolios():
    """
    Periodic task to reconcile all user portfolios
    Validates portfolio balances against trade history
    """
    import asyncio

    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from server_fastapi.database import get_database_url
    from server_fastapi.services.portfolio_reconciliation import (
        PortfolioReconciliationService,
    )

    async def run_reconciliation():
        # Create async engine for this task
        engine = create_async_engine(get_database_url(), echo=False)
        async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            try:
                service = PortfolioReconciliationService(db_session=session)
                results = await service.reconcile_all_portfolios()

                # Summary statistics
                total = len(results)
                success = sum(1 for r in results if r["status"] == "success")
                discrepancies = sum(
                    1 for r in results if r["status"] == "discrepancies_found"
                )
                errors = sum(1 for r in results if r["status"] == "error")

                return {
                    "status": "completed",
                    "total_portfolios": total,
                    "success": success,
                    "discrepancies": discrepancies,
                    "errors": errors,
                    "results": results,
                }
            finally:
                await engine.dispose()

    # Run the async function
    return asyncio.run(run_reconciliation())
