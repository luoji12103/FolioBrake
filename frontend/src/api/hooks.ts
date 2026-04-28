import { useEffect, useState, useCallback, useRef } from "react";
import api from "../api/client";

// ---------------------------------------------------------------------------
// Generic fetch hook — mimics TanStack Query's useQuery
// ---------------------------------------------------------------------------

interface QueryState<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
  refetch: () => void;
}

function useQuery<T>(fetcher: () => Promise<T>): QueryState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const execute = useCallback(() => {
    setIsLoading(true);
    setError(null);
    fetcherRef
      .current()
      .then(setData)
      .catch((err: unknown) => {
        const message =
          err instanceof Error ? err.message : "Unknown error";
        setError(message);
      })
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    execute();
  }, [execute]);

  return { data, error, isLoading, refetch: execute };
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export function useHealth() {
  return useQuery(async () => {
    const { data } = await api.get("/health");
    return data as { status: string; version: string };
  });
}

// ---------------------------------------------------------------------------
// Instruments (ETF universe)
// ---------------------------------------------------------------------------

export interface Instrument {
  id: number;
  symbol: string;
  name: string;
  exchange: string;
  type: string;
  category: string | null;
  created_at: string;
}

export function useInstruments() {
  return useQuery(async () => {
    const { data } = await api.get("/data/instruments");
    return data as Instrument[];
  });
}

// ---------------------------------------------------------------------------
// Bars (OHLCV)
// ---------------------------------------------------------------------------

export interface Bar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export function useBars(
  symbol: string | null,
  startDate?: string,
  endDate?: string
) {
  const fetcher = useCallback(async () => {
    if (!symbol) return [] as Bar[];
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    const query = params.toString();
    const { data } = await api.get(
      `/data/bars/${symbol}${query ? `?${query}` : ""}`
    );
    return data as Bar[];
  }, [symbol, startDate, endDate]);

  return useQuery(fetcher);
}

// ---------------------------------------------------------------------------
// Quality
// ---------------------------------------------------------------------------

export interface QualityCheck {
  symbol: string;
  bars_count: number;
  date_range_start: string | null;
  date_range_end: string | null;
  missing_dates: number;
  status: "OK" | "WARNING" | "ERROR";
  issues: string[];
}

export function useQuality(symbol: string | null) {
  const fetcher = useCallback(async () => {
    if (!symbol) return null;
    const { data } = await api.get(`/data/quality/${symbol}`);
    return data as QualityCheck;
  }, [symbol]);

  return useQuery(fetcher);
}

// ---------------------------------------------------------------------------
// Signals
// ---------------------------------------------------------------------------

export interface Signal {
  symbol: string;
  name: string;
  score: number;
  rank: number;
  target_weight: number;
  action: "BUY" | "SELL" | "HOLD";
  reason: string;
}

export function useSignals() {
  return useQuery(async () => {
    const { data } = await api.get("/strategy/signals");
    return data as Signal[];
  });
}

// ---------------------------------------------------------------------------
// Portfolio
// ---------------------------------------------------------------------------

export interface PortfolioTarget {
  symbol: string;
  name: string;
  target_weight: number;
  current_weight: number;
}

export function usePortfolio() {
  return useQuery(async () => {
    const { data } = await api.get("/strategy/portfolio");
    return data as PortfolioTarget[];
  });
}

// ---------------------------------------------------------------------------
// Risk State
// ---------------------------------------------------------------------------

export type RiskLevel = "NORMAL" | "CAUTION" | "DEFENSIVE" | "HALT";

export interface RiskState {
  level: RiskLevel;
  description: string;
  triggered_at: string;
  reason: string;
}

export function useRiskState() {
  return useQuery(async () => {
    const { data } = await api.get("/risk/state");
    return data as RiskState;
  });
}

// ---------------------------------------------------------------------------
// Risk Rules
// ---------------------------------------------------------------------------

export type RuleSeverity = "INFO" | "WARNING" | "CRITICAL";

export interface RiskRule {
  id: string;
  name: string;
  description: string;
  severity: RuleSeverity;
  triggered: boolean;
  threshold: string;
  current_value: string;
}

export function useRiskRules() {
  return useQuery(async () => {
    const { data } = await api.get("/risk/rules");
    return data as RiskRule[];
  });
}

