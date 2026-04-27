# 05 — Strategy Specification

## Strategy name

`risk_aware_etf_rotation_v1`

## Strategy objective

Create a weekly ETF target portfolio that improves risk-adjusted returns while controlling:

- Maximum drawdown.
- Volatility.
- Turnover.
- Single-ETF concentration.
- Liquidity risk.
- Trading cost.

## Rebalance schedule

- Compute signals after market close on the final trading day of each week.
- Execute simulated rebalance at next trading day's open or VWAP proxy.
- If execution assumptions are unavailable, use next-day open with slippage.

## Candidate ETF scoring

Each ETF receives a composite score:

```
score = w_trend * trend_score
      + w_momentum * momentum_score
      + w_volatility * volatility_score
      + w_liquidity * liquidity_score
      + w_regime * regime_score
      - w_cost * cost_penalty
      - w_concentration * concentration_penalty
```

### Trend features

- Price above SMA 60/120/200.
- SMA slope.
- EMA crossover state.
- Donchian breakout state.

### Momentum features

- 1-month return.
- 3-month return.
- 6-month return.
- 12-month return.
- Risk-adjusted momentum: return / realized volatility.
- Relative strength rank across ETF universe.

### Volatility features

- 20/60-day realized volatility.
- ATR proxy.
- Bollinger bandwidth.
- Volatility percentile vs historical window.

### Drawdown features

- Current drawdown from rolling high.
- Rolling max drawdown.
- Drawdown duration.
- Distance from high.

### Liquidity features

- Average daily turnover amount.
- Volume stability.
- Low-volume days count.
- Staleness/missing-bar ratio.

### Market-regime features

- Broad-index trend state.
- Percent of ETFs above their medium-term moving average.
- Equity ETF vs defensive ETF relative strength.
- Volatility regime.

## Allocation constraints

Initial default constraints:

| Constraint | Default |
|---|---:|
| Max ETF holdings | 5 |
| Min ETF holdings | 1 |
| Max single ETF weight | 35% |
| Min nonzero ETF weight | 5% |
| Max weekly turnover | 50% |
| Minimum holding period | 2 weeks |
| Max equity ETF exposure, normal | 90% |
| Max equity ETF exposure, caution | 60% |
| Max equity ETF exposure, defensive | 40% |
| Max equity ETF exposure, halt | 0–20% |

## Risk profiles

### Conservative

- Target annual volatility: 8%.
- Max tolerated drawdown: 10%.
- Max equity exposure: 60%.
- Max single ETF: 25%.

### Balanced

- Target annual volatility: 12%.
- Max tolerated drawdown: 15%.
- Max equity exposure: 80%.
- Max single ETF: 30%.

### Growth

- Target annual volatility: 15%.
- Max tolerated drawdown: 20%.
- Max equity exposure: 90%.
- Max single ETF: 35%.

## Portfolio construction method

MVP method:

1. Filter ETF universe by data quality and liquidity.
2. Compute composite score.
3. Rank ETFs by score.
4. Keep top K satisfying category constraints.
5. Assign weights by normalized positive scores or inverse-volatility weighting.
6. Apply risk-profile exposure cap.
7. Apply turnover constraint.
8. Apply do-not-trade overlay.
9. Generate final target weights and explanation logs.

## Why not a complex ML model first

The project goal is engineering-grade practical deployment under real-world constraints. A rule-based scoring strategy is easier to audit, explain, and defend in a course presentation. ML can be added after the system can reliably ingest data, backtest without leakage, and reject fragile strategies.

## Required ablation studies

1. Buy-and-hold broad ETF benchmark.
2. Equal-weight ETF benchmark.
3. Rotation without risk overlay.
4. Rotation with risk overlay.
5. Rotation with audit-approved parameters only.

## Key metrics

- CAGR / annualized return.
- Annualized volatility.
- Sharpe ratio.
- Sortino ratio.
- Calmar ratio.
- Maximum drawdown.
- Drawdown duration.
- Hit rate.
- Profit factor.
- Average holding period.
- Turnover.
- Number of trades.
- Transaction cost impact.
- Exposure by ETF category.
- Tail loss / worst day / worst week.
