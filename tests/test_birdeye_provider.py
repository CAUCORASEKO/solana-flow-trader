from decimal import Decimal
from typing import Any

import pytest

from solana_flow_trader.providers.birdeye import (
    BirdeyeNormalizer,
    BirdeyeProvider,
)

TOKEN_A = "ProviderTokenA111111111111111111111111111111"
TOKEN_B = "ProviderTokenB111111111111111111111111111111"


class FakeBirdeyeClient:
    def __init__(
        self,
        *,
        token_list_data: Any = None,
        overview_data: Any = None,
    ) -> None:
        self.token_list_data = token_list_data
        self.overview_data = overview_data

        self.last_token_list_kwargs: dict[str, Any] | None = None
        self.last_overview_token: str | None = None

    def token_list(
        self,
        **kwargs: Any,
    ) -> Any:
        self.last_token_list_kwargs = kwargs
        return self.token_list_data

    def token_overview(
        self,
        token_mint: str,
        **kwargs: Any,
    ) -> Any:
        self.last_overview_token = token_mint
        return self.overview_data


def test_provider_has_stable_name() -> None:
    provider = BirdeyeProvider(
        client=FakeBirdeyeClient()
    )

    assert provider.name == "birdeye"


def test_discover_tokens_normalizes_items() -> None:
    client = FakeBirdeyeClient(
        token_list_data={
            "items": [
                {
                    "address": TOKEN_A,
                    "symbol": "AAA",
                    "price": "1.25",
                    "marketCap": "1000000",
                    "liquidity": "300000",
                },
                {
                    "address": TOKEN_B,
                    "symbol": "BBB",
                    "price": "0.50",
                    "marketCap": "500000",
                    "liquidity": "150000",
                },
            ]
        }
    )

    provider = BirdeyeProvider(
        client=client,
        normalizer=BirdeyeNormalizer(),
    )

    candidates = provider.discover_tokens(limit=2)

    assert len(candidates) == 2

    assert candidates[0].token_mint == TOKEN_A
    assert candidates[0].symbol == "AAA"
    assert candidates[0].price_usd == Decimal("1.25")

    assert candidates[1].token_mint == TOKEN_B
    assert candidates[1].liquidity_usd == Decimal("150000")

    assert client.last_token_list_kwargs == {
        "limit": 2,
        "sort_by": "liquidity",
        "sort_type": "desc",
    }


def test_discover_tokens_accepts_direct_list_shape() -> None:
    provider = BirdeyeProvider(
        client=FakeBirdeyeClient(
            token_list_data=[
                {
                    "address": TOKEN_A,
                    "symbol": "AAA",
                }
            ]
        )
    )

    candidates = provider.discover_tokens(limit=1)

    assert len(candidates) == 1
    assert candidates[0].token_mint == TOKEN_A


def test_get_snapshot_normalizes_overview() -> None:
    client = FakeBirdeyeClient(
        overview_data={
            "address": TOKEN_A,
            "symbol": "AAA",
            "price": "1.50",
            "marketCap": "1200000",
            "liquidity": "350000",
            "v24hUSD": "400000",
            "vBuy24hUSD": "250000",
            "vSell24hUSD": "150000",
            "buy24h": 120,
            "sell24h": 80,
        }
    )

    provider = BirdeyeProvider(
        client=client
    )

    snapshot = provider.get_snapshot(TOKEN_A)

    assert snapshot.token_mint == TOKEN_A
    assert snapshot.source == "birdeye"

    assert snapshot.price_usd == Decimal("1.50")
    assert snapshot.market_cap_usd == Decimal("1200000")
    assert snapshot.liquidity_usd == Decimal("350000")

    assert snapshot.buy_volume_usd == Decimal("250000")
    assert snapshot.sell_volume_usd == Decimal("150000")
    assert snapshot.transactions == 200

    assert client.last_overview_token == TOKEN_A


def test_get_snapshot_accepts_nested_item_shape() -> None:
    provider = BirdeyeProvider(
        client=FakeBirdeyeClient(
            overview_data={
                "item": {
                    "address": TOKEN_A,
                    "symbol": "AAA",
                    "price": "2",
                }
            }
        )
    )

    snapshot = provider.get_snapshot(TOKEN_A)

    assert snapshot.token_mint == TOKEN_A
    assert snapshot.price_usd == Decimal("2")


def test_get_snapshot_can_restore_requested_mint() -> None:
    provider = BirdeyeProvider(
        client=FakeBirdeyeClient(
            overview_data={
                "price": "3",
            }
        )
    )

    snapshot = provider.get_snapshot(TOKEN_A)

    assert snapshot.token_mint == TOKEN_A
    assert snapshot.price_usd == Decimal("3")


def test_get_snapshot_rejects_empty_token_mint() -> None:
    provider = BirdeyeProvider(
        client=FakeBirdeyeClient()
    )

    with pytest.raises(ValueError, match="token_mint"):
        provider.get_snapshot(" ")


def test_discover_rejects_invalid_items_shape() -> None:
    provider = BirdeyeProvider(
        client=FakeBirdeyeClient(
            token_list_data={
                "items": "not-a-list",
            }
        )
    )

    with pytest.raises(
        ValueError,
        match="items must be a list",
    ):
        provider.discover_tokens()


def test_discover_rejects_invalid_item() -> None:
    provider = BirdeyeProvider(
        client=FakeBirdeyeClient(
            token_list_data={
                "items": [
                    "not-an-object",
                ]
            }
        )
    )

    with pytest.raises(
        ValueError,
        match="item must be an object",
    ):
        provider.discover_tokens()


def test_overview_rejects_non_object_data() -> None:
    provider = BirdeyeProvider(
        client=FakeBirdeyeClient(
            overview_data=[
                {
                    "address": TOKEN_A,
                }
            ]
        )
    )

    with pytest.raises(
        ValueError,
        match="overview data must be an object",
    ):
        provider.get_snapshot(TOKEN_A)
