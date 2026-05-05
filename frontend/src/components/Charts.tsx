import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
  AreaChart, Area, BarChart, Bar, Brush,
} from "recharts";

interface EquityChartProps {
  data: { date: string; total_value: number }[];
  benchmarkData?: { date: string; total_value: number }[];
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
  const startValue = data[0]?.total_value || 100000;
  return (
    <ResponsiveContainer width="100%" height={350}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={11} tickLine={false} />
        <YAxis stroke="var(--color-text-muted)" fontSize={11} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={startValue} stroke="var(--color-text-muted)" strokeDasharray="5 5" strokeWidth={1} />
        <Area type="monotone" dataKey="total_value" name="Portfolio" stroke="#4f8cff" fill="#4f8cff20" strokeWidth={2} />
        {benchmarkData && (
          <Area type="monotone" dataKey="total_value" name="Benchmark" data={benchmarkData} stroke="#8b8fa3" fill="none" strokeWidth={1} strokeDasharray="4 4" />
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
