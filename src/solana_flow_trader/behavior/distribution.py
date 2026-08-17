"""Outcome distribution summaries for behavioral samples."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from solana_flow_trader.behavior.sample import BehaviorSample
from solana_flow_trader.matching import BehaviorLabel


@dataclass(frozen=True, slots=True)
class OutcomeDistribution:
    """Distribution summary for one behavioral family."""

    label: BehaviorLabel
    sample_count: int

    mfe_p25_pct: Decimal | None
    mfe_p50_pct: Decimal | None
    mfe_p75_pct: Decimal | None

    mae_p25_pct: Decimal | None
    mae_p50_pct: Decimal | None
    mae_p75_pct: Decimal | None

    return_15s_p25_pct: Decimal | None
    return_15s_p50_pct: Decimal | None
    return_15s_p75_pct: Decimal | None

    return_30s_p25_pct: Decimal | None
    return_30s_p50_pct: Decimal | None
    return_30s_p75_pct: Decimal | None

    return_60s_p25_pct: Decimal | None
    return_60s_p50_pct: Decimal | None
    return_60s_p75_pct: Decimal | None

    positive_15s_rate: Decimal | None
    positive_30s_rate: Decimal | None
    positive_60s_rate: Decimal | None


class OutcomeDistributionCalculator:
    """Calculate percentiles and positive-outcome rates."""

    def calculate(
        self,
        samples: tuple[BehaviorSample, ...],
        *,
        label: BehaviorLabel,
    ) -> OutcomeDistribution:
        family = tuple(
            sample for sample in samples if sample.label == label
        )

        mfe = self._present(
            sample.outcome.mfe_pct for sample in family
        )
        mae = self._present(
            sample.outcome.mae_pct for sample in family
        )
        return_15s = self._present(
            sample.outcome.return_15s_pct for sample in family
        )
        return_30s = self._present(
            sample.outcome.return_30s_pct for sample in family
        )
        return_60s = self._present(
            sample.outcome.return_60s_pct for sample in family
        )

        return OutcomeDistribution(
            label=label,
            sample_count=len(family),
            mfe_p25_pct=self._percentile(mfe, Decimal("0.25")),
            mfe_p50_pct=self._percentile(mfe, Decimal("0.50")),
            mfe_p75_pct=self._percentile(mfe, Decimal("0.75")),
            mae_p25_pct=self._percentile(mae, Decimal("0.25")),
            mae_p50_pct=self._percentile(mae, Decimal("0.50")),
            mae_p75_pct=self._percentile(mae, Decimal("0.75")),
            return_15s_p25_pct=self._percentile(
                return_15s,
                Decimal("0.25"),
            ),
            return_15s_p50_pct=self._percentile(
                return_15s,
                Decimal("0.50"),
            ),
            return_15s_p75_pct=self._percentile(
                return_15s,
                Decimal("0.75"),
            ),
            return_30s_p25_pct=self._percentile(
                return_30s,
                Decimal("0.25"),
            ),
            return_30s_p50_pct=self._percentile(
                return_30s,
                Decimal("0.50"),
            ),
            return_30s_p75_pct=self._percentile(
                return_30s,
                Decimal("0.75"),
            ),
            return_60s_p25_pct=self._percentile(
                return_60s,
                Decimal("0.25"),
            ),
            return_60s_p50_pct=self._percentile(
                return_60s,
                Decimal("0.50"),
            ),
            return_60s_p75_pct=self._percentile(
                return_60s,
                Decimal("0.75"),
            ),
            positive_15s_rate=self._positive_rate(return_15s),
            positive_30s_rate=self._positive_rate(return_30s),
            positive_60s_rate=self._positive_rate(return_60s),
        )

    @staticmethod
    def _present(
        values,
    ) -> list[Decimal]:
        return sorted(
            value
            for value in values
            if value is not None
        )

    @staticmethod
    def _percentile(
        values: list[Decimal],
        percentile: Decimal,
    ) -> Decimal | None:
        if not values:
            return None

        if len(values) == 1:
            return values[0]

        position = percentile * Decimal(len(values) - 1)

        lower_index = int(position)
        upper_index = min(lower_index + 1, len(values) - 1)

        lower_value = values[lower_index]
        upper_value = values[upper_index]

        fraction = position - Decimal(lower_index)

        return lower_value + (
            upper_value - lower_value
        ) * fraction

    @staticmethod
    def _positive_rate(
        values: list[Decimal],
    ) -> Decimal | None:
        if not values:
            return None

        positive = sum(value > 0 for value in values)

        return Decimal(positive) / Decimal(len(values))
