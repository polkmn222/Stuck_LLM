import { useState, type PointerEvent } from "react";

import type { MarketChartWindow, MarketQuote } from "../../shared/types";

interface MarketChartProps {
  ariaLabel?: string;
  activeWindow?: MarketChartWindow;
  availableWindows?: MarketChartWindow[];
  isWindowLoading?: boolean;
  onWindowSelect?: (window: MarketChartWindow) => void;
  quote: MarketQuote;
  variant?: "compact" | "expanded";
}

function formatCurrency(value: number, currency: string): string {
  const fractionDigits = currency === "KRW" ? 0 : 2;
  return `${value.toLocaleString("en-US", {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: fractionDigits,
  })} ${currency}`;
}

function formatPrice(quote: MarketQuote): string {
  return formatCurrency(quote.lastPrice, quote.currency);
}

function formatChange(changePct: number | null): string {
  if (changePct === null) {
    return "n/a";
  }
  const prefix = changePct > 0 ? "+" : "";
  return `${prefix}${changePct.toFixed(2)}%`;
}

function changeClassName(changePct: number | null): string {
  if (changePct === null) {
    return "is-flat";
  }
  if (changePct > 0) {
    return "is-up";
  }
  if (changePct < 0) {
    return "is-down";
  }
  return "is-flat";
}

interface ChartPoint {
  x: number;
  y: number;
  value: number;
  timestamp: string;
}

interface ChartTick {
  label: string;
  x?: number;
  y?: number;
  value?: number;
}

const CHART_WIDTH = 760;
const CHART_HEIGHT = 360;
const CHART_MARGIN = {
  top: 26,
  right: 30,
  bottom: 54,
  left: 78,
};

function chartPoints(quote: MarketQuote): ChartPoint[] {
  const values = quote.chartBars.map((bar) => bar.close);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const spread = maximum - minimum || 1;
  const maxIndex = Math.max(values.length - 1, 1);
  const plotWidth = CHART_WIDTH - CHART_MARGIN.left - CHART_MARGIN.right;
  const plotHeight = CHART_HEIGHT - CHART_MARGIN.top - CHART_MARGIN.bottom;
  const rawTimes = quote.chartBars.map((bar) => Date.parse(bar.timestamp));
  const hasValidTimes = rawTimes.every(Number.isFinite);
  const minimumTime = hasValidTimes ? Math.min(...rawTimes) : 0;
  const maximumTime = hasValidTimes ? Math.max(...rawTimes) : 0;
  const canUseTimeScale = hasValidTimes && maximumTime > minimumTime;

  return quote.chartBars.map((bar, index) => {
    const value = bar.close;
    const x = canUseTimeScale
      ? CHART_MARGIN.left + ((rawTimes[index] - minimumTime) / (maximumTime - minimumTime)) * plotWidth
      : CHART_MARGIN.left + (index / maxIndex) * plotWidth;
    const y = CHART_MARGIN.top + ((maximum - value) / spread) * plotHeight;
    return {
      value,
      timestamp: bar.timestamp,
      x,
      y,
    };
  });
}

function linePath(points: ChartPoint[]): string {
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");
}

function yAxisTicks(values: number[], currency: string): ChartTick[] {
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const spread = maximum - minimum || 1;
  const plotHeight = CHART_HEIGHT - CHART_MARGIN.top - CHART_MARGIN.bottom;
  return [0, 1, 2, 3, 4].map((index) => {
    const value = maximum - (spread / 4) * index;
    const y = CHART_MARGIN.top + ((maximum - value) / spread) * plotHeight;
    return {
      label: formatCurrency(value, currency),
      value,
      y,
    };
  });
}

function xAxisTicks(points: ChartPoint[], window: MarketChartWindow): ChartTick[] {
  if (points.length === 0) {
    return [];
  }
  const indexes = Array.from(
    new Set([
      0,
      Math.floor((points.length - 1) / 2),
      points.length - 1,
    ]),
  );
  return indexes.map((index) => ({
    label: formatAxisLabel(points[index].timestamp, window),
    x: points[index].x,
  }));
}

function nearestPoint(points: ChartPoint[], x: number): ChartPoint | null {
  if (points.length === 0) {
    return null;
  }
  return points.reduce((nearest, point) => (
    Math.abs(point.x - x) < Math.abs(nearest.x - x) ? point : nearest
  ));
}

