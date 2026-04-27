# 07 — Backtest Audit Gatekeeper

## Purpose

The audit gatekeeper prevents fragile strategies from entering paper trading merely because of a good-looking backtest curve.

## Gatekeeper output

The audit result must be one of:

- `GREEN`: eligible for simulated/paper trading.
- `YELLOW`: observation only; user can inspect but system should not present it as deployable.
- `RED`: rejected due to fragility, likely overfitting, leakage risk, or unacceptable risk.

## Mandatory audit checks

### 1. Data leakage check

Verify that every signal uses only data available at or before decision time.

Fail conditions:

- Feature uses same-day close for same-day execution without proper delay.
- Backtest rebalances on prices not available at decision time.
- ETF universe includes only current live ETFs without warning.

### 2. Walk-forward validation

Run strategy over rolling windows:

- Train/parameter selection window: e.g., 3 years.
- Validation/test window: e.g., 6–12 months.
- Roll forward by 1–3 months.

Report:

- Median out-of-sample Sharpe.
- Worst-window max drawdown.
- Percent of windows beating benchmark.
- Stability of selected parameters.

### 3. Parameter stability

Test nearby parameter grids:

- Momentum windows: 1/3/6/12 months.
- Trend windows: 60/120/200 days.
- Volatility windows: 20/60 days.
- Risk thresholds: conservative/balanced/growth.

Report whether performance is concentrated in a tiny parameter island.

### 4. Cost stress test

Run base, 2x, 3x, 5x cost assumptions.

Metrics:

- CAGR drop.
- Sharpe drop.
- Turnover sensitivity.
- Whether alpha disappears under reasonable cost stress.

### 5. Regime slicing

Evaluate separately under:

- Uptrend periods.
- Downtrend periods.
- Sideways periods.
- High-volatility periods.
- Crash/rebound periods.

### 6. Bootstrap / trade shuffle

Assess whether performance depends on a few lucky trades.

Methods:

- Block bootstrap returns.
- Shuffle trade order where methodologically acceptable.
- Remove top N winning trades and recompute performance.

### 7. Benchmark comparison

Compare against:

- Buy-and-hold broad ETF.
- Equal-weight ETF universe.
- Simple 60/40-like ETF proxy if possible.
- Cash or money-market proxy.

### 8. Turnover and implementation feasibility

Reject or downgrade if:

- Turnover is too high for target user.
- Average holding period is too short.
- Strategy depends on low-liquidity ETFs.
- Most returns are consumed by costs.

## Suggested scoring

Each check scores 0–100. Weighted audit score:

| Check | Weight |
|---|---:|
| Leakage/data integrity | 20% |
| Walk-forward | 20% |
| Parameter stability | 15% |
| Cost stress | 15% |
| Regime robustness | 10% |
| Benchmark comparison | 10% |
| Turnover/feasibility | 10% |

Grade mapping:

- GREEN: score >= 75 and no critical failure.
- YELLOW: score 55–74 and no critical leakage failure.
- RED: score < 55 or any critical leakage failure.

## Critical failures

Immediate RED:

- Look-ahead bias detected.
- Backtest cannot reproduce from stored config.
- Negative or invalid price data used without correction.
- Strategy only works before costs.
- Max drawdown exceeds user profile threshold by more than 50%.

## Audit report contents

- Strategy config hash.
- Data source versions and data date range.
- Universe list.
- Backtest assumptions.
- Audit check table.
- GREEN/YELLOW/RED status.
- Human-readable explanation.
- Recommendations for next step.

## GUI representation

Audit result should be prominent:

- Green badge: deployable to simulation.
- Yellow badge: watch only.
- Red badge: rejected.

Do not hide audit failures behind charts.
