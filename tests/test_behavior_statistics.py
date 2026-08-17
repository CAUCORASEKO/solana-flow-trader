from decimal import Decimal

from solana_flow_trader.behavior import (
    BehaviorSample,
    BehaviorStatisticsCalculator,
)
from solana_flow_trader.features import EventFeatureVector
from solana_flow_trader.matching import BehaviorLabel
from solana_flow_trader.outcomes import EventOutcome


def make_features() -> EventFeatureVector:
    return EventFeatureVector(
        token_mint="StatsToken111111111111111111111111111111",
        window_seconds=20,
        sample_count=3,
        price_return_pct=Decimal("10"),
        price_velocity_pct_per_second=Decimal("0.5"),
        volume_change_pct=Decimal("50"),
        transaction_change_pct=Decimal("40"),
        buy_sell_volume_ratio=Decimal("2"),
        buy_sell_transaction_ratio=Decimal("1.5"),
        liquidity_change_pct=Decimal("3"),
        market_cap_change_pct=Decimal("10"),
    )


def make_sample(
    event_id: str,
    label: BehaviorLabel,
    *,
    mfe: str,
    mae: str,
    return_5s: str,
    return_15s: str,
    return_30s: str,
    return_60s: str,
    time_to_mfe: str,
    time_to_mae: str,
) -> BehaviorSample:
    return BehaviorSample(
        event_id=event_id,
        label=label,
        features=make_features(),
        outcome=EventOutcome(
            event_id=event_id,
            return_5s_pct=Decimal(return_5s),
            return_15s_pct=Decimal(return_15s),
            return_30s_pct=Decimal(return_30s),
            return_60s_pct=Decimal(return_60s),
            mfe_pct=Decimal(mfe),
            mae_pct=Decimal(mae),
            time_to_mfe_seconds=Decimal(time_to_mfe),
            time_to_mae_seconds=Decimal(time_to_mae),
            observation_seconds=60,
            sample_count=10,
        ),
    )


def test_calculates_family_medians() -> None:
    samples = (
        make_sample(
            "bull-1",
            BehaviorLabel.BULL,
            mfe="20",
            mae="-5",
            return_5s="5",
            return_15s="10",
            return_30s="15",
            return_60s="12",
            time_to_mfe="20",
            time_to_mae="3",
        ),
        make_sample(
            "bull-2",
            BehaviorLabel.BULL,
            mfe="40",
            mae="-7",
            return_5s="10",
            return_15s="20",
            return_30s="30",
            return_60s="25",
            time_to_mfe="30",
            time_to_mae="5",
        ),
        make_sample(
            "bull-3",
            BehaviorLabel.BULL,
            mfe="30",
            mae="-6",
            return_5s="8",
            return_15s="15",
            return_30s="20",
            return_60s="18",
            time_to_mfe="25",
            time_to_mae="4",
        ),
    )

    stats = BehaviorStatisticsCalculator().calculate(
        samples,
        label=BehaviorLabel.BULL,
    )

    assert stats.sample_count == 3
    assert stats.median_mfe_pct == Decimal("30")
    assert stats.median_mae_pct == Decimal("-6")
    assert stats.median_return_5s_pct == Decimal("8")
    assert stats.median_return_15s_pct == Decimal("15")
    assert stats.median_return_30s_pct == Decimal("20")
    assert stats.median_return_60s_pct == Decimal("18")
    assert stats.median_time_to_mfe_seconds == Decimal("25")
    assert stats.median_time_to_mae_seconds == Decimal("4")


def test_filters_samples_by_label() -> None:
    samples = (
        make_sample(
            "bull-1",
            BehaviorLabel.BULL,
            mfe="20",
            mae="-5",
            return_5s="5",
            return_15s="10",
            return_30s="15",
            return_60s="12",
            time_to_mfe="20",
            time_to_mae="3",
        ),
        make_sample(
            "bear-1",
            BehaviorLabel.BEAR,
            mfe="3",
            mae="-30",
            return_5s="-8",
            return_15s="-15",
            return_30s="-25",
            return_60s="-20",
            time_to_mfe="2",
            time_to_mae="22",
        ),
    )

    stats = BehaviorStatisticsCalculator().calculate(
        samples,
        label=BehaviorLabel.BEAR,
    )

    assert stats.sample_count == 1
    assert stats.median_mae_pct == Decimal("-30")
    assert stats.median_return_30s_pct == Decimal("-25")


def test_empty_family_returns_none_statistics() -> None:
    stats = BehaviorStatisticsCalculator().calculate(
        (),
        label=BehaviorLabel.TRAP,
    )

    assert stats.sample_count == 0
    assert stats.median_mfe_pct is None
    assert stats.median_mae_pct is None
    assert stats.median_return_5s_pct is None
    assert stats.median_time_to_mfe_seconds is None
