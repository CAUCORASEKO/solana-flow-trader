from datetime import UTC, datetime
from decimal import Decimal

import pytest

from solana_flow_trader.providers.birdeye import (
    BirdeyeNormalizationError,
    BirdeyeNormalizer,
)

TOKEN = "BirdeyeToken111111111111111111111111111111"


def test_normalizes_token_list_candidate() -> None:
    now = datetime.now(UTC)
    creation_time = int(now.timestamp()) - 3600

    payload = {
        "address": TOKEN,
        "symbol": "BIRD",
        "name": "Birdeye Test",
        "price": "0.0125",
        "marketCap": "1500000",
        "liquidity": 250000,
        "volume_24h_usd": "900000",
        "price_change_24h_percent": "-12.5",
        "volume_24h_change_percent": "85.2",
        "holder": 4200,
        "creationTime": creation_time,
    }

    candidate = BirdeyeNormalizer().token_candidate(payload)

    assert candidate.token_mint == TOKEN
    assert candidate.symbol == "BIRD"
    assert candidate.price_usd == Decimal("0.0125")
    assert candidate.market_cap_usd == Decimal("1500000")
    assert candidate.liquidity_usd == Decimal("250000")
    assert candidate.volume_24h_usd == Decimal("900000")
    assert candidate.price_change_24h_pct == Decimal("-12.5")
    assert candidate.volume_change_24h_pct == Decimal("85.2")
    assert candidate.holder_count == 4200
    assert candidate.token_age_seconds is not None


def test_candidate_tolerates_missing_optional_fields() -> None:
    candidate = BirdeyeNormalizer().token_candidate(
        {
            "address": TOKEN,
        }
    )

    assert candidate.token_mint == TOKEN
    assert candidate.symbol is None
    assert candidate.market_cap_usd is None
    assert candidate.liquidity_usd is None


def test_candidate_requires_address() -> None:
    with pytest.raises(
        BirdeyeNormalizationError,
        match="address",
    ):
        BirdeyeNormalizer().token_candidate(
            {
                "symbol": "BAD",
            }
        )


def test_normalizes_token_overview_snapshot() -> None:
    observed_at = datetime(
        2026,
        8,
        17,
        20,
        0,
        tzinfo=UTC,
    )

    payload = {
        "address": TOKEN,
        "symbol": "BIRD",
        "price": "0.02",
        "marketCap": "2000000",
        "liquidity": "300000",
        "v24hUSD": "1000000",
        "vBuy24hUSD": "620000",
        "vSell24hUSD": "380000",
        "buy24h": 800,
        "sell24h": 500,
        "uniqueWalletBuy24h": 450,
        "uniqueWalletSell24h": 300,
        "creationTime": int(
            datetime(
                2026,
                8,
                17,
                19,
                0,
                tzinfo=UTC,
            ).timestamp()
        ),
    }

    snapshot = BirdeyeNormalizer().market_snapshot(
        payload,
        observed_at=observed_at,
    )

    assert snapshot.timestamp == observed_at
    assert snapshot.token_mint == TOKEN
    assert snapshot.source == "birdeye"

    assert snapshot.price_usd == Decimal("0.02")
    assert snapshot.market_cap_usd == Decimal("2000000")
    assert snapshot.liquidity_usd == Decimal("300000")

    assert snapshot.volume_usd == Decimal("1000000")
    assert snapshot.buy_volume_usd == Decimal("620000")
    assert snapshot.sell_volume_usd == Decimal("380000")

    assert snapshot.buys == 800
    assert snapshot.sells == 500
    assert snapshot.transactions == 1300

    assert snapshot.unique_buyers == 450
    assert snapshot.unique_sellers == 300
    assert snapshot.token_age_seconds == 3600


def test_snapshot_can_use_requested_mint_when_payload_omits_address() -> None:
    snapshot = BirdeyeNormalizer().market_snapshot(
        {
            "symbol": "BIRD",
            "price": "1",
        },
        requested_token_mint=TOKEN,
        observed_at=datetime(
            2026,
            8,
            17,
            20,
            0,
            tzinfo=UTC,
        ),
    )

    assert snapshot.token_mint == TOKEN


def test_snapshot_rejects_missing_address_and_requested_mint() -> None:
    with pytest.raises(
        BirdeyeNormalizationError,
        match="address",
    ):
        BirdeyeNormalizer().market_snapshot(
            {
                "price": "1",
            },
            observed_at=datetime(
                2026,
                8,
                17,
                20,
                0,
                tzinfo=UTC,
            ),
        )


def test_snapshot_rejects_naive_observed_at() -> None:
    with pytest.raises(
        BirdeyeNormalizationError,
        match="timezone-aware",
    ):
        BirdeyeNormalizer().market_snapshot(
            {
                "address": TOKEN,
                "price": "1",
            },
            observed_at=datetime(
                2026,
                8,
                17,
                20,
                0,
            ),
        )


def test_invalid_numeric_value_is_rejected() -> None:
    with pytest.raises(
        BirdeyeNormalizationError,
        match="decimal",
    ):
        BirdeyeNormalizer().token_candidate(
            {
                "address": TOKEN,
                "marketCap": "definitely-not-a-number",
            }
        )


def test_alternative_field_names_can_be_normalized() -> None:
    candidate = BirdeyeNormalizer().token_candidate(
        {
            "tokenAddress": TOKEN,
            "priceUsd": "0.5",
            "market_cap": "500000",
            "liquidityUsd": "100000",
            "volume24hUSD": "250000",
        }
    )

    assert candidate.token_mint == TOKEN
    assert candidate.price_usd == Decimal("0.5")
    assert candidate.market_cap_usd == Decimal("500000")
    assert candidate.liquidity_usd == Decimal("100000")
    assert candidate.volume_24h_usd == Decimal("250000")
