from decimal import Decimal

from solana_flow_trader.behavior import (
    BehaviorSample,
    OutcomeDistributionCalculator,
)
from solana_flow_trader.features import EventFeatureVector
from solana_flow_trader.matching import BehaviorLabel
from solana_flow_trader.outcomes import EventOutcome


def make_features() -> EventFeatureVector:
    return EventFeatureVector(
        token_mint="DistributionToken1111111111111111111111111",
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
    *,
    mfe: str,
    mae: str,
    return_15s: str,
    return_30s: str,
    return_60s: str,
) -> BehaviorSample:
    return BehaviorSample(
        event_id=event_id,
        label=BehaviorLabel.BULL,
        features=make_features(),
        outcome=EventOutcome(
            event_id=event_id,
            return_5s_pct=None,
            return_15s_pct=Decimal(return_15s),
            return_30s_pct=Decimal(return_30s),
            return_60s_pct=Decimal(return_60s),
            mfe_pct=Decimal(mfe),
            mae_pct=Decimal(mae),
            time_to_mfe_seconds=None,
            time_to_mae_seconds=None,
            observation_seconds=60,
            sample_count=10,
        ),
    )


def test_calculates_outcome_percentiles() -> None:
    samples = (
        make_sample(
            "event-1",
            mfe="10",
            mae="-12",
            return_15s="-5",
            return_30s="0",
            return_60s="5",
        ),
        make_sample(
            "event-2",
            mfe="20",
            mae="-8",
            return_15s="5",
            return_30s="10",
            return_60s="15",
        ),
        make_sample(
            "event-3",
            mfe="30",
            mae="-4",
            return_15s="15",
            return_30s="20",
            return_60s="25",
        ),
        make_sample(
            "event-4",
            mfe="40",
            mae="-2",
            return_15s="25",
            return_30s="30",
            return_60s="35",
        ),
        make_sample(
            "event-5",
            mfe="50",
            mae="-1",
            return_15s="35",
            return_30s="40",
            return_60s="45",
        ),
    )

    result = OutcomeDistributionCalculator().calculate(
        samples,
        label=BehaviorLabel.BULL,
    )

    assert result.sample_count == 5

    assert result.mfe_p25_pct == Decimal("20")
    assert result.mfe_p50_pct == Decimal("30")
    assert result.mfe_p75_pct == Decimal("40")

    assert result.mae_p25_pct == Decimal("-8")
    assert result.mae_p50_pct == Decimal("-4")
    assert result.mae_p75_pct == Decimal("-2")

    assert result.return_30s_p25_pct == Decimal("10")
    assert result.return_30s_p50_pct == Decimal("20")
    assert result.return_30s_p75_pct == Decimal("30")


def test_calculates_positive_rates() -> None:
    samples = (
        make_sample(
            "event-1",
            mfe="10",
            mae="-10",
            return_15s="-5",
            return_30s="-5",
            return_60s="-5",
        ),
        make_sample(
            "event-2",
            mfe="20",
            mae="-5",
            return_15s="5",
            return_30s="5",
            return_60s="5",
        ),
        make_sample(
            "event-3",
            mfe="30",
            mae="-3",
            return_15s="10",
            return_30s="10",
            return_60s="10",
        ),
        make_sample(
            "event-4",
            mfe="40",
            mae="-2",
            return_15s="20",
            return_30s="20",
            return_60s="20",
        ),
    )

    result = OutcomeDistributionCalculator().calculate(
        samples,
        label=BehaviorLabel.BULL,
    )

    assert result.positive_15s_rate == Decimal("0.75")
    assert result.positive_30s_rate == Decimal("0.75")
    assert result.positive_60s_rate == Decimal("0.75")


def test_empty_family_returns_none_distribution() -> None:
    result = OutcomeDistributionCalculator().calculate(
        (),
        label=BehaviorLabel.BEAR,
    )

    assert result.sample_count == 0
    assert result.mfe_p25_pct is None
    assert result.mfe_p50_pct is None
    assert result.mfe_p75_pct is None
    assert result.positive_30s_rate is None
