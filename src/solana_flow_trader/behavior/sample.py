"""Behavioral sample models."""

from __future__ import annotations

from dataclasses import dataclass

from solana_flow_trader.features import EventFeatureVector
from solana_flow_trader.matching import BehaviorLabel
from solana_flow_trader.outcomes import EventOutcome


@dataclass(frozen=True, slots=True)
class BehaviorSample:
    """One historical behavioral sample with measured outcome."""

    event_id: str
    label: BehaviorLabel
    features: EventFeatureVector
    outcome: EventOutcome

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty")

        if self.event_id != self.outcome.event_id:
            raise ValueError(
                "event_id must match outcome.event_id"
            )
