from datetime import UTC, datetime
from decimal import Decimal

import pytest

from solana_flow_trader.models import MarketSnapshot


def make_snapshot(**overrides: object) -> MarketSnapshot:
    values: dict[str, object] = {
        "timestamp": datetime(2026, 8, 15, 10, 30, tzinfo=UTC),
        "token_mint": "ExampleMint1111111111111111111111111111111",
        "symbol": "TEST",
        "price_usd": Decimal("0.0123"),
        "market_cap_usd": Decimal("125000"),
        "liquidity_usd": Decimal("42000"),
        "volume_usd": Decimal("18000"),
        "buy_volume_usd": Decimal("11000"),
        "sell_volume_usd": Decimal("7000"),
        "transactions": 320,
        "buys": 210,
        "sells": 110,
        "unique_buyers": 150,
        "unique_sellers": 82,
        "token_age_seconds": 720,
        "source": "synthetic",
    }
    values.update(overrides)
    return MarketSnapshot(**values)  # type: ignore[arg-type]


def test_market_snapshot_accepts_valid_observation() -> None:
    snapshot = make_snapshot()

    assert snapshot.symbol == "TEST"
    assert snapshot.price_usd == Decimal("0.0123")
    assert snapshot.timestamp_utc.tzinfo == UTC


def test_market_snapshot_requires_timezone_aware_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        make_snapshot(timestamp=datetime(2026, 8, 15, 10, 30))


def test_market_snapshot_rejects_empty_token_mint() -> None:
    with pytest.raises(ValueError, match="token_mint"):
        make_snapshot(token_mint="   ")


def test_market_snapshot_rejects_empty_source() -> None:
    with pytest.raises(ValueError, match="source"):
        make_snapshot(source="")


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("price_usd", Decimal("-0.01")),
        ("market_cap_usd", Decimal("-1")),
        ("liquidity_usd", Decimal("-1")),
        ("volume_usd", Decimal("-1")),
        ("buy_volume_usd", Decimal("-1")),
        ("sell_volume_usd", Decimal("-1")),
    ],
)
def test_market_snapshot_rejects_negative_decimal_fields(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        make_snapshot(**{field_name: value})


@pytest.mark.parametrize(
    "field_name",
    [
        "transactions",
        "buys",
        "sells",
        "unique_buyers",
        "unique_sellers",
        "token_age_seconds",
    ],
)
def test_market_snapshot_rejects_negative_integer_fields(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        make_snapshot(**{field_name: -1})


def test_market_snapshot_allows_missing_optional_market_values() -> None:
    snapshot = make_snapshot(
        symbol=None,
        price_usd=None,
        market_cap_usd=None,
        liquidity_usd=None,
        volume_usd=None,
        buy_volume_usd=None,
        sell_volume_usd=None,
        transactions=None,
        buys=None,
        sells=None,
        unique_buyers=None,
        unique_sellers=None,
        token_age_seconds=None,
    )

    assert snapshot.symbol is None
    assert snapshot.price_usd is None
