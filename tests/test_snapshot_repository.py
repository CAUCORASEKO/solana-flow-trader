from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from solana_flow_trader.models import MarketSnapshot
from solana_flow_trader.storage import SnapshotRepository

TOKEN_A = "TokenA111111111111111111111111111111111"
TOKEN_B = "TokenB111111111111111111111111111111111"


def make_snapshot(
    *,
    token_mint: str = TOKEN_A,
    timestamp: datetime | None = None,
    price_usd: Decimal | None = Decimal("0.01234567890123456789"),
) -> MarketSnapshot:
    return MarketSnapshot(
        timestamp=timestamp or datetime(2026, 8, 15, 10, 0, tzinfo=UTC),
        token_mint=token_mint,
        symbol="TEST",
        price_usd=price_usd,
        market_cap_usd=Decimal("125000.123456789"),
        liquidity_usd=Decimal("42000.987654321"),
        volume_usd=Decimal("18000.111111111"),
        buy_volume_usd=Decimal("11000.222222222"),
        sell_volume_usd=Decimal("6999.888888889"),
        transactions=320,
        buys=210,
        sells=110,
        unique_buyers=150,
        unique_sellers=82,
        token_age_seconds=720,
        source="synthetic",
    )


@pytest.fixture
def repository(tmp_path: Path) -> SnapshotRepository:
    return SnapshotRepository(tmp_path / "snapshots.sqlite3")


def test_repository_starts_empty(repository: SnapshotRepository) -> None:
    assert repository.count() == 0


def test_repository_saves_and_restores_snapshot_exactly(
    repository: SnapshotRepository,
) -> None:
    original = make_snapshot()

    repository.save(original)

    restored = repository.get_for_token(TOKEN_A)

    assert repository.count() == 1
    assert restored == [original]
    assert restored[0].price_usd == Decimal("0.01234567890123456789")


def test_repository_preserves_missing_optional_values(
    repository: SnapshotRepository,
) -> None:
    snapshot = make_snapshot(price_usd=None)

    repository.save(snapshot)

    restored = repository.get_for_token(TOKEN_A)

    assert restored[0].price_usd is None


def test_repository_returns_snapshots_in_time_order(
    repository: SnapshotRepository,
) -> None:
    base = datetime(2026, 8, 15, 10, 0, tzinfo=UTC)

    repository.save_many(
        [
            make_snapshot(timestamp=base + timedelta(seconds=20)),
            make_snapshot(timestamp=base),
            make_snapshot(timestamp=base + timedelta(seconds=10)),
        ]
    )

    restored = repository.get_for_token(TOKEN_A)

    assert [snapshot.timestamp for snapshot in restored] == [
        base,
        base + timedelta(seconds=10),
        base + timedelta(seconds=20),
    ]


def test_repository_filters_by_token(repository: SnapshotRepository) -> None:
    repository.save_many(
        [
            make_snapshot(token_mint=TOKEN_A),
            make_snapshot(token_mint=TOKEN_B),
        ]
    )

    restored = repository.get_for_token(TOKEN_A)

    assert len(restored) == 1
    assert restored[0].token_mint == TOKEN_A


def test_repository_filters_by_time_range(repository: SnapshotRepository) -> None:
    base = datetime(2026, 8, 15, 10, 0, tzinfo=UTC)

    repository.save_many(
        [
            make_snapshot(timestamp=base),
            make_snapshot(timestamp=base + timedelta(seconds=10)),
            make_snapshot(timestamp=base + timedelta(seconds=20)),
        ]
    )

    restored = repository.get_for_token(
        TOKEN_A,
        start=base + timedelta(seconds=5),
        end=base + timedelta(seconds=15),
    )

    assert len(restored) == 1
    assert restored[0].timestamp == base + timedelta(seconds=10)


def test_repository_rejects_empty_token_query(
    repository: SnapshotRepository,
) -> None:
    with pytest.raises(ValueError, match="token_mint"):
        repository.get_for_token("")


def test_repository_rejects_naive_query_datetime(
    repository: SnapshotRepository,
) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        repository.get_for_token(
            TOKEN_A,
            start=datetime(2026, 8, 15, 10, 0),
        )


def test_save_many_with_empty_iterable_is_noop(
    repository: SnapshotRepository,
) -> None:
    repository.save_many([])

    assert repository.count() == 0
