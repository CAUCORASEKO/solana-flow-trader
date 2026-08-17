from decimal import Decimal

import pytest

from solana_flow_trader.features import EventFeatureVector
from solana_flow_trader.matching import (
    BehavioralMatcher,
    BehaviorLabel,
    LabeledFeatureVector,
)


def make_vector(**overrides: object) -> EventFeatureVector:
    values: dict[str, object] = {
        "token_mint": "BehaviorToken111111111111111111111111111",
        "window_seconds": 20,
        "sample_count": 3,
        "price_return_pct": Decimal("20"),
        "price_velocity_pct_per_second": Decimal("1"),
        "volume_change_pct": Decimal("100"),
        "transaction_change_pct": Decimal("80"),
        "buy_sell_volume_ratio": Decimal("2"),
        "buy_sell_transaction_ratio": Decimal("1.8"),
        "liquidity_change_pct": Decimal("5"),
        "market_cap_change_pct": Decimal("20"),
    }
    values.update(overrides)
    return EventFeatureVector(**values)  # type: ignore[arg-type]


def labeled(
    event_id: str,
    label: BehaviorLabel,
    **overrides: object,
) -> LabeledFeatureVector:
    return LabeledFeatureVector(
        event_id=event_id,
        label=label,
        features=make_vector(**overrides),
    )


def test_identical_bull_history_produces_full_bull_score() -> None:
    matcher = BehavioralMatcher()

    result = matcher.match(
        make_vector(),
        [
            labeled("bull-1", BehaviorLabel.BULL),
            labeled(
                "bear-1",
                BehaviorLabel.BEAR,
                price_return_pct=Decimal("-20"),
                price_velocity_pct_per_second=Decimal("-1"),
                buy_sell_volume_ratio=Decimal("0.5"),
            ),
        ],
    )

    assert result.bull.score == Decimal("1")
    assert result.bull.match_count == 1
    assert result.bull.top_matches[0].event_id == "bull-1"
    assert result.bear.score < result.bull.score


def test_returns_top_matches_ordered_by_similarity() -> None:
    matcher = BehavioralMatcher(top_k=2)

    result = matcher.match(
        make_vector(),
        [
            labeled("bull-best", BehaviorLabel.BULL),
            labeled(
                "bull-medium",
                BehaviorLabel.BULL,
                volume_change_pct=Decimal("70"),
            ),
            labeled(
                "bull-low",
                BehaviorLabel.BULL,
                volume_change_pct=Decimal("10"),
                price_return_pct=Decimal("5"),
            ),
        ],
    )

    assert result.bull.match_count == 3
    assert len(result.bull.top_matches) == 2
    assert result.bull.top_matches[0].event_id == "bull-best"
    assert result.bull.top_matches[0].score >= result.bull.top_matches[1].score


def test_family_score_is_average_of_top_k_matches() -> None:
    matcher = BehavioralMatcher(top_k=2)

    result = matcher.match(
        make_vector(),
        [
            labeled("bull-1", BehaviorLabel.BULL),
            labeled(
                "bull-2",
                BehaviorLabel.BULL,
                volume_change_pct=Decimal("50"),
            ),
            labeled(
                "bull-3",
                BehaviorLabel.BULL,
                volume_change_pct=Decimal("0"),
            ),
        ],
    )

    top = result.bull.top_matches

    expected = (top[0].score + top[1].score) / Decimal("2")

    assert result.bull.score == expected


def test_empty_family_returns_zero_score() -> None:
    matcher = BehavioralMatcher()

    result = matcher.match(
        make_vector(),
        [
            labeled("bull-1", BehaviorLabel.BULL),
        ],
    )

    assert result.bear.score == Decimal("0")
    assert result.bear.match_count == 0
    assert result.bear.top_matches == ()

    assert result.trap.score == Decimal("0")
    assert result.trap.match_count == 0
    assert result.trap.top_matches == ()


def test_trap_family_is_scored_independently() -> None:
    matcher = BehavioralMatcher()

    result = matcher.match(
        make_vector(),
        [
            labeled(
                "bull-distant",
                BehaviorLabel.BULL,
                volume_change_pct=Decimal("10"),
                transaction_change_pct=Decimal("5"),
            ),
            labeled("trap-close", BehaviorLabel.TRAP),
        ],
    )

    assert result.trap.score == Decimal("1")
    assert result.trap.score > result.bull.score
    assert result.trap.top_matches[0].event_id == "trap-close"


def test_missing_features_preserve_comparison_metadata() -> None:
    matcher = BehavioralMatcher()

    result = matcher.match(
        make_vector(volume_change_pct=None),
        [
            labeled("bull-1", BehaviorLabel.BULL),
        ],
    )

    best = result.bull.top_matches[0]

    assert best.compared_features == 7
    assert best.skipped_features == 1


def test_rejects_non_positive_top_k() -> None:
    with pytest.raises(ValueError, match="top_k"):
        BehavioralMatcher(top_k=0)


def test_labeled_vector_requires_event_id() -> None:
    with pytest.raises(ValueError, match="event_id"):
        LabeledFeatureVector(
            event_id=" ",
            label=BehaviorLabel.BULL,
            features=make_vector(),
        )
