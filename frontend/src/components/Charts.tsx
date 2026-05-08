import { useState, useEffect, useRef, useCallback } from "react";
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
  ReferenceArea, AreaChart, Area, BarChart, Bar, Brush,
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

function useChartZoom() {
  const [refAreaLeft, setRefAreaLeft] = useState<string | null>(null);
  const [refAreaRight, setRefAreaRight] = useState<string | null>(null);
  const [zoomDomain, setZoomDomain] = useState<{ left: string; right: string } | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);

  const onMouseDown = useCallback((e: any) => {
    if (e?.activeLabel) {
      setRefAreaLeft(e.activeLabel);
      setIsSelecting(true);
    }
  }, []);

  const onMouseMove = useCallback((e: any) => {
    if (isSelecting && e?.activeLabel) {
      setRefAreaRight(e.activeLabel);
    }
  }, [isSelecting]);

  const onMouseUp = useCallback(() => {
    if (refAreaLeft && refAreaRight && refAreaLeft !== refAreaRight) {
      const [left, right] = refAreaLeft < refAreaRight
        ? [refAreaLeft, refAreaRight]
        : [refAreaRight, refAreaLeft];
      setZoomDomain({ left, right });
    }
    setRefAreaLeft(null);
    setRefAreaRight(null);
    setIsSelecting(false);
  }, [refAreaLeft, refAreaRight]);

  const resetZoom = useCallback(() => {
    setZoomDomain(null);
    setRefAreaLeft(null);
    setRefAreaRight(null);
    setIsSelecting(false);
  }, []);

  return {
    refAreaLeft,
    refAreaRight,
    zoomDomain,
    isZoomed: zoomDomain !== null,
    onMouseDown,
    onMouseMove,
    onMouseUp,
    resetZoom,
  };
}

interface TooltipEntry {
  name: string;
  value: number | string;
  color: string;
  dataKey: string;
  payload?: Record<string, any>;
}

interface EnhancedTooltipProps {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
  currency?: boolean;
  percentage?: boolean;
}

