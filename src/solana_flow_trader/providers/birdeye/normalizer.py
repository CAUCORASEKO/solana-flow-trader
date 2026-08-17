"""Normalize Birdeye REST payloads into internal domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from solana_flow_trader.models import MarketSnapshot
from solana_flow_trader.providers.token_candidate import TokenCandidate


class BirdeyeNormalizationError(ValueError):
    """Raised when a Birdeye payload cannot be safely normalized."""


class BirdeyeNormalizer:
    """Convert provider-specific Birdeye payloads into internal models."""

    SOURCE = "birdeye"

    def token_candidate(
        self,
        payload: dict[str, Any],
    ) -> TokenCandidate:
        """Normalize one Token List V3 record."""

        token_mint = self._required_text(
            self._first(
                payload,
                "address",
                "tokenAddress",
            ),
            field_name="address",
        )

        creation_time = self._optional_int(
            self._first(
                payload,
                "creationTime",
                "creation_time",
            )
        )

        return TokenCandidate(
            token_mint=token_mint,
            symbol=self._optional_text(payload.get("symbol")),
            name=self._optional_text(payload.get("name")),
            price_usd=self._optional_decimal(
                self._first(
                    payload,
                    "price",
                    "priceUsd",
                    "price_usd",
                )
            ),
            market_cap_usd=self._optional_decimal(
                self._first(
                    payload,
                    "marketCap",
                    "market_cap",
                    "marketCapUsd",
                )
            ),
            liquidity_usd=self._optional_decimal(
                self._first(
                    payload,
                    "liquidity",
                    "liquidityUsd",
                    "liquidity_usd",
                )
            ),
            volume_24h_usd=self._optional_decimal(
                self._first(
                    payload,
                    "volume_24h_usd",
                    "volume24hUSD",
                    "v24hUSD",
                    "volume24h",
                )
            ),
            price_change_24h_pct=self._optional_decimal(
                self._first(
                    payload,
                    "price_change_24h_percent",
                    "priceChange24hPercent",
                    "priceChange24h",
                )
            ),
            volume_change_24h_pct=self._optional_decimal(
                self._first(
                    payload,
                    "volume_24h_change_percent",
                    "volumeChange24hPercent",
                    "volumeChange24h",
                )
            ),
            holder_count=self._optional_int(
                self._first(
                    payload,
                    "holder",
                    "holders",
                    "holderCount",
                )
            ),
            token_age_seconds=self._age_seconds(creation_time),
        )

    def market_snapshot(
        self,
        payload: dict[str, Any],
        *,
        requested_token_mint: str | None = None,
        observed_at: datetime | None = None,
    ) -> MarketSnapshot:
        """Normalize one Token Overview response."""

        token_mint = self._optional_text(
            self._first(
                payload,
                "address",
                "tokenAddress",
            )
        )

        if token_mint is None:
            token_mint = requested_token_mint

        token_mint = self._required_text(
            token_mint,
            field_name="address",
        )

        creation_time = self._optional_int(
            self._first(
                payload,
                "creationTime",
                "creation_time",
            )
        )

        buys = self._optional_int(
            self._first(
                payload,
                "buy24h",
                "buys24h",
                "buy_24h",
            )
        )
        sells = self._optional_int(
            self._first(
                payload,
                "sell24h",
                "sells24h",
                "sell_24h",
            )
        )

        transactions = self._optional_int(
            self._first(
                payload,
                "trade24h",
                "trades24h",
                "txns24h",
            )
        )

        if transactions is None and buys is not None and sells is not None:
            transactions = buys + sells

        timestamp = observed_at or datetime.now(UTC)

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise BirdeyeNormalizationError(
                "observed_at must be timezone-aware"
            )

        return MarketSnapshot(
            timestamp=timestamp,
            token_mint=token_mint,
            symbol=self._optional_text(payload.get("symbol")),
            price_usd=self._optional_decimal(
                self._first(
                    payload,
                    "price",
                    "priceUsd",
                    "price_usd",
                )
            ),
            market_cap_usd=self._optional_decimal(
                self._first(
                    payload,
                    "marketCap",
                    "market_cap",
                )
            ),
            liquidity_usd=self._optional_decimal(
                self._first(
                    payload,
                    "liquidity",
                    "liquidityUsd",
                )
            ),
            volume_usd=self._optional_decimal(
                self._first(
                    payload,
                    "v24hUSD",
                    "volume24hUSD",
                    "volume_24h_usd",
                )
            ),
            buy_volume_usd=self._optional_decimal(
                self._first(
                    payload,
                    "vBuy24hUSD",
                    "buyVolume24hUSD",
                    "buy_volume_24h_usd",
                )
            ),
            sell_volume_usd=self._optional_decimal(
                self._first(
                    payload,
                    "vSell24hUSD",
                    "sellVolume24hUSD",
                    "sell_volume_24h_usd",
                )
            ),
            transactions=transactions,
            buys=buys,
            sells=sells,
            unique_buyers=self._optional_int(
                self._first(
                    payload,
                    "uniqueWalletBuy24h",
                    "uniqueBuyers24h",
                )
            ),
            unique_sellers=self._optional_int(
                self._first(
                    payload,
                    "uniqueWalletSell24h",
                    "uniqueSellers24h",
                )
            ),
            token_age_seconds=self._age_seconds(
                creation_time,
                now=timestamp,
            ),
            source=self.SOURCE,
        )

    @staticmethod
    def _first(
        payload: dict[str, Any],
        *keys: str,
    ) -> Any:
        for key in keys:
            if key in payload and payload[key] is not None:
                return payload[key]

        return None

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None

        text = str(value).strip()

        return text or None

    @classmethod
    def _required_text(
        cls,
        value: Any,
        *,
        field_name: str,
    ) -> str:
        text = cls._optional_text(value)

        if text is None:
            raise BirdeyeNormalizationError(
                f"{field_name} is required"
            )

        return text

    @staticmethod
    def _optional_decimal(value: Any) -> Decimal | None:
        if value is None:
            return None

        if isinstance(value, bool):
            raise BirdeyeNormalizationError(
                "boolean value cannot be converted to Decimal"
            )

        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise BirdeyeNormalizationError(
                f"invalid decimal value: {value!r}"
            ) from exc

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None:
            return None

        if isinstance(value, bool):
            raise BirdeyeNormalizationError(
                "boolean value cannot be converted to int"
            )

        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise BirdeyeNormalizationError(
                f"invalid integer value: {value!r}"
            ) from exc

    @staticmethod
    def _age_seconds(
        creation_time: int | None,
        *,
        now: datetime | None = None,
    ) -> int | None:
        if creation_time is None:
            return None

        current = now or datetime.now(UTC)

        created = datetime.fromtimestamp(
            creation_time,
            tz=UTC,
        )

        age = int((current.astimezone(UTC) - created).total_seconds())

        return max(age, 0)
