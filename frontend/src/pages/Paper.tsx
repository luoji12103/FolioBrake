import { useState } from "react";
import { ErrorMessage } from "../components/ErrorMessage";
import { usePaperHoldings, usePaperPnl, PaperHolding } from "../api/hooks";
import "./shared.css";

/* ---- Format helpers ---- */

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

/* ---- Skeleton ---- */

function PaperSkeleton() {
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 20 }}>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="skeleton" style={{ height: 90 }} />
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

/* ---- Summary cards ---- */

function PortfolioSummary({
  pnl,
}: {
  pnl: NonNullable<ReturnType<typeof usePaperPnl>["data"]>;
}) {
  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-label">Total Value</div>
        <div className="metric-value" style={{ fontSize: 22, color: "var(--color-text)" }}>
          {fmtCurrency(pnl.total_value)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Cash</div>
        <div className="metric-value" style={{ fontSize: 22, color: "var(--color-text)" }}>
          {fmtCurrency(pnl.cash)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Invested</div>
        <div className="metric-value" style={{ fontSize: 22, color: "var(--color-text)" }}>
          {fmtCurrency(pnl.invested)}
        </div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Total P&amp;L</div>
        <div
          className={`metric-value ${pnl.total_pnl >= 0 ? "positive" : "negative"}`}
          style={{ fontSize: 22 }}
        >
          {fmtCurrency(pnl.total_pnl)}
          <span style={{ fontSize: 14, marginLeft: 6 }}>
            ({fmtPct(pnl.total_pnl_pct)})
          </span>
        </div>
      </div>
    </div>
  );
}

/* ---- Holdings table ---- */

function HoldingsTable({ holdings }: { holdings: PaperHolding[] }) {
  if (!holdings || holdings.length === 0) {
    return (
      <div className="card">
        <div className="card-title">Holdings</div>
        <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>
          No holdings in this portfolio.
        </p>
      </div>
    );
  }

  const sorted = [...holdings].sort(
    (a, b) => b.market_value - a.market_value
  );

  return (
    <div className="card">
      <div className="card-title">Holdings ({holdings.length})</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Instrument ID</th>
              <th>Quantity</th>
              <th>Avg Cost</th>
              <th>Current Price</th>
              <th>Market Value</th>
              <th>P&amp;L</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((h) => (
              <tr key={h.instrument_id}>
                <td style={{ fontWeight: 600 }}>{h.instrument_id}</td>
                <td>{h.quantity.toLocaleString()}</td>
                <td>{fmtCurrency(h.avg_cost)}</td>
                <td>{fmtCurrency(h.current_price)}</td>
                <td>{fmtCurrency(h.market_value)}</td>
                <td
                  style={{
                    color:
                      h.pnl >= 0
                        ? "var(--color-green)"
                        : "var(--color-red)",
                    fontWeight: 600,
                  }}
                >
                  {fmtCurrency(h.pnl)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---- Order history (placeholder with static data structure) ---- */

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
  /* Orders would come from an API in production — show empty state */
  const [orders] = useState<Order[]>([]);

  return (
    <div className="card">
      <div className="card-title">Order History</div>
      {orders.length === 0 ? (
        <p style={{ color: "var(--color-text-muted)", fontSize: 14 }}>
          No orders have been placed yet.
        </p>
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
                      <span
                        className={`badge ${o.action === "BUY" ? "badge-buy" : "badge-sell"}`}
                      >
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

/* ---- Apply Signal button (disabled) ---- */

function ApplySignalButton() {
  return (
    <div className="card">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
            Apply Latest Signals
          </h3>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)" }}>
            Execute trades based on the most recent weekly signals.
          </p>
        </div>
        <button className="btn btn-primary" disabled title="Coming soon">
          Apply Signal
        </button>
      </div>
    </div>
  );
}

/* ---- Page ---- */

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
          No portfolio data available. Initialize a paper portfolio to see data here.
        </div>
      )}

      {!isLoading && !error && pnl && (
        <>
          <PortfolioSummary pnl={pnl} />
          <ApplySignalButton />
          <HoldingsTable holdings={holdings || []} />
          <OrderHistory />
        </>
      )}
    </div>
  );
}

export default Paper;
