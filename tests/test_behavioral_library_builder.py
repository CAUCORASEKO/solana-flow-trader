from datetime import UTC, datetime
from decimal import Decimal

import pytest

from solana_flow_trader.behavior import BehavioralLibraryBuilder
from solana_flow_trader.collectors import SyntheticCollector, SyntheticScenario
from solana_flow_trader.events import HistoricalEventMiner
from solana_flow_trader.features import PreEventFeatureExtractor
from solana_flow_trader.matching import BehaviorLabel
from solana_flow_trader.outcomes import OutcomeAnalyzer

TOKEN = "LibraryToken111111111111111111111111111111"


def make_snapshots(
    multipliers: list[str],
    *,
    interval_seconds: int = 5,
):
    collector = SyntheticCollector()

    scenario = SyntheticScenario(
        token_mint=TOKEN,
        symbol="LIB",
        start_time=datetime(
            2026,
            8,
            17,
            12,
            0,
            tzinfo=UTC,
        ),
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


def make_builder() -> BehavioralLibraryBuilder:
    return BehavioralLibraryBuilder(
        event_miner=HistoricalEventMiner(
            threshold_pct=Decimal("20"),
            max_window_seconds=15,
        ),
        feature_extractor=PreEventFeatureExtractor(
            window_seconds=15,
        ),
        outcome_analyzer=OutcomeAnalyzer(
            observation_seconds=30,
        ),
    )


def test_build_returns_none_for_empty_input() -> None:
    assert make_builder().build([]) is None


def test_build_creates_bull_behavior_sample_with_outcome() -> None:
    library = make_builder().build(
        make_snapshots(
            [
                "1.00",
                "1.05",
                "1.10",
                "1.25",
                "1.35",
                "1.30",
            ]
        )
    )

    assert library is not None
    assert library.token_mint == TOKEN
    assert library.bull_count == 1
    assert library.bear_count == 0
    assert len(library.samples) == 1

    sample = library.samples[0]

    assert sample.label == BehaviorLabel.BULL
    assert sample.event_id == f"{TOKEN}:0"
    assert sample.outcome.event_id == sample.event_id
    assert sample.outcome.mfe_pct is not None


def test_build_creates_bull_and_bear_samples() -> None:
    library = make_builder().build(
        make_snapshots(
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
    )

    assert library is not None
    assert library.bull_count == 1
    assert library.bear_count == 1
    assert library.trap_count == 0
    assert len(library.samples) == 2

    assert all(
        sample.outcome.event_id == sample.event_id
        for sample in library.samples
    )


def test_event_ids_are_stable_and_unique() -> None:
    library = make_builder().build(
        make_snapshots(
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
    )

    assert library is not None

    assert [
        sample.event_id
        for sample in library.samples
    ] == [
        f"{TOKEN}:0",
        f"{TOKEN}:1",
    ]


def test_library_counts_empty_behavior_families() -> None:
    library = make_builder().build(
        make_snapshots(
            [
                "1.00",
                "1.01",
                "1.02",
            ]
        )
    )

    assert library is not None
    assert library.samples == ()
    assert library.bull_count == 0
    assert library.bear_count == 0
    assert library.trap_count == 0


def test_builder_requires_one_token() -> None:
    snapshots = make_snapshots(
        ["1.00", "1.30"]
    )

    second = snapshots[1]

    snapshots[1] = type(second)(
        timestamp=second.timestamp,
        token_mint="OtherToken111111111111111111111111111111",
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

    with pytest.raises(ValueError, match="same token"):
        make_builder().build(snapshots)
