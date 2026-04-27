import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { BacktestPanel } from "./BacktestPanel";
import { uiCopy } from "../../shared/i18n";

const backtestResponse = {
  simulationId: "backtest_001",
  analysisRequestId: "analysis_001",
  market: "KR",
  symbol: "005930",
  entryAt: "2026-04-22T15:30:00+09:00",
  exitAt: "2026-04-24T15:30:00+09:00",
  entryPrice: 70000,
  exitPrice: 72000,
  quantity: 10,
  grossReturnPct: 2.86,
  grossPnl: 20000,
  maxDrawdownPct: 0,
  source: "seeded_local_fixture",
  equityCurve: [
    {
      timestamp: "2026-04-22T15:30:00+09:00",
      price: 70000,
      value: 700000,
      returnPct: 0,
    },
    {
      timestamp: "2026-04-23T15:30:00+09:00",
      price: 71000,
      value: 710000,
      returnPct: 1.43,
    },
    {
      timestamp: "2026-04-24T15:30:00+09:00",
      price: 72000,
      value: 720000,
      returnPct: 2.86,
    },
  ],
} as const;

describe("BacktestPanel", () => {
  it("runs a seeded simulation and renders the PnL graph", async () => {
    const onRunBacktest = vi.fn().mockResolvedValue(backtestResponse);

    render(<BacktestPanel copy={uiCopy.en.backtest} onRunBacktest={onRunBacktest} />);

    fireEvent.click(screen.getByRole("button", { name: "Run PnL" }));

    await screen.findByText("20,000 KRW");

    expect(onRunBacktest).toHaveBeenCalledWith({
      market: "KR",
      symbol: "005930",
      entryAt: "2026-04-22T15:30:00+09:00",
      exitAt: "2026-04-24T15:30:00+09:00",
      quantity: 10,
      analysisRequestId: null,
    });
    expect(screen.getByRole("img", { name: "PnL equity curve" })).toBeInTheDocument();
    expect(screen.getByText("+2.86%")).toBeInTheDocument();
  });
});
