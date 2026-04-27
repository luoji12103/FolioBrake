# MVP Acceptance Checklist

## Data

- [ ] ETF universe config exists.
- [ ] Historical data can be fetched.
- [ ] Cleaned bars are stored.
- [ ] Data quality report is generated.
- [ ] Data source and fetch timestamp are stored.

## Strategy

- [ ] Feature registry implemented.
- [ ] Weekly scoring works.
- [ ] Portfolio constraints work.
- [ ] Explanation logs exist.

## Risk overlay

- [ ] Risk states implemented.
- [ ] Daily rules implemented.
- [ ] Overlay can allow/reduce/block/manual-confirm.
- [ ] Original and final target weights are both stored.

## Backtest

- [ ] Backtest runs end-to-end.
- [ ] Costs/slippage applied.
- [ ] Benchmarks included.
- [ ] Metrics computed.
- [ ] Trade logs generated.

## Audit

- [ ] Leakage check.
- [ ] Walk-forward check.
- [ ] Parameter stability check.
- [ ] Cost stress check.
- [ ] Regime slicing.
- [ ] GREEN/YELLOW/RED grade.

## GUI

- [ ] Dashboard.
- [ ] ETF universe.
- [ ] Signals.
- [ ] Risk overlay.
- [ ] Backtest.
- [ ] Audit.
- [ ] Paper portfolio.

## Deployment

- [ ] Docker Compose works.
- [ ] `.env.example` complete.
- [ ] README quickstart works.
- [ ] Demo script documented.

## Report/presentation

- [ ] Results reproducible.
- [ ] Metrics table exported.
- [ ] Charts exported.
- [ ] Limitations stated.
- [ ] AI assistance acknowledged if required.
