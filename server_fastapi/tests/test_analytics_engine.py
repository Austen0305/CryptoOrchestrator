import pytest
import asyncio

from server_fastapi.services.analytics_engine import AnalyticsEngine, PerformanceMetrics, BotConfig


@pytest.mark.asyncio
async def test_generate_performance_report_basic():
    engine = AnalyticsEngine()

    # Provide a fake bot
    async def fake_get_bot(bot_id: str):
        return BotConfig(id=bot_id, name=f"Bot {bot_id}")

    # Provide sample metrics
    async def fake_calculate_performance_metrics(bot_id: str, period: str = '30d'):
        return PerformanceMetrics(
            botId=bot_id,
            period=period,
            totalReturn=0.1234,
            sharpeRatio=1.23,
            maxDrawdown=0.045,
            winRate=0.56,
            averageWin=150.5,
            averageLoss=45.25,
            profitFactor=2.5,
            totalTrades=42,
        )

    engine._get_bot = fake_get_bot
    engine.calculate_performance_metrics = fake_calculate_performance_metrics

    report = await engine.generate_performance_report('bot-1', '30d')

    assert 'Performance Report for Bot bot-1 (30d)' in report
    assert 'Total Return:' in report
    assert 'Sharpe Ratio:' in report
    assert 'Profit Factor:' in report
    assert 'Total Trades:' in report
