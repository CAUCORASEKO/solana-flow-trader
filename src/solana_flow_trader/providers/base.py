"""Market-data provider contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from solana_flow_trader.models import MarketSnapshot

from .token_candidate import TokenCandidate


class MarketDataProvider(ABC):
    """Normalized interface implemented by external market-data providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a stable provider identifier."""

    @abstractmethod
    def discover_tokens(
        self,
        *,
        limit: int = 100,
    ) -> Sequence[TokenCandidate]:
        """Discover potentially interesting Solana tokens."""

    @abstractmethod
    def get_snapshot(
        self,
        token_mint: str,
    ) -> MarketSnapshot:
        """Return the latest normalized snapshot for one token."""

    def get_snapshots(
        self,
        token_mints: Sequence[str],
    ) -> list[MarketSnapshot]:
        """Return normalized snapshots for multiple tokens."""

        return [
            self.get_snapshot(token_mint)
            for token_mint in token_mints
        ]
