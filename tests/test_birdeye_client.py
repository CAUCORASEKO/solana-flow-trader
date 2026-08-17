import httpx
import pytest

from solana_flow_trader.providers.birdeye import (
    BirdeyeClient,
    BirdeyeClientError,
    BirdeyeHTTPError,
    BirdeyeResponseError,
)

TOKEN = "ClientToken1111111111111111111111111111111"


def test_token_list_sends_expected_headers_and_parameters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/defi/v3/token/list"
        assert request.headers["X-API-KEY"] == "test-key"
        assert request.headers["x-chain"] == "solana"

        assert request.url.params["limit"] == "25"
        assert request.url.params["offset"] == "50"
        assert request.url.params["sort_by"] == "market_cap"
        assert request.url.params["sort_type"] == "desc"
        assert request.url.params["min_liquidity"] == "50000"

        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "items": [
                        {
                            "address": TOKEN,
                        }
                    ]
                },
            },
        )

    client = BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    data = client.token_list(
        limit=25,
        offset=50,
        sort_by="market_cap",
        filters={
            "min_liquidity": 50000,
        },
    )

    client.close()

    assert data["items"][0]["address"] == TOKEN


def test_token_overview_sends_address_and_frames() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/defi/token_overview"
        assert request.url.params["address"] == TOKEN
        assert request.url.params["frames"] == "5s,15s,1m"

        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "address": TOKEN,
                    "price": 1.25,
                },
            },
        )

    client = BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    data = client.token_overview(
        TOKEN,
        frames=("5s", "15s", "1m"),
    )

    client.close()

    assert data["address"] == TOKEN
    assert data["price"] == 1.25


def test_context_manager_closes_cleanly() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {},
            },
        )

    with BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.token_list(limit=1) == {}


def test_http_error_preserves_status_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={
                "message": "rate limit reached",
            },
        )

    client = BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(BirdeyeHTTPError) as exc_info:
        client.token_list()

    client.close()

    assert exc_info.value.status_code == 429
    assert "rate limit" in str(exc_info.value)


def test_api_success_false_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": False,
                "message": "provider rejected request",
            },
        )

    client = BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        BirdeyeResponseError,
        match="provider rejected request",
    ):
        client.token_list()

    client.close()


def test_missing_data_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": True,
            },
        )

    client = BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        BirdeyeResponseError,
        match="does not contain data",
    ):
        client.token_list()

    client.close()


def test_invalid_json_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="not-json",
        )

    client = BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        BirdeyeResponseError,
        match="valid JSON",
    ):
        client.token_list()

    client.close()


def test_timeout_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout(
            "timeout",
            request=request,
        )

    client = BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
        BirdeyeClientError,
        match="timed out",
    ):
        client.token_list()

    client.close()


def test_rejects_empty_api_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        BirdeyeClient(api_key=" ")


def test_rejects_invalid_token_list_limit() -> None:
    client = BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200)
        ),
    )

    with pytest.raises(ValueError, match="limit"):
        client.token_list(limit=101)

    client.close()


def test_rejects_more_than_eight_frames() -> None:
    client = BirdeyeClient(
        api_key="test-key",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200)
        ),
    )

    with pytest.raises(ValueError, match="at most 8"):
        client.token_overview(
            TOKEN,
            frames=(
                "5s",
                "10s",
                "15s",
                "20s",
                "25s",
                "30s",
                "35s",
                "40s",
                "45s",
            ),
        )

    client.close()
