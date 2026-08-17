"""Behavioral matching across labeled historical event families."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from solana_flow_trader.features import EventFeatureVector
from solana_flow_trader.matching.feature_similarity import (
    FeatureSimilarity,
    FeatureSimilarityResult,
)


class BehaviorLabel(StrEnum):
    """Historical behavior family label."""

    BULL = "bull"
    BEAR = "bear"
    TRAP = "trap"


@dataclass(frozen=True, slots=True)
class LabeledFeatureVector:
    """Historical feature vector with behavior metadata."""

    event_id: str
    label: BehaviorLabel
    features: EventFeatureVector

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty")


@dataclass(frozen=True, slots=True)
class BehavioralMatch:
    """Similarity between current state and one historical event."""

    event_id: str
    label: BehaviorLabel
    score: Decimal
    compared_features: int
    skipped_features: int


@dataclass(frozen=True, slots=True)
class BehaviorFamilyResult:
    """Aggregated result for one behavior family."""

    label: BehaviorLabel
    score: Decimal
    match_count: int
    top_matches: tuple[BehavioralMatch, ...]


@dataclass(frozen=True, slots=True)
class BehavioralMatchResult:
    """Complete behavioral comparison for current conditions."""

    bull: BehaviorFamilyResult
    bear: BehaviorFamilyResult
    trap: BehaviorFamilyResult


class BehavioralMatcher:
    """Compare a live feature vector against labeled historical families."""

    def __init__(
        self,
        *,
        top_k: int = 3,
        similarity: FeatureSimilarity | None = None,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        self.top_k = top_k
        self.similarity = similarity or FeatureSimilarity()

    def match(
        self,
        current: EventFeatureVector,
        historical: list[LabeledFeatureVector],
    ) -> BehavioralMatchResult:
        matches = [self._compare_one(current, item) for item in historical]

        return BehavioralMatchResult(
            bull=self._aggregate_family(matches, BehaviorLabel.BULL),
            bear=self._aggregate_family(matches, BehaviorLabel.BEAR),
            trap=self._aggregate_family(matches, BehaviorLabel.TRAP),
        )

    def _compare_one(
        self,
        current: EventFeatureVector,
        historical: LabeledFeatureVector,
    ) -> BehavioralMatch:
        result: FeatureSimilarityResult = self.similarity.compare(
            current,
            historical.features,
        )

        return BehavioralMatch(
            event_id=historical.event_id,
            label=historical.label,
            score=result.score,
            compared_features=result.compared_features,
            skipped_features=result.skipped_features,
        )

    def _aggregate_family(
        self,
        matches: list[BehavioralMatch],
        label: BehaviorLabel,
    ) -> BehaviorFamilyResult:
        family_matches = [match for match in matches if match.label == label]

        if not family_matches:
            return BehaviorFamilyResult(
                label=label,
                score=Decimal("0"),
                match_count=0,
                top_matches=(),
            )

        ordered = sorted(
            family_matches,
            key=lambda match: match.score,
            reverse=True,
        )

        top_matches = tuple(ordered[: self.top_k])

        score = sum(
            (match.score for match in top_matches),
            Decimal("0"),
        ) / Decimal(len(top_matches))

        return BehaviorFamilyResult(
            label=label,
            score=score,
            match_count=len(family_matches),
            top_matches=top_matches,
        )
