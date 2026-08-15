"""Synthetic market-data collector for deterministic research tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from solana_flow_trader.models import MarketSnapshot


@dataclass(frozen=True, slots=True)
class SyntheticScenario:
    """Configuration for a deterministic synthetic token sequence."""

    token_mint: str
    symbol: str
    start_time: datetime
    start_price_usd: Decimal
    market_cap_usd: Decimal
    liquidity_usd: Decimal
    token_age_seconds: int
    source: str = "synthetic"


class SyntheticCollector:
    """Generate deterministic MarketSnapshot sequences."""

    def generate(
        self,
        scenario: SyntheticScenario,
        price_multipliers: list[Decimal],
        *,
        interval_seconds: int = 1,
    ) -> list[MarketSnapshot]:
        if not price_multipliers:
            return []

        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")

        if scenario.start_time.tzinfo is None or scenario.start_time.utcoffset() is None:
            raise ValueError("start_time must be timezone-aware")

        if scenario.start_price_usd <= 0:
            raise ValueError("start_price_usd must be positive")

        snapshots: list[MarketSnapshot] = []

        previous_price = scenario.start_price_usd

        for index, multiplier in enumerate(price_multipliers):
            if multiplier <= 0:
                raise ValueError("price multipliers must be positive")

            price = scenario.start_price_usd * multiplier

            price_change = price - previous_price

            if price_change >= 0:
                buy_volume = Decimal("1000") + Decimal(index * 125)
                sell_volume = Decimal("450") + Decimal(index * 40)
            else:
                buy_volume = Decimal("450") + Decimal(index * 40)
                sell_volume = Decimal("1000") + Decimal(index * 125)

            volume = buy_volume + sell_volume

            buys = 20 + index * 3 if price_change >= 0 else 10 + index
            sells = 10 + index if price_change >= 0 else 20 + index * 3

            snapshot = MarketSnapshot(
                timestamp=scenario.start_time
                + timedelta(seconds=index * interval_seconds),
                token_mint=scenario.token_mint,
                symbol=scenario.symbol,
                price_usd=price,
                market_cap_usd=scenario.market_cap_usd * multiplier,
                liquidity_usd=scenario.liquidity_usd,
                volume_usd=volume,
                buy_volume_usd=buy_volume,
                sell_volume_usd=sell_volume,
                transactions=buys + sells,
                buys=buys,
                sells=sells,
                unique_buyers=max(1, buys - 2),
                unique_sellers=max(1, sells - 2),
                token_age_seconds=scenario.token_age_seconds
                + index * interval_seconds,
                source=scenario.source,
            )

            snapshots.append(snapshot)
            previous_price = price

        return snapshots
