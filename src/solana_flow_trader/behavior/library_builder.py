"""Build behavioral libraries from historical market snapshots."""

from __future__ import annotations

from dataclasses import dataclass

from solana_flow_trader.events import EventDirection, HistoricalEventMiner
from solana_flow_trader.features import PreEventFeatureExtractor
from solana_flow_trader.matching import BehaviorLabel, LabeledFeatureVector
from solana_flow_trader.models import MarketSnapshot


@dataclass(frozen=True, slots=True)
class BehavioralLibrary:
    """Historical behavior samples for one token."""

    token_mint: str
    samples: tuple[LabeledFeatureVector, ...]

    def __post_init__(self) -> None:
        if not self.token_mint.strip():
            raise ValueError("token_mint must not be empty")

    @property
    def bull_count(self) -> int:
        return sum(
            sample.label == BehaviorLabel.BULL
            for sample in self.samples
        )

    @property
    def bear_count(self) -> int:
        return sum(
            sample.label == BehaviorLabel.BEAR
            for sample in self.samples
        )

    @property
    def trap_count(self) -> int:
        return sum(
            sample.label == BehaviorLabel.TRAP
            for sample in self.samples
        )


class BehavioralLibraryBuilder:
    """Create labeled behavioral samples from historical snapshots."""

    def __init__(
        self,
        *,
        event_miner: HistoricalEventMiner,
        feature_extractor: PreEventFeatureExtractor,
    ) -> None:
        self.event_miner = event_miner
        self.feature_extractor = feature_extractor

    def build(
        self,
        snapshots: list[MarketSnapshot],
    ) -> BehavioralLibrary | None:
        if not snapshots:
            return None

        ordered = sorted(
            snapshots,
            key=lambda snapshot: snapshot.timestamp,
        )

        token_mints = {
            snapshot.token_mint
            for snapshot in ordered
        }

        if len(token_mints) != 1:
            raise ValueError(
                "all snapshots must belong to the same token"
            )

        token_mint = ordered[0].token_mint

        events = self.event_miner.mine(ordered)

        samples: list[LabeledFeatureVector] = []

        for index, event in enumerate(events):
            features = self.feature_extractor.extract(
                event,
                ordered,
            )

            if features is None:
                continue

            label = self._label_for_direction(
                event.direction,
            )

            samples.append(
                LabeledFeatureVector(
                    event_id=f"{token_mint}:{index}",
                    label=label,
                    features=features,
                )
            )

        return BehavioralLibrary(
            token_mint=token_mint,
            samples=tuple(samples),
        )

    @staticmethod
    def _label_for_direction(
        direction: EventDirection,
    ) -> BehaviorLabel:
        if direction == EventDirection.BULL:
            return BehaviorLabel.BULL

        return BehaviorLabel.BEAR
