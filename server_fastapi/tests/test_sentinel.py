from datetime import UTC, datetime, timedelta

from server_fastapi.core.events import TradeEvent
from server_fastapi.services.sentinel_service import SentinelService


def test_detect_wash_trading_circular() -> None:
    """
    Verifies that A -> B -> A pattern is detected as Wash Trading.
    """
    sentinel = SentinelService(window_minutes=60)

    base_time = datetime.now(UTC)

    # 1. Trade 1: A sells to B
    trade1 = TradeEvent(
        trade_id="t1",
        buyer_id="trader_A",
        seller_id="trader_B",
        asset="BTC-USD",
        amount=1.0,
        price=50000.0,
        timestamp=base_time - timedelta(minutes=10),
    )
    alert1 = sentinel.ingest_trade(trade1)
    assert alert1 is None, "First trade should be clean"

    # 2. Trade 2: B sells BACK to A (Reversal)
    trade2 = TradeEvent(
        trade_id="t2",
        buyer_id="trader_B",
        seller_id="trader_A",
        asset="BTC-USD",
        amount=1.0,
        price=50100.0,  # Slight price change
        timestamp=base_time,
    )

    alert2 = sentinel.ingest_trade(trade2)

    assert alert2 is not None, "Should detect circular trading"
    assert alert2.abuse_type == "WASH_TRADING_CIRCULAR"
    # Note: details order might depend on implementation,
    # but A <-> B should be there.
    assert (
        "trader_A <-> trader_B" in alert2.details
        or "trader_B <-> trader_A" in alert2.details
    )


def test_clean_trading() -> None:
    """
    Verifies that normal trading A -> B, C -> D is not flagged.
    """
    sentinel = SentinelService(window_minutes=60)
    base_time = datetime.now(UTC)

    trade1 = TradeEvent(
        trade_id="t1",
        buyer_id="A",
        seller_id="B",
        asset="BTC",
        amount=1.0,
        price=100.0,
        timestamp=base_time,
    )
    sentinel.ingest_trade(trade1)

    trade2 = TradeEvent(
        trade_id="t2",
        buyer_id="C",
        seller_id="D",
        asset="BTC",
        amount=1.0,
        price=100.0,
        timestamp=base_time,
    )
    alert = sentinel.ingest_trade(trade2)
    assert alert is None


def test_detect_sandwich_attack() -> None:
    """
    Verifies that Attacker Buy -> Victim Buy -> Attacker Sell is detected.
    """
    sentinel = SentinelService(window_minutes=60)
    base_time = datetime.now(UTC)
    asset = "SOL-USD"
    attacker = "attacker_1"
    victim = "victim_1"

    # 1. Attacker Buy (Front-run)
    t1 = TradeEvent(
        trade_id="t1",
        buyer_id=attacker,
        seller_id="seller_1",
        asset=asset,
        amount=10.0,
        price=100.0,
        timestamp=base_time - timedelta(seconds=5),
    )
    sentinel.ingest_trade(t1)

    # 2. Victim Buy
    t2 = TradeEvent(
        trade_id="t2",
        buyer_id=victim,
        seller_id="seller_2",
        asset=asset,
        amount=1.0,
        price=101.0,
        timestamp=base_time - timedelta(seconds=2),
    )
    sentinel.ingest_trade(t2)

    # 3. Attacker Sell (Back-run)
    t3 = TradeEvent(
        trade_id="t3",
        buyer_id="buyer_3",
        seller_id=attacker,
        asset=asset,
        amount=10.0,
        price=102.0,
        timestamp=base_time,
    )
    alert = sentinel.ingest_trade(t3)

    assert alert is not None
    assert alert.abuse_type == "MARKET_MANIPULATION_SANDWICH"
    assert attacker in alert.details
