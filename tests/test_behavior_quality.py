from decimal import Decimal

from solana_flow_trader.behavior import (
    BehaviorQualityProfiler,
    OutcomeDistribution,
    QualityLevel,
)
from solana_flow_trader.matching import BehaviorLabel


def make_distribution(
    *,
    sample_count: int = 40,
    continuation_rate: str | None = "0.80",
    median_mfe: str | None = "35",
    median_mae: str | None = "-6",
    return_30s_p25: str | None = "15",
    return_30s_p50: str | None = "25",
    return_30s_p75: str | None = "30",
) -> OutcomeDistribution:
    def decimal_or_none(value: str | None) -> Decimal | None:
        return None if value is None else Decimal(value)

    return OutcomeDistribution(
        label=BehaviorLabel.BULL,
        sample_count=sample_count,
        mfe_p25_pct=None,
        mfe_p50_pct=decimal_or_none(median_mfe),
        mfe_p75_pct=None,
        mae_p25_pct=None,
        mae_p50_pct=decimal_or_none(median_mae),
        mae_p75_pct=None,
        return_15s_p25_pct=None,
        return_15s_p50_pct=None,
        return_15s_p75_pct=None,
        return_30s_p25_pct=decimal_or_none(return_30s_p25),
        return_30s_p50_pct=decimal_or_none(return_30s_p50),
        return_30s_p75_pct=decimal_or_none(return_30s_p75),
        return_60s_p25_pct=None,
        return_60s_p50_pct=None,
        return_60s_p75_pct=None,
        positive_15s_rate=None,
        positive_30s_rate=decimal_or_none(continuation_rate),
        positive_60s_rate=None,
    )


def test_profiles_high_quality_family() -> None:
    profile = BehaviorQualityProfiler().profile(
        make_distribution()
    )

    assert profile.continuation_quality == QualityLevel.HIGH
    assert profile.upside_quality == QualityLevel.HIGH
    assert profile.adverse_excursion_quality == QualityLevel.MODERATE
    assert profile.consistency_quality == QualityLevel.HIGH
    assert profile.evidence_quality == QualityLevel.HIGH


def test_profiles_moderate_family() -> None:
    profile = BehaviorQualityProfiler().profile(
        make_distribution(
            sample_count=15,
            continuation_rate="0.60",
            median_mfe="20",
            median_mae="-10",
            return_30s_p25="5",
            return_30s_p50="15",
            return_30s_p75="25",
        )
    )

    assert profile.continuation_quality == QualityLevel.MODERATE
    assert profile.upside_quality == QualityLevel.MODERATE
    assert profile.adverse_excursion_quality == QualityLevel.MODERATE
    assert profile.consistency_quality == QualityLevel.MODERATE
    assert profile.evidence_quality == QualityLevel.MODERATE


def test_profiles_low_quality_family() -> None:
    profile = BehaviorQualityProfiler().profile(
        make_distribution(
            sample_count=4,
            continuation_rate="0.40",
            median_mfe="8",
            median_mae="-20",
            return_30s_p25="-20",
            return_30s_p50="2",
            return_30s_p75="25",
        )
    )

    assert profile.continuation_quality == QualityLevel.LOW
    assert profile.upside_quality == QualityLevel.LOW
    assert profile.adverse_excursion_quality == QualityLevel.LOW
    assert profile.consistency_quality == QualityLevel.LOW
    assert profile.evidence_quality == QualityLevel.LOW


def test_missing_distribution_values_produce_unknown_quality() -> None:
    profile = BehaviorQualityProfiler().profile(
        make_distribution(
            sample_count=0,
            continuation_rate=None,
            median_mfe=None,
            median_mae=None,
            return_30s_p25=None,
            return_30s_p50=None,
            return_30s_p75=None,
        )
    )

    assert profile.continuation_quality == QualityLevel.UNKNOWN
    assert profile.upside_quality == QualityLevel.UNKNOWN
    assert profile.adverse_excursion_quality == QualityLevel.UNKNOWN
    assert profile.consistency_quality == QualityLevel.UNKNOWN
    assert profile.evidence_quality == QualityLevel.UNKNOWN
