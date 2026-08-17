"""Birdeye implementation of the normalized market-data provider contract."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from solana_flow_trader.models import MarketSnapshot
from solana_flow_trader.providers import (
    MarketDataProvider,
    TokenCandidate,
)

from .client import BirdeyeClient
from .normalizer import BirdeyeNormalizer


class BirdeyeProvider(MarketDataProvider):
    """Normalized Solana market-data provider backed by Birdeye REST."""

    def __init__(
        self,
        *,
        client: BirdeyeClient,
        normalizer: BirdeyeNormalizer | None = None,
    ) -> None:
        self.client = client
        self.normalizer = normalizer or BirdeyeNormalizer()

    @property
    def name(self) -> str:
        return "birdeye"

    def discover_tokens(
        self,
        *,
        limit: int = 100,
    ) -> Sequence[TokenCandidate]:
        """Discover high-liquidity candidates from Birdeye Token List V3."""

        data = self.client.token_list(
            limit=limit,
            sort_by="liquidity",
            sort_type="desc",
        )

        items = self._extract_items(data)

        return [
            self.normalizer.token_candidate(item)
            for item in items
        ]

    def get_snapshot(
        self,
        token_mint: str,
    ) -> MarketSnapshot:
        """Return the latest normalized Birdeye token overview."""

        if not token_mint.strip():
            raise ValueError("token_mint must not be empty")

        data = self.client.token_overview(token_mint)

        payload = self._extract_overview(data)

        return self.normalizer.market_snapshot(
            payload,
            requested_token_mint=token_mint,
            observed_at=datetime.now(UTC),
        )

    @staticmethod
    def _extract_items(
        data: Any,
    ) -> list[dict[str, Any]]:
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = (
                data.get("items")
                or data.get("tokens")
                or data.get("list")
                or []
            )
        else:
            raise ValueError(
                "Birdeye token list data has unsupported shape"
            )

        if not isinstance(items, list):
            raise ValueError(
                "Birdeye token list items must be a list"
            )

        normalized: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                raise ValueError(
                    "Birdeye token list item must be an object"
                )

            normalized.append(item)

        return normalized

    @staticmethod
    def _extract_overview(
        data: Any,
    ) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError(
                "Birdeye token overview data must be an object"
            )

        nested = data.get("item")

        if isinstance(nested, dict):
            return nested

        return data