function EnhancedTooltip({
  active, payload, label, currency, percentage,
}: EnhancedTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-header">{label}</div>
      <div className="chart-tooltip-body">
        {payload.map((p, i) => {
          const val = typeof p.value === "number" ? p.value : Number(p.value);
          const formatted = currency
            ? `$${val.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
            : percentage
              ? `${val.toFixed(2)}%`
              : typeof p.value === "number"
                ? p.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                : p.value;

          return (
            <div key={i} className="chart-tooltip-row">
              <span className="chart-tooltip-dot" style={{ background: p.color }} />
              <span className="chart-tooltip-name">{p.name}</span>
              <span className="chart-tooltip-value" style={{ color: p.color }}>{formatted}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DrawdownTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const val = payload[0]?.value ?? 0;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-header">{label}</div>
      <div className="chart-tooltip-body">
        <div className="chart-tooltip-row">
          <span className="chart-tooltip-dot" style={{ background: "#f87171" }} />
          <span className="chart-tooltip-name">Drawdown</span>
          <span className="chart-tooltip-value chart-tooltip-value--red">
            {typeof val === "number" ? `${val.toFixed(2)}%` : val}
          </span>
        </div>
      </div>
    </div>
  );
}

interface ChartToolbarProps {
  isZoomed: boolean;
  onResetZoom: () => void;
  onScreenshot?: () => void;
}

function ChartToolbar({ isZoomed, onResetZoom, onScreenshot }: ChartToolbarProps) {
  return (
    <div className="chart-toolbar">
      {isZoomed && (
        <button className="chart-toolbar-btn" onClick={onResetZoom} title="Reset zoom">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10" /><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          <span>Reset</span>
        </button>
      )}
      {onScreenshot && (
        <button className="chart-toolbar-btn" onClick={onScreenshot} title="Download chart as image">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          <span>Save</span>
        </button>
      )}
    </div>
  );
}

function downloadChartAsPNG(containerRef: React.RefObject<HTMLDivElement | null>, filename: string) {
  if (!containerRef.current) return;
  const svgEl = containerRef.current.querySelector("svg");
  if (!svgEl) return;

  const svgData = new XMLSerializer().serializeToString(svgEl);
  const svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(svgBlob);

  const img = new Image();
  img.onload = () => {
    const scale = 2;
    const canvas = document.createElement("canvas");
    canvas.width = svgEl.clientWidth * scale;
    canvas.height = svgEl.clientHeight * scale;
    const ctx = canvas.getContext("2d")!;
    ctx.scale(scale, scale);

    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--color-surface").trim() || "#12141f";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.drawImage(img, 0, 0, svgEl.clientWidth, svgEl.clientHeight);
    URL.revokeObjectURL(url);

    const pngUrl = canvas.toDataURL("image/png");
    const link = document.createElement("a");
    link.download = filename;
    link.href = pngUrl;
    link.click();
  };
  img.src = url;
}

interface EquityChartProps {
  data: { date: string; value: number }[];
  benchmarkData?: { date: string; value: number }[];
}

export function EquityChart({ data, benchmarkData }: EquityChartProps) {
  const isMobile = useIsMobile();
  const containerRef = useRef<HTMLDivElement>(null);
  const zoom = useChartZoom();
  const startValue = data[0]?.value || 100000;

  const displayData = zoom.zoomDomain
    ? data.filter((d) => d.date >= zoom.zoomDomain!.left && d.date <= zoom.zoomDomain!.right)
    : data;

  const displayBenchmark = zoom.zoomDomain && benchmarkData
    ? benchmarkData.filter((d) => d.date >= zoom.zoomDomain!.left && d.date <= zoom.zoomDomain!.right)
    : benchmarkData;

  const handleScreenshot = useCallback(() => {
    downloadChartAsPNG(containerRef, "equity-chart.png");
  }, []);

  return (
    <div className="chart-container" ref={containerRef}>
      <ChartToolbar isZoomed={zoom.isZoomed} onResetZoom={zoom.resetZoom} onScreenshot={handleScreenshot} />
      <ResponsiveContainer width="100%" height={isMobile ? 240 : 350}>
        <AreaChart
          data={displayData}
          onMouseDown={!isMobile ? zoom.onMouseDown : undefined}
          onMouseMove={!isMobile ? zoom.onMouseMove : undefined}
          onMouseUp={!isMobile ? zoom.onMouseUp : undefined}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
          <XAxis
            dataKey="date"
            stroke="var(--color-text-dim)"
            fontSize={isMobile ? 10 : 11}
            tickLine={false}
            axisLine={false}
            allowDataOverflow
          />
          <YAxis
            stroke="var(--color-text-dim)"
            fontSize={isMobile ? 10 : 11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
            domain={["auto", "auto"]}
            allowDataOverflow
          />
          <Tooltip content={<EnhancedTooltip currency />} />
          <ReferenceLine y={startValue} stroke="var(--color-text-dim)" strokeDasharray="5 5" strokeWidth={1} />
          <defs>
            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#5b9aff" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#5b9aff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area type="monotone" dataKey="value" name="Portfolio" stroke="#5b9aff" fill="url(#equityGrad)" strokeWidth={2} animationDuration={800} />
          {displayBenchmark && (
            <Area type="monotone" dataKey="value" name="Benchmark" data={displayBenchmark} stroke="var(--color-text-dim)" fill="none" strokeWidth={1} strokeDasharray="4 4" />
          )}
          {!isMobile && (
            <Brush
              dataKey="date"
              height={30}
              stroke="var(--color-border)"
              fill="var(--color-surface)"
              travellerWidth={8}
            />
          )}
          {zoom.refAreaLeft && zoom.refAreaRight && (
            <ReferenceArea
              x1={zoom.refAreaLeft}
              x2={zoom.refAreaRight}
              strokeOpacity={0.3}
              stroke="var(--color-accent)"
              fill="var(--color-accent)"
              fillOpacity={0.1}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

interface DrawdownChartProps {
  data: { date: string; drawdown: number }[];
}

export function DrawdownChart({ data }: DrawdownChartProps) {
  const isMobile = useIsMobile();
  const containerRef = useRef<HTMLDivElement>(null);
  const zoom = useChartZoom();

  const displayData = zoom.zoomDomain
    ? data.filter((d) => d.date >= zoom.zoomDomain!.left && d.date <= zoom.zoomDomain!.right)
    : data;

  const handleScreenshot = useCallback(() => {
    downloadChartAsPNG(containerRef, "drawdown-chart.png");
  }, []);

  return (
    <div className="chart-container" ref={containerRef}>
      <ChartToolbar isZoomed={zoom.isZoomed} onResetZoom={zoom.resetZoom} onScreenshot={handleScreenshot} />
      <ResponsiveContainer width="100%" height={isMobile ? 150 : 200}>
        <AreaChart
          data={displayData}
          onMouseDown={!isMobile ? zoom.onMouseDown : undefined}
          onMouseMove={!isMobile ? zoom.onMouseMove : undefined}
          onMouseUp={!isMobile ? zoom.onMouseUp : undefined}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
          <XAxis
            dataKey="date"
            stroke="var(--color-text-dim)"
            fontSize={isMobile ? 10 : 11}
            tickLine={false}
            axisLine={false}
            allowDataOverflow
          />
          <YAxis
            stroke="var(--color-text-dim)"
            fontSize={isMobile ? 10 : 11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v.toFixed(1)}%`}
            domain={["auto", "auto"]}
            allowDataOverflow
          />
          <Tooltip content={<DrawdownTooltip />} />
          <ReferenceLine y={0} stroke="var(--color-text-dim)" strokeDasharray="3 3" />
          <defs>
            <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f87171" stopOpacity={0} />
              <stop offset="100%" stopColor="#f87171" stopOpacity={0.2} />
            </linearGradient>
          </defs>
          <Area type="monotone" dataKey="drawdown" name="Drawdown" stroke="#f87171" fill="url(#ddGrad)" strokeWidth={2} animationDuration={800} />
          {!isMobile && (
            <Brush
              dataKey="date"
              height={24}
              stroke="var(--color-border)"
              fill="var(--color-surface)"
              travellerWidth={8}
            />
          )}
          {zoom.refAreaLeft && zoom.refAreaRight && (
            <ReferenceArea
              x1={zoom.refAreaLeft}
              x2={zoom.refAreaRight}
              strokeOpacity={0.3}
              stroke="var(--color-accent)"
              fill="var(--color-accent)"
              fillOpacity={0.1}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

interface WeightBarChartProps {
  data: { symbol: string; target_weight: number }[];
}

export function WeightBarChart({ data }: WeightBarChartProps) {
  const isMobile = useIsMobile();
  const containerRef = useRef<HTMLDivElement>(null);

  const handleScreenshot = useCallback(() => {
    downloadChartAsPNG(containerRef, "weights-chart.png");
  }, []);

  return (
    <div className="chart-container" ref={containerRef}>
      <ChartToolbar isZoomed={false} onResetZoom={() => {}} onScreenshot={handleScreenshot} />
      <ResponsiveContainer width="100%" height={isMobile ? 160 : 200}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
          <XAxis
            dataKey="symbol"
            stroke="var(--color-text-dim)"
            fontSize={isMobile ? 10 : 12}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            stroke="var(--color-text-dim)"
            fontSize={isMobile ? 10 : 11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v.toFixed(1)}%`}
          />
          <Tooltip content={<EnhancedTooltip percentage />} />
          <defs>
            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#5b9aff" stopOpacity={1} />
              <stop offset="100%" stopColor="#5b9aff" stopOpacity={0.6} />
            </linearGradient>
          </defs>
          <Bar dataKey="target_weight" name="Weight" fill="url(#barGrad)" radius={[4, 4, 0, 0]} animationDuration={600} />
        </BarChart>
      </ResponsiveContainer>
    </div>
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
  const containerRef = useRef<HTMLDivElement>(null);
  const zoom = useChartZoom();

  const displayData = zoom.zoomDomain
    ? data.filter((d) => d.date >= zoom.zoomDomain!.left && d.date <= zoom.zoomDomain!.right)
    : data;

  const handleScreenshot = useCallback(() => {
    downloadChartAsPNG(containerRef, "rolling-metrics-chart.png");
  }, []);

  return (
    <div className="chart-container" ref={containerRef}>
      <ChartToolbar isZoomed={zoom.isZoomed} onResetZoom={zoom.resetZoom} onScreenshot={handleScreenshot} />
      <ResponsiveContainer width="100%" height={isMobile ? 180 : 250}>
        <AreaChart
          data={displayData}
          onMouseDown={!isMobile ? zoom.onMouseDown : undefined}
          onMouseMove={!isMobile ? zoom.onMouseMove : undefined}
          onMouseUp={!isMobile ? zoom.onMouseUp : undefined}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
          <XAxis
            dataKey="date"
            stroke="var(--color-text-dim)"
            fontSize={isMobile ? 10 : 11}
            tickLine={false}
            axisLine={false}
            allowDataOverflow
          />
          <YAxis
            stroke="var(--color-text-dim)"
            fontSize={isMobile ? 10 : 11}
            tickLine={false}
            axisLine={false}
            allowDataOverflow
          />
          <Tooltip content={<EnhancedTooltip />} />
          <Area type="monotone" dataKey="sharpe" name="Sharpe" stroke="#5b9aff" fill="#5b9aff10" strokeWidth={2} animationDuration={800} />
          <Area type="monotone" dataKey="volatility" name="Volatility" stroke="#fbbf24" fill="none" strokeWidth={1} strokeDasharray="4 4" />
          <Area type="monotone" dataKey="max_drawdown" name="Max DD" stroke="#f87171" fill="none" strokeWidth={1} />
          {!isMobile && (
            <Brush
              dataKey="date"
              height={24}
              stroke="var(--color-border)"
              fill="var(--color-surface)"
              travellerWidth={8}
            />
          )}
          {zoom.refAreaLeft && zoom.refAreaRight && (
            <ReferenceArea
              x1={zoom.refAreaLeft}
              x2={zoom.refAreaRight}
              strokeOpacity={0.3}
              stroke="var(--color-accent)"
              fill="var(--color-accent)"
              fillOpacity={0.1}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
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
  const containerRef = useRef<HTMLDivElement>(null);

  const handleScreenshot = useCallback(() => {
    downloadChartAsPNG(containerRef, "risk-timeline-chart.png");
  }, []);

  return (
    <div className="chart-container" ref={containerRef}>
      <ChartToolbar isZoomed={false} onResetZoom={() => {}} onScreenshot={handleScreenshot} />
      <ResponsiveContainer width="100%" height={isMobile ? 90 : 120}>
        <BarChart data={data} barCategoryGap={0}>
          <XAxis dataKey="date" stroke="var(--color-text-dim)" fontSize={10} tickLine={false} axisLine={false} />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null;
              const state = payload[0]?.value as number;
              return (
                <div className="chart-tooltip">
                  <div className="chart-tooltip-header">{label}</div>
                  <div className="chart-tooltip-body">
                    <div className="chart-tooltip-row">
                      <span className="chart-tooltip-dot" style={{ background: RISK_COLORS[state] }} />
                      <span className="chart-tooltip-name">Risk</span>
                      <span className="chart-tooltip-value" style={{ color: RISK_COLORS[state] }}>
                        {RISK_LABELS[state] || "?"}
                      </span>
                    </div>
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
    </div>
  );
}
