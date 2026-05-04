import { afterEach, describe, expect, it, vi } from "vitest";

import {
  clearConversations,
  deleteConversation,
  deleteLlmCredential,
  fetchConversation,
  fetchConversations,
  fetchLlmCredentialStatus,
  fetchMarketQuote,
  fetchSettings,
  runBacktest,
  saveLlmCredential,
  saveSettings,
  sendConversationMessage,
  testLlmCredential,
} from "./api";

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body,
  } as Response;
}

describe("shared api", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("maps settings between API and UI shapes", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          provider: "openai",
          analysis_mode: "quick",
          default_market: "KR",
          default_horizon: null,
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          provider: "claude",
          analysis_mode: "deep",
          default_market: "US",
          default_horizon: "swing",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchSettings()).resolves.toEqual({
      provider: "openai",
      analysisMode: "quick",
      defaultMarket: "KR",
      defaultHorizon: null,
    });
    await expect(
      saveSettings({
        provider: "claude",
        analysisMode: "deep",
        defaultMarket: "US",
        defaultHorizon: "swing",
      }),
    ).resolves.toEqual({
      provider: "claude",
      analysisMode: "deep",
      defaultMarket: "US",
      defaultHorizon: "swing",
    });

    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/settings",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({
          provider: "claude",
          analysis_mode: "deep",
          default_market: "US",
          default_horizon: "swing",
        }),
      }),
    );
  });

  it("maps LLM credential status and save/delete requests without raw key exposure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          configured: false,
          provider: null,
          model: null,
          base_url: null,
          api_key_mask: null,
          key_source: null,
          created_at: null,
          updated_at: null,
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          configured: true,
          provider: "openai",
          model: "gpt-4.1-mini",
          base_url: "https://api.openai.com/v1",
          api_key_mask: "sk-...7890",
          key_source: "local_encrypted_state",
          created_at: "2026-04-27T12:00:00+09:00",
          updated_at: "2026-04-27T12:00:00+09:00",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          configured: false,
          provider: null,
          model: null,
          base_url: null,
          api_key_mask: null,
          key_source: null,
          created_at: null,
          updated_at: null,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchLlmCredentialStatus()).resolves.toEqual({
      configured: false,
      provider: null,
      model: null,
      baseUrl: null,
      apiKeyMask: null,
      keySource: null,
      createdAt: null,
      updatedAt: null,
    });

    await expect(
      saveLlmCredential({
        provider: "openai",
        model: "gpt-4.1-mini",
        baseUrl: null,
        apiKey: "sk-live-secret-7890",
      }),
    ).resolves.toEqual({
      configured: true,
      provider: "openai",
      model: "gpt-4.1-mini",
      baseUrl: "https://api.openai.com/v1",
      apiKeyMask: "sk-...7890",
      keySource: "local_encrypted_state",
      createdAt: "2026-04-27T12:00:00+09:00",
      updatedAt: "2026-04-27T12:00:00+09:00",
    });

    await expect(deleteLlmCredential()).resolves.toEqual({
      configured: false,
      provider: null,
      model: null,
      baseUrl: null,
      apiKeyMask: null,
      keySource: null,
      createdAt: null,
      updatedAt: null,
    });

    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/credentials/llm", {
      headers: expect.any(Headers),
      method: "PUT",
      signal: expect.any(AbortSignal),
      body: JSON.stringify({
        provider: "openai",
        model: "gpt-4.1-mini",
        base_url: null,
        api_key: "sk-live-secret-7890",
      }),
    });
    expect(fetchMock).toHaveBeenNthCalledWith(3, "/api/credentials/llm", {
      headers: expect.any(Headers),
      method: "DELETE",
      signal: expect.any(AbortSignal),
    });
  });

  it("maps LLM connection test results without raw key exposure", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse({
        configured: true,
        status: "provider_error",
        provider: "cerebras",
        model: "llama3.1-8b",
        base_url: "https://api.cerebras.ai/v1",
        key_source: "local_encrypted_state",
        error_code: "auth_error",
        message: "Authentication failed. Check the saved provider key.",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(testLlmCredential()).resolves.toEqual({
      configured: true,
      status: "provider_error",
      provider: "cerebras",
      model: "llama3.1-8b",
      baseUrl: "https://api.cerebras.ai/v1",
      keySource: "local_encrypted_state",
      errorCode: "auth_error",
      message: "Authentication failed. Check the saved provider key.",
    });

    expect(fetchMock).toHaveBeenCalledWith("/api/credentials/llm/test", {
      headers: expect.any(Headers),
      method: "POST",
      signal: expect.any(AbortSignal),
    });
  });

  it("deletes one conversation or clears all conversations", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ deleted_count: 1 }))
      .mockResolvedValueOnce(jsonResponse({ deleted_count: 3 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(deleteConversation("conv_aapl")).resolves.toBe(1);
    await expect(clearConversations()).resolves.toBe(3);

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/conversations/conv_aapl", {
      headers: expect.any(Headers),
      method: "DELETE",
      signal: expect.any(AbortSignal),
    });
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/conversations", {
      headers: expect.any(Headers),
      method: "DELETE",
      signal: expect.any(AbortSignal),
    });
  });

  it("fetches market quotes with a selected chart window", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse({
        market: "US",
        symbol: "AAPL",
        name: "Apple Inc",
        exchange: "NASDAQ",
        currency: "USD",
        last_price: 270.71,
        previous_close: 267.52,
        change_pct: 1.19,
        as_of_at: "2026-04-29T16:00:00-04:00",
        source: "serpapi_google_finance",
        chart_window: "5D",
        chart_bars: [
          {
            timestamp: "2026-04-24T16:00:00-04:00",
            open: 268,
            high: 268,
            low: 268,
            close: 268,
            volume: 100,
          },
          {
            timestamp: "2026-04-29T16:00:00-04:00",
            open: 270.71,
            high: 270.71,
            low: 270.71,
            close: 270.71,
            volume: 200,
          },
        ],
        key_stats: [],
        news_items: [],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchMarketQuote("US", "AAPL", "5D")).resolves.toMatchObject({
      market: "US",
      symbol: "AAPL",
      chartWindow: "5D",
      chartBars: [
        { close: 268 },
        { close: 270.71 },
      ],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/market-data/quotes/US/AAPL?window=5D",
      {
        headers: expect.any(Headers),
        signal: expect.any(AbortSignal),
      },
    );
  });

  it("maps conversation summaries and message-level market snapshots", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          conversations: [
            {
              conversation_id: "conv_aapl",
              title: "AAPL",
              status: "market_snapshot",
              updated_at: "2026-04-28T20:00:00Z",
              last_message: "Here is the market snapshot for Apple.",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          conversation_id: "conv_aapl",
          status: "market_snapshot",
          missing_inputs: [],
          analysis_request: null,
          analysis_result: null,
          market_snapshot: null,
          messages: [
            {
              id: "msg_user",
              role: "user",
              content: "AAPL",
              meta: "US market / quick mode",
              created_at: "2026-04-28T19:59:59Z",
              market_snapshot: null,
            },
            {
              id: "msg_assistant",
              role: "assistant",
              content: "Here is the market snapshot for Apple.",
              meta: "market snapshot",
              created_at: "2026-04-28T20:00:00Z",
              market_snapshot: {
                market: "US",
                symbol: "AAPL",
                name: "Apple Inc",
                exchange: "NASDAQ",
                currency: "USD",
                last_price: 207.15,
                previous_close: 204.59,
                change_pct: 1.25,
                as_of_at: "2026-04-28T16:00:00-04:00",
                source: "serpapi_google_finance",
                chart_bars: [
                  {
                    timestamp: "2026-04-28T09:30:00-04:00",
                    open: 204.59,
                    high: 204.59,
                    low: 204.59,
                    close: 204.59,
                    volume: 1000,
                  },
                  {
                    timestamp: "2026-04-28T16:00:00-04:00",
                    open: 207.15,
                    high: 207.15,
                    low: 207.15,
                    close: 207.15,
                    volume: 2000,
                  },
                ],
                key_stats: [{ label: "Market cap", value: "$3.12T" }],
                news_items: [
                  {
                    title: "Apple supplier checks improve",
                    url: "https://example.com/apple-suppliers",
                    source: "Market Wire",
                    published_at: "2026-04-28T13:15:00-04:00",
                    snippet: "Supplier checks pointed to stronger iPhone demand.",
                  },
                ],
              },
            },
          ],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchConversations()).resolves.toEqual([
      {
        conversationId: "conv_aapl",
        title: "AAPL",
        status: "market_snapshot",
        updatedAt: "2026-04-28T20:00:00Z",
        lastMessage: "Here is the market snapshot for Apple.",
      },
    ]);
    await expect(fetchConversation("conv_aapl")).resolves.toMatchObject({
      conversationId: "conv_aapl",
      messages: [
        { content: "AAPL", marketSnapshot: null },
        {
          content: "Here is the market snapshot for Apple.",
          marketSnapshot: {
            symbol: "AAPL",
            keyStats: [{ label: "Market cap", value: "$3.12T" }],
            newsItems: [{ title: "Apple supplier checks improve" }],
          },
        },
      ],
    });

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/conversations", {
      headers: expect.any(Headers),
      signal: expect.any(AbortSignal),
    });
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/conversations/conv_aapl", {
      headers: expect.any(Headers),
      signal: expect.any(AbortSignal),
    });
  });

  it("uses the conversation message endpoint after a conversation exists", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        conversation_id: "conv_001",
        status: "ready_for_analysis",
        missing_inputs: [],
        analysis_request: {
          market: "KR",
          symbol: "005930",
          stock_name: "Samsung Electronics",
          horizon_type: "swing",
          analysis_mode: "quick",
        },
        market_snapshot: null,
        messages: [],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await sendConversationMessage({
      content: "Use a swing horizon.",
      conversationId: "conv_001",
      market: "KR",
      horizonType: "swing",
      analysisMode: "quick",
      responseLanguage: "ko",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/conversations/conv_001/messages",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          content: "Use a swing horizon.",
          market: "KR",
          horizon_type: "swing",
          analysis_mode: "quick",
          response_language: "ko",
        }),
      }),
    );
  });

  it("maps analysis source audit metadata without source body exposure", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        conversation_id: "conv_001",
        status: "analysis_completed",
        missing_inputs: [],
        analysis_request: {
          market: "KR",
          symbol: "005930",
          stock_name: "Samsung Electronics",
          horizon_type: "swing",
          analysis_mode: "deep",
        },
        analysis_result: {
          analysis_request_id: "analysis_001",
          status: "completed",
          included_document_count: 1,
          excluded_document_count: 1,
          source_audit: {
            source_warnings: ["missing_credential:naver_news"],
            included_by_source_type: { tavily_news: 1 },
            excluded_by_reason: { published_after_as_of_at: 1 },
            prompt_document_ids: ["src_included"],
          },
          source_documents: [
            {
              id: "src_included",
              source_type: "tavily_news",
              source_name: "Tavily Search",
              url: "https://example.com/demand",
              title: "Demand improved before cutoff",
              published_at: "2026-04-24T08:30:00+09:00",
              fetched_at: "2026-04-24T09:00:00+09:00",
              included_in_analysis: true,
              exclusion_reason: null,
              language: "en",
              adapter: "tavily_news",
              relevance_score: 0.86,
              safety_flags: ["external_api", "untrusted_source_text"],
              content_text: "server should not expose this through UI mapping",
            },
            {
              id: "src_excluded",
              source_type: "gnews_news",
              source_name: "GNews Wire",
              url: "https://example.com/future",
              title: "Future source",
              published_at: "2026-04-24T09:01:00+09:00",
              fetched_at: "2026-04-24T09:00:00+09:00",
              included_in_analysis: false,
              exclusion_reason: "published_after_as_of_at",
              language: "en",
              adapter: "gnews_news",
              relevance_score: 0.82,
              safety_flags: ["external_api", "untrusted_source_text"],
            },
          ],
          evidence_items: [],
          summary: "Audited source summary.",
          score_result: {
            score_id: "score_001",
            analysis_request_id: "analysis_001",
            status: "scored",
            buy_probability: 52.9,
            hold_probability: 35.3,
            sell_probability: 11.8,
            confidence_score: 0.74,
            expected_return_min_pct: -0.1,
            expected_return_max_pct: 3.4,
            downside_probability: 11.8,
            similar_event_sample_count: 8,
            similar_event_win_rate: 62.5,
            similar_event_median_return_pct: 1.4,
            confidence_factors: ["eligible_weight", "stance_diversity"],
            drivers: [
              {
                source_document_id: "src_included",
                stance: "bullish",
                weight: 0.7,
                probability_impact: "supports_buy",
                summary: "Demand improved",
              },
            ],
            rationale: "Normalized evidence weights.",
          },
          provider: "openai",
          model: "gpt-4.1-mini",
          provider_error_code: null,
        },
        market_snapshot: null,
        messages: [],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      sendConversationMessage({
        content: "Samsung swing deep",
        conversationId: null,
        market: "KR",
        horizonType: "swing",
        analysisMode: "deep",
        responseLanguage: "en",
      }),
    ).resolves.toMatchObject({
      analysisResult: {
        sourceAudit: {
          sourceWarnings: ["missing_credential:naver_news"],
          includedBySourceType: { tavily_news: 1 },
          excludedByReason: { published_after_as_of_at: 1 },
          promptDocumentIds: ["src_included"],
        },
        sourceDocuments: [
          {
            id: "src_included",
            fetchedAt: "2026-04-24T09:00:00+09:00",
            includedInAnalysis: true,
            language: "en",
            adapter: "tavily_news",
            relevanceScore: 0.86,
            safetyFlags: ["external_api", "untrusted_source_text"],
          },
          {
            id: "src_excluded",
            exclusionReason: "published_after_as_of_at",
          },
        ],
        scoreResult: {
          buyProbability: 52.9,
          holdProbability: 35.3,
          sellProbability: 11.8,
          confidenceScore: 0.74,
          confidenceFactors: ["eligible_weight", "stance_diversity"],
          expectedReturnMinPct: -0.1,
          expectedReturnMaxPct: 3.4,
          downsideProbability: 11.8,
          similarEventSampleCount: 8,
          similarEventWinRate: 62.5,
          similarEventMedianReturnPct: 1.4,
          drivers: [
            {
              sourceDocumentId: "src_included",
              probabilityImpact: "supports_buy",
            },
          ],
        },
      },
    });
  });

  it("maps news digest fields between API and UI shapes", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        conversation_id: "conv_news",
        status: "news_digest",
        missing_inputs: [],
        analysis_request: null,
        analysis_result: null,
        market_snapshot: null,
        news_digest: {
          digest_id: "digest_apple",
          status: "completed",
          market: "US",
          symbol: "AAPL",
          stock_name: "Apple Inc",
          query: "Apple Inc AAPL stock news",
          generated_at: "2026-04-29T20:00:00Z",
          summary: "Apple news summary.",
          key_points: ["Apple earnings preview"],
          important_articles: [
            {
              id: "news_1",
              title: "Apple earnings preview",
              url: "https://example.com/apple",
              source: "Example Markets",
              published_at: "2026-04-29T13:00:00-04:00",
              snippet: "Services and AI remain in focus.",
              provider: "tavily_news",
              query: "Apple Inc AAPL stock news",
              rank: 0,
              category: "earnings",
              headline_ko: "오늘 Q2 2026 실적 발표 예정",
              summary_ko: "애플은 장 마감 후 실적을 발표합니다.",
              importance_score: 42,
              source_domain: "example.com",
            },
          ],
          additional_articles: [],
          provider_runs: [
            {
              provider: "serpapi_google_web",
              query: "Apple Inc AAPL stock news",
              result_count: 3,
              status: "completed",
              warning: null,
            },
          ],
          warnings: [],
        },
        messages: [
          {
            id: "msg_news",
            role: "assistant",
            content: "Apple news summary.",
            meta: "news digest",
            created_at: "2026-04-29T20:00:00Z",
            market_snapshot: null,
            news_digest: {
              digest_id: "digest_apple",
              status: "completed",
              market: "US",
              symbol: "AAPL",
              stock_name: "Apple Inc",
              query: "Apple Inc AAPL stock news",
              generated_at: "2026-04-29T20:00:00Z",
              summary: "Apple news summary.",
              key_points: ["Apple earnings preview"],
              important_articles: [
                {
                  id: "news_1",
                  title: "Apple earnings preview",
                  url: "https://example.com/apple",
                  source: "Example Markets",
                  published_at: "2026-04-29T13:00:00-04:00",
                  snippet: "Services and AI remain in focus.",
                  provider: "tavily_news",
                  query: "Apple Inc AAPL stock news",
                  rank: 0,
                  category: "earnings",
                  headline_ko: "오늘 Q2 2026 실적 발표 예정",
                  summary_ko: "애플은 장 마감 후 실적을 발표합니다.",
                  importance_score: 42,
                  source_domain: "example.com",
                },
              ],
              additional_articles: [],
              provider_runs: [
                {
                  provider: "serpapi_google_web",
                  query: "Apple Inc AAPL stock news",
                  result_count: 3,
                  status: "completed",
                  warning: null,
                },
              ],
              warnings: [],
            },
          },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchConversation("conv_news")).resolves.toMatchObject({
      status: "news_digest",
      newsDigest: {
        digestId: "digest_apple",
        importantArticles: [
          {
            title: "Apple earnings preview",
            publishedAt: "2026-04-29T13:00:00-04:00",
            provider: "tavily_news",
            category: "earnings",
            headlineKo: "오늘 Q2 2026 실적 발표 예정",
            summaryKo: "애플은 장 마감 후 실적을 발표합니다.",
            sourceDomain: "example.com",
          },
        ],
        providerRuns: [{ provider: "serpapi_google_web", resultCount: 3 }],
      },
      messages: [
        {
          newsDigest: {
            symbol: "AAPL",
            importantArticles: [{ url: "https://example.com/apple" }],
          },
        },
      ],
    });
  });

  it("maps conversation-level PnL simulation results", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        conversation_id: "conv_pnl",
        status: "pnl_simulation",
        missing_inputs: [],
        analysis_request: null,
        analysis_result: null,
        market_snapshot: null,
        news_digest: null,
        backtest_result: {
          simulation_id: "backtest_apple",
          analysis_request_id: null,
          market: "US",
          symbol: "AAPL",
          entry_at: "2026-04-01T16:00:00-04:00",
          exit_at: "2026-04-24T16:00:00-04:00",
          entry_price: 190,
          exit_price: 207.15,
          quantity: 1,
          gross_return_pct: 9.03,
          gross_pnl: 17.15,
          max_drawdown_pct: -2.38,
          equity_curve: [
            {
              timestamp: "2026-04-01T16:00:00-04:00",
              price: 190,
              value: 190,
              return_pct: 0,
            },
          ],
          source: "seeded_local_fixture",
        },
        messages: [
          {
            id: "msg_pnl",
            role: "assistant",
            content: "PnL simulation",
            meta: "PnL simulation",
            created_at: "2026-04-30T00:00:00Z",
            market_snapshot: null,
            news_digest: null,
            backtest_result: {
              simulation_id: "backtest_apple",
              analysis_request_id: null,
              evaluation_kind: "pnl_simulation",
              market: "US",
              symbol: "AAPL",
              entry_at: "2026-04-01T16:00:00-04:00",
              exit_at: "2026-04-24T16:00:00-04:00",
              entry_price: 190,
              exit_price: 207.15,
              quantity: 1,
              gross_return_pct: 9.03,
              gross_pnl: 17.15,
              max_drawdown_pct: -2.38,
              equity_curve: [],
              source: "seeded_local_fixture",
            },
          },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchConversation("conv_pnl")).resolves.toMatchObject({
      status: "pnl_simulation",
      backtestResult: {
        symbol: "AAPL",
        grossReturnPct: 9.03,
      },
      messages: [
        {
          backtestResult: {
            simulationId: "backtest_apple",
            evaluationKind: "pnl_simulation",
            grossPnl: 17.15,
          },
        },
      ],
    });
  });

  it("maps backtest simulations between API and UI shapes", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        simulation_id: "backtest_001",
        analysis_request_id: null,
        evaluation_kind: "pnl_simulation",
        market: "KR",
        symbol: "005930",
        entry_at: "2026-04-22T15:30:00+09:00",
        exit_at: "2026-04-24T15:30:00+09:00",
        entry_price: 70000,
        exit_price: 72000,
        quantity: 10,
        gross_return_pct: 2.86,
        gross_pnl: 20000,
        max_drawdown_pct: 0,
        source: "seeded_local_fixture",
        equity_curve: [
          {
            timestamp: "2026-04-22T15:30:00+09:00",
            price: 70000,
            value: 700000,
            return_pct: 0,
          },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      runBacktest({
        market: "KR",
        symbol: "005930",
        entryAt: "2026-04-22T15:30:00+09:00",
        exitAt: "2026-04-24T15:30:00+09:00",
        quantity: 10,
        analysisRequestId: null,
      }),
    ).resolves.toEqual({
      simulationId: "backtest_001",
      analysisRequestId: null,
      evaluationKind: "pnl_simulation",
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
      ],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/backtests/simulations",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          analysis_request_id: null,
          market: "KR",
          symbol: "005930",
          entry_at: "2026-04-22T15:30:00+09:00",
          exit_at: "2026-04-24T15:30:00+09:00",
          quantity: 10,
        }),
      }),
    );
  });

  it("aborts stalled requests after the default timeout", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn((_url: string, init?: RequestInit) => {
      return new Promise((_resolve, reject) => {
        const signal = init?.signal;
        signal?.addEventListener("abort", () => {
          reject(new DOMException("Aborted", "AbortError"));
        });
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const request = expect(fetchSettings()).rejects.toThrow("Request timed out.");
    await vi.advanceTimersByTimeAsync(30_000);

    await request;
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/settings",
      expect.objectContaining({
        signal: expect.any(AbortSignal),
      }),
    );
  });
});
