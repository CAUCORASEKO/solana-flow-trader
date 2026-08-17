"""Historical quality profiles for behavioral families."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from solana_flow_trader.behavior.distribution import OutcomeDistribution
from solana_flow_trader.matching import BehaviorLabel


class QualityLevel(StrEnum):
    """Qualitative research classification."""

    UNKNOWN = "unknown"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class BehaviorQualityProfile:
    """Auditable historical quality summary for one behavior family."""

    label: BehaviorLabel
    sample_count: int

    continuation_rate: Decimal | None
    median_mfe_pct: Decimal | None
    median_mae_pct: Decimal | None

    continuation_quality: QualityLevel
    upside_quality: QualityLevel
    adverse_excursion_quality: QualityLevel
    consistency_quality: QualityLevel
    evidence_quality: QualityLevel


class BehaviorQualityProfiler:
    """Build qualitative profiles from measured outcome distributions."""

    def profile(
        self,
        distribution: OutcomeDistribution,
    ) -> BehaviorQualityProfile:
        continuation_rate = distribution.positive_30s_rate

        return BehaviorQualityProfile(
            label=distribution.label,
            sample_count=distribution.sample_count,
            continuation_rate=continuation_rate,
            median_mfe_pct=distribution.mfe_p50_pct,
            median_mae_pct=distribution.mae_p50_pct,
            continuation_quality=self._continuation_quality(
                continuation_rate
            ),
            upside_quality=self._upside_quality(
                distribution.mfe_p50_pct
            ),
            adverse_excursion_quality=self._adverse_quality(
                distribution.mae_p50_pct
            ),
            consistency_quality=self._consistency_quality(
                distribution
            ),
            evidence_quality=self._evidence_quality(
                distribution.sample_count
            ),
        )

    @staticmethod
    def _continuation_quality(
        rate: Decimal | None,
    ) -> QualityLevel:
        if rate is None:
            return QualityLevel.UNKNOWN

        if rate >= Decimal("0.75"):
            return QualityLevel.HIGH

        if rate >= Decimal("0.55"):
            return QualityLevel.MODERATE

        return QualityLevel.LOW

    @staticmethod
    def _upside_quality(
        median_mfe: Decimal | None,
    ) -> QualityLevel:
        if median_mfe is None:
            return QualityLevel.UNKNOWN

        if median_mfe >= Decimal("30"):
            return QualityLevel.HIGH

        if median_mfe >= Decimal("15"):
            return QualityLevel.MODERATE

        return QualityLevel.LOW

    @staticmethod
    def _adverse_quality(
        median_mae: Decimal | None,
    ) -> QualityLevel:
        if median_mae is None:
            return QualityLevel.UNKNOWN

        absolute_mae = abs(median_mae)

        if absolute_mae <= Decimal("5"):
            return QualityLevel.HIGH

        if absolute_mae <= Decimal("12"):
            return QualityLevel.MODERATE

        return QualityLevel.LOW

    @staticmethod
    def _consistency_quality(
        distribution: OutcomeDistribution,
    ) -> QualityLevel:
        p25 = distribution.return_30s_p25_pct
        p75 = distribution.return_30s_p75_pct

        if p25 is None or p75 is None:
            return QualityLevel.UNKNOWN

        spread = abs(p75 - p25)

        if spread <= Decimal("15"):
            return QualityLevel.HIGH

        if spread <= Decimal("30"):
            return QualityLevel.MODERATE

        return QualityLevel.LOW

    @staticmethod
    def _evidence_quality(
        sample_count: int,
    ) -> QualityLevel:
        if sample_count <= 0:
            return QualityLevel.UNKNOWN

        if sample_count >= 30:
            return QualityLevel.HIGH

        if sample_count >= 10:
            return QualityLevel.MODERATE

        return QualityLevel.LOW
