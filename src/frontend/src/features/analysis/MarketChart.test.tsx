import { fireEvent, render, screen } from "@testing-library/react";

import { MarketChart } from "./MarketChart";
import type { MarketQuote } from "../../shared/types";

const aaplQuote: MarketQuote = {
  market: "US",
  symbol: "AAPL",
  name: "Apple Inc",
  exchange: "NASDAQ",
  currency: "USD",
  lastPrice: 270.71,
  previousClose: 267.56,
  changePct: 1.18,
  asOfAt: "2026-04-28T16:00:00-04:00",
  source: "serpapi_google_finance",
  chartWindow: "5D",
  chartBars: [
    {
      timestamp: "2026-04-23T16:00:00-04:00",
      open: 267.56,
      high: 267.56,
      low: 267.56,
      close: 267.56,
      volume: 100,
    },
    {
      timestamp: "2026-04-24T16:00:00-04:00",
      open: 274.3,
      high: 274.3,
      low: 274.3,
      close: 274.3,
      volume: 120,
    },
    {
      timestamp: "2026-04-28T16:00:00-04:00",
      open: 270.71,
      high: 270.71,
      low: 270.71,
      close: 270.71,
      volume: 200,
    },
  ],
  keyStats: [],
  newsItems: [],
};

describe("MarketChart", () => {
  it("renders Google Finance style chart context for windowed US quotes", () => {
    render(<MarketChart quote={aaplQuote} />);

    const chartSvg = document.querySelector(".market-chart-plot svg");
    expect(chartSvg).toHaveAttribute("viewBox", "0 0 760 360");
    expect(screen.getByText("Start 267.56 USD")).toBeInTheDocument();
    expect(screen.getByLabelText("Latest 270.71 USD")).toBeInTheDocument();
    expect(screen.getAllByText("274.30 USD").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Apr 23")).toBeInTheDocument();
    expect(screen.getByText("Apr 28")).toBeInTheDocument();
    expect(screen.getByText("5D")).toBeInTheDocument();
  });

  it("shows a hover tooltip with the nearest chart price", () => {
    render(<MarketChart quote={aaplQuote} />);

    const chartSvg = document.querySelector(".market-chart-plot svg");
    expect(chartSvg).not.toBeNull();
    chartSvg!.getBoundingClientRect = () => ({
      bottom: 360,
      height: 360,
      left: 0,
      right: 760,
      top: 0,
      width: 760,
      x: 0,
      y: 0,
      toJSON: () => "",
    });

    expect(screen.queryByText("Price: 274.30 USD")).not.toBeInTheDocument();
    fireEvent.pointerMove(chartSvg!, { clientX: 405, clientY: 160 });

    expect(screen.getAllByText("Apr 24").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Price: 274.30 USD")).toBeInTheDocument();
  });

  it("colors the chart line from the selected window range, not the quote-level change", () => {
    render(
      <MarketChart
        quote={{
          ...aaplQuote,
          changePct: 1.18,
          chartBars: [
            aaplQuote.chartBars[0],
            {
              timestamp: "2026-04-24T16:00:00-04:00",
              open: 264.3,
              high: 264.3,
              low: 264.3,
              close: 264.3,
              volume: 120,
            },
          ],
          lastPrice: 264.3,
        }}
      />,
    );

    expect(document.querySelector(".market-chart-is-down")).toBeInTheDocument();
    expect(screen.getByText("+1.18%")).toBeInTheDocument();
    expect(document.querySelector(".market-chart-line")).toHaveClass("market-chart-line");
  });
});
