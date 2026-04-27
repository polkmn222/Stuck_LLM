import { afterEach, describe, expect, it, vi } from "vitest";

import {
  deleteLlmCredential,
  fetchLlmCredentialStatus,
  fetchSettings,
  runBacktest,
  saveLlmCredential,
  saveSettings,
  sendConversationMessage,
} from "./api";

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body,
  } as Response;
}

describe("shared api", () => {
  afterEach(() => {
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
        }),
      }),
    );
  });

  it("maps backtest simulations between API and UI shapes", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        simulation_id: "backtest_001",
        analysis_request_id: null,
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
});
