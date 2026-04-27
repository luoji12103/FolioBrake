# 14 — Report and Presentation Outline

## Technical report outline

### 1. Introduction

- Problem: retail investors have access to many trading tools but lack robust, explainable, risk-aware ETF decision systems.
- Contribution: ETF rotation + audit gatekeeper + do-not-trade overlay + deployable GUI.

### 2. Related work and non-duplication

Discuss existing projects:

- Backtrader.
- vectorbt.
- Qlib.
- FinRL.
- LEAN.
- RQAlpha/vn.py/WonderTrader if relevant.
- AKShare/Tushare/efinance as data sources.

Explain that this project does not attempt to replace them; it builds a retail-facing decision/risk/audit layer.

### 3. System design

- Architecture diagram.
- Backend services.
- Frontend GUI.
- Docker Compose deployment.
- Data flow.

### 4. Data

- A-share ETF universe.
- Historical daily data.
- Data cleaning and validation.
- Survivorship bias limitations.
- Data source limitations.

### 5. Strategy

- Weekly ETF rotation.
- Feature families.
- Scoring model.
- Portfolio constraints.
- Risk profiles.

### 6. Do-not-trade overlay

- Risk states.
- Rules.
- Overlay decision actions.
- Examples.

### 7. Backtesting methodology

- Execution assumptions.
- Transaction costs and slippage.
- Benchmarks.
- Metrics.
- No-lookahead design.

### 8. Audit gatekeeper

- Walk-forward validation.
- Parameter stability.
- Cost stress.
- Regime slicing.
- GREEN/YELLOW/RED grade.

### 9. Results

- Main performance table.
- Equity curve.
- Drawdown chart.
- Benchmark comparison.
- Ablation study: with/without risk overlay.
- Audit results.

### 10. Deployment demonstration

- Docker Compose.
- Tauri GUI.
- Paper/simulated trading walkthrough.

### 11. Limitations

- Data quality and source reliability.
- Survivorship bias in ETF universe if not fully solved.
- No real-money A-share execution.
- Backtest assumptions may differ from real execution.
- Historical performance not predictive guarantee.

### 12. Future work

- US ETF support.
- Broker paper-trading adapters.
- Improved ETF classification.
- More robust data vendors.
- Portfolio upload and diagnosis.

## 12-minute presentation structure

| Time | Content |
|---:|---|
| 0:00–1:00 | Problem and target user. |
| 1:00–2:00 | Why existing tools are insufficient for retail investors. |
| 2:00–3:30 | System overview and architecture. |
| 3:30–5:00 | Strategy: ETF rotation and constraints. |
| 5:00–6:30 | Do-not-trade risk overlay. |
| 6:30–8:00 | Backtest audit gatekeeper. |
| 8:00–10:00 | Results and ablation. |
| 10:00–11:15 | GUI/deployment demo. |
| 11:15–12:00 | Limitations and next steps. |

## Likely Q&A questions

### Why not use a complex AI model?

Because the Track B objective emphasizes a realistic trading system. A simple, auditable strategy is more appropriate for a retail investor product than a black-box model that is difficult to validate.

### How do you prevent overfitting?

Through walk-forward testing, parameter stability, cost stress, regime slicing, leakage checks, and audit gatekeeper grades.

### Why A-share ETFs instead of stocks?

ETFs reduce idiosyncratic single-stock risk, are more suitable for low-frequency personal investing, and allow a manageable MVP universe.

### What is innovative here?

The fusion of ETF rotation, mandatory backtest credibility audit, and explicit do-not-trade risk overlay in a cross-platform GUI for individual investors.

### Is this investment advice?

No. It is an educational decision-support and simulation tool. Real-money auto-trading is out of MVP scope.
