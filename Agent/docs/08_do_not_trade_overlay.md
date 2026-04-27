# 08 — Do-Not-Trade Risk Overlay

## Purpose

The do-not-trade overlay explicitly models the value of not trading. It can block new positions, reduce risk exposure, or require manual confirmation when market conditions are abnormal.

## State machine

Risk state:

- `NORMAL`: strategy operates normally.
- `CAUTION`: reduce risk; allow only high-confidence trades.
- `DEFENSIVE`: reduce equity exposure; prioritize defensive ETFs or cash.
- `HALT`: block new risk-increasing trades.

## Decision actions

- `ALLOW`: execute simulated rebalance as planned.
- `REDUCE`: scale down target risky exposure.
- `BLOCK`: prevent risk-increasing trades.
- `MANUAL_CONFIRM`: show warning and require user confirmation in GUI.

## Daily risk rules

### Trend break rule

Trigger when broad market proxy or current holding falls below medium/long-term moving average and momentum is negative.

Action:

- CAUTION or DEFENSIVE depending on severity.
- Block new equity ETF additions if severe.

### Volatility spike rule

Trigger when realized volatility exceeds a historical percentile threshold.

Action:

- Reduce exposure according to risk profile.

### Portfolio drawdown rule

Trigger when portfolio drawdown exceeds user risk threshold.

Action:

- DEFENSIVE or HALT.

### Liquidity degradation rule

Trigger when an ETF has poor average amount, abnormal volume collapse, or zero/near-zero trading days.

Action:

- Block trading that ETF.

### Price anomaly rule

Trigger when price movement or estimated ETF premium/discount is abnormal.

Action:

- Manual confirmation or block.

### Cost coverage rule

Trigger when estimated transaction cost exceeds expected edge threshold.

Action:

- Skip rebalance.

### Calendar/event risk rule

Trigger around known high-risk market calendar periods, major holidays, or manually configured macro/policy events.

Action:

- Manual confirmation or reduce exposure.

## Intraday extension

MVP can include intraday observation but not intraday alpha. Intraday snapshot should support:

- Current price move check.
- Volume/amount check.
- Abnormal gap check.
- Risk alert in GUI.

No high-frequency order generation in MVP.

## Overlay calculation order

1. Strategy creates target weights.
2. Overlay reads market, ETF, and portfolio risk state.
3. Overlay modifies target weights or blocks trade.
4. System stores both original target and final target.
5. Explanation log records why the overlay acted.

## Example explanation

```
Original action: Buy 159915.SZ to 20% weight.
Overlay decision: BLOCK.
Reason: ETF volatility percentile above 95%, broad-market trend negative, and portfolio drawdown exceeded balanced profile caution threshold.
Final action: No new position opened.
```

## Report metrics

- Number of blocked trades.
- Number of reduced trades.
- Return impact of overlay.
- Drawdown impact of overlay.
- Turnover impact of overlay.
- Worst-case days avoided.
