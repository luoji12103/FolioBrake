import { useState, useEffect, useCallback } from "react";
import { ErrorMessage } from "../components/ErrorMessage";
import { DataTable, type ColumnDef } from "../components/DataTable";
import { usePaperHoldings, usePaperPnl, PaperHolding } from "../api/hooks";
import api from "../api/client";
import "./shared.css";

function fmtCurrency(v: number): string {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(v);
}

function fmtPct(v: number): string {
  return `${(v * 100).toFixed(2)}%`;
}

function PaperSkeleton() {
  return (
    <div style={{ marginTop: "var(--space-4)" }}>
      <div className="metrics-grid">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton" style={{ width: "40%", height: 12 }} />
            <div className="skeleton" style={{ width: "65%", height: 28 }} />
          </div>
        ))}
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="skeleton-row">
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      ))}
    </div>
  );
}

function PortfolioSummary({
  pnl,
}: {
  pnl: NonNullable<ReturnType<typeof usePaperPnl>["data"]>;
}) {
  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-label">Total Value</div>
        <div className="metric-value" style={{ fontSize: "var(--text-xl)", color: "var(--color-text)" }}>
          {fmtCurrency(pnl.total_value)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Cash</div>
        <div className="metric-value" style={{ fontSize: "var(--text-xl)", color: "var(--color-text)" }}>
          {fmtCurrency(pnl.cash)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Invested</div>
        <div className="metric-value" style={{ fontSize: "var(--text-xl)", color: "var(--color-text)" }}>
          {fmtCurrency(pnl.invested)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Total P&amp;L</div>
        <div
          className={`metric-value ${pnl.total_pnl >= 0 ? "positive" : "negative"}`}
          style={{ fontSize: "var(--text-xl)" }}
        >
          {fmtCurrency(pnl.total_pnl)}
          <span style={{ fontSize: "var(--text-sm)", marginLeft: "var(--space-1)", fontWeight: 500 }}>
            ({fmtPct(pnl.total_pnl_pct)})
          </span>
        </div>
      </div>
    </div>
  );
}

const HOLDINGS_COLUMNS: ColumnDef<PaperHolding>[] = [
  {
    key: "instrument_id",
    label: "Instrument ID",
    sortable: true,
    render: (v) => <span style={{ fontWeight: 600, color: "var(--color-accent)" }}>{String(v)}</span>,
  },
  {
    key: "quantity",
    label: "Quantity",
    sortable: true,
    align: "right",
    render: (v) => <span style={{ fontVariantNumeric: "tabular-nums" }}>{(v as number).toLocaleString()}</span>,
  },
  {
    key: "avg_cost",
    label: "Avg Cost",
    sortable: true,
    align: "right",
    render: (v) => <span style={{ fontVariantNumeric: "tabular-nums" }}>{fmtCurrency(v as number)}</span>,
  },
  {
    key: "current_price",
    label: "Current Price",
    sortable: true,
    align: "right",
    render: (v) => <span style={{ fontVariantNumeric: "tabular-nums" }}>{fmtCurrency(v as number)}</span>,
  },
  {
    key: "market_value",
    label: "Market Value",
    sortable: true,
    align: "right",
    render: (v) => <span style={{ fontVariantNumeric: "tabular-nums", fontWeight: 500 }}>{fmtCurrency(v as number)}</span>,
  },
  {
    key: "pnl",
    label: "P&L",
    sortable: true,
    align: "right",
    render: (v) => (
      <span
        style={{
          color: (v as number) >= 0 ? "var(--color-green)" : "var(--color-red)",
          fontWeight: 600,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {fmtCurrency(v as number)}
      </span>
    ),
  },
];

function HoldingsTable({ holdings }: { holdings: PaperHolding[] }) {
  if (!holdings || holdings.length === 0) {
    return (
      <div className="card">
        <div className="card-title">Holdings</div>
        <div className="state-banner state-empty" style={{ marginBottom: 0 }}>
          <div className="state-empty-icon">{"\uD83D\uDCE6"}</div>
          <div className="state-empty-title">No holdings yet</div>
          <div className="state-empty-desc">
            Apply trading signals to populate your paper portfolio.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">Holdings ({holdings.length})</div>
      <DataTable
        data={holdings as unknown as Record<string, unknown>[]}
        columns={HOLDINGS_COLUMNS as unknown as ColumnDef<Record<string, unknown>>[]}
        pageSize={20}
        filterPlaceholder="Search holdings\u2026"
      />
    </div>
  );
}

interface Order {
  id: string;
  date: string;
  symbol: string;
  action: "BUY" | "SELL";
  quantity: number;
  price: number;
  notional: number;
  status: "FILLED" | "PENDING" | "CANCELLED";
}

function OrderHistory() {
  const [orders] = useState<Order[]>([]);

  return (
    <div className="card">
      <div className="card-title">Order History</div>
      {orders.length === 0 ? (
        <div className="state-banner state-empty" style={{ marginBottom: 0 }}>
          <div className="state-empty-icon">{"\uD83D\uDCCB"}</div>
          <div className="state-empty-title">No orders placed</div>
          <div className="state-empty-desc">
            Order history will appear here once you start executing trades.
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Symbol</th>
                <th>Action</th>
                <th>Quantity</th>
                <th>Price</th>
                <th>Notional</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => {
                const statusMap: Record<string, string> = {
                  FILLED: "badge-pass",
                  PENDING: "badge-warn",
                  CANCELLED: "badge-fail",
                };
                return (
                  <tr key={o.id}>
                    <td>{new Date(o.date).toLocaleDateString("en-CN")}</td>
                    <td style={{ fontWeight: 600 }}>{o.symbol}</td>
                    <td>
                      <span className={`badge ${o.action === "BUY" ? "badge-buy" : "badge-sell"}`}>
                        {o.action}
                      </span>
                    </td>
                    <td>{o.quantity.toLocaleString()}</td>
                    <td>{fmtCurrency(o.price)}</td>
                    <td>{fmtCurrency(o.notional)}</td>
                    <td>
                      <span className={`badge ${statusMap[o.status] || ""}`}>
                        {o.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

interface RebalanceTrade {
  symbol: string;
  side: string;
  current_value: number;
  target_value: number;
  delta: number;
  estimated_cost: number;
}

interface RebalancePreview {
  portfolio_id: number;
  total_value: number;
  estimated_total_cost: number;
  cost_pct_of_value: number;
  trades: RebalanceTrade[];
  trade_count: number;
}

function RebalanceDialog({
  portfolioId,
  targetWeights,
  signalDate,
  onClose,
  onExecuted,
}: {
  portfolioId: string;
  targetWeights: Record<string, number>;
  signalDate: string;
  onClose: () => void;
  onExecuted: () => void;
}) {
  const [preview, setPreview] = useState<RebalancePreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);
  const [execResult, setExecResult] = useState<{
    orders_executed: number;
  } | null>(null);

  useEffect(() => {
    api
      .post("/paper/preview-rebalance", {
        portfolio_id: Number(portfolioId),
        signal_date: signalDate,
        target_weights: targetWeights,
      })
      .then((res) => setPreview(res.data))
      .catch((err) =>
        setError(err.response?.data?.detail || err.message)
      )
      .finally(() => setLoading(false));
  }, [portfolioId, signalDate, targetWeights]);

  const handleExecute = async () => {
    setExecuting(true);
    setError(null);
    try {
      const res = await api.post("/paper/execute-rebalance", {
        portfolio_id: Number(portfolioId),
        signal_date: signalDate,
        target_weights: targetWeights,
      });
      setExecResult(res.data);
      onExecuted();
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
            "Execution failed";
      setError(msg);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h3>
            {execResult
              ? "Rebalance Complete"
              : "Confirm Rebalance"}
          </h3>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: "center", padding: "var(--space-8)" }}>
            <div className="state-loading-icon" />
            <p
              style={{
                marginTop: "var(--space-3)",
                color: "var(--color-text-dim)",
                fontSize: "var(--text-sm)",
              }}
            >
              Calculating preview...
            </p>
          </div>
        )}

        {error && (
          <div className="state-banner state-error">
            {error}
          </div>
        )}

        {execResult && (
          <div style={{ textAlign: "center", padding: "var(--space-4)" }}>
            <div
              style={{
                fontSize: 40,
                marginBottom: "var(--space-3)",
              }}
            >
              {"\u2705"}
            </div>
            <p
              style={{
                fontSize: "var(--text-base)",
                fontWeight: 600,
                color: "var(--color-green)",
              }}
            >
              {execResult.orders_executed} order
              {execResult.orders_executed !== 1 ? "s" : ""}{" "}
              executed successfully
            </p>
          </div>
        )}

        {preview && !execResult && (
          <>
            <div
              className="metrics-grid"
              style={{
                gridTemplateColumns: "1fr 1fr 1fr",
                marginBottom: "var(--space-4)",
              }}
            >
              <div>
                <div className="metric-label">Portfolio Value</div>
                <div
                  style={{
                    fontSize: "var(--text-base)",
                    fontWeight: 600,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {fmtCurrency(preview.total_value)}
                </div>
              </div>
              <div>
                <div className="metric-label">Trades</div>
                <div
                  style={{
                    fontSize: "var(--text-base)",
                    fontWeight: 600,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {preview.trade_count}
                </div>
              </div>
              <div>
                <div className="metric-label">Est. Cost</div>
                <div
                  style={{
                    fontSize: "var(--text-base)",
                    fontWeight: 600,
                    color: "var(--color-yellow)",
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {fmtCurrency(preview.estimated_total_cost)}
                  <span
                    style={{
                      fontSize: "var(--text-xs)",
                      marginLeft: "var(--space-1)",
                      color: "var(--color-text-dim)",
                    }}
                  >
                    ({preview.cost_pct_of_value}%)
                  </span>
                </div>
              </div>
            </div>

            {preview.trades.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Side</th>
                      <th>Current</th>
                      <th>Target</th>
                      <th>Delta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.trades.map((t) => (
                      <tr key={t.symbol}>
                        <td
                          style={{
                            fontWeight: 600,
                            color: "var(--color-accent)",
                          }}
                        >
                          {t.symbol}
                        </td>
                        <td>
                          <span
                            className={`badge ${t.side === "BUY" ? "badge-buy" : "badge-sell"}`}
                          >
                            {t.side}
                          </span>
                        </td>
                        <td style={{ fontVariantNumeric: "tabular-nums" }}>
                          {fmtCurrency(t.current_value)}
                        </td>
                        <td style={{ fontVariantNumeric: "tabular-nums" }}>
                          {fmtCurrency(t.target_value)}
                        </td>
                        <td
                          style={{
                            fontVariantNumeric: "tabular-nums",
                            fontWeight: 500,
                            color:
                              t.delta >= 0
                                ? "var(--color-green)"
                                : "var(--color-red)",
                          }}
                        >
                          {t.delta >= 0 ? "+" : ""}
                          {fmtCurrency(t.delta)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div
                className="state-banner state-empty"
                style={{ marginBottom: 0 }}
              >
                Portfolio is already balanced. No trades needed.
              </div>
            )}
          </>
        )}

        <div className="modal-footer">
          {execResult ? (
            <button className="btn btn-primary" onClick={onClose}>
              Done
            </button>
          ) : (
            <>
              <button className="btn" onClick={onClose}>
                Cancel
              </button>
              <button
                className="btn-danger"
                onClick={handleExecute}
                disabled={
                  executing || loading || !preview || preview.trade_count === 0
                }
              >
                {executing ? "Executing..." : "Execute Rebalance"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function RebalanceButton({ portfolioId }: { portfolioId: string }) {
  const [open, setOpen] = useState(false);
  const [targetWeights, setTargetWeights] = useState<Record<
    string,
    number
  > | null>(null);
  const [loadingWeights, setLoadingWeights] = useState(false);
  const [weightError, setWeightError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchWeights = useCallback(async () => {
    setLoadingWeights(true);
    setWeightError(null);
    try {
      const { data } = await api.get("/strategy/portfolio");
      if (!data || data.length === 0) {
        setWeightError(
          "No strategy portfolio found. Run the strategy first."
        );
        return;
      }
      const weights: Record<string, number> = {};
      for (const p of data) {
        weights[String(p.instrument_id)] = p.target_weight;
      }
      setTargetWeights(weights);
      setOpen(true);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to fetch strategy weights";
      setWeightError(msg);
    } finally {
      setLoadingWeights(false);
    }
  }, []);

  const signalDate = new Date().toISOString().slice(0, 10);

  return (
    <div className="card">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-4)",
        }}
      >
        <div>
          <h3
            style={{
              fontSize: "var(--text-base)",
              fontWeight: 600,
              marginBottom: "var(--space-1)",
            }}
          >
            Rebalance Portfolio
          </h3>
          <p
            style={{
              fontSize: "var(--text-sm)",
              color: "var(--color-text-dim)",
            }}
          >
            Execute trades to match the latest strategy target weights.
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={fetchWeights}
          disabled={loadingWeights}
        >
          {loadingWeights ? "Loading..." : "Rebalance"}
        </button>
      </div>
      {weightError && (
        <div
          className="state-banner state-error"
          style={{ marginTop: "var(--space-3)", marginBottom: 0 }}
        >
          {weightError}
        </div>
      )}
      {open && targetWeights && (
        <RebalanceDialog
          key={refreshKey}
          portfolioId={portfolioId}
          targetWeights={targetWeights}
          signalDate={signalDate}
          onClose={() => setOpen(false)}
          onExecuted={() => setRefreshKey((k) => k + 1)}
        />
      )}
    </div>
  );
}

const DEFAULT_PORTFOLIO_ID = "default";

function Paper() {
  const [portfolioId] = useState<string>(DEFAULT_PORTFOLIO_ID);
  const {
    data: holdings,
    error: holdingsErr,
    isLoading: holdingsLoading,
    refetch: refetchHoldings,
  } = usePaperHoldings(portfolioId);
  const {
    data: pnl,
    error: pnlErr,
    isLoading: pnlLoading,
    refetch: refetchPnl,
  } = usePaperPnl(portfolioId);

  const isLoading = holdingsLoading || pnlLoading;
  const error = holdingsErr || pnlErr;

  return (
    <div className="page">
      <h2>Paper Portfolio</h2>

      {isLoading && <PaperSkeleton />}

      {error && (
        <ErrorMessage
          message={`Failed to load portfolio data: ${error}`}
          onRetry={() => { refetchHoldings(); refetchPnl(); }}
        />
      )}

      {!isLoading && !error && !pnl && !holdings && (
        <div className="state-banner state-empty">
          <div className="state-empty-icon">{"\uD83D\uDCBC"}</div>
          <div className="state-empty-title">No portfolio data</div>
          <div className="state-empty-desc">
            Initialize a paper portfolio from the Signals page to start tracking performance.
          </div>
        </div>
      )}

      {!isLoading && !error && pnl && (
        <>
          <PortfolioSummary pnl={pnl} />
          <RebalanceButton portfolioId={portfolioId} />
          <HoldingsTable holdings={holdings || []} />
          <button
            className="btn-secondary"
            onClick={() => window.open(`/api/reports/portfolio/1/csv`, "_blank")}
            style={{ marginTop: "var(--space-4)" }}
          >
            Export CSV
          </button>
          <OrderHistory />
        </>
      )}
    </div>
  );
}

export default Paper;
