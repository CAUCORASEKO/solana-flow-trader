# Solana Flow Trader — Technical Specification v0.1

## 1. Purpose

Solana Flow Trader is a research-first trading intelligence system for Solana.

The project is developed in three major stages:

1. Research and data collection
2. Trading validation
3. Desktop product

The system must prove that its strategies have positive expectancy after realistic execution costs before autonomous live trading is enabled.

---

## 2. Initial Development Target

Development environment:

- macOS Intel (`x86_64`)
- Python 3.11
- VS Code / terminal
- Local-first research workflow

The first versions are command-line research tools.

A desktop application is a later product layer and must not be required by the research or trading core.

---

## 3. Core Principles

### 3.1 Research before execution

No real-money execution during the initial development stages.

The progression is:

Research
→ Replay
→ Paper Trading
→ Shadow Execution
→ Tiny Live Trading
→ Controlled Autonomous Trading

### 3.2 Independent intelligence

Trading intelligence must not depend on Axiom's user interface.

Axiom may be used as a manual reference platform, but market intelligence, strategy logic, risk management, and execution must remain modular.

### 3.3 Capital preservation

Survival and capital preservation have priority over trade frequency.

The initial risk hypothesis is:

- Maximum capital allocation per trade: 1% of current wallet value.
- 1% is a ceiling, not a mandatory position size.
- Position size may be reduced according to liquidity, execution quality, token risk, or strategy confidence.
- Position sizing, not a narrow fixed stop, is the primary control over catastrophic per-trade loss.

### 3.4 Thesis-based exits

A position may tolerate large percentage fluctuations when the underlying trade thesis remains valid.

Exit decisions may be driven by:

- flow reversal
- liquidity deterioration
- thesis invalidation
- execution deterioration
- profit protection
- time decay
- emergency risk conditions

---

## 4. Market Opportunity Architecture

The system contains two principal opportunity engines.

### 4.1 Behavior Hunter

Used for tokens with sufficient recent history.

Pipeline:

1. Rank/select interesting tokens.
2. Retrieve recent market history.
3. Detect previous strong bullish and bearish movements.
4. Analyze the conditions preceding those movements.
5. Extract behavioral signatures.
6. Compare live conditions with historical event families.
7. Classify the current state as:
   - Bull candidate
   - Bear candidate
   - Trap/failure candidate
   - No trade

Historical analysis may include:

- volume
- transaction rate
- buy/sell flow
- large trade activity
- unique wallets
- liquidity
- price velocity
- RSI
- MFI
- MACD
- VWAP
- Volume Profile
- fractals
- Ichimoku
- volatility
- market structure

Indicators are contextual features, not standalone trade triggers.

Features that do not improve predictive value should later be removed.

### 4.2 Launch Hunter

Used for newly launched tokens without meaningful history.

The system must detect new tokens or liquidity pairs as early as practical.

Initial launch analysis may include:

- token age
- initial market cap
- initial liquidity
- liquidity / market-cap relationship
- transactions per second
- volume acceleration
- buy/sell imbalance
- unique buyers and sellers
- large trade clusters
- buyer concentration
- wallet diversity
- price response
- liquidity behavior
- chase risk

Launch Hunter must initially operate as a collector and observer.

No live-money launch execution should be enabled until launch behavior has been statistically validated.

---

## 5. Token Selection

The system should not deeply analyze every Solana token.

The initial selection funnel is:

Market universe
→ Market-cap ranking
→ Liquidity filter
→ Current activity filter
→ Interesting candidates
→ Deep analysis

Market cap is an initial discovery criterion, not sufficient by itself.

Liquidity and current activity must also be considered.

---

## 6. Historical Event Mining

For each selected token, the Historical Event Miner must identify strong previous movements.

Example labels:

- Strong Bull
- Strong Bear
- Bull Trap
- Bear Trap
- Failed Continuation
- Failed Bounce

Each event must have:

- pre-event window
- event window
- post-event evaluation window

Example observation scales may include:

- 5 seconds
- 15 seconds
- 30 seconds
- 60 seconds
- 2 minutes
- 5 minutes
- 15 minutes

Exact windows must be determined experimentally.

---

## 7. Behavioral Signatures

Each historical event should produce a feature vector.

Example features:

### Flow
- buy volume
- sell volume
- buy/sell imbalance
- transaction acceleration
- unique buyer growth
- unique seller growth
- large buy clusters
- large sell clusters

### Price response
- price velocity
- price acceleration
- realized volatility
- volume-to-price efficiency
- buy-flow efficiency
- sell-flow efficiency

### Technical context
- RSI
- MFI
- MACD
- VWAP relationship
- fractal structure
- Volume Profile position
- Ichimoku state

### Market context
- market cap
- liquidity
- token age
- volume regime
- volatility regime

Live conditions will later be compared against historical event families.

The system must compare current conditions against both successful and failed historical patterns.

---

## 8. Live Event Matching

Live market state:

→ feature extraction
→ comparison with historical signatures
→ similarity calculation

Example outputs:

- Bull similarity
- Bear similarity
- Trap similarity
- Execution quality
- Risk quality

A high similarity score alone must never bypass safety gates.

---

