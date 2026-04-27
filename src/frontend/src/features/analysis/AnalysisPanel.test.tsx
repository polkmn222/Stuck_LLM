import { render, screen } from "@testing-library/react";

import { AnalysisPanel } from "./AnalysisPanel";
import { uiCopy } from "../../shared/i18n";

describe("AnalysisPanel", () => {
  it("renders a seeded market snapshot without completed probabilities", () => {
    render(
      <AnalysisPanel
        copy={uiCopy.en.analysis}
        snapshot={{
          conversationId: "conv_001",
          status: "ready_for_analysis",
          missingInputs: [],
          analysisRequest: {
            market: "KR",
            symbol: "005930",
            stockName: "Samsung Electronics",
            horizonType: "swing",
            analysisMode: "quick",
          },
          marketSnapshot: {
            market: "KR",
            symbol: "005930",
            name: "Samsung Electronics",
            exchange: "KRX",
            currency: "KRW",
            lastPrice: 72000,
            asOfAt: "2026-04-24T15:30:00+09:00",
            source: "seeded_local_fixture",
          },
          messages: [],
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Market snapshot" })).toBeInTheDocument();
    expect(screen.getByText("Samsung Electronics")).toBeInTheDocument();
    expect(screen.getByText("72,000 KRW")).toBeInTheDocument();
    expect(screen.getByText("Probabilities pending")).toBeInTheDocument();
  });
});
