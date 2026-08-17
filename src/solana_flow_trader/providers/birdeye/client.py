"""HTTP client for the Birdeye REST API."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import httpx


class BirdeyeClientError(RuntimeError):
    """Base error raised by the Birdeye HTTP client."""


class BirdeyeHTTPError(BirdeyeClientError):
    """Raised when Birdeye returns a non-successful HTTP response."""

    def __init__(
        self,
        *,
        status_code: int,
        message: str,
    ) -> None:
        self.status_code = status_code
        super().__init__(f"Birdeye HTTP {status_code}: {message}")


class BirdeyeResponseError(BirdeyeClientError):
    """Raised when a Birdeye response cannot be interpreted safely."""


class BirdeyeClient:
    """Small synchronous REST client for Birdeye Data Services."""

    BASE_URL = "https://public-api.birdeye.so"

    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("api_key must not be empty")

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "accept": "application/json",
                "X-API-KEY": api_key,
                "x-chain": "solana",
            },
            timeout=timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        """Close underlying HTTP resources."""
        self._client.close()

    def __enter__(self) -> BirdeyeClient:
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        self.close()

    def token_list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "liquidity",
        sort_type: str = "desc",
        filters: Mapping[str, object] | None = None,
    ) -> Any:
        """Retrieve a page from Token List V3."""

        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")

        if offset < 0:
            raise ValueError("offset must be non-negative")

        if offset + limit > 10_000:
            raise ValueError("offset + limit must not exceed 10000")

        if sort_type not in {"asc", "desc"}:
            raise ValueError("sort_type must be 'asc' or 'desc'")

        if not sort_by.strip():
            raise ValueError("sort_by must not be empty")

        params: dict[str, object] = {
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_type": sort_type,
        }

        if filters:
            params.update(filters)

        return self._get_data(
            "/defi/v3/token/list",
            params=params,
        )

    def token_overview(
        self,
        token_mint: str,
        *,
        frames: Sequence[str] | None = None,
    ) -> Any:
        """Retrieve current overview statistics for one token."""

        if not token_mint.strip():
            raise ValueError("token_mint must not be empty")

        params: dict[str, object] = {
            "address": token_mint,
        }

        if frames is not None:
            cleaned_frames = [
                frame.strip()
                for frame in frames
                if frame.strip()
            ]

            if not cleaned_frames:
                raise ValueError("frames must contain at least one value")

            if len(cleaned_frames) > 8:
                raise ValueError("frames must contain at most 8 values")

            params["frames"] = ",".join(cleaned_frames)

        return self._get_data(
            "/defi/token_overview",
            params=params,
        )

    def _get_data(
        self,
        path: str,
        *,
        params: Mapping[str, object],
    ) -> Any:
        try:
            response = self._client.get(
                path,
                params=params,
            )
        except httpx.TimeoutException as exc:
            raise BirdeyeClientError(
                "Birdeye request timed out"
            ) from exc
        except httpx.RequestError as exc:
            raise BirdeyeClientError(
                f"Birdeye request failed: {exc}"
            ) from exc

        if not response.is_success:
            raise BirdeyeHTTPError(
                status_code=response.status_code,
                message=self._response_message(response),
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise BirdeyeResponseError(
                "Birdeye response is not valid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise BirdeyeResponseError(
                "Birdeye response must be a JSON object"
            )

        if payload.get("success") is False:
            message = (
                payload.get("message")
                or payload.get("error")
                or "API reported failure"
            )

            raise BirdeyeResponseError(
                f"Birdeye API failure: {message}"
            )

        if "data" not in payload:
            raise BirdeyeResponseError(
                "Birdeye response does not contain data"
            )

        return payload["data"]

    @staticmethod
    def _response_message(
        response: httpx.Response,
    ) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text or response.reason_phrase

        if isinstance(payload, dict):
            message = (
                payload.get("message")
                or payload.get("error")
            )

            if message is not None:
                return str(message)

        return response.reason_phrase
