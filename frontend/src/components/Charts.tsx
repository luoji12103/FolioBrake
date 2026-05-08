import { useState, useEffect } from "react";
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
  AreaChart, Area, BarChart, Bar, Brush,
} from "recharts";

function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" && window.innerWidth <= breakpoint
  );
  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [breakpoint]);
  return isMobile;
}

interface EquityChartProps {
  data: { date: string; value: number }[];
  benchmarkData?: { date: string; value: number }[];
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "var(--color-surface-overlay)",
      border: "1px solid var(--color-border)",
      borderRadius: "var(--radius-md)",
      padding: "10px 14px",
      fontSize: "var(--text-sm)",
      boxShadow: "var(--shadow-md)",
    }}>
      <div style={{ color: "var(--color-text-dim)", marginBottom: 4, fontSize: "var(--text-xs)" }}>{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} style={{ color: p.color, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
          {p.name}: {typeof p.value === "number" ? p.value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : p.value}
        </div>
      ))}
    </div>
  );
}

export function EquityChart({ data, benchmarkData }: EquityChartProps) {
  const isMobile = useIsMobile();
  const startValue = data[0]?.value || 100000;
  return (
    <ResponsiveContainer width="100%" height={isMobile ? 240 : 350}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
        <XAxis dataKey="date" stroke="var(--color-text-dim)" fontSize={isMobile ? 10 : 11} tickLine={false} axisLine={false} />
        <YAxis stroke="var(--color-text-dim)" fontSize={isMobile ? 10 : 11} tickLine={false} axisLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={startValue} stroke="var(--color-text-dim)" strokeDasharray="5 5" strokeWidth={1} />
        <defs>
          <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#5b9aff" stopOpacity={0.25} />
            <stop offset="100%" stopColor="#5b9aff" stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="value" name="Portfolio" stroke="#5b9aff" fill="url(#equityGrad)" strokeWidth={2} />
        {benchmarkData && (
          <Area type="monotone" dataKey="value" name="Benchmark" data={benchmarkData} stroke="var(--color-text-dim)" fill="none" strokeWidth={1} strokeDasharray="4 4" />
        )}
        {!isMobile && <Brush dataKey="date" height={30} stroke="var(--color-border)" fill="var(--color-surface)" />}
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface DrawdownChartProps {
  data: { date: string; drawdown: number }[];
}

export function DrawdownChart({ data }: DrawdownChartProps) {
  const isMobile = useIsMobile();
  return (
    <ResponsiveContainer width="100%" height={isMobile ? 150 : 200}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
        <XAxis dataKey="date" stroke="var(--color-text-dim)" fontSize={isMobile ? 10 : 11} tickLine={false} axisLine={false} />
        <YAxis stroke="var(--color-text-dim)" fontSize={isMobile ? 10 : 11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v.toFixed(1)}%`} unit="%" />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={0} stroke="var(--color-text-dim)" strokeDasharray="3 3" />
        <defs>
          <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f87171" stopOpacity={0} />
            <stop offset="100%" stopColor="#f87171" stopOpacity={0.2} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="drawdown" name="Drawdown" stroke="#f87171" fill="url(#ddGrad)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface WeightBarChartProps {
  data: { symbol: string; target_weight: number }[];
}

export function WeightBarChart({ data }: WeightBarChartProps) {
  const isMobile = useIsMobile();
  return (
    <ResponsiveContainer width="100%" height={isMobile ? 160 : 200}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
        <XAxis dataKey="symbol" stroke="var(--color-text-dim)" fontSize={isMobile ? 10 : 12} axisLine={false} tickLine={false} />
        <YAxis stroke="var(--color-text-dim)" fontSize={isMobile ? 10 : 11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v.toFixed(1)}%`} unit="%" />
        <Tooltip content={<CustomTooltip />} />
        <defs>
          <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#5b9aff" stopOpacity={1} />
            <stop offset="100%" stopColor="#5b9aff" stopOpacity={0.6} />
          </linearGradient>
        </defs>
        <Bar dataKey="target_weight" name="Weight" fill="url(#barGrad)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface RollingMetric {
  date: string;
  sharpe: number;
  volatility: number;
  max_drawdown: number;
}

export function RollingMetricsChart({ data }: { data: RollingMetric[] }) {
  const isMobile = useIsMobile();
  return (
    <ResponsiveContainer width="100%" height={isMobile ? 180 : 250}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
        <XAxis dataKey="date" stroke="var(--color-text-dim)" fontSize={isMobile ? 10 : 11} tickLine={false} axisLine={false} />
        <YAxis stroke="var(--color-text-dim)" fontSize={isMobile ? 10 : 11} tickLine={false} axisLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Area type="monotone" dataKey="sharpe" name="Sharpe" stroke="#5b9aff" fill="#5b9aff10" strokeWidth={2} />
        <Area type="monotone" dataKey="volatility" name="Volatility" stroke="#fbbf24" fill="none" strokeWidth={1} strokeDasharray="4 4" />
        <Area type="monotone" dataKey="max_drawdown" name="Max DD" stroke="#f87171" fill="none" strokeWidth={1} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface RiskTimelinePoint {
  date: string;
  state: number;
}

const RISK_COLORS: Record<number, string> = { 0: "#3ae0a0", 1: "#fbbf24", 2: "#fb923c", 3: "#f87171" };
const RISK_LABELS: Record<number, string> = { 0: "NORMAL", 1: "CAUTION", 2: "DEFENSIVE", 3: "HALT" };

export function RiskTimelineChart({ data }: { data: RiskTimelinePoint[] }) {
  const isMobile = useIsMobile();
  return (
    <ResponsiveContainer width="100%" height={isMobile ? 90 : 120}>
      <BarChart data={data} barCategoryGap={0}>
        <XAxis dataKey="date" stroke="var(--color-text-dim)" fontSize={10} tickLine={false} axisLine={false} />
        <Tooltip
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const state = payload[0]?.value as number;
            return (
              <div style={{
                background: "var(--color-surface-overlay)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "8px 12px",
                fontSize: "var(--text-xs)",
                boxShadow: "var(--shadow-md)",
              }}>
                <div style={{ color: "var(--color-text-dim)" }}>{label}</div>
                <div style={{ color: RISK_COLORS[state], fontWeight: 600 }}>
                  {RISK_LABELS[state] || "?"}
                </div>
              </div>
            );
          }}
        />
        <Bar dataKey="state" name="Risk" radius={[2, 2, 0, 0]}>
          {data.map((entry, idx) => (
            <rect key={idx} fill={RISK_COLORS[entry.state] || "#4e5270"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
