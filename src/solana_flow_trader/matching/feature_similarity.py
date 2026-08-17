"""Similarity scoring for event feature vectors."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from solana_flow_trader.features import EventFeatureVector


@dataclass(frozen=True, slots=True)
class FeatureSimilarityResult:
    """Similarity result between two event feature vectors."""

    score: Decimal
    compared_features: int
    skipped_features: int


class FeatureSimilarity:
    """Compare observable feature vectors using normalized relative distance."""

    FEATURE_NAMES = (
        "price_return_pct",
        "price_velocity_pct_per_second",
        "volume_change_pct",
        "transaction_change_pct",
        "buy_sell_volume_ratio",
        "buy_sell_transaction_ratio",
        "liquidity_change_pct",
        "market_cap_change_pct",
    )

    def compare(
        self,
        current: EventFeatureVector,
        historical: EventFeatureVector,
    ) -> FeatureSimilarityResult:
        similarities: list[Decimal] = []
        skipped = 0

        for feature_name in self.FEATURE_NAMES:
            current_value = getattr(current, feature_name)
            historical_value = getattr(historical, feature_name)

            if current_value is None or historical_value is None:
                skipped += 1
                continue

            similarities.append(
                self._value_similarity(
                    current_value,
                    historical_value,
                )
            )

        if not similarities:
            return FeatureSimilarityResult(
                score=Decimal("0"),
                compared_features=0,
                skipped_features=skipped,
            )

        score = sum(similarities, Decimal("0")) / Decimal(len(similarities))

        return FeatureSimilarityResult(
            score=score,
            compared_features=len(similarities),
            skipped_features=skipped,
        )

    @staticmethod
    def _value_similarity(
        current: Decimal,
        historical: Decimal,
    ) -> Decimal:
        scale = max(
            abs(current),
            abs(historical),
            Decimal("1"),
        )

        relative_distance = abs(current - historical) / scale

        similarity = Decimal("1") - relative_distance

        if similarity < 0:
            return Decimal("0")

        if similarity > 1:
            return Decimal("1")

        return similarity