## 9. Entry Philosophy

The project focuses on aggressive short-duration market movements.

The goal is not to predict exact tops or bottoms.

The preferred entry concept is:

- identify strong activity
- determine directional force
- recognize historically familiar conditions
- avoid chasing exhausted movement
- confirm execution quality
- enter only when the current event has acceptable similarity and risk characteristics

Traditional technical indicators are supporting context rather than primary entry triggers.

---

## 10. Risk Engine

Initial risk constraints:

### Per-trade allocation
Maximum:
- 1% of current wallet value

Possible allocation:
- 0%
- partial allocation
- up to 1%

### Additional controls
Future Risk Engine must support:

- maximum simultaneous exposure
- maximum session drawdown
- maximum daily drawdown
- maximum consecutive losses
- minimum SOL reserve
- emergency kill switch

The system must never assume that a high-confidence signal justifies unlimited risk.

---

## 11. Stop-Loss Philosophy

The system does not rely primarily on narrow percentage stops because the target market may have extremely large normal price ranges.

Instead, exits may use:

- thesis invalidation
- flow reversal
- liquidity deterioration
- structural failure
- emergency conditions

The maximum per-trade capital allocation limits catastrophic exposure.

A hard emergency exit mechanism must still exist.

---

## 12. Profit Engine

The target market may produce very large gains and equally violent reversals.

Profit-taking must therefore be actively managed.

Potential mechanisms:

- partial profit taking
- dynamic profit locking
- drawdown-from-peak monitoring
- flow deterioration exit
- reversal velocity detection
- liquidity deterioration exit
- full exit
- runner position

The project should measure:

- MFE: Maximum Favorable Excursion
- MAE: Maximum Adverse Excursion
- time to MFE
- realized profit
- profit capture efficiency
- maximum profit giveback
- reason for exit

Profit Capture Efficiency:

realized profit / maximum favorable excursion

This metric will be used to evaluate whether the exit logic captures enough of fast market moves.

---

## 13. Execution Layer

Execution must remain independent from strategy logic.

The execution layer will later be responsible for:

- obtaining executable quotes
- route quality
- slippage estimation
- price impact
- fees
- transaction submission
- confirmation
- retry/failure handling
- emergency exits

No strategy may assume that theoretical market price equals executable price.

---

## 14. Realistic Performance Model

Research must maintain at least two performance views.

### Theoretical P&L
Uses idealized strategy prices.

### Realistic P&L
Includes estimates or real observations of:

- trading fees
- network fees
- priority fees
- slippage
- price impact
- latency
- failed execution
- execution deterioration

A strategy is not considered profitable merely because theoretical P&L is positive.

---

## 15. Research Metrics

Minimum strategy evaluation should eventually include:

- number of trades
- win rate
- average winner
- average loser
- expectancy per trade
- profit factor
- maximum drawdown
- longest losing streak
- MFE
- MAE
- profit capture efficiency
- execution cost
- theoretical P&L
- realistic P&L

---

## 16. Development Phases

### Phase 0 — Repository Foundation
- package structure
- linting
- tests
- documentation

### Phase 1 — Market Data Collector
- capture and persist raw market observations

### Phase 2 — Token Ranking
- market cap
- liquidity
- current activity

### Phase 3 — Historical Event Miner
- detect strong bull/bear movements
- label historical events

### Phase 4 — Feature Extraction
- flow
- volume
- indicators
- market context

### Phase 5 — Behavioral Profiler
- event families
- winners
- traps
- failures

### Phase 6 — Live Matcher
- compare current state with historical signatures

### Phase 7 — Launch Hunter Collector
- detect and record newly launched tokens

### Phase 8 — Launch Research
- identify early characteristics of successful and failed launches

### Phase 9 — Risk Engine
- position allocation
- exposure limits
- kill switches

### Phase 10 — Profit Engine
- partial exits
- profit lock
- reversal detection

### Phase 11 — Replay / Backtesting
- deterministic historical experiments

### Phase 12 — Paper Trading
- virtual wallet
- live signals
- virtual execution

### Phase 13 — Shadow Execution
- real quotes and execution conditions
- no transaction signing

### Phase 14 — Tiny Live Trading
- minimum practical real-money tests

### Phase 15 — Controlled Autonomous Trading
- risk-limited autonomous execution

### Phase 16 — Desktop Product
- Intel Mac desktop UI
- start/stop controls
- monitoring
- settings
- position visualization
- packaging

---

## 17. Initial Software Architecture

Initial source structure:

src/solana_flow_trader/
- market/
- models/
- storage/
- events/
- indicators/
- behavior/
- launches/
- matching/
- strategy/
- risk/
- profit/
- execution/
- research/

Initial implementation should favor small, testable modules.

The desktop UI must remain separate from the trading core.

---

## 18. Safety Boundary

During Research, Replay, Paper Trading, and Shadow Execution:

- no private key is required
- no transaction is signed
- no real trade is submitted

Live execution must be implemented as an explicit later capability.

---

## 19. Current First Milestone

The first functional milestone is:

> Represent a market observation in a stable internal data model and persist it locally in a form suitable for future historical event analysis.

No trading logic is required for this milestone.

