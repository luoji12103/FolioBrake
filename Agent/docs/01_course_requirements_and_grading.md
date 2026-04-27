# 01 — Course Requirements and Grading Mapping

## Source materials summarized

The project is for FTEC 4320 Financial Data Analysis. The uploaded Week 9 lecture slides state that the final project is the course capstone, with three tracks: Research Track, Practical Track, and Competition Track. The slides also state that grading is split into oral presentation and report/code, and that the Week 9 Practical Track examples include backtesting systems, enhanced pairs trading with ML, and trading strategies with alternative data.

The uploaded syllabus states that the course emphasizes state-of-the-art financial data analysis, multimodal financial data, AI/statistical modeling, end-to-end data workflows, implementation, experimentation, and communication. It also provides the rubric: final project grading includes data analysis skills, code quality, presentation of results/explanations, creativity, and performance; presentation grading includes organization, slide quality, technical soundness, and responses to questions.

## Deadline note

There is a date inconsistency across sources:

- Canvas/user-provided assignment text: final report/code due **Fri May 29, 2026 11:59pm**.
- Week 9 lecture slide: report and code due **May 29, 23:59**.
- Syllabus: final project due **May 10, 2026**, presentation due **May 6, 2026**.

Use the Canvas assignment and Week 9 slide deadline as operational deadline, but mention in the project plan that Canvas is the authoritative source.

## Track B requirements mapping

| Track B requirement | How this project satisfies it |
|---|---|
| Design a reasonable trading strategy | Risk-aware A-share ETF rotation with weekly allocation and daily risk overlay. |
| Full trading pipeline | Data ingestion, cleaning, feature engineering, signal generation, portfolio construction, backtesting, audit, paper/simulated trading, GUI. |
| Realistic deployment | Docker Compose deployment and local paper/simulated trading. Optional future broker adapters. |
| Demonstration | Tauri GUI, backtest report, risk/audit report, deployment walkthrough. |
| Technical report | Report outline provided in this handoff. |
| Codebase | Modular backend/frontend/ops structure specified in this handoff. |

## Rubric mapping

| Rubric item | Target implementation evidence |
|---|---|
| Data analysis skills | A-share ETF data ingestion, cleaned OHLCV, adjusted prices, liquidity fields, benchmark data, feature registry, data quality checks. |
| Code quality | Typed Python backend, modular services, tests, Docker Compose, clean API contracts, clear repository structure. |
| Presentation of results and explanations | GUI dashboards, audit report, trade explanation logs, strategy comparison tables, performance plots. |
| Creativity | Combination of ETF rotation + backtest audit gatekeeper + do-not-trade overlay for retail investors. |
| Performance | Out-of-sample metrics, risk-adjusted returns, max drawdown reduction, turnover control, benchmark comparison. |

## Presentation expectations

The oral presentation should explain:

1. What problem is being solved and why it matters.
2. Data sources and data workflow.
3. Strategy design.
4. Backtesting and audit methodology.
5. Results and ablation studies.
6. Deployment/demo walkthrough.
7. Limitations and future work.

The Week 9 slide states the oral presentation is designed earlier than the report deadline, so the presentation can show partial implementation if the problem, data, methods, and preliminary results are clear.

## Academic integrity and AI usage

The syllabus permits use of generative AI but warns against relying too much on it. Implementation should therefore include:

- Human-authored design decisions.
- Clear commit history.
- Explicit acknowledgement of AI assistance if required by course policy.
- No plagiarism of existing open-source code without license compliance.
- Source citations in report for all external libraries and data sources.
