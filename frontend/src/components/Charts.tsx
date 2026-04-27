import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar,
} from "recharts";

interface EquityChartProps {
  data: { date: string; total_value: number }[];
}

export function EquityChart({ data }: EquityChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
        <XAxis dataKey="date" stroke="#8b8fa3" fontSize={12} />
        <YAxis stroke="#8b8fa3" fontSize={12} />
        <Tooltip
          contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a", borderRadius: 8 }}
          labelStyle={{ color: "#e4e6ef" }}
        />
        <Area type="monotone" dataKey="total_value" stroke="#4f8cff" fill="#4f8cff20" />
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
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
        <XAxis dataKey="date" stroke="#8b8fa3" fontSize={12} />
        <YAxis stroke="#8b8fa3" fontSize={12} />
        <Tooltip
          contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a", borderRadius: 8 }}
        />
        <Area type="monotone" dataKey="drawdown" stroke="#f87171" fill="#f8717120" />
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
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
        <XAxis dataKey="symbol" stroke="#8b8fa3" fontSize={12} />
        <YAxis stroke="#8b8fa3" fontSize={12} />
        <Tooltip
          contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a", borderRadius: 8 }}
        />
        <Bar dataKey="target_weight" fill="#4f8cff" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
