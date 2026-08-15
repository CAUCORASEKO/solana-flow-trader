from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from solana_flow_trader.collectors import SyntheticCollector, SyntheticScenario
from solana_flow_trader.storage import SnapshotRepository


def test_synthetic_sequence_can_be_persisted_and_restored(tmp_path: Path) -> None:
    collector = SyntheticCollector()
    repository = SnapshotRepository(tmp_path / "snapshots.sqlite3")

    scenario = SyntheticScenario(
        token_mint="PipelineToken111111111111111111111111111111",
        symbol="PIPE",
        start_time=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        start_price_usd=Decimal("1"),
        market_cap_usd=Decimal("100000"),
        liquidity_usd=Decimal("50000"),
        token_age_seconds=120,
    )

    generated = collector.generate(
        scenario,
        [
            Decimal("1.00"),
            Decimal("1.08"),
            Decimal("1.22"),
            Decimal("1.36"),
            Decimal("1.18"),
        ],
        interval_seconds=5,
    )

    repository.save_many(generated)

    restored = repository.get_for_token(scenario.token_mint)

    assert repository.count() == 5
    assert restored == generated
