"""add_database_views

Revision ID: add_db_views_001
Revises: optimize_query_indexes_001
Create Date: 2025-12-06 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_db_views_001'
down_revision = 'optimize_query_indexes_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create database views for common query patterns.
    Views improve query performance by pre-computing joins and aggregations.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    def table_exists(table_name: str) -> bool:
        return table_name in inspector.get_table_names()
    
    def view_exists(view_name: str) -> bool:
        # Check if view exists (PostgreSQL)
        if bind.dialect.name == 'postgresql':
            result = bind.execute(sa.text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = :view_name)"
            ).bindparams(view_name=view_name))
            return result.scalar()
        return False
    
    # View: User Portfolio Summary
    # Aggregates portfolio data with user information
    if table_exists('portfolios') and table_exists('users') and not view_exists('v_user_portfolio_summary'):
        op.execute("""
            CREATE VIEW v_user_portfolio_summary AS
            SELECT 
                u.id as user_id,
                u.email,
                p.mode,
                p.total_value,
                p.available_balance,
                p.total_pnl,
                p.total_pnl_percent,
                p.updated_at as portfolio_updated_at
            FROM users u
            LEFT JOIN portfolios p ON u.id = p.user_id
        """)
    
    # View: Bot Performance Summary
    # Aggregates bot performance metrics
    if table_exists('bots') and table_exists('trades') and not view_exists('v_bot_performance_summary'):
        op.execute("""
            CREATE VIEW v_bot_performance_summary AS
            SELECT 
                b.id as bot_id,
                b.user_id,
                b.name as bot_name,
                b.strategy,
                b.is_active,
                COUNT(t.id) as total_trades,
                SUM(CASE WHEN t.side = 'buy' THEN t.amount * t.price ELSE 0 END) as total_buy_volume,
                SUM(CASE WHEN t.side = 'sell' THEN t.amount * t.price ELSE 0 END) as total_sell_volume,
                AVG(t.pnl) as avg_pnl,
                SUM(t.pnl) as total_pnl,
                MAX(t.created_at) as last_trade_at
            FROM bots b
            LEFT JOIN trades t ON b.id = t.bot_id
            GROUP BY b.id, b.user_id, b.name, b.strategy, b.is_active
        """)
    
    # View: Daily Trading Activity
    # Aggregates daily trading statistics
    if table_exists('trades') and not view_exists('v_daily_trading_activity'):
        op.execute("""
            CREATE VIEW v_daily_trading_activity AS
            SELECT 
                DATE(created_at) as trade_date,
                user_id,
                mode,
                COUNT(*) as trade_count,
                SUM(amount * price) as total_volume,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades
            FROM trades
            GROUP BY DATE(created_at), user_id, mode
        """)
    
    # View: Risk Alert Summary
    # Aggregates risk alerts by user
    if table_exists('risk_alerts') and not view_exists('v_risk_alert_summary'):
        op.execute("""
            CREATE VIEW v_risk_alert_summary AS
            SELECT 
                user_id,
                alert_type,
                severity,
                COUNT(*) as alert_count,
                MAX(created_at) as last_alert_at,
                COUNT(CASE WHEN acknowledged = false THEN 1 END) as unacknowledged_count
            FROM risk_alerts
            GROUP BY user_id, alert_type, severity
        """)


def downgrade() -> None:
    """Drop database views"""
    bind = op.get_bind()
    
    views = [
        'v_risk_alert_summary',
        'v_daily_trading_activity',
        'v_bot_performance_summary',
        'v_user_portfolio_summary'
    ]
    
    for view_name in views:
        try:
            op.execute(f"DROP VIEW IF EXISTS {view_name}")
        except Exception as e:
            # Log but don't fail if view doesn't exist
            print(f"Could not drop view {view_name}: {e}")
