import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
  AreaChart, Area, BarChart, Bar, Brush,
} from "recharts";

interface EquityChartProps {
  data: { date: string; value: number }[];
  benchmarkData?: { date: string; value: number }[];
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "10px 14px", fontSize: 13 }}>
      <div style={{ color: "var(--color-text-muted)", marginBottom: 4, fontSize: 12 }}>{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {typeof p.value === "number" ? p.value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : p.value}
        </div>
      ))}
    </div>
  );
}

export function EquityChart({ data, benchmarkData }: EquityChartProps) {
  const startValue = data[0]?.value || 100000;
  return (
    <ResponsiveContainer width="100%" height={350}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={11} tickLine={false} />
        <YAxis stroke="var(--color-text-muted)" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={startValue} stroke="var(--color-text-muted)" strokeDasharray="5 5" strokeWidth={1} />
        <Area type="monotone" dataKey="value" name="Portfolio" stroke="#4f8cff" fill="#4f8cff20" strokeWidth={2} />
        {benchmarkData && (
          <Area type="monotone" dataKey="value" name="Benchmark" data={benchmarkData} stroke="#8b8fa3" fill="none" strokeWidth={1} strokeDasharray="4 4" />
        )}
        <Brush dataKey="date" height={30} stroke="var(--color-border)" fill="var(--color-surface)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface DrawdownChartProps {
  data: { date: string; drawdown: number }[];
}

export function DrawdownChart({ data }: DrawdownChartProps) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={11} tickLine={false} />
        <YAxis stroke="var(--color-text-muted)" fontSize={11} tickLine={false} tickFormatter={(v) => `${v.toFixed(1)}%`} unit="%" />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={0} stroke="var(--color-text-muted)" strokeWidth={1} />
        <Area type="monotone" dataKey="drawdown" name="Drawdown" stroke="#f87171" fill="#f8717120" strokeWidth={1} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface WeightBarChartProps {
  data: { symbol: string; target_weight: number }[];
}

export function WeightBarChart({ data }: WeightBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis dataKey="symbol" stroke="var(--color-text-muted)" fontSize={12} />
        <YAxis stroke="var(--color-text-muted)" fontSize={11} tickLine={false} tickFormatter={(v) => `${v.toFixed(1)}%`} unit="%" />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="target_weight" name="Weight" fill="#4f8cff" radius={[4, 4, 0, 0]} />
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
  return (
    <ResponsiveContainer width="100%" height={250}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={11} tickLine={false} />
        <YAxis stroke="var(--color-text-muted)" fontSize={11} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Area type="monotone" dataKey="sharpe" name="Sharpe" stroke="#4f8cff" fill="#4f8cff10" strokeWidth={2} />
        <Area type="monotone" dataKey="volatility" name="Volatility" stroke="#fbbf24" fill="none" strokeWidth={1} strokeDasharray="4 4" />
        <Area type="monotone" dataKey="max_drawdown" name="Max DD" stroke="#f87171" fill="none" strokeWidth={1} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface RiskTimelinePoint {
  date: string;
  state: number;  // 0=NORMAL, 1=CAUTION, 2=DEFENSIVE, 3=HALT
}

const RISK_COLORS: Record<number, string> = { 0: "#34d399", 1: "#fbbf24", 2: "#f97316", 3: "#f87171" };
const RISK_LABELS: Record<number, string> = { 0: "NORMAL", 1: "CAUTION", 2: "DEFENSIVE", 3: "HALT" };

export function RiskTimelineChart({ data }: { data: RiskTimelinePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={120}>
      <BarChart data={data} barCategoryGap={0}>
        <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={10} tickLine={false} />
        <Tooltip
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const state = payload[0]?.value as number;
            return (
              <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, padding: "8px 12px", fontSize: 12 }}>
                <div style={{ color: "var(--color-text-muted)" }}>{label}</div>
                <div style={{ color: RISK_COLORS[state] || "#8b8fa3", fontWeight: 600 }}>{RISK_LABELS[state] || "UNKNOWN"}</div>
              </div>
            );
          }}
        />
        <Bar dataKey="state" fill="#4f8cff" radius={[2, 2, 0, 0]}>
          {data.map((_, i) => (
            <rect key={i} fill={RISK_COLORS[data[i].state] || "#4f8cff"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
