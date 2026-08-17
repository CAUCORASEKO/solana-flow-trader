"""Statistical summaries for behavioral samples."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median

from solana_flow_trader.behavior.sample import BehaviorSample
from solana_flow_trader.matching import BehaviorLabel


@dataclass(frozen=True, slots=True)
class BehaviorStatistics:
    """Summary statistics for one behavioral family."""

    label: BehaviorLabel
    sample_count: int

    median_return_5s_pct: Decimal | None
    median_return_15s_pct: Decimal | None
    median_return_30s_pct: Decimal | None
    median_return_60s_pct: Decimal | None

    median_mfe_pct: Decimal | None
    median_mae_pct: Decimal | None

    median_time_to_mfe_seconds: Decimal | None
    median_time_to_mae_seconds: Decimal | None


class BehaviorStatisticsCalculator:
    """Calculate outcome statistics for behavioral samples."""

    def calculate(
        self,
        samples: tuple[BehaviorSample, ...],
        *,
        label: BehaviorLabel,
    ) -> BehaviorStatistics:
        family = tuple(
            sample for sample in samples if sample.label == label
        )

        return BehaviorStatistics(
            label=label,
            sample_count=len(family),
            median_return_5s_pct=self._median_optional(
                sample.outcome.return_5s_pct
                for sample in family
            ),
            median_return_15s_pct=self._median_optional(
                sample.outcome.return_15s_pct
                for sample in family
            ),
            median_return_30s_pct=self._median_optional(
                sample.outcome.return_30s_pct
                for sample in family
            ),
            median_return_60s_pct=self._median_optional(
                sample.outcome.return_60s_pct
                for sample in family
            ),
            median_mfe_pct=self._median_optional(
                sample.outcome.mfe_pct
                for sample in family
            ),
            median_mae_pct=self._median_optional(
                sample.outcome.mae_pct
                for sample in family
            ),
            median_time_to_mfe_seconds=self._median_optional(
                sample.outcome.time_to_mfe_seconds
                for sample in family
            ),
            median_time_to_mae_seconds=self._median_optional(
                sample.outcome.time_to_mae_seconds
                for sample in family
            ),
        )

    @staticmethod
    def _median_optional(
        values,
    ) -> Decimal | None:
        present = [
            value
            for value in values
            if value is not None
        ]

        if not present:
            return None

        return Decimal(str(median(present)))
