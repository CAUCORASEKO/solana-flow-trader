from datetime import UTC, datetime
from decimal import Decimal

from solana_flow_trader.models import MarketSnapshot
from solana_flow_trader.providers import (
    MarketDataProvider,
    TokenCandidate,
)


class FakeMarketDataProvider(MarketDataProvider):
    @property
    def name(self) -> str:
        return "fake"

    def discover_tokens(
        self,
        *,
        limit: int = 100,
    ) -> list[TokenCandidate]:
        return [
            TokenCandidate(
                token_mint=f"Token{index}",
                symbol=f"T{index}",
            )
            for index in range(limit)
        ]

    def get_snapshot(
        self,
        token_mint: str,
    ) -> MarketSnapshot:
        return MarketSnapshot(
            timestamp=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
            token_mint=token_mint,
            symbol="TEST",
            price_usd=Decimal("1"),
            market_cap_usd=Decimal("1000000"),
            liquidity_usd=Decimal("100000"),
            volume_usd=Decimal("50000"),
            buy_volume_usd=None,
            sell_volume_usd=None,
            transactions=None,
            buys=None,
            sells=None,
            unique_buyers=None,
            unique_sellers=None,
            token_age_seconds=None,
            source="fake",
        )


def test_provider_exposes_stable_name() -> None:
    provider = FakeMarketDataProvider()

    assert provider.name == "fake"


def test_provider_discovers_normalized_candidates() -> None:
    provider = FakeMarketDataProvider()

    candidates = provider.discover_tokens(limit=3)

    assert len(candidates) == 3
    assert all(
        isinstance(candidate, TokenCandidate)
        for candidate in candidates
    )


def test_default_get_snapshots_uses_single_snapshot_method() -> None:
    provider = FakeMarketDataProvider()

    snapshots = provider.get_snapshots(
        ["TokenA", "TokenB", "TokenC"]
    )

    assert len(snapshots) == 3
    assert [
        snapshot.token_mint
        for snapshot in snapshots
    ] == [
        "TokenA",
        "TokenB",
        "TokenC",
    ]
