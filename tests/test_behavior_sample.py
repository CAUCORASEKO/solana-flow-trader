from decimal import Decimal

import pytest

from solana_flow_trader.behavior import BehaviorSample
from solana_flow_trader.features import EventFeatureVector
from solana_flow_trader.matching import BehaviorLabel
from solana_flow_trader.outcomes import EventOutcome


def make_features() -> EventFeatureVector:
    return EventFeatureVector(
        token_mint="SampleToken111111111111111111111111111111",
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


def make_outcome(event_id: str) -> EventOutcome:
    return EventOutcome(
        event_id=event_id,
        return_5s_pct=Decimal("5"),
        return_15s_pct=Decimal("15"),
        return_30s_pct=Decimal("20"),
        return_60s_pct=Decimal("18"),
        mfe_pct=Decimal("25"),
        mae_pct=Decimal("-4"),
        time_to_mfe_seconds=Decimal("22"),
        time_to_mae_seconds=Decimal("3"),
        observation_seconds=60,
        sample_count=10,
    )


def test_behavior_sample_accepts_matching_event_id() -> None:
    sample = BehaviorSample(
        event_id="event-1",
        label=BehaviorLabel.BULL,
        features=make_features(),
        outcome=make_outcome("event-1"),
    )

    assert sample.event_id == "event-1"


def test_behavior_sample_rejects_mismatched_outcome_event_id() -> None:
    with pytest.raises(ValueError, match="outcome.event_id"):
        BehaviorSample(
            event_id="event-1",
            label=BehaviorLabel.BULL,
            features=make_features(),
            outcome=make_outcome("event-2"),
        )
