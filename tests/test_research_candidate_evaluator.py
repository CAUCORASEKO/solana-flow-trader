from decimal import Decimal

import pytest

from solana_flow_trader.behavior import (
    BehaviorQualityProfile,
    QualityLevel,
)
from solana_flow_trader.matching import (
    BehavioralMatchResult,
    BehaviorFamilyResult,
    BehaviorLabel,
)
from solana_flow_trader.research import (
    CandidateDirection,
    CandidateStatus,
    ResearchCandidateEvaluator,
)


def family(
    label: BehaviorLabel,
    score: str,
) -> BehaviorFamilyResult:
    return BehaviorFamilyResult(
        label=label,
        score=Decimal(score),
        match_count=10,
        top_matches=(),
    )


def match_result(
    *,
    bull: str,
    bear: str,
    trap: str,
) -> BehavioralMatchResult:
    return BehavioralMatchResult(
        bull=family(BehaviorLabel.BULL, bull),
        bear=family(BehaviorLabel.BEAR, bear),
        trap=family(BehaviorLabel.TRAP, trap),
    )


def quality(
    label: BehaviorLabel,
    *,
    continuation: QualityLevel = QualityLevel.HIGH,
    upside: QualityLevel = QualityLevel.HIGH,
    adverse: QualityLevel = QualityLevel.MODERATE,
    consistency: QualityLevel = QualityLevel.HIGH,
    evidence: QualityLevel = QualityLevel.HIGH,
) -> BehaviorQualityProfile:
    return BehaviorQualityProfile(
        label=label,
        sample_count=40,
        continuation_rate=Decimal("0.80"),
        median_mfe_pct=Decimal("35"),
        median_mae_pct=Decimal("-6"),
        continuation_quality=continuation,
        upside_quality=upside,
        adverse_excursion_quality=adverse,
        consistency_quality=consistency,
        evidence_quality=evidence,
    )


def test_selects_strong_bull_research_candidate() -> None:
    result = ResearchCandidateEvaluator().evaluate(
        match_result(
            bull="0.91",
            bear="0.20",
            trap="0.15",
        ),
        bull_quality=quality(BehaviorLabel.BULL),
        bear_quality=quality(BehaviorLabel.BEAR),
    )

    assert result.direction == CandidateDirection.BULL
    assert result.status == CandidateStatus.RESEARCH_CANDIDATE
    assert result.directional_similarity == Decimal("0.91")


def test_selects_strong_bear_research_candidate() -> None:
    result = ResearchCandidateEvaluator().evaluate(
        match_result(
            bull="0.18",
            bear="0.88",
            trap="0.12",
        ),
        bull_quality=quality(BehaviorLabel.BULL),
        bear_quality=quality(BehaviorLabel.BEAR),
    )

    assert result.direction == CandidateDirection.BEAR
    assert result.status == CandidateStatus.RESEARCH_CANDIDATE


def test_high_trap_similarity_rejects_candidate() -> None:
    result = ResearchCandidateEvaluator().evaluate(
        match_result(
            bull="0.92",
            bear="0.15",
            trap="0.70",
        ),
        bull_quality=quality(BehaviorLabel.BULL),
        bear_quality=quality(BehaviorLabel.BEAR),
    )

    assert result.status == CandidateStatus.REJECT
    assert "trap" in result.reason


def test_small_directional_margin_rejects_candidate() -> None:
    result = ResearchCandidateEvaluator().evaluate(
        match_result(
            bull="0.82",
            bear="0.77",
            trap="0.10",
        ),
        bull_quality=quality(BehaviorLabel.BULL),
        bear_quality=quality(BehaviorLabel.BEAR),
    )

    assert result.status == CandidateStatus.REJECT
    assert "margin" in result.reason


def test_intermediate_similarity_returns_watch() -> None:
    result = ResearchCandidateEvaluator().evaluate(
        match_result(
            bull="0.72",
            bear="0.20",
            trap="0.10",
        ),
        bull_quality=quality(BehaviorLabel.BULL),
        bear_quality=quality(BehaviorLabel.BEAR),
    )

    assert result.direction == CandidateDirection.BULL
    assert result.status == CandidateStatus.WATCH


def test_low_evidence_returns_watch() -> None:
    result = ResearchCandidateEvaluator().evaluate(
        match_result(
            bull="0.90",
            bear="0.15",
            trap="0.10",
        ),
        bull_quality=quality(
            BehaviorLabel.BULL,
            evidence=QualityLevel.LOW,
        ),
        bear_quality=quality(BehaviorLabel.BEAR),
    )

    assert result.status == CandidateStatus.WATCH
    assert "evidence" in result.reason


def test_low_continuation_quality_returns_watch() -> None:
    result = ResearchCandidateEvaluator().evaluate(
        match_result(
            bull="0.90",
            bear="0.15",
            trap="0.10",
        ),
        bull_quality=quality(
            BehaviorLabel.BULL,
            continuation=QualityLevel.LOW,
        ),
        bear_quality=quality(BehaviorLabel.BEAR),
    )

    assert result.status == CandidateStatus.WATCH
    assert "continuation" in result.reason


def test_equal_direction_scores_are_rejected() -> None:
    result = ResearchCandidateEvaluator().evaluate(
        match_result(
            bull="0.80",
            bear="0.80",
            trap="0.10",
        ),
        bull_quality=quality(BehaviorLabel.BULL),
        bear_quality=quality(BehaviorLabel.BEAR),
    )

    assert result.direction == CandidateDirection.NONE
    assert result.status == CandidateStatus.REJECT


def test_rejects_invalid_similarity_configuration() -> None:
    with pytest.raises(ValueError):
        ResearchCandidateEvaluator(
            watch_similarity=Decimal("0.90"),
            candidate_similarity=Decimal("0.80"),
        )
