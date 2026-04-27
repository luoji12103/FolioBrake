# ADR-0001 — Project Direction

## Status

Accepted.

## Context

The project must satisfy FTEC 4320 Track B requirements while also being suitable for a long-term open-source project. Existing open-source quant frameworks already cover generic backtesting, AI quant pipelines, and trading infrastructure.

## Decision

Build **Retail ETF Guardian**, focused on A-share ETF rotation, backtest audit gatekeeping, and do-not-trade risk controls for individual investors.

## Consequences

Positive:

- Clear differentiation from generic frameworks.
- Strong course alignment.
- Manageable MVP.
- Practical open-source value.

Negative:

- Requires careful data-quality handling.
- A-share real-money execution remains outside MVP.
- ETF universe survivorship bias must be documented or mitigated.
