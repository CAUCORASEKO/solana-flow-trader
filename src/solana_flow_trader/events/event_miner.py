"""Historical directional event detection."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from solana_flow_trader.events.historical_event import (
    EventDirection,
    HistoricalEvent,
)
from solana_flow_trader.models import MarketSnapshot


class HistoricalEventMiner:
    """Detect representative bullish and bearish movements."""

    def __init__(
        self,
        *,
        threshold_pct: Decimal,
        max_window_seconds: int,
    ) -> None:
        if threshold_pct <= 0:
            raise ValueError("threshold_pct must be positive")

        if max_window_seconds <= 0:
            raise ValueError("max_window_seconds must be positive")

        self.threshold_pct = threshold_pct
        self.max_window_seconds = max_window_seconds

    def mine(self, snapshots: list[MarketSnapshot]) -> list[HistoricalEvent]:
        if len(snapshots) < 2:
            return []

        ordered = sorted(snapshots, key=lambda snapshot: snapshot.timestamp)

        token_mints = {snapshot.token_mint for snapshot in ordered}
        if len(token_mints) != 1:
            raise ValueError("all snapshots must belong to the same token")

        events: list[HistoricalEvent] = []
        start_index = 0

        while start_index < len(ordered) - 1:
            event = self._find_event_from_start(ordered, start_index)

            if event is None:
                start_index += 1
                continue

            events.append(event)

            # Avoid emitting all overlapping sub-movements
            # of the same representative impulse.
            start_index = event.end_index + 1

        return events

    def _find_event_from_start(
        self,
        snapshots: list[MarketSnapshot],
        start_index: int,
    ) -> HistoricalEvent | None:
        start = snapshots[start_index]

        if start.price_usd is None or start.price_usd <= 0:
            return None

        deadline = start.timestamp + timedelta(seconds=self.max_window_seconds)

        for index in range(start_index + 1, len(snapshots)):
            current = snapshots[index]

            if current.timestamp > deadline:
                break

            if current.price_usd is None:
                continue

            return_pct = self._return_pct(
                start.price_usd,
                current.price_usd,
            )

            if return_pct >= self.threshold_pct:
                end_index = self._extend_bull_event(
                    snapshots,
                    index,
                    deadline,
                )
                return self._build_event(
                    snapshots,
                    start_index,
                    end_index,
                    EventDirection.BULL,
                )

            if return_pct <= -self.threshold_pct:
                end_index = self._extend_bear_event(
                    snapshots,
                    index,
                    deadline,
                )
                return self._build_event(
                    snapshots,
                    start_index,
                    end_index,
                    EventDirection.BEAR,
                )

        return None

    @staticmethod
    def _extend_bull_event(
        snapshots: list[MarketSnapshot],
        trigger_index: int,
        deadline: datetime,
    ) -> int:
        best_index = trigger_index
        best_price = snapshots[trigger_index].price_usd

        if best_price is None:
            return trigger_index

        for index in range(trigger_index + 1, len(snapshots)):
            current = snapshots[index]

            if current.timestamp > deadline:
                break

            if current.price_usd is None:
                continue

            if current.price_usd > best_price:
                best_price = current.price_usd
                best_index = index

        return best_index

    @staticmethod
    def _extend_bear_event(
        snapshots: list[MarketSnapshot],
        trigger_index: int,
        deadline: datetime,
    ) -> int:
        best_index = trigger_index
        best_price = snapshots[trigger_index].price_usd

        if best_price is None:
            return trigger_index

        for index in range(trigger_index + 1, len(snapshots)):
            current = snapshots[index]

            if current.timestamp > deadline:
                break

            if current.price_usd is None:
                continue

            if current.price_usd < best_price:
                best_price = current.price_usd
                best_index = index

        return best_index

    def _build_event(
        self,
        snapshots: list[MarketSnapshot],
        start_index: int,
        end_index: int,
        direction: EventDirection,
    ) -> HistoricalEvent:
        start = snapshots[start_index]
        end = snapshots[end_index]

        if start.price_usd is None or end.price_usd is None:
            raise ValueError("event endpoints must contain prices")

        return_pct = self._return_pct(
            start.price_usd,
            end.price_usd,
        )

        duration_seconds = Decimal(
            str((end.timestamp - start.timestamp).total_seconds())
        )

        return HistoricalEvent(
            token_mint=start.token_mint,
            direction=direction,
            start_time=start.timestamp,
            end_time=end.timestamp,
            start_price=start.price_usd,
            end_price=end.price_usd,
            return_pct=return_pct,
            duration_seconds=duration_seconds,
            start_index=start_index,
            end_index=end_index,
        )

    @staticmethod
    def _return_pct(
        start_price: Decimal,
        end_price: Decimal,
    ) -> Decimal:
        return ((end_price / start_price) - Decimal("1")) * Decimal("100")
