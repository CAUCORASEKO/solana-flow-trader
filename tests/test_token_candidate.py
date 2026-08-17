from decimal import Decimal

import pytest

from solana_flow_trader.providers import TokenCandidate


def make_candidate(**overrides: object) -> TokenCandidate:
    values: dict[str, object] = {
        "token_mint": "CandidateToken11111111111111111111111111111",
        "symbol": "TEST",
        "name": "Test Token",
        "price_usd": Decimal("0.0125"),
        "market_cap_usd": Decimal("1500000"),
        "liquidity_usd": Decimal("250000"),
        "volume_24h_usd": Decimal("900000"),
        "price_change_24h_pct": Decimal("35"),
        "volume_change_24h_pct": Decimal("120"),
        "holder_count": 2500,
        "token_age_seconds": 3600,
    }

    values.update(overrides)

    return TokenCandidate(**values)


def test_token_candidate_stores_normalized_values() -> None:
    candidate = make_candidate()

    assert candidate.symbol == "TEST"
    assert candidate.market_cap_usd == Decimal("1500000")
    assert candidate.liquidity_usd == Decimal("250000")
    assert candidate.volume_24h_usd == Decimal("900000")


def test_token_candidate_allows_missing_optional_values() -> None:
    candidate = make_candidate(
        symbol=None,
        name=None,
        price_usd=None,
        market_cap_usd=None,
        liquidity_usd=None,
        volume_24h_usd=None,
        price_change_24h_pct=None,
        volume_change_24h_pct=None,
        holder_count=None,
        token_age_seconds=None,
    )

    assert candidate.symbol is None
    assert candidate.market_cap_usd is None


def test_token_candidate_rejects_empty_mint() -> None:
    with pytest.raises(ValueError, match="token_mint"):
        make_candidate(token_mint=" ")


@pytest.mark.parametrize(
    "field_name",
    [
        "price_usd",
        "market_cap_usd",
        "liquidity_usd",
        "volume_24h_usd",
    ],
)
def test_token_candidate_rejects_negative_market_values(
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        make_candidate(
            **{field_name: Decimal("-1")}
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "holder_count",
        "token_age_seconds",
    ],
)
def test_token_candidate_rejects_negative_integer_values(
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        make_candidate(
            **{field_name: -1}
        )


def test_percentage_changes_may_be_negative() -> None:
    candidate = make_candidate(
        price_change_24h_pct=Decimal("-80"),
        volume_change_24h_pct=Decimal("-25"),
    )

    assert candidate.price_change_24h_pct == Decimal("-80")
    assert candidate.volume_change_24h_pct == Decimal("-25")
