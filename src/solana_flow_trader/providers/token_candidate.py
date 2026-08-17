"""Normalized token discovery candidate."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class TokenCandidate:
    """A token discovered by a market-data provider.

    This model intentionally contains only normalized discovery information.
    Provider-specific payloads must not leak into the research core.
    """

    token_mint: str
    symbol: str | None = None
    name: str | None = None

    price_usd: Decimal | None = None
    market_cap_usd: Decimal | None = None
    liquidity_usd: Decimal | None = None
    volume_24h_usd: Decimal | None = None

    price_change_24h_pct: Decimal | None = None
    volume_change_24h_pct: Decimal | None = None

    holder_count: int | None = None
    token_age_seconds: int | None = None

    def __post_init__(self) -> None:
        if not self.token_mint.strip():
            raise ValueError("token_mint must not be empty")

        non_negative_decimals = {
            "price_usd": self.price_usd,
            "market_cap_usd": self.market_cap_usd,
            "liquidity_usd": self.liquidity_usd,
            "volume_24h_usd": self.volume_24h_usd,
        }

        for field_name, value in non_negative_decimals.items():
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")

        non_negative_integers = {
            "holder_count": self.holder_count,
            "token_age_seconds": self.token_age_seconds,
        }

        for field_name, value in non_negative_integers.items():
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")
