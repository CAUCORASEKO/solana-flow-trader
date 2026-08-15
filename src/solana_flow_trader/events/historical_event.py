"""Historical market event models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class EventDirection(StrEnum):
    """Direction of a historical price event."""

    BULL = "bull"
    BEAR = "bear"


@dataclass(frozen=True, slots=True)
class HistoricalEvent:
    """A representative historical directional price movement."""

    token_mint: str
    direction: EventDirection

    start_time: datetime
    end_time: datetime

    start_price: Decimal
    end_price: Decimal

    return_pct: Decimal
    duration_seconds: Decimal

    start_index: int
    end_index: int

    def __post_init__(self) -> None:
        if not self.token_mint.strip():
            raise ValueError("token_mint must not be empty")

        if self.start_time.tzinfo is None or self.start_time.utcoffset() is None:
            raise ValueError("start_time must be timezone-aware")

        if self.end_time.tzinfo is None or self.end_time.utcoffset() is None:
            raise ValueError("end_time must be timezone-aware")

        if self.end_time < self.start_time:
            raise ValueError("end_time must not be before start_time")

        if self.start_price <= 0:
            raise ValueError("start_price must be positive")

        if self.end_price <= 0:
            raise ValueError("end_price must be positive")

        if self.start_index < 0:
            raise ValueError("start_index must be non-negative")

        if self.end_index < self.start_index:
            raise ValueError("end_index must not be before start_index")
