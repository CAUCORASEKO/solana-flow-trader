from decimal import Decimal

from solana_flow_trader.features import EventFeatureVector
from solana_flow_trader.matching import FeatureSimilarity


def make_vector(**overrides: object) -> EventFeatureVector:
    values: dict[str, object] = {
        "token_mint": "SimilarityToken111111111111111111111111111",
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


def test_identical_vectors_have_full_similarity() -> None:
    matcher = FeatureSimilarity()

    result = matcher.compare(
        make_vector(),
        make_vector(),
    )

    assert result.score == Decimal("1")
    assert result.compared_features == 8
    assert result.skipped_features == 0


def test_different_vectors_reduce_similarity() -> None:
    matcher = FeatureSimilarity()

    current = make_vector()

    historical = make_vector(
        price_return_pct=Decimal("10"),
        volume_change_pct=Decimal("50"),
        buy_sell_volume_ratio=Decimal("1"),
    )

    result = matcher.compare(current, historical)

    assert Decimal("0") < result.score < Decimal("1")


def test_missing_values_are_skipped() -> None:
    matcher = FeatureSimilarity()

    current = make_vector(
        volume_change_pct=None,
        liquidity_change_pct=None,
    )

    historical = make_vector()

    result = matcher.compare(current, historical)

    assert result.compared_features == 6
    assert result.skipped_features == 2


def test_no_comparable_features_returns_zero_score() -> None:
    matcher = FeatureSimilarity()

    current = make_vector(
        price_return_pct=None,
        price_velocity_pct_per_second=None,
        volume_change_pct=None,
        transaction_change_pct=None,
        buy_sell_volume_ratio=None,
        buy_sell_transaction_ratio=None,
        liquidity_change_pct=None,
        market_cap_change_pct=None,
    )

    historical = make_vector()

    result = matcher.compare(current, historical)

    assert result.score == Decimal("0")
    assert result.compared_features == 0
    assert result.skipped_features == 8


def test_zero_values_can_match_exactly() -> None:
    matcher = FeatureSimilarity()

    result = matcher.compare(
        make_vector(
            liquidity_change_pct=Decimal("0"),
        ),
        make_vector(
            liquidity_change_pct=Decimal("0"),
        ),
    )

    assert result.score == Decimal("1")
