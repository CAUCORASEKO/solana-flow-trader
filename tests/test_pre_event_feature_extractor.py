from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from solana_flow_trader.events import EventDirection, HistoricalEvent
from solana_flow_trader.features import PreEventFeatureExtractor
from solana_flow_trader.models import MarketSnapshot

TOKEN = "FeatureToken111111111111111111111111111111"


def make_snapshot(
    *,
    timestamp: datetime,
    price: str,
    volume: str,
    transactions: int,
    buys: int,
    sells: int,
    buy_volume: str,
    sell_volume: str,
    liquidity: str,
    market_cap: str,
) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=timestamp,
        token_mint=TOKEN,
        symbol="FTR",
        price_usd=Decimal(price),
        market_cap_usd=Decimal(market_cap),
        liquidity_usd=Decimal(liquidity),
        volume_usd=Decimal(volume),
        buy_volume_usd=Decimal(buy_volume),
        sell_volume_usd=Decimal(sell_volume),
        transactions=transactions,
        buys=buys,
        sells=sells,
        unique_buyers=max(1, buys - 1),
        unique_sellers=max(1, sells - 1),
        token_age_seconds=600,
        source="synthetic",
    )


def make_event(start_time: datetime) -> HistoricalEvent:
    return HistoricalEvent(
        token_mint=TOKEN,
        direction=EventDirection.BULL,
        start_time=start_time,
        end_time=start_time + timedelta(seconds=10),
        start_price=Decimal("1.20"),
        end_price=Decimal("1.50"),
        return_pct=Decimal("25"),
        duration_seconds=Decimal("10"),
        start_index=3,
        end_index=5,
    )


def test_extracts_pre_event_features() -> None:
    base = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)

    snapshots = [
        make_snapshot(
            timestamp=base,
            price="1.00",
            volume="1000",
            transactions=100,
            buys=55,
            sells=45,
            buy_volume="600",
            sell_volume="400",
            liquidity="50000",
            market_cap="100000",
        ),
        make_snapshot(
            timestamp=base + timedelta(seconds=10),
            price="1.10",
            volume="1500",
            transactions=140,
            buys=85,
            sells=55,
            buy_volume="950",
            sell_volume="550",
            liquidity="51000",
            market_cap="110000",
        ),
        make_snapshot(
            timestamp=base + timedelta(seconds=20),
            price="1.20",
            volume="2000",
            transactions=200,
            buys=130,
            sells=70,
            buy_volume="1400",
            sell_volume="600",
            liquidity="52500",
            market_cap="120000",
        ),
    ]

    extractor = PreEventFeatureExtractor(window_seconds=20)
    features = extractor.extract(
        make_event(base + timedelta(seconds=20)),
        snapshots,
    )

    assert features is not None
    assert features.sample_count == 3
    assert features.price_return_pct == Decimal("20.0")
    assert features.price_velocity_pct_per_second == Decimal("1.0")
    assert features.volume_change_pct == Decimal("100")
    assert features.transaction_change_pct == Decimal("100")
    assert features.buy_sell_volume_ratio == Decimal("1400") / Decimal("600")
    assert features.buy_sell_transaction_ratio == Decimal("130") / Decimal("70")
    assert features.liquidity_change_pct == Decimal("5.00")
    assert features.market_cap_change_pct == Decimal("20.0")


def test_extract_uses_only_configured_window() -> None:
    base = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)

    snapshots = [
        make_snapshot(
            timestamp=base,
            price="0.50",
            volume="100",
            transactions=10,
            buys=5,
            sells=5,
            buy_volume="50",
            sell_volume="50",
            liquidity="40000",
            market_cap="50000",
        ),
        make_snapshot(
            timestamp=base + timedelta(seconds=20),
            price="1.00",
            volume="1000",
            transactions=100,
            buys=60,
            sells=40,
            buy_volume="700",
            sell_volume="300",
            liquidity="50000",
            market_cap="100000",
        ),
        make_snapshot(
            timestamp=base + timedelta(seconds=30),
            price="1.20",
            volume="2000",
            transactions=200,
            buys=140,
            sells=60,
            buy_volume="1500",
            sell_volume="500",
            liquidity="52000",
            market_cap="120000",
        ),
    ]

    extractor = PreEventFeatureExtractor(window_seconds=10)
    features = extractor.extract(
        make_event(base + timedelta(seconds=30)),
        snapshots,
    )

    assert features is not None
    assert features.sample_count == 2
    assert features.price_return_pct == Decimal("20.0")


def test_returns_none_when_no_token_data_exists() -> None:
    extractor = PreEventFeatureExtractor(window_seconds=20)

    event = make_event(datetime(2026, 8, 17, 12, 0, tzinfo=UTC))

    assert extractor.extract(event, []) is None


def test_zero_denominators_return_none() -> None:
    base = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)

    snapshots = [
        make_snapshot(
            timestamp=base,
            price="1",
            volume="0",
            transactions=0,
            buys=0,
            sells=0,
            buy_volume="0",
            sell_volume="0",
            liquidity="0",
            market_cap="0",
        ),
        make_snapshot(
            timestamp=base + timedelta(seconds=10),
            price="1",
            volume="100",
            transactions=10,
            buys=10,
            sells=0,
            buy_volume="100",
            sell_volume="0",
            liquidity="100",
            market_cap="100",
        ),
    ]

    extractor = PreEventFeatureExtractor(window_seconds=10)
    features = extractor.extract(
        make_event(base + timedelta(seconds=10)),
        snapshots,
    )

    assert features is not None
    assert features.volume_change_pct is None
    assert features.transaction_change_pct is None
    assert features.buy_sell_volume_ratio is None
    assert features.buy_sell_transaction_ratio is None
    assert features.liquidity_change_pct is None
    assert features.market_cap_change_pct is None


def test_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        PreEventFeatureExtractor(window_seconds=0)
