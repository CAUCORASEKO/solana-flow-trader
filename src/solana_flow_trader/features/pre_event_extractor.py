"""Pre-event context feature extraction."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from solana_flow_trader.events import HistoricalEvent
from solana_flow_trader.features.event_features import EventFeatureVector
from solana_flow_trader.models import MarketSnapshot


class PreEventFeatureExtractor:
    """Extract observable market features from a window before an event."""

    def __init__(self, *, window_seconds: int) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self.window_seconds = window_seconds

    def extract(
        self,
        event: HistoricalEvent,
        snapshots: list[MarketSnapshot],
    ) -> EventFeatureVector | None:
        if not snapshots:
            return None

        token_snapshots = [
            snapshot
            for snapshot in snapshots
            if snapshot.token_mint == event.token_mint
        ]

        if not token_snapshots:
            return None

        window_start = event.start_time - timedelta(seconds=self.window_seconds)

        window = sorted(
            [
                snapshot
                for snapshot in token_snapshots
                if window_start <= snapshot.timestamp <= event.start_time
            ],
            key=lambda snapshot: snapshot.timestamp,
        )

        if not window:
            return None

        first = window[0]
        last = window[-1]

        price_return_pct = self._change_pct(
            first.price_usd,
            last.price_usd,
        )

        elapsed_seconds = Decimal(
            str((last.timestamp - first.timestamp).total_seconds())
        )

        if price_return_pct is not None and elapsed_seconds > 0:
            price_velocity_pct_per_second = price_return_pct / elapsed_seconds
        else:
            price_velocity_pct_per_second = None

        volume_change_pct = self._change_pct(
            first.volume_usd,
            last.volume_usd,
        )

        transaction_change_pct = self._change_pct_int(
            first.transactions,
            last.transactions,
        )

        buy_sell_volume_ratio = self._ratio(
            last.buy_volume_usd,
            last.sell_volume_usd,
        )

        buy_sell_transaction_ratio = self._ratio_int(
            last.buys,
            last.sells,
        )

        liquidity_change_pct = self._change_pct(
            first.liquidity_usd,
            last.liquidity_usd,
        )

        market_cap_change_pct = self._change_pct(
            first.market_cap_usd,
            last.market_cap_usd,
        )

        return EventFeatureVector(
            token_mint=event.token_mint,
            window_seconds=self.window_seconds,
            sample_count=len(window),
            price_return_pct=price_return_pct,
            price_velocity_pct_per_second=price_velocity_pct_per_second,
            volume_change_pct=volume_change_pct,
            transaction_change_pct=transaction_change_pct,
            buy_sell_volume_ratio=buy_sell_volume_ratio,
            buy_sell_transaction_ratio=buy_sell_transaction_ratio,
            liquidity_change_pct=liquidity_change_pct,
            market_cap_change_pct=market_cap_change_pct,
        )

    @staticmethod
    def _change_pct(
        start: Decimal | None,
        end: Decimal | None,
    ) -> Decimal | None:
        if start is None or end is None or start == 0:
            return None

        return ((end / start) - Decimal("1")) * Decimal("100")

    @staticmethod
    def _change_pct_int(
        start: int | None,
        end: int | None,
    ) -> Decimal | None:
        if start is None or end is None or start == 0:
            return None

        return (
            (Decimal(end) / Decimal(start)) - Decimal("1")
        ) * Decimal("100")

    @staticmethod
    def _ratio(
        numerator: Decimal | None,
        denominator: Decimal | None,
    ) -> Decimal | None:
        if numerator is None or denominator is None or denominator == 0:
            return None

        return numerator / denominator

    @staticmethod
    def _ratio_int(
        numerator: int | None,
        denominator: int | None,
    ) -> Decimal | None:
        if numerator is None or denominator is None or denominator == 0:
            return None

        return Decimal(numerator) / Decimal(denominator)
