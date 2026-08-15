"""SQLite persistence for normalized market snapshots."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from solana_flow_trader.models import MarketSnapshot


class SnapshotRepository:
    """Persist and query MarketSnapshot objects using SQLite."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc TEXT NOT NULL,
                    token_mint TEXT NOT NULL,
                    symbol TEXT,
                    price_usd TEXT,
                    market_cap_usd TEXT,
                    liquidity_usd TEXT,
                    volume_usd TEXT,
                    buy_volume_usd TEXT,
                    sell_volume_usd TEXT,
                    transactions INTEGER,
                    buys INTEGER,
                    sells INTEGER,
                    unique_buyers INTEGER,
                    unique_sellers INTEGER,
                    token_age_seconds INTEGER,
                    source TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_market_snapshots_token_time
                ON market_snapshots (token_mint, timestamp_utc)
                """
            )

    def save(self, snapshot: MarketSnapshot) -> None:
        """Persist one market snapshot."""
        self.save_many([snapshot])

    def save_many(self, snapshots: Iterable[MarketSnapshot]) -> None:
        """Persist multiple market snapshots in one transaction."""
        rows = [self._snapshot_to_row(snapshot) for snapshot in snapshots]

        if not rows:
            return

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO market_snapshots (
                    timestamp_utc,
                    token_mint,
                    symbol,
                    price_usd,
                    market_cap_usd,
                    liquidity_usd,
                    volume_usd,
                    buy_volume_usd,
                    sell_volume_usd,
                    transactions,
                    buys,
                    sells,
                    unique_buyers,
                    unique_sellers,
                    token_age_seconds,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def get_for_token(
        self,
        token_mint: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[MarketSnapshot]:
        """Return snapshots for a token ordered oldest to newest."""
        if not token_mint.strip():
            raise ValueError("token_mint must not be empty")

        clauses = ["token_mint = ?"]
        parameters: list[object] = [token_mint]

        if start is not None:
            clauses.append("timestamp_utc >= ?")
            parameters.append(self._datetime_to_storage(start))

        if end is not None:
            clauses.append("timestamp_utc <= ?")
            parameters.append(self._datetime_to_storage(end))

        query = f"""
            SELECT
                timestamp_utc,
                token_mint,
                symbol,
                price_usd,
                market_cap_usd,
                liquidity_usd,
                volume_usd,
                buy_volume_usd,
                sell_volume_usd,
                transactions,
                buys,
                sells,
                unique_buyers,
                unique_sellers,
                token_age_seconds,
                source
            FROM market_snapshots
            WHERE {" AND ".join(clauses)}
            ORDER BY timestamp_utc ASC, id ASC
        """

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [self._row_to_snapshot(row) for row in rows]

    def count(self) -> int:
        """Return the number of persisted snapshots."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM market_snapshots"
            ).fetchone()

        if row is None:
            return 0

        return int(row["count"])

    @staticmethod
    def _snapshot_to_row(snapshot: MarketSnapshot) -> tuple[object, ...]:
        return (
            SnapshotRepository._datetime_to_storage(snapshot.timestamp),
            snapshot.token_mint,
            snapshot.symbol,
            SnapshotRepository._decimal_to_storage(snapshot.price_usd),
            SnapshotRepository._decimal_to_storage(snapshot.market_cap_usd),
            SnapshotRepository._decimal_to_storage(snapshot.liquidity_usd),
            SnapshotRepository._decimal_to_storage(snapshot.volume_usd),
            SnapshotRepository._decimal_to_storage(snapshot.buy_volume_usd),
            SnapshotRepository._decimal_to_storage(snapshot.sell_volume_usd),
            snapshot.transactions,
            snapshot.buys,
            snapshot.sells,
            snapshot.unique_buyers,
            snapshot.unique_sellers,
            snapshot.token_age_seconds,
            snapshot.source,
        )

    @staticmethod
    def _row_to_snapshot(row: sqlite3.Row) -> MarketSnapshot:
        return MarketSnapshot(
            timestamp=datetime.fromisoformat(row["timestamp_utc"]),
            token_mint=row["token_mint"],
            symbol=row["symbol"],
            price_usd=SnapshotRepository._decimal_from_storage(row["price_usd"]),
            market_cap_usd=SnapshotRepository._decimal_from_storage(
                row["market_cap_usd"]
            ),
            liquidity_usd=SnapshotRepository._decimal_from_storage(
                row["liquidity_usd"]
            ),
            volume_usd=SnapshotRepository._decimal_from_storage(row["volume_usd"]),
            buy_volume_usd=SnapshotRepository._decimal_from_storage(
                row["buy_volume_usd"]
            ),
            sell_volume_usd=SnapshotRepository._decimal_from_storage(
                row["sell_volume_usd"]
            ),
            transactions=row["transactions"],
            buys=row["buys"],
            sells=row["sells"],
            unique_buyers=row["unique_buyers"],
            unique_sellers=row["unique_sellers"],
            token_age_seconds=row["token_age_seconds"],
            source=row["source"],
        )

    @staticmethod
    def _decimal_to_storage(value: Decimal | None) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _decimal_from_storage(value: str | None) -> Decimal | None:
        if value is None:
            return None
        return Decimal(value)

    @staticmethod
    def _datetime_to_storage(value: datetime) -> str:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")

        return value.astimezone(UTC).isoformat()
