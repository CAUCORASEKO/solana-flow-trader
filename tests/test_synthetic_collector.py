from datetime import UTC, datetime
from decimal import Decimal

import pytest

from solana_flow_trader.collectors import SyntheticCollector, SyntheticScenario


def make_scenario(**overrides: object) -> SyntheticScenario:
    values: dict[str, object] = {
        "token_mint": "SyntheticToken11111111111111111111111111111",
        "symbol": "SYN",
        "start_time": datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        "start_price_usd": Decimal("1"),
        "market_cap_usd": Decimal("100000"),
        "liquidity_usd": Decimal("50000"),
        "token_age_seconds": 60,
    }
    values.update(overrides)
    return SyntheticScenario(**values)  # type: ignore[arg-type]


def test_generate_returns_deterministic_snapshots() -> None:
    collector = SyntheticCollector()
    scenario = make_scenario()

    snapshots = collector.generate(
        scenario,
        [
            Decimal("1.00"),
            Decimal("1.10"),
            Decimal("1.25"),
            Decimal("1.20"),
        ],
    )

    assert len(snapshots) == 4
    assert snapshots[0].price_usd == Decimal("1.00")
    assert snapshots[1].price_usd == Decimal("1.10")
    assert snapshots[2].price_usd == Decimal("1.25")
    assert snapshots[3].price_usd == Decimal("1.20")


def test_generate_advances_timestamps() -> None:
    collector = SyntheticCollector()
    scenario = make_scenario()

    snapshots = collector.generate(
        scenario,
        [Decimal("1"), Decimal("1.1"), Decimal("1.2")],
        interval_seconds=5,
    )

    assert snapshots[0].timestamp == datetime(2026, 8, 15, 12, 0, tzinfo=UTC)
    assert snapshots[1].timestamp == datetime(2026, 8, 15, 12, 0, 5, tzinfo=UTC)
    assert snapshots[2].timestamp == datetime(2026, 8, 15, 12, 0, 10, tzinfo=UTC)


def test_generate_updates_token_age() -> None:
    collector = SyntheticCollector()
    scenario = make_scenario(token_age_seconds=100)

    snapshots = collector.generate(
        scenario,
        [Decimal("1"), Decimal("1.1"), Decimal("1.2")],
        interval_seconds=10,
    )

    assert [snapshot.token_age_seconds for snapshot in snapshots] == [
        100,
        110,
        120,
    ]


def test_rising_price_has_buy_dominance() -> None:
    collector = SyntheticCollector()
    scenario = make_scenario()

    snapshots = collector.generate(
        scenario,
        [Decimal("1"), Decimal("1.2")],
    )

    rising = snapshots[1]

    assert rising.buy_volume_usd is not None
    assert rising.sell_volume_usd is not None
    assert rising.buy_volume_usd > rising.sell_volume_usd
    assert rising.buys is not None
    assert rising.sells is not None
    assert rising.buys > rising.sells


def test_falling_price_has_sell_dominance() -> None:
    collector = SyntheticCollector()
    scenario = make_scenario()

    snapshots = collector.generate(
        scenario,
        [Decimal("1"), Decimal("0.8")],
    )

    falling = snapshots[1]

    assert falling.buy_volume_usd is not None
    assert falling.sell_volume_usd is not None
    assert falling.sell_volume_usd > falling.buy_volume_usd
    assert falling.buys is not None
    assert falling.sells is not None
    assert falling.sells > falling.buys


def test_empty_price_sequence_returns_empty_list() -> None:
    collector = SyntheticCollector()

    assert collector.generate(make_scenario(), []) == []


def test_generate_rejects_non_positive_interval() -> None:
    collector = SyntheticCollector()

    with pytest.raises(ValueError, match="interval_seconds"):
        collector.generate(
            make_scenario(),
            [Decimal("1")],
            interval_seconds=0,
        )


def test_generate_rejects_naive_start_time() -> None:
    collector = SyntheticCollector()

    with pytest.raises(ValueError, match="timezone-aware"):
        collector.generate(
            make_scenario(start_time=datetime(2026, 8, 15, 12, 0)),
            [Decimal("1")],
        )


def test_generate_rejects_non_positive_start_price() -> None:
    collector = SyntheticCollector()

    with pytest.raises(ValueError, match="start_price_usd"):
        collector.generate(
            make_scenario(start_price_usd=Decimal("0")),
            [Decimal("1")],
        )


def test_generate_rejects_non_positive_multiplier() -> None:
    collector = SyntheticCollector()

    with pytest.raises(ValueError, match="multipliers"):
        collector.generate(
            make_scenario(),
            [Decimal("1"), Decimal("0")],
        )
