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
// Data Health
// ---------------------------------------------------------------------------

export interface DataHealth {
  sources: {
    name: string;
    status: string;
    instruments_count: number;
    bars_count: number;
  }[];
  data_quality: {
    total_instruments: number;
    instruments_with_gaps: number;
    latest_bar_date: string | null;
    stale_instruments: number;
  };
}

export function useDataHealth() {
  return useQuery(async () => {
    const { data } = await api.get("/data/health");
    return data as DataHealth;
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
    try {
      const { data } = await api.get(`/data/quality/${symbol}`);
      return data as QualityCheck;
    } catch {
      return null;
    }
  }, [symbol]);

  return useQuery(fetcher);
}

// ---------------------------------------------------------------------------
// Signals
// ---------------------------------------------------------------------------

export interface Signal {
  instrument_id: number;
  symbol: string;
  score: number;
  rank: number;
  reason: Record<string, any>;
}

export function useSignals() {
  return useQuery(async () => {
    const { data } = await api.get("/strategy/signals");
    return data as Signal[];
  });
}

// ---------------------------------------------------------------------------
// Signal History
// ---------------------------------------------------------------------------

export interface SignalHistoryEntry {
  id: number;
  date: string;
  instrument_id: number;
  symbol: string;
  score: number;
  rank: number;
  reason: Record<string, any>;
  subsequent_return_7d: number;
  subsequent_return_30d: number;
  is_correct: boolean;
}

export interface SignalStatistics {
  total_signals: number;
  accuracy_7d: number;
  accuracy_30d: number;
  avg_return_7d: number;
  avg_return_30d: number;
}

export function useSignalHistory() {
  return useQuery(async () => {
    const { data } = await api.get("/strategy/signal-history");
    return data as { signals: SignalHistoryEntry[]; statistics: SignalStatistics };
  });
}

// ---------------------------------------------------------------------------
// Portfolio
// ---------------------------------------------------------------------------

export interface PortfolioTarget {
  instrument_id: number;
  symbol: string;
  target_weight: number;
  score: number;
  constraint_info: Record<string, any>;
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
  state: RiskLevel;
  transition_reason: string;
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

export interface RiskRule {
  date: string;
  rule_name: string;
  triggered: boolean;
  severity: "INFO" | "WARNING" | "CRITICAL";
  detail: Record<string, any>;
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

export interface OverlayDecision {
  decision: string;
  reason: string;
}

export function useRiskOverlay() {
  return useQuery(async () => {
    const { data } = await api.get("/risk/overlay");
    return data as OverlayDecision;
  });
}

// ---------------------------------------------------------------------------
// Risk Alerts
// ---------------------------------------------------------------------------

export interface RiskAlert {
  id: number;
  timestamp: string;
  type: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  title: string;
  message: string;
  read: boolean;
}

export function useRiskAlerts() {
  return useQuery(async () => {
    const { data } = await api.get("/risk/alerts");
    return data as { alerts: RiskAlert[]; unread_count: number };
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
  metrics: Record<string, number>;
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
  instrument_id: number;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  pnl: number;
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
// Paper Portfolios
// ---------------------------------------------------------------------------

export interface PaperPortfolio {
  id: number;
  name: string;
  initial_capital: number;
  created_at: string;
}

export function usePaperPortfolios() {
  return useQuery(async () => {
    const { data } = await api.get("/paper/portfolios");
    return data as PaperPortfolio[];
  });
}

// ---------------------------------------------------------------------------
// Paper Performance
// ---------------------------------------------------------------------------

export interface PaperPerformance {
  portfolio_id: number;
  equity_curve: { date: string; value: number }[];
  benchmark_curve: { date: string; value: number }[];
  drawdown_curve: { date: string; drawdown: number }[];
  metrics: {
    total_return: number;
    cagr: number;
    sharpe_ratio: number;
    max_drawdown: number;
    volatility: number;
    win_rate: number;
  };
  monthly_returns: { month: string; return: number }[];
}

export function usePaperPerformance(portfolioId: string | null) {
  const fetcher = useCallback(async () => {
    if (!portfolioId) return null;
    try {
      const { data } = await api.get(`/paper/performance/${portfolioId}`);
      return data as PaperPerformance;
    } catch {
      return null;
    }
  }, [portfolioId]);

  return useQuery(fetcher);
}

// ---------------------------------------------------------------------------
// Strategy Configs
// ---------------------------------------------------------------------------

export interface StrategyConfigEntry {
  id: number;
  name: string;
  version: string;
  parameters: Record<string, any>;
  universe_filter: Record<string, any>;
  risk_profile: string;
  created_at: string | null;
}

export function useStrategyConfigs() {
  return useQuery(async () => {
    const { data } = await api.get("/strategy/configs");
    return data as StrategyConfigEntry[];
  });
}

export async function createStrategyConfig(payload: {
  name: string;
  version?: string;
  parameters?: Record<string, any>;
  universe_filter?: Record<string, any>;
  risk_profile?: string;
}): Promise<StrategyConfigEntry> {
  const { data } = await api.post("/strategy/configs", payload);
  return data as StrategyConfigEntry;
}

export async function updateStrategyConfig(
  configId: number,
  payload: {
    name?: string;
    version?: string;
    parameters?: Record<string, any>;
    universe_filter?: Record<string, any>;
    risk_profile?: string;
  }
): Promise<StrategyConfigEntry> {
  const { data } = await api.put(`/strategy/configs/${configId}`, payload);
  return data as StrategyConfigEntry;
}

export async function deleteStrategyConfig(configId: number): Promise<void> {
  await api.delete(`/strategy/configs/${configId}`);
}

// ---------------------------------------------------------------------------
// WebSocket — real-time price & risk updates
// ---------------------------------------------------------------------------

export interface PriceUpdate {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
}

interface WebSocketMessage {
  type: string;
  data: unknown;
}

function useWebSocket<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${protocol}//${window.location.host}${path}`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!cancelled) setConnected(true);
      };

      ws.onmessage = (event) => {
        if (cancelled) return;
        try {
          const msg = JSON.parse(event.data) as WebSocketMessage;
          if (msg.type === "PRICE_UPDATE" || msg.type === "RISK_STATE_CHANGE") {
            setData(msg.data as T);
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (cancelled) return;
        setConnected(false);
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [path]);

  return { data, connected };
}

export function useRealtimePrices() {
  return useWebSocket<PriceUpdate>("/ws/prices");
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

// ---------------------------------------------------------------------------
// Sync Progress (polling)
// ---------------------------------------------------------------------------

export interface SyncProgress {
  instrument_id: number;
  progress: number;
  total: number;
  synced: number;
  status: string;
  error: string | null;
}

export function useSyncProgress(instrumentId: number | null, active: boolean) {
  const [progress, setProgress] = useState<SyncProgress | null>(null);

  useEffect(() => {
    if (!instrumentId || !active) {
      setProgress(null);
      return;
    }

    const interval = setInterval(async () => {
      try {
        const { data } = await api.get(`/data/sync-progress/${instrumentId}`);
        setProgress(data as SyncProgress);
        if (data.status === "done" || data.status === "error") {
          clearInterval(interval);
        }
      } catch {
        // endpoint might not be ready yet
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [instrumentId, active]);

  return progress;
}
