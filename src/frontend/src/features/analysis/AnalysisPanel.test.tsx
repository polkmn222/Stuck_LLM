import { render, screen } from "@testing-library/react";

import { AnalysisPanel } from "./AnalysisPanel";
import { uiCopy } from "../../shared/i18n";
import type { ConversationSnapshot } from "../../shared/types";

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
            previousClose: 71600,
            changePct: 0.56,
            asOfAt: "2026-04-24T15:30:00+09:00",
            source: "seeded_local_fixture",
            chartWindow: "1D",
            chartBars: [
              {
                timestamp: "2026-04-22T00:00:00+09:00",
                open: 70000,
                high: 71200,
                low: 69800,
                close: 71000,
                volume: 12000000,
              },
              {
                timestamp: "2026-04-23T00:00:00+09:00",
                open: 71300,
                high: 72100,
                low: 70800,
                close: 71600,
                volume: 13000000,
              },
              {
                timestamp: "2026-04-24T00:00:00+09:00",
                open: 71800,
                high: 72600,
                low: 71000,
                close: 72000,
                volume: 15500000,
              },
            ],
            keyStats: [],
            newsItems: [],
          },
          messages: [],
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Market snapshot" })).toBeInTheDocument();
    expect(screen.getByText("Samsung Electronics")).toBeInTheDocument();
    expect(screen.getByText("005930")).toBeInTheDocument();
    expect(screen.getAllByText("72,000 KRW").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("KRX")).toBeInTheDocument();
    expect(screen.getByText("2026-04-24T15:30:00+09:00")).toBeInTheDocument();
    expect(screen.getByText("+0.56%")).toBeInTheDocument();
    expect(screen.getByLabelText("Samsung Electronics price chart")).toBeInTheDocument();
    expect(
      screen.getByRole("table", { name: "Samsung Electronics chart data" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "72,000 KRW" })).toBeInTheDocument();
    expect(screen.getByText("Probabilities pending")).toBeInTheDocument();
  });

  it("renders setup-needed and provider-error statuses without internal details", () => {
    const baseSnapshot: Omit<ConversationSnapshot, "status"> = {
      conversationId: "conv_001",
      missingInputs: [],
      analysisRequest: {
        market: "KR",
        symbol: "005930",
        stockName: "Samsung Electronics",
        horizonType: "swing",
        analysisMode: "quick",
      },
      marketSnapshot: null,
      messages: [],
    };

    const { rerender } = render(
      <AnalysisPanel
        copy={uiCopy.en.analysis}
        snapshot={{
          ...baseSnapshot,
          status: "setup_needed",
        }}
      />,
    );

    expect(screen.getByText("LLM setup needed")).toBeInTheDocument();

    rerender(
      <AnalysisPanel
        copy={uiCopy.en.analysis}
        snapshot={{
          ...baseSnapshot,
          status: "provider_error",
        }}
      />,
    );

    expect(screen.getByText("Provider error")).toBeInTheDocument();
    expect(screen.queryByText(/stack|trace|secret/i)).not.toBeInTheDocument();
  });

  it("renders source audit trail with included and excluded evidence", () => {
    render(
      <AnalysisPanel
        copy={uiCopy.en.analysis}
        snapshot={{
          conversationId: "conv_001",
          status: "analysis_completed",
          missingInputs: [],
          analysisRequest: {
            market: "KR",
            symbol: "005930",
            stockName: "Samsung Electronics",
            horizonType: "swing",
            analysisMode: "deep",
          },
          analysisResult: {
            analysisRequestId: "analysis_001",
            status: "completed",
            includedDocumentCount: 1,
            excludedDocumentCount: 1,
            sourceAudit: {
              sourceWarnings: ["missing_credential:naver_news"],
              includedBySourceType: { tavily_news: 1 },
              excludedByReason: { published_after_as_of_at: 1 },
              promptDocumentIds: ["src_included"],
            },
            sourceDocuments: [
              {
                id: "src_included",
                sourceType: "tavily_news",
                sourceName: "Tavily Search",
                url: "https://example.com/demand",
                title: "Demand improved before cutoff",
                publishedAt: "2026-04-24T08:30:00+09:00",
                fetchedAt: "2026-04-24T09:00:00+09:00",
                includedInAnalysis: true,
                exclusionReason: null,
                language: "en",
                adapter: "tavily_news",
                relevanceScore: 0.86,
                safetyFlags: ["external_api", "untrusted_source_text"],
              },
              {
                id: "src_excluded",
                sourceType: "gnews_news",
                sourceName: "GNews Wire",
                url: "https://example.com/future",
                title: "Future source",
                publishedAt: "2026-04-24T09:01:00+09:00",
                fetchedAt: "2026-04-24T09:00:00+09:00",
                includedInAnalysis: false,
                exclusionReason: "published_after_as_of_at",
                language: "en",
                adapter: "gnews_news",
                relevanceScore: 0.82,
                safetyFlags: ["external_api", "untrusted_source_text"],
              },
            ],
            evidenceItems: [],
            summary: "Audited source summary.",
            provider: "openai",
            model: "gpt-4.1-mini",
            providerErrorCode: null,
          },
          marketSnapshot: null,
          messages: [],
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Source audit" })).toBeInTheDocument();
    expect(screen.getByText("1 included")).toBeInTheDocument();
    expect(screen.getByText("1 excluded")).toBeInTheDocument();
    expect(screen.getByText("missing_credential:naver_news")).toBeInTheDocument();
    expect(screen.getByText("Provider: openai")).toBeInTheDocument();
    expect(screen.getByText("Model: gpt-4.1-mini")).toBeInTheDocument();
    expect(screen.getByText("Demand improved before cutoff")).toBeInTheDocument();
    expect(screen.getByText("Future source")).toBeInTheDocument();
    expect(screen.getByText("Used in prompt")).toBeInTheDocument();
    expect(screen.getByText("Excluded")).toBeInTheDocument();
    expect(screen.getByText("published_after_as_of_at")).toBeInTheDocument();
  });

  it("renders completed buy hold sell probabilities", () => {
    render(
      <AnalysisPanel
        copy={uiCopy.en.analysis}
        snapshot={{
          conversationId: "conv_score",
          status: "analysis_completed",
          missingInputs: [],
          analysisRequest: {
            market: "US",
            symbol: "AAPL",
            stockName: "Apple",
            horizonType: "swing",
            analysisMode: "quick",
          },
          analysisResult: {
            analysisRequestId: "analysis_score",
            status: "completed",
            includedDocumentCount: 1,
            excludedDocumentCount: 0,
            sourceAudit: {
              sourceWarnings: [],
              includedBySourceType: { global_macro: 1 },
              excludedByReason: {},
              promptDocumentIds: ["src_macro"],
            },
            sourceDocuments: [],
            evidenceItems: [],
            summary: "Score summary.",
            scoreResult: {
              scoreId: "score_001",
              analysisRequestId: "analysis_score",
              status: "scored",
              buyProbability: 52.9,
              holdProbability: 35.3,
              sellProbability: 11.8,
              confidenceScore: 0.74,
              expectedReturnMinPct: -0.1,
              expectedReturnMaxPct: 3.4,
              downsideProbability: 11.8,
              similarEventSampleCount: 8,
              similarEventWinRate: 62.5,
              similarEventMedianReturnPct: 1.4,
              confidenceFactors: ["eligible_weight", "stance_diversity"],
              drivers: [],
              rationale: "Normalized evidence weights.",
            },
            provider: "openai",
            model: "gpt-4.1-mini",
            providerErrorCode: null,
          },
          marketSnapshot: null,
          messages: [],
        }}
      />,
    );

    expect(screen.getByLabelText("Buy hold sell probabilities")).toBeInTheDocument();
    expect(screen.getByText("52.9%")).toBeInTheDocument();
    expect(screen.getByText("35.3%")).toBeInTheDocument();
    expect(screen.getByText("11.8%")).toBeInTheDocument();
    expect(screen.getByText("Confidence: 0.74")).toBeInTheDocument();
    expect(screen.getByText("Confidence factors: eligible_weight, stance_diversity")).toBeInTheDocument();
    expect(screen.getByText(/Expected return: -0.1% to \+3.4%/)).toBeInTheDocument();
    expect(screen.getByText(/Downside risk: 11.8%/)).toBeInTheDocument();
    expect(screen.getByText(/Similar events: 8 samples/)).toBeInTheDocument();
    expect(screen.getByText(/62.5% win rate/)).toBeInTheDocument();
    expect(screen.queryByText("Probabilities pending")).not.toBeInTheDocument();
  });
});