// ---------------------------------------------------------------------------
// Risk Overlay
// ---------------------------------------------------------------------------

export interface OverlayEntry {
  symbol: string;
  name: string;
  original_weight: number;
  final_weight: number;
  adjustment: number;
  reason: string;
}

export function useRiskOverlay() {
  return useQuery(async () => {
    const { data } = await api.get("/risk/overlay");
    return data as OverlayEntry[];
  });
}

// ---------------------------------------------------------------------------
// Backtest Results
// ---------------------------------------------------------------------------

export interface BacktestMetrics {
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  annual_return: number;
  volatility: number;
}

export interface TradeLogEntry {
  date: string;
  symbol: string;
  action: "BUY" | "SELL";
  quantity: number;
  price: number;
  notional: number;
  reason: string;
}

export interface BenchmarkRow {
  metric: string;
  strategy: number | string;
  benchmark: number | string;
}

export interface BacktestResult {
  run_id: string;
  config: {
    strategy: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    benchmark: string;
  };
  metrics: BacktestMetrics;
  trade_log: TradeLogEntry[];
  benchmark_comparison: BenchmarkRow[];
  equity_curve: { date: string; value: number }[];
}

export function useBacktestResults(runId: string | null) {
  const fetcher = useCallback(async () => {
    if (!runId) return null;
    const { data } = await api.get(`/backtest/results/${runId}`);
    return data as BacktestResult;
  }, [runId]);

  return useQuery(fetcher);
}

// ---------------------------------------------------------------------------
// Audit Report
// ---------------------------------------------------------------------------

export type CheckResult = "PASS" | "WARN" | "FAIL";

export interface AuditCheck {
  id: string;
  category: string;
  name: string;
  description: string;
  result: CheckResult;
  detail: string;
}

export interface AuditReport {
  run_id: string;
  grade: "GREEN" | "YELLOW" | "RED";
  score: number;
  max_score: number;
  checks: AuditCheck[];
  summary: string;
  created_at: string;
}

export function useAuditReport(runId: string | null) {
  const fetcher = useCallback(async () => {
    if (!runId) return null;
    const { data } = await api.get(`/audit/report/${runId}`);
    return data as AuditReport;
  }, [runId]);

  return useQuery(fetcher);
}

// ---------------------------------------------------------------------------
// Paper Holdings
// ---------------------------------------------------------------------------

export interface PaperHolding {
  symbol: string;
  name: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  current_value: number;
  pnl: number;
  pnl_pct: number;
}

export function usePaperHoldings(portfolioId: string | null) {
  const fetcher = useCallback(async () => {
    if (!portfolioId) return [];
    const { data } = await api.get(`/paper/holdings/${portfolioId}`);
    return data as PaperHolding[];
  }, [portfolioId]);

  return useQuery(fetcher);
}

// ---------------------------------------------------------------------------
// Paper PnL
// ---------------------------------------------------------------------------

export interface PnLSnapshot {
  portfolio_id: string;
  total_value: number;
  cash: number;
  invested: number;
  total_pnl: number;
  total_pnl_pct: number;
  date: string;
}

export function usePaperPnl(portfolioId: string | null) {
  const fetcher = useCallback(async () => {
    if (!portfolioId) return null;
    const { data } = await api.get(`/paper/pnl/${portfolioId}`);
    return data as PnLSnapshot;
  }, [portfolioId]);

  return useQuery(fetcher);
}

// ---------------------------------------------------------------------------
// Mutation hook (for POST / PUT / DELETE requests)
// ---------------------------------------------------------------------------

interface MutationState<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
  mutate: (body?: unknown) => Promise<T | null>;
  reset: () => void;
}

export function useMutation<T>(
  method: "post" | "put" | "delete",
  url: string
): MutationState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const mutate = useCallback(
    async (body?: unknown): Promise<T | null> => {
      setIsLoading(true);
      setError(null);
      try {
        const response =
          method === "delete"
            ? await api.delete(url)
            : await api[method](url, body);
        setData(response.data as T);
        return response.data as T;
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Unknown error";
        setError(message);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [method, url]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return { data, error, isLoading, mutate, reset };
}
