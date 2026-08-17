"""Research candidate evaluation from behavioral evidence."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from solana_flow_trader.behavior import (
    BehaviorQualityProfile,
    QualityLevel,
)
from solana_flow_trader.matching import BehavioralMatchResult


class CandidateDirection(StrEnum):
    """Directional research hypothesis."""

    NONE = "none"
    BULL = "bull"
    BEAR = "bear"


class CandidateStatus(StrEnum):
    """Research-stage candidate status."""

    REJECT = "reject"
    WATCH = "watch"
    RESEARCH_CANDIDATE = "research_candidate"


@dataclass(frozen=True, slots=True)
class ResearchCandidate:
    """Auditable research decision for one live market state."""

    direction: CandidateDirection
    status: CandidateStatus

    directional_similarity: Decimal
    opposing_similarity: Decimal
    trap_similarity: Decimal

    continuation_quality: QualityLevel
    upside_quality: QualityLevel
    adverse_excursion_quality: QualityLevel
    consistency_quality: QualityLevel
    evidence_quality: QualityLevel

    reason: str


class ResearchCandidateEvaluator:
    """Combine historical similarity and quality into research status."""

    def __init__(
        self,
        *,
        candidate_similarity: Decimal = Decimal("0.80"),
        watch_similarity: Decimal = Decimal("0.65"),
        max_trap_similarity: Decimal = Decimal("0.55"),
        min_similarity_margin: Decimal = Decimal("0.10"),
    ) -> None:
        if not Decimal("0") <= watch_similarity <= Decimal("1"):
            raise ValueError("watch_similarity must be between 0 and 1")

        if not Decimal("0") <= candidate_similarity <= Decimal("1"):
            raise ValueError("candidate_similarity must be between 0 and 1")

        if candidate_similarity < watch_similarity:
            raise ValueError(
                "candidate_similarity must be >= watch_similarity"
            )

        if not Decimal("0") <= max_trap_similarity <= Decimal("1"):
            raise ValueError("max_trap_similarity must be between 0 and 1")

        if min_similarity_margin < 0:
            raise ValueError("min_similarity_margin must be non-negative")

        self.candidate_similarity = candidate_similarity
        self.watch_similarity = watch_similarity
        self.max_trap_similarity = max_trap_similarity
        self.min_similarity_margin = min_similarity_margin

    def evaluate(
        self,
        match_result: BehavioralMatchResult,
        *,
        bull_quality: BehaviorQualityProfile,
        bear_quality: BehaviorQualityProfile,
    ) -> ResearchCandidate:
        bull_score = match_result.bull.score
        bear_score = match_result.bear.score
        trap_score = match_result.trap.score

        if bull_score > bear_score:
            direction = CandidateDirection.BULL
            directional_score = bull_score
            opposing_score = bear_score
            quality = bull_quality
        elif bear_score > bull_score:
            direction = CandidateDirection.BEAR
            directional_score = bear_score
            opposing_score = bull_score
            quality = bear_quality
        else:
            return ResearchCandidate(
                direction=CandidateDirection.NONE,
                status=CandidateStatus.REJECT,
                directional_similarity=bull_score,
                opposing_similarity=bear_score,
                trap_similarity=trap_score,
                continuation_quality=QualityLevel.UNKNOWN,
                upside_quality=QualityLevel.UNKNOWN,
                adverse_excursion_quality=QualityLevel.UNKNOWN,
                consistency_quality=QualityLevel.UNKNOWN,
                evidence_quality=QualityLevel.UNKNOWN,
                reason="bull and bear similarity are tied",
            )

        margin = directional_score - opposing_score

        if trap_score > self.max_trap_similarity:
            status = CandidateStatus.REJECT
            reason = "trap similarity exceeds allowed maximum"

        elif margin < self.min_similarity_margin:
            status = CandidateStatus.REJECT
            reason = "directional similarity margin is too small"

        elif directional_score < self.watch_similarity:
            status = CandidateStatus.REJECT
            reason = "directional similarity is below watch threshold"

        elif directional_score < self.candidate_similarity:
            status = CandidateStatus.WATCH
            reason = "direction is interesting but similarity is not yet strong enough"

        elif quality.evidence_quality in {
            QualityLevel.UNKNOWN,
            QualityLevel.LOW,
        }:
            status = CandidateStatus.WATCH
            reason = "historical evidence depth is insufficient"

        elif quality.continuation_quality == QualityLevel.LOW:
            status = CandidateStatus.WATCH
            reason = "historical continuation quality is weak"

        else:
            status = CandidateStatus.RESEARCH_CANDIDATE
            reason = "similarity and historical quality support research selection"

        return ResearchCandidate(
            direction=direction,
            status=status,
            directional_similarity=directional_score,
            opposing_similarity=opposing_score,
            trap_similarity=trap_score,
            continuation_quality=quality.continuation_quality,
            upside_quality=quality.upside_quality,
            adverse_excursion_quality=quality.adverse_excursion_quality,
            consistency_quality=quality.consistency_quality,
            evidence_quality=quality.evidence_quality,
            reason=reason,
        )
