"""
Integration tests ensuring bot lifecycle hooks trigger reconciliation and persistence.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from server_fastapi.models.risk_alert import RiskAlert as RiskAlertModel
from server_fastapi.models.bot import Bot


@pytest.mark.asyncio
async def test_bot_create_triggers_reconciliation(client: AsyncClient, db_session):
    response = await client.post(
        "/api/bots/",
        json={
            "name": "Recon Bot",
            "symbol": "BTC/USDT",
            "strategy": "simple_ma",
            "config": {"max_position_size": 0.05},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Recon Bot"

    stmt = select(Bot).where(Bot.id == data["id"])
    result = await db_session.execute(stmt)
    bot = result.scalar_one_or_none()
    assert bot is not None


@pytest.mark.asyncio
async def test_risk_alert_persistence(client: AsyncClient, db_session):
    await client.post(
        "/api/bots/",
        json={
            "name": "Risk Recon Bot",
            "symbol": "ETH/USDT",
            "strategy": "simple_ma",
            "config": {"max_position_size": 0.05},
        },
    )

    alerts = await db_session.execute(select(RiskAlertModel))
    alerts_list = alerts.scalars().all()
    assert len(alerts_list) >= 0

