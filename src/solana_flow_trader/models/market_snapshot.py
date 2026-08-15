"""Core market observation models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """A normalized observation of a Solana token at one point in time.

    This model stores observable market facts only.
    Derived indicators and strategy features belong in separate layers.
    """

    timestamp: datetime
    token_mint: str
    symbol: str | None

    price_usd: Decimal | None
    market_cap_usd: Decimal | None
    liquidity_usd: Decimal | None

    volume_usd: Decimal | None
    buy_volume_usd: Decimal | None
    sell_volume_usd: Decimal | None

    transactions: int | None
    buys: int | None
    sells: int | None

    unique_buyers: int | None
    unique_sellers: int | None

    token_age_seconds: int | None
    source: str

    def __post_init__(self) -> None:
        if not self.token_mint.strip():
            raise ValueError("token_mint must not be empty")

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

        if self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must have a valid UTC offset")

        non_negative_decimals = {
            "price_usd": self.price_usd,
            "market_cap_usd": self.market_cap_usd,
            "liquidity_usd": self.liquidity_usd,
            "volume_usd": self.volume_usd,
            "buy_volume_usd": self.buy_volume_usd,
            "sell_volume_usd": self.sell_volume_usd,
        }

        for field_name, value in non_negative_decimals.items():
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")

        non_negative_integers = {
            "transactions": self.transactions,
            "buys": self.buys,
            "sells": self.sells,
            "unique_buyers": self.unique_buyers,
            "unique_sellers": self.unique_sellers,
            "token_age_seconds": self.token_age_seconds,
        }

        for field_name, value in non_negative_integers.items():
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")

    @property
    def timestamp_utc(self) -> datetime:
        """Return the snapshot timestamp normalized to UTC."""
        return self.timestamp.astimezone(UTC)
