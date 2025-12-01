"""
Unit tests for RiskService database-backed operations.
"""
import pytest
from sqlalchemy import select

from server_fastapi.services.risk_service import RiskService
from server_fastapi.models.risk_limit import RiskLimit as RiskLimitModel


@pytest.mark.asyncio
async def test_update_user_limits_persists(db_session):
    service = RiskService(db_session=db_session)
    user_id = "user-test"

    updated = await service.update_user_limits(
        user_id,
        {
            "maxPositionSize": 25,
            "maxDailyLoss": 7,
        },
    )

    assert updated.maxPositionSize == 25
    assert updated.maxDailyLoss == 7

    stmt = select(RiskLimitModel).where(RiskLimitModel.user_id == user_id)
    result = await db_session.execute(stmt)
    limits = result.scalars().all()
    assert len(limits) == 2
    stored = {limit.limit_type: limit.value for limit in limits}
    assert stored["max_position_size"] == 25
    assert stored["max_daily_loss"] == 7


@pytest.mark.asyncio
async def test_get_user_alerts_falls_back_to_db(db_session):
    service = RiskService(db_session=db_session)
    alert = await service.create_alert_db(
        user_id="alert-user",
        alert_type="portfolio_reconciliation",
        severity="medium",
        message="Discrepancy found",
        current_value=1.0,
        threshold_value=0.0,
    )
    assert alert is not None

    alerts = await service.get_user_alerts("alert-user")
    assert any(a.message == "Discrepancy found" for a in alerts)

