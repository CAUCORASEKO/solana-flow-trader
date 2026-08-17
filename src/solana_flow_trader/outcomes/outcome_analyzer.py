"""Post-event market outcome analysis."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from solana_flow_trader.events import HistoricalEvent
from solana_flow_trader.models import MarketSnapshot
from solana_flow_trader.outcomes.event_outcome import EventOutcome


class OutcomeAnalyzer:
    """Measure what happened after a historical event start."""

    HORIZONS = (5, 15, 30, 60)

    def __init__(self, *, observation_seconds: int = 60) -> None:
        if observation_seconds <= 0:
            raise ValueError("observation_seconds must be positive")

        self.observation_seconds = observation_seconds

    def analyze(
        self,
        event_id: str,
        event: HistoricalEvent,
        snapshots: list[MarketSnapshot],
    ) -> EventOutcome | None:
        if not event_id.strip():
            raise ValueError("event_id must not be empty")

        if not snapshots:
            return None

        token_snapshots = [
            snapshot
            for snapshot in snapshots
            if snapshot.token_mint == event.token_mint
            and snapshot.price_usd is not None
        ]

        if not token_snapshots:
            return None

        observation_end = event.start_time + timedelta(
            seconds=self.observation_seconds
        )

        window = sorted(
            [
                snapshot
                for snapshot in token_snapshots
                if event.start_time <= snapshot.timestamp <= observation_end
            ],
            key=lambda snapshot: snapshot.timestamp,
        )

        if not window:
            return None

        entry_price = event.start_price

        horizon_returns = {
            horizon: self._return_at_horizon(
                window,
                event.start_time,
                entry_price,
                horizon,
            )
            for horizon in self.HORIZONS
        }

        mfe_pct: Decimal | None = None
        mae_pct: Decimal | None = None
        time_to_mfe_seconds: Decimal | None = None
        time_to_mae_seconds: Decimal | None = None

        for snapshot in window:
            if snapshot.price_usd is None:
                continue

            return_pct = self._return_pct(
                entry_price,
                snapshot.price_usd,
            )

            elapsed = Decimal(
                str(
                    (
                        snapshot.timestamp - event.start_time
                    ).total_seconds()
                )
            )

            if mfe_pct is None or return_pct > mfe_pct:
                mfe_pct = return_pct
                time_to_mfe_seconds = elapsed

            if mae_pct is None or return_pct < mae_pct:
                mae_pct = return_pct
                time_to_mae_seconds = elapsed

        return EventOutcome(
            event_id=event_id,
            return_5s_pct=horizon_returns[5],
            return_15s_pct=horizon_returns[15],
            return_30s_pct=horizon_returns[30],
            return_60s_pct=horizon_returns[60],
            mfe_pct=mfe_pct,
            mae_pct=mae_pct,
            time_to_mfe_seconds=time_to_mfe_seconds,
            time_to_mae_seconds=time_to_mae_seconds,
            observation_seconds=self.observation_seconds,
            sample_count=len(window),
        )

    @staticmethod
    def _return_at_horizon(
        snapshots: list[MarketSnapshot],
        start_time,
        entry_price: Decimal,
        horizon_seconds: int,
    ) -> Decimal | None:
        target_time = start_time + timedelta(seconds=horizon_seconds)

        candidates = [
            snapshot
            for snapshot in snapshots
            if snapshot.timestamp <= target_time
            and snapshot.price_usd is not None
        ]

        if not candidates:
            return None

        snapshot = candidates[-1]

        return OutcomeAnalyzer._return_pct(
            entry_price,
            snapshot.price_usd,
        )

    @staticmethod
    def _return_pct(
        start_price: Decimal,
        end_price: Decimal,
    ) -> Decimal:
        return ((end_price / start_price) - Decimal("1")) * Decimal("100")
