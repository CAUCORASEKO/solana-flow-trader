"""Feature models derived from historical event context."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class EventFeatureVector:
    """Observable features describing the context before an event."""

    token_mint: str

    window_seconds: int
    sample_count: int

    price_return_pct: Decimal | None
    price_velocity_pct_per_second: Decimal | None

    volume_change_pct: Decimal | None
    transaction_change_pct: Decimal | None

    buy_sell_volume_ratio: Decimal | None
    buy_sell_transaction_ratio: Decimal | None

    liquidity_change_pct: Decimal | None
    market_cap_change_pct: Decimal | None

    def __post_init__(self) -> None:
        if not self.token_mint.strip():
            raise ValueError("token_mint must not be empty")

        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        if self.sample_count <= 0:
            raise ValueError("sample_count must be positive")
