from datetime import UTC, datetime
from decimal import Decimal

import pytest

from solana_flow_trader.collectors import SyntheticCollector, SyntheticScenario
from solana_flow_trader.events import EventDirection, HistoricalEventMiner


def make_snapshots(
    multipliers: list[str],
    *,
    interval_seconds: int = 5,
):
    collector = SyntheticCollector()

    scenario = SyntheticScenario(
        token_mint="EventToken1111111111111111111111111111111",
        symbol="EVT",
        start_time=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        start_price_usd=Decimal("1"),
        market_cap_usd=Decimal("100000"),
        liquidity_usd=Decimal("50000"),
        token_age_seconds=100,
    )

    return collector.generate(
        scenario,
        [Decimal(value) for value in multipliers],
        interval_seconds=interval_seconds,
    )


def test_detects_representative_bull_event() -> None:
    snapshots = make_snapshots(
        ["1.00", "1.10", "1.22", "1.35", "1.50"]
    )

    miner = HistoricalEventMiner(
        threshold_pct=Decimal("20"),
        max_window_seconds=30,
    )

    events = miner.mine(snapshots)

    assert len(events) == 1

    event = events[0]

    assert event.direction == EventDirection.BULL
    assert event.start_index == 0
    assert event.end_index == 4
    assert event.start_price == Decimal("1.00")
    assert event.end_price == Decimal("1.50")
    assert event.return_pct == Decimal("50.0")


def test_detects_representative_bear_event() -> None:
    snapshots = make_snapshots(
        ["1.00", "0.94", "0.82", "0.70", "0.62"]
    )

    miner = HistoricalEventMiner(
        threshold_pct=Decimal("20"),
        max_window_seconds=30,
    )

    events = miner.mine(snapshots)

    assert len(events) == 1

    event = events[0]

    assert event.direction == EventDirection.BEAR
    assert event.start_index == 0
    assert event.end_index == 4
    assert event.end_price == Decimal("0.62")
    assert event.return_pct == Decimal("-38.00")


def test_does_not_emit_overlapping_sub_events_for_same_impulse() -> None:
    snapshots = make_snapshots(
        ["1.00", "1.10", "1.21", "1.35", "1.50"]
    )

    miner = HistoricalEventMiner(
        threshold_pct=Decimal("20"),
        max_window_seconds=30,
    )

    events = miner.mine(snapshots)

    assert len(events) == 1
    assert events[0].start_index == 0
    assert events[0].end_index == 4


def test_detects_multiple_separate_events() -> None:
    snapshots = make_snapshots(
        [
            "1.00",
            "1.10",
            "1.25",
            "1.30",
            "1.28",
            "1.27",
            "1.00",
            "0.90",
            "0.75",
            "0.70",
        ]
    )

    miner = HistoricalEventMiner(
        threshold_pct=Decimal("20"),
        max_window_seconds=15,
    )

    events = miner.mine(snapshots)

    assert len(events) == 2
    assert events[0].direction == EventDirection.BULL
    assert events[1].direction == EventDirection.BEAR


def test_ignores_move_that_does_not_reach_threshold() -> None:
    snapshots = make_snapshots(
        ["1.00", "1.05", "1.10", "1.15"]
    )

    miner = HistoricalEventMiner(
        threshold_pct=Decimal("20"),
        max_window_seconds=30,
    )

    assert miner.mine(snapshots) == []


def test_respects_max_window() -> None:
    snapshots = make_snapshots(
        ["1.00", "1.05", "1.10", "1.25"],
        interval_seconds=20,
    )

    miner = HistoricalEventMiner(
        threshold_pct=Decimal("20"),
        max_window_seconds=30,
    )

    assert miner.mine(snapshots) == []


def test_requires_one_token_per_sequence() -> None:
    snapshots = make_snapshots(["1.00", "1.30"])

    second = snapshots[1]

    snapshots[1] = type(second)(
        timestamp=second.timestamp,
        token_mint="DifferentToken111111111111111111111111111",
        symbol=second.symbol,
        price_usd=second.price_usd,
        market_cap_usd=second.market_cap_usd,
        liquidity_usd=second.liquidity_usd,
        volume_usd=second.volume_usd,
        buy_volume_usd=second.buy_volume_usd,
        sell_volume_usd=second.sell_volume_usd,
        transactions=second.transactions,
        buys=second.buys,
        sells=second.sells,
        unique_buyers=second.unique_buyers,
        unique_sellers=second.unique_sellers,
        token_age_seconds=second.token_age_seconds,
        source=second.source,
    )

    miner = HistoricalEventMiner(
        threshold_pct=Decimal("20"),
        max_window_seconds=30,
    )

    with pytest.raises(ValueError, match="same token"):
        miner.mine(snapshots)


def test_rejects_non_positive_threshold() -> None:
    with pytest.raises(ValueError, match="threshold_pct"):
        HistoricalEventMiner(
            threshold_pct=Decimal("0"),
            max_window_seconds=30,
        )


def test_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError, match="max_window_seconds"):
        HistoricalEventMiner(
            threshold_pct=Decimal("20"),
            max_window_seconds=0,
        )
