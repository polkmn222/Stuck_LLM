import { FormEvent, useState } from "react";

import type { BacktestRequest, BacktestResult, EquityPoint } from "../../shared/types";
import type { UiCopy } from "../../shared/i18n";

interface BacktestPanelProps {
  copy: UiCopy["backtest"];
  onRunBacktest: (request: BacktestRequest) => Promise<BacktestResult>;
}

const DEFAULT_REQUEST: BacktestRequest = {
  analysisRequestId: null,
  market: "KR",
  symbol: "005930",
  entryAt: "2026-04-22T15:30:00+09:00",
  exitAt: "2026-04-24T15:30:00+09:00",
  quantity: 10,
};

function currencyFor(market: BacktestResult["market"]): string {
  return market === "KR" ? "KRW" : "USD";
}

function formatMoney(value: number, currency: string): string {
  const maximumFractionDigits = currency === "KRW" ? 0 : 2;
  return `${value.toLocaleString("en-US", { maximumFractionDigits })} ${currency}`;
}

function formatSignedPercent(value: number): string {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function curvePoints(points: EquityPoint[]): string {
  if (points.length === 0) {
    return "";
  }

  const width = 220;
  const height = 88;
  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return points
    .map((point, index) => {
      const x = points.length === 1 ? width / 2 : (index / (points.length - 1)) * width;
      const y = height - ((point.value - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function BacktestPanel({ copy, onRunBacktest }: BacktestPanelProps) {
  const [request, setRequest] = useState<BacktestRequest>(DEFAULT_REQUEST);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsRunning(true);
    setError(null);

    try {
      setResult(await onRunBacktest(request));
    } catch {
      setError(copy.error);
    } finally {
      setIsRunning(false);
    }
  }

  const currency = result ? currencyFor(result.market) : "KRW";

  return (
    <section className="panel pnl-panel" aria-label={copy.aria}>
      <div className="panel-heading">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2>{copy.title}</h2>
      </div>

      <form className="pnl-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>{copy.symbol}</span>
          <input
            aria-label={copy.symbol}
            onChange={(event) =>
              setRequest((current) => ({ ...current, symbol: event.target.value.toUpperCase() }))
            }
            value={request.symbol}
          />
        </label>
        <button disabled={isRunning} type="submit">
          {copy.run}
        </button>
      </form>

      {result ? (
        <div className="pnl-result">
          <div className="pnl-metric">
            <span>{copy.grossPnl}</span>
            <strong>{formatMoney(result.grossPnl, currency)}</strong>
          </div>
          <div className="pnl-mini-grid">
            <span>{formatSignedPercent(result.grossReturnPct)}</span>
            <span>
              {copy.maxDrawdown} {formatSignedPercent(result.maxDrawdownPct)}
            </span>
          </div>
          <svg
            aria-label={copy.chartLabel}
            className="pnl-chart"
            role="img"
            viewBox="0 0 220 88"
          >
            <polyline points={curvePoints(result.equityCurve)} />
          </svg>
        </div>
      ) : (
        <p className="muted-copy">{copy.empty}</p>
      )}
      {error ? <p className="inline-error">{error}</p> : null}
    </section>
  );
}
