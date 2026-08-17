"""Outcome models for historical market events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class EventOutcome:
    """Observed post-event performance for one historical event."""

    event_id: str

    return_5s_pct: Decimal | None
    return_15s_pct: Decimal | None
    return_30s_pct: Decimal | None
    return_60s_pct: Decimal | None

    mfe_pct: Decimal | None
    mae_pct: Decimal | None

    time_to_mfe_seconds: Decimal | None
    time_to_mae_seconds: Decimal | None

    observation_seconds: int
    sample_count: int

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty")

        if self.observation_seconds <= 0:
            raise ValueError("observation_seconds must be positive")

        if self.sample_count <= 0:
            raise ValueError("sample_count must be positive")
