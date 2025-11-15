"""
Background Task Queue with Celery
For long-running tasks like backtesting, data analysis, etc.
"""
from celery import Celery
from celery.schedules import crontab
import os

# Initialize Celery
celery_app = Celery(
    'cryptoorchestrator',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes warning
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-data': {
        'task': 'tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'update-market-data': {
        'task': 'tasks.update_market_data',
        'schedule': 60.0,  # Every minute
    },
    'calculate-portfolio-metrics': {
        'task': 'tasks.calculate_portfolio_metrics',
        'schedule': 300.0,  # Every 5 minutes
    },
    'check-system-health': {
        'task': 'tasks.check_system_health',
        'schedule': 120.0,  # Every 2 minutes
    },
    'reconcile-portfolios': {
        'task': 'tasks.reconcile_portfolios',
        'schedule': 3600.0,  # Every hour
    },
}


@celery_app.task(name='tasks.run_backtest')
def run_backtest_task(bot_id: str, start_date: str, end_date: str):
    """
    Run backtesting in background
    Usage: run_backtest_task.delay('bot_123', '2024-01-01', '2024-12-31')
    """
    from server_fastapi.services.backtesting_service import BacktestingService
    
    service = BacktestingService()
    result = service.run_backtest(bot_id, start_date, end_date)
    return result


@celery_app.task(name='tasks.train_ml_model')
def train_ml_model_task(model_type: str, data_path: str):
    """
    Train ML model in background
    Usage: train_ml_model_task.delay('lstm', '/data/btc_history.csv')
    """
    from server_fastapi.services.ml_training_service import MLTrainingService
    
    service = MLTrainingService()
    result = service.train_model(model_type, data_path)
    return result


@celery_app.task(name='tasks.update_market_data')
def update_market_data():
    """Update market data from exchanges"""
    from server_fastapi.services.market_data_service import MarketDataService
    
    service = MarketDataService()
    result = service.fetch_latest_data()
    return {"status": "success", "pairs_updated": len(result)}


@celery_app.task(name='tasks.calculate_portfolio_metrics')
def calculate_portfolio_metrics():
    """Calculate portfolio performance metrics"""
    from server_fastapi.services.portfolio_service import PortfolioService
    
    service = PortfolioService()
    result = service.calculate_all_metrics()
    return {"status": "success", "portfolios_processed": len(result)}


@celery_app.task(name='tasks.cleanup_old_data')
def cleanup_old_data():
    """Clean up old logs, cache, and temporary data"""
    import shutil
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=30)
    
    # Cleanup logic here
    return {"status": "success", "cutoff_date": cutoff_date.isoformat()}


@celery_app.task(name='tasks.check_system_health')
def check_system_health():
    """Check system health and send alerts if needed"""
    from server_fastapi.routes.health_advanced import health_checker
    import asyncio
    
    # Run async health check
    health = asyncio.run(health_checker.check_all())
    
    if health.status == "unhealthy":
        # Send alert
        from server_fastapi.services.performance_monitoring import performance_monitor
        from server_fastapi.services.performance_monitoring import Alert, AlertSeverity
        
        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            component="system_health",
            message=f"System unhealthy: {len([c for c in health.components if c.status == 'unhealthy'])} components down"
        )
        asyncio.run(performance_monitor.alert_callback(alert))
    
    return {"status": health.status}


@celery_app.task(name='tasks.send_trading_report')
def send_trading_report(user_id: str, period: str = 'daily'):
    """
    Generate and send trading performance report
    Usage: send_trading_report.delay('user_123', 'weekly')
    """
    from server_fastapi.services.reporting_service import ReportingService
    
    service = ReportingService()
    report = service.generate_report(user_id, period)
    
    # Send via email/notification
    return {"status": "success", "report_id": report.id}


@celery_app.task(name='tasks.process_large_dataset')
def process_large_dataset(dataset_id: str):
    """
    Process large datasets asynchronously
    """
    # Heavy data processing here
    return {"status": "success", "dataset_id": dataset_id}


@celery_app.task(bind=True, name='tasks.long_running_task')
def long_running_task(self, iterations: int = 100):
    """
    Example of a long-running task with progress updates
    """
    for i in range(iterations):
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': i, 'total': iterations, 'status': f'Processing {i}/{iterations}'}
        )
        
        # Do work here
        import time
        time.sleep(0.1)
    
    return {'status': 'completed', 'result': 'Success!'}


@celery_app.task(name='tasks.reconcile_portfolios')
def reconcile_portfolios():
    """
    Periodic task to reconcile all user portfolios
    Validates portfolio balances against trade history
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from server_fastapi.services.portfolio_reconciliation import PortfolioReconciliationService
    from server_fastapi.database import get_database_url
    
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
                success = sum(1 for r in results if r['status'] == 'success')
                discrepancies = sum(1 for r in results if r['status'] == 'discrepancies_found')
                errors = sum(1 for r in results if r['status'] == 'error')
                
                return {
                    'status': 'completed',
                    'total_portfolios': total,
                    'success': success,
                    'discrepancies': discrepancies,
                    'errors': errors,
                    'results': results
                }
            finally:
                await engine.dispose()
    
    # Run the async function
    return asyncio.run(run_reconciliation())
