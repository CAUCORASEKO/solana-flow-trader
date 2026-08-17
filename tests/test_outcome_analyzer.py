from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from solana_flow_trader.events import EventDirection, HistoricalEvent
from solana_flow_trader.models import MarketSnapshot
from solana_flow_trader.outcomes import OutcomeAnalyzer

TOKEN = "OutcomeToken111111111111111111111111111111"


def make_snapshot(
    *,
    timestamp: datetime,
    price: str,
) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=timestamp,
        token_mint=TOKEN,
        symbol="OUT",
        price_usd=Decimal(price),
        market_cap_usd=Decimal("100000"),
        liquidity_usd=Decimal("50000"),
        volume_usd=Decimal("1000"),
        buy_volume_usd=Decimal("600"),
        sell_volume_usd=Decimal("400"),
        transactions=100,
        buys=60,
        sells=40,
        unique_buyers=50,
        unique_sellers=30,
        token_age_seconds=600,
        source="synthetic",
    )


def make_event(start_time: datetime) -> HistoricalEvent:
    return HistoricalEvent(
        token_mint=TOKEN,
        direction=EventDirection.BULL,
        start_time=start_time,
        end_time=start_time + timedelta(seconds=10),
        start_price=Decimal("1"),
        end_price=Decimal("1.25"),
        return_pct=Decimal("25"),
        duration_seconds=Decimal("10"),
        start_index=0,
        end_index=2,
    )


def test_analyzes_returns_mfe_and_mae() -> None:
    base = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)

    snapshots = [
        make_snapshot(timestamp=base, price="1.00"),
        make_snapshot(timestamp=base + timedelta(seconds=5), price="1.10"),
        make_snapshot(timestamp=base + timedelta(seconds=15), price="1.30"),
        make_snapshot(timestamp=base + timedelta(seconds=30), price="0.90"),
        make_snapshot(timestamp=base + timedelta(seconds=60), price="1.20"),
    ]

    outcome = OutcomeAnalyzer(
        observation_seconds=60
    ).analyze(
        "event-1",
        make_event(base),
        snapshots,
    )

    assert outcome is not None
    assert outcome.return_5s_pct == Decimal("10.0")
    assert outcome.return_15s_pct == Decimal("30.0")
    assert outcome.return_30s_pct == Decimal("-10.0")
    assert outcome.return_60s_pct == Decimal("20.0")

    assert outcome.mfe_pct == Decimal("30.0")
    assert outcome.mae_pct == Decimal("-10.0")

    assert outcome.time_to_mfe_seconds == Decimal("15.0")
    assert outcome.time_to_mae_seconds == Decimal("30.0")


def test_horizon_uses_latest_observation_at_or_before_target() -> None:
    base = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)

    snapshots = [
        make_snapshot(timestamp=base, price="1"),
        make_snapshot(
            timestamp=base + timedelta(seconds=4),
            price="1.08",
        ),
        make_snapshot(
            timestamp=base + timedelta(seconds=7),
            price="1.20",
        ),
    ]

    outcome = OutcomeAnalyzer(
        observation_seconds=10
    ).analyze(
        "event-1",
        make_event(base),
        snapshots,
    )

    assert outcome is not None
    assert outcome.return_5s_pct == Decimal("8.00")


def test_observation_window_is_respected() -> None:
    base = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)

    snapshots = [
        make_snapshot(timestamp=base, price="1"),
        make_snapshot(
            timestamp=base + timedelta(seconds=30),
            price="1.20",
        ),
        make_snapshot(
            timestamp=base + timedelta(seconds=120),
            price="3.00",
        ),
    ]

    outcome = OutcomeAnalyzer(
        observation_seconds=60
    ).analyze(
        "event-1",
        make_event(base),
        snapshots,
    )

    assert outcome is not None
    assert outcome.mfe_pct == Decimal("20.0")


def test_returns_none_for_empty_snapshots() -> None:
    base = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)

    assert (
        OutcomeAnalyzer().analyze(
            "event-1",
            make_event(base),
            [],
        )
        is None
    )


def test_rejects_empty_event_id() -> None:
    base = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="event_id"):
        OutcomeAnalyzer().analyze(
            " ",
            make_event(base),
            [
                make_snapshot(
                    timestamp=base,
                    price="1",
                )
            ],
        )


def test_rejects_non_positive_observation_window() -> None:
    with pytest.raises(ValueError, match="observation_seconds"):
        OutcomeAnalyzer(observation_seconds=0)
