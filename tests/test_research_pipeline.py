from datetime import UTC, datetime
from decimal import Decimal

from solana_flow_trader.behavior import (
    BehavioralLibraryBuilder,
    BehaviorQualityProfiler,
    OutcomeDistributionCalculator,
)
from solana_flow_trader.collectors import (
    SyntheticCollector,
    SyntheticScenario,
)
from solana_flow_trader.events import HistoricalEventMiner
from solana_flow_trader.features import (
    EventFeatureVector,
    PreEventFeatureExtractor,
)
from solana_flow_trader.matching import (
    BehavioralMatcher,
    BehaviorLabel,
    LabeledFeatureVector,
)
from solana_flow_trader.outcomes import OutcomeAnalyzer
from solana_flow_trader.research import (
    CandidateDirection,
    CandidateStatus,
    ResearchCandidateEvaluator,
)

TOKEN = "PipelineResearchToken1111111111111111111111111"


def make_history():
    collector = SyntheticCollector()

    scenario = SyntheticScenario(
        token_mint=TOKEN,
        symbol="PIPE",
        start_time=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        start_price_usd=Decimal("1"),
        market_cap_usd=Decimal("100000"),
        liquidity_usd=Decimal("50000"),
        token_age_seconds=100,
    )

    return collector.generate(
        scenario,
        [
            Decimal("1.00"),
            Decimal("1.08"),
            Decimal("1.20"),
            Decimal("1.32"),
            Decimal("1.38"),
            Decimal("1.35"),
            Decimal("1.10"),
            Decimal("0.95"),
            Decimal("0.80"),
            Decimal("0.72"),
        ],
        interval_seconds=5,
    )


def test_complete_research_pipeline_selects_bull_candidate() -> None:
    snapshots = make_history()

    library = BehavioralLibraryBuilder(
        event_miner=HistoricalEventMiner(
            threshold_pct=Decimal("20"),
            max_window_seconds=15,
        ),
        feature_extractor=PreEventFeatureExtractor(
            window_seconds=15,
        ),
        outcome_analyzer=OutcomeAnalyzer(
            observation_seconds=30,
        ),
    ).build(snapshots)

    assert library is not None
    assert library.bull_count >= 1
    assert library.bear_count >= 1

    matcher_history = [
        LabeledFeatureVector(
            event_id=sample.event_id,
            label=sample.label,
            features=sample.features,
        )
        for sample in library.samples
    ]

    bull_distribution = OutcomeDistributionCalculator().calculate(
        library.samples,
        label=BehaviorLabel.BULL,
    )
    bear_distribution = OutcomeDistributionCalculator().calculate(
        library.samples,
        label=BehaviorLabel.BEAR,
    )

    bull_quality = BehaviorQualityProfiler().profile(
        bull_distribution
    )
    bear_quality = BehaviorQualityProfiler().profile(
        bear_distribution
    )

    bull_sample = next(
        sample
        for sample in library.samples
        if sample.label == BehaviorLabel.BULL
    )

    current = EventFeatureVector(
        token_mint=bull_sample.features.token_mint,
        window_seconds=bull_sample.features.window_seconds,
        sample_count=bull_sample.features.sample_count,
        price_return_pct=bull_sample.features.price_return_pct,
        price_velocity_pct_per_second=(
            bull_sample.features.price_velocity_pct_per_second
        ),
        volume_change_pct=bull_sample.features.volume_change_pct,
        transaction_change_pct=(
            bull_sample.features.transaction_change_pct
        ),
        buy_sell_volume_ratio=(
            bull_sample.features.buy_sell_volume_ratio
        ),
        buy_sell_transaction_ratio=(
            bull_sample.features.buy_sell_transaction_ratio
        ),
        liquidity_change_pct=(
            bull_sample.features.liquidity_change_pct
        ),
        market_cap_change_pct=(
            bull_sample.features.market_cap_change_pct
        ),
    )

    match_result = BehavioralMatcher(
        top_k=1
    ).match(
        current,
        matcher_history,
    )

    candidate = ResearchCandidateEvaluator(
        candidate_similarity=Decimal("0.80"),
        watch_similarity=Decimal("0.65"),
        max_trap_similarity=Decimal("0.55"),
        min_similarity_margin=Decimal("0.05"),
    ).evaluate(
        match_result,
        bull_quality=bull_quality,
        bear_quality=bear_quality,
    )

    assert match_result.bull.score == Decimal("1")
    assert match_result.bull.score > match_result.bear.score

    assert candidate.direction == CandidateDirection.BULL

    # The synthetic library is intentionally tiny, so evidence quality
    # should prevent promotion to a full research candidate.
    assert candidate.status == CandidateStatus.WATCH
    assert "evidence" in candidate.reason
