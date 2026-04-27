# ADR-0003 — No Real-Money Auto-Trading in MVP

## Status

Accepted.

## Decision

MVP supports backtesting, signal-only mode, simulated/paper trading, and manual review. It does not support real-money automatic A-share order execution.

## Rationale

Real-money execution introduces regulatory, broker, reliability, and safety issues that are not necessary for the course project. The practical-track deployment goal can be satisfied through realistic local deployment and simulated/paper trading walkthrough.