function tooltipX(point: ChartPoint): number {
  const tooltipWidth = 134;
  const preferred = point.x + 10;
  const rightLimit = CHART_WIDTH - CHART_MARGIN.right - tooltipWidth;
  return Math.max(CHART_MARGIN.left, Math.min(preferred, rightLimit));
}

function tooltipY(point: ChartPoint): number {
  const tooltipHeight = 60;
  const preferred = point.y - tooltipHeight - 10;
  return Math.max(CHART_MARGIN.top, preferred);
}

function formatVolume(volume: number): string {
  return volume.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

function formatAxisLabel(timestamp: string, window: MarketChartWindow): string {
  const isoParts = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(timestamp);
  if (isoParts) {
    const [, year, month, day, hour, minute] = isoParts;
    if (window === "1D") {
      const hourNumber = Number(hour);
      const period = hourNumber >= 12 ? "PM" : "AM";
      const displayHour = hourNumber % 12 || 12;
      return `${displayHour}:${minute} ${period}`;
    }
    return new Date(Number(year), Number(month) - 1, Number(day)).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp.slice(0, 10);
  }
  if (window === "1D") {
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  }
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function MarketChart({
  ariaLabel,
  activeWindow,
  availableWindows = [],
  isWindowLoading = false,
  onWindowSelect,
  quote,
  variant = "expanded",
}: MarketChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<ChartPoint | null>(null);
  const closes = quote.chartBars.map((bar) => bar.close);
  const keyStats = quote.keyStats ?? [];
  const newsItems = quote.newsItems ?? [];
  if (closes.length < 2 && keyStats.length === 0 && newsItems.length === 0) {
    return null;
  }

  const points = closes.length >= 2 ? chartPoints(quote) : [];
  const path = points.length >= 2 ? linePath(points) : null;
  const startPoint = points[0] ?? null;
  const latestPoint = points[points.length - 1] ?? null;
  const ticksY = closes.length >= 2 ? yAxisTicks(closes, quote.currency) : [];
  const ticksX = points.length >= 2 ? xAxisTicks(points, quote.chartWindow) : [];
  const startLabel = startPoint ? `Start ${formatCurrency(startPoint.value, quote.currency)}` : null;
  const latestLabel = latestPoint
    ? `Latest ${formatCurrency(latestPoint.value, quote.currency)}`
    : null;
  const chartDirection = startPoint && latestPoint
    ? changeClassName(latestPoint.value - startPoint.value)
    : changeClassName(quote.changePct);
  function handlePointerMove(event: PointerEvent<SVGSVGElement>) {
    if (points.length === 0) {
      return;
    }
    const rect = event.currentTarget.getBoundingClientRect();
    const width = rect.width || CHART_WIDTH;
    const svgX = ((event.clientX - rect.left) / width) * CHART_WIDTH;
    setHoveredPoint(nearestPoint(points, svgX));
  }

  return (
    <div className={`market-chart market-chart-${variant} market-chart-${chartDirection}`}>
      {availableWindows.length ? (
        <div aria-label="Chart range" className="market-chart-window-controls">
          {availableWindows.map((window) => (
            <button
              aria-pressed={(activeWindow ?? quote.chartWindow) === window}
              disabled={isWindowLoading}
              key={window}
              onClick={() => onWindowSelect?.(window)}
              type="button"
            >
              {window}
            </button>
          ))}
        </div>
      ) : null}
      <div
        aria-label={ariaLabel ?? `${quote.name} price chart`}
        className="market-chart-visual"
        role="img"
      >
        <div className="market-chart-header">
          <div className="market-chart-identity">
            <strong>{quote.name}</strong>
            <span>{quote.symbol}</span>
          </div>
          <div className="market-chart-price">
            <strong>{formatPrice(quote)}</strong>
            <em className={changeClassName(quote.changePct)}>{formatChange(quote.changePct)}</em>
          </div>
        </div>
        <div className="market-chart-meta">
          <span>{quote.exchange}</span>
          <span>{quote.chartWindow}</span>
          <span>{quote.asOfAt}</span>
        </div>
        {path ? (
          <div className="market-chart-plot">
            <svg
              aria-hidden="true"
              focusable="false"
              onPointerLeave={() => setHoveredPoint(null)}
              onPointerMove={handlePointerMove}
              viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
            >
              {ticksY.map((tick) => (
                <g key={`y-${tick.label}-${tick.y}`}>
                  <path
                    className="market-chart-gridline"
                    d={`M ${CHART_MARGIN.left} ${tick.y?.toFixed(2)} L ${CHART_WIDTH - CHART_MARGIN.right} ${tick.y?.toFixed(2)}`}
                  />
                  <text
                    className="market-chart-y-label"
                    textAnchor="end"
                    x={CHART_MARGIN.left - 12}
                    y={(tick.y ?? 0) + 4}
                  >
                    {tick.label}
                  </text>
                </g>
              ))}
              {startPoint ? (
                <path
                  className="market-chart-start-line"
                  d={`M ${CHART_MARGIN.left} ${startPoint.y.toFixed(2)} L ${CHART_WIDTH - CHART_MARGIN.right} ${startPoint.y.toFixed(2)}`}
                />
              ) : null}
              <path className="market-chart-line-shadow" d={path} />
              <path className="market-chart-line" d={path} />
              {latestPoint ? (
                <circle
                  className="market-chart-latest-dot"
                  cx={latestPoint.x.toFixed(2)}
                  cy={latestPoint.y.toFixed(2)}
                  r="2.4"
                />
              ) : null}
              {ticksX.map((tick) => (
                <text
                  className="market-chart-x-label"
                  key={`x-${tick.label}-${tick.x}`}
                  textAnchor="middle"
                  x={tick.x}
                  y={CHART_HEIGHT - 18}
                >
                  {tick.label}
                </text>
              ))}
              <rect
                className="market-chart-hover-zone"
                height={CHART_HEIGHT - CHART_MARGIN.top - CHART_MARGIN.bottom}
                width={CHART_WIDTH - CHART_MARGIN.left - CHART_MARGIN.right}
                x={CHART_MARGIN.left}
                y={CHART_MARGIN.top}
              />
              {hoveredPoint ? (
                <g className="market-chart-tooltip">
                  <path
                    className="market-chart-hover-line"
                    d={`M ${hoveredPoint.x.toFixed(2)} ${CHART_MARGIN.top} L ${hoveredPoint.x.toFixed(2)} ${CHART_HEIGHT - CHART_MARGIN.bottom}`}
                  />
                  <rect
                    height="60"
                    rx="4"
                    width="134"
                    x={tooltipX(hoveredPoint)}
                    y={tooltipY(hoveredPoint)}
                  />
                  <text x={tooltipX(hoveredPoint) + 10} y={tooltipY(hoveredPoint) + 18}>
                    {formatAxisLabel(hoveredPoint.timestamp, quote.chartWindow)}
                  </text>
                  <path
                    className="market-chart-tooltip-swatch"
                    d={`M ${tooltipX(hoveredPoint) + 10} ${tooltipY(hoveredPoint) + 38} L ${tooltipX(hoveredPoint) + 38} ${tooltipY(hoveredPoint) + 38}`}
                  />
                  <text x={tooltipX(hoveredPoint) + 44} y={tooltipY(hoveredPoint) + 42}>
                    {`Price: ${formatCurrency(hoveredPoint.value, quote.currency)}`}
                  </text>
                </g>
              ) : null}
            </svg>
            <div className="market-chart-reference">
              {startLabel ? <span>{startLabel}</span> : null}
              {latestLabel ? <span aria-label={latestLabel}>{latestLabel}</span> : null}
            </div>
          </div>
        ) : null}
        {keyStats.length ? (
          <dl className="market-key-stats">
            {keyStats.map((stat) => (
              <div key={`${stat.label}-${stat.value}`}>
                <dt>{stat.label}</dt>
                <dd>{stat.value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
        {newsItems.length ? (
          <ul className="market-news-list">
            {newsItems.map((item) => (
              <li key={`${item.title}-${item.url ?? ""}`}>
                {item.url ? (
                  <a href={item.url} rel="noreferrer" target="_blank">
                    {item.title}
                  </a>
                ) : (
                  <strong>{item.title}</strong>
                )}
                <span>
                  {[item.source, item.publishedAt].filter(Boolean).join(" / ")}
                </span>
                {item.snippet ? <p>{item.snippet}</p> : null}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
      <table className="sr-only market-chart-table">
        <caption>{quote.name} chart data</caption>
        <thead>
          <tr>
            <th scope="col">Timestamp</th>
            <th scope="col">Close</th>
            <th scope="col">Volume</th>
          </tr>
        </thead>
        <tbody>
          {quote.chartBars.map((bar) => (
            <tr key={bar.timestamp}>
              <td>{bar.timestamp}</td>
              <td>{formatCurrency(bar.close, quote.currency)}</td>
              <td>{formatVolume(bar.volume)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
