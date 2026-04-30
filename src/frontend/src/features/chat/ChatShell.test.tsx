import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { ChatShell } from "./ChatShell";
import { uiCopy } from "../../shared/i18n";

describe("ChatShell", () => {
  it("sends a message with the active settings and renders the persisted response", async () => {
    const firstSnapshot = {
      conversationId: "conv_001",
      status: "needs_input",
      missingInputs: ["horizon"],
      analysisRequest: null,
      marketSnapshot: null,
      messages: [
        {
          id: "msg_user",
          role: "user",
          content: "Should I buy Samsung Electronics?",
          meta: "submitted",
          createdAt: "2026-04-25T00:00:00Z",
        },
        {
          id: "msg_assistant",
          role: "assistant",
          content: "Which investment horizon should I use?",
          meta: "missing horizon",
          createdAt: "2026-04-25T00:00:01Z",
        },
      ],
    } as const;
    const secondSnapshot = {
      ...firstSnapshot,
      status: "ready_for_analysis",
      missingInputs: [],
      messages: [
        ...firstSnapshot.messages,
        {
          id: "msg_user_2",
          role: "user",
          content: "Use a swing horizon.",
          meta: "submitted",
          createdAt: "2026-04-25T00:00:02Z",
        },
      ],
    } as const;
    const onSendMessage = vi
      .fn()
      .mockResolvedValueOnce(firstSnapshot)
      .mockResolvedValueOnce(secondSnapshot);
    const onAnalysisChange = vi.fn();

    render(
      <ChatShell
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "KR",
          defaultHorizon: null,
        }}
        copy={uiCopy.en.chat}
        onAnalysisChange={onAnalysisChange}
        onSendMessage={onSendMessage}
        responseLanguage="ko"
      />,
    );

    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "Should I buy Samsung Electronics?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByText("Which investment horizon should I use?");

    expect(screen.getByRole("heading", { name: "Stock Analysis Agent" })).toBeInTheDocument();
    expect(onSendMessage).toHaveBeenCalledWith({
      content: "Should I buy Samsung Electronics?",
      conversationId: null,
      market: "KR",
      horizonType: null,
      analysisMode: "quick",
      responseLanguage: "ko",
    });
    expect(onAnalysisChange).toHaveBeenCalledWith(expect.objectContaining({ status: "needs_input" }));
    expect(screen.getByLabelText("Message")).toHaveValue("");

    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "Use a swing horizon." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByText("Use a swing horizon.");

    expect(onSendMessage).toHaveBeenLastCalledWith({
      content: "Use a swing horizon.",
      conversationId: "conv_001",
      market: "KR",
      horizonType: null,
      analysisMode: "quick",
      responseLanguage: "ko",
    });
  });

  it("does not send blank messages", async () => {
    const onSendMessage = vi.fn();

    render(
      <ChatShell
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "KR",
          defaultHorizon: null,
        }}
        copy={uiCopy.en.chat}
        onAnalysisChange={vi.fn()}
        onSendMessage={onSendMessage}
        responseLanguage="en"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(onSendMessage).not.toHaveBeenCalled());
  });

  it("scrolls to the newest conversation content after a message update", async () => {
    const scrollIntoView = vi.fn();
    const previousScrollIntoView = HTMLElement.prototype.scrollIntoView;
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: scrollIntoView,
    });
    const onSendMessage = vi.fn().mockResolvedValue({
      conversationId: "conv_scroll",
      status: "market_snapshot",
      missingInputs: [],
      analysisRequest: null,
      analysisResult: null,
      marketSnapshot: null,
      messages: [
        {
          id: "msg_user_scroll",
          role: "user",
          content: "AAPL",
          meta: "US market / quick mode",
          createdAt: "2026-04-29T00:00:00Z",
        },
        {
          id: "msg_assistant_scroll",
          role: "assistant",
          content: "Here is the AAPL snapshot.",
          meta: "market snapshot",
          createdAt: "2026-04-29T00:00:01Z",
        },
      ],
    });

    try {
      render(
        <ChatShell
          settings={{
            provider: "openai",
            analysisMode: "quick",
            defaultMarket: "US",
            defaultHorizon: null,
          }}
          copy={uiCopy.en.chat}
          onAnalysisChange={vi.fn()}
          onSendMessage={onSendMessage}
          responseLanguage="en"
        />,
      );
      scrollIntoView.mockClear();

      fireEvent.change(screen.getByLabelText("Message"), {
        target: { value: "AAPL" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Send" }));

      await screen.findByText("Here is the AAPL snapshot.");
      expect(scrollIntoView).toHaveBeenCalledWith({ block: "end", behavior: "smooth" });
    } finally {
      if (previousScrollIntoView) {
        Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
          configurable: true,
          value: previousScrollIntoView,
        });
      } else {
        delete (HTMLElement.prototype as { scrollIntoView?: unknown }).scrollIntoView;
      }
    }
  });

  it("shows English request activity while waiting for the chat response", async () => {
    const pendingSnapshot = {
      conversationId: "conv_pending",
      status: "chat_completed",
      missingInputs: [],
      analysisRequest: null,
      analysisResult: null,
      marketSnapshot: null,
      messages: [
        {
          id: "msg_user_pending",
          role: "user",
          content: "AAPL",
          meta: "US market / quick mode",
          createdAt: "2026-04-29T00:00:00Z",
        },
        {
          id: "msg_assistant_pending",
          role: "assistant",
          content: "Here is the AAPL snapshot.",
          meta: "market snapshot",
          createdAt: "2026-04-29T00:00:01Z",
        },
      ],
    } as const;
    let resolveSendMessage: (snapshot: typeof pendingSnapshot) => void = () => undefined;
    const onSendMessage = vi.fn().mockReturnValue(
      new Promise((resolve) => {
        resolveSendMessage = resolve;
      }),
    );

    render(
      <ChatShell
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "US",
          defaultHorizon: null,
        }}
        copy={uiCopy.en.chat}
        onAnalysisChange={vi.fn()}
        onSendMessage={onSendMessage}
        responseLanguage="en"
      />,
    );

    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "AAPL" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Thinking...")).toBeInTheDocument();
    expect(screen.getByText("Checking LLM intent and provider response")).toBeInTheDocument();
    expect(screen.getByText("Resolving ticker and market data API")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();

    resolveSendMessage(pendingSnapshot);

    await screen.findByText("Here is the AAPL snapshot.");
    await waitFor(() => expect(screen.queryByText("Thinking...")).not.toBeInTheDocument());
  });

  it("shows Korean request activity while waiting for the chat response", async () => {
    const pendingSnapshot = {
      conversationId: "conv_pending_ko",
      status: "chat_completed",
      missingInputs: [],
      analysisRequest: null,
      analysisResult: null,
      marketSnapshot: null,
      messages: [
        {
          id: "msg_user_pending_ko",
          role: "user",
          content: "애플",
          meta: "KR market / quick mode",
          createdAt: "2026-04-29T00:00:00Z",
        },
        {
          id: "msg_assistant_pending_ko",
          role: "assistant",
          content: "애플 스냅샷입니다.",
          meta: "시장 스냅샷",
          createdAt: "2026-04-29T00:00:01Z",
        },
      ],
    } as const;
    let resolveSendMessage: (snapshot: typeof pendingSnapshot) => void = () => undefined;
    const onSendMessage = vi.fn().mockReturnValue(
      new Promise((resolve) => {
        resolveSendMessage = resolve;
      }),
    );

    render(
      <ChatShell
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "KR",
          defaultHorizon: null,
        }}
        copy={uiCopy.ko.chat}
        onAnalysisChange={vi.fn()}
        onSendMessage={onSendMessage}
        responseLanguage="ko"
      />,
    );

    fireEvent.change(screen.getByLabelText("메시지"), {
      target: { value: "애플" },
    });
    fireEvent.click(screen.getByRole("button", { name: "전송" }));

    expect(await screen.findByText("생각중...")).toBeInTheDocument();
    expect(screen.getByText("LLM 의도와 제공자 응답 확인 중")).toBeInTheDocument();
    expect(screen.getByText("티커와 시장 데이터 API 확인 중")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "전송" })).toBeDisabled();

    resolveSendMessage(pendingSnapshot);

    await screen.findByText("애플 스냅샷입니다.");
    await waitFor(() => expect(screen.queryByText("생각중...")).not.toBeInTheDocument());
  });

  it("renders missing API-key setup copy as red text without internal details", async () => {
    const onSendMessage = vi.fn().mockResolvedValue({
      conversationId: "conv_setup_needed",
      status: "setup_needed",
      missingInputs: [],
      analysisRequest: null,
      analysisResult: {
        analysisRequestId: "analysis_setup",
        status: "setup_needed",
        includedDocumentCount: 1,
        excludedDocumentCount: 0,
        sourceAudit: {
          sourceWarnings: [],
          includedBySourceType: {},
          excludedByReason: {},
          promptDocumentIds: [],
        },
        sourceDocuments: [],
        evidenceItems: [],
        summary: "API key is required. Save a provider API key in Settings > Model.",
        provider: null,
        model: null,
        providerErrorCode: null,
      },
      marketSnapshot: null,
      messages: [
        {
          id: "msg_user",
          role: "user",
          content: "Should I buy Samsung Electronics?",
          meta: "KR market / quick mode",
          createdAt: "2026-04-25T00:00:00Z",
        },
        {
          id: "msg_assistant",
          role: "assistant",
          content: "API key is required. Save a provider API key in Settings > Model.",
          meta: "setup needed",
          createdAt: "2026-04-25T00:00:01Z",
        },
      ],
    });

    render(
      <ChatShell
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "KR",
          defaultHorizon: "swing",
        }}
        copy={uiCopy.en.chat}
        onAnalysisChange={vi.fn()}
        onSendMessage={onSendMessage}
        responseLanguage="en"
      />,
    );

    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "Should I buy Samsung Electronics?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    const setupMessage = await screen.findByText(
      "API key is required. Save a provider API key in Settings > Model.",
    );

    expect(setupMessage.closest("article")).toHaveClass("message-needs-api-key");
    expect(screen.queryByText(/stack|trace|secret|raw key/i)).not.toBeInTheDocument();
  });

  it("renders provider error messages without internal details", async () => {
    const onSendMessage = vi.fn().mockResolvedValue({
      conversationId: "conv_provider_error",
      status: "provider_error",
      missingInputs: [],
      analysisRequest: null,
      analysisResult: null,
      marketSnapshot: null,
      messages: [
        {
          id: "msg_user",
          role: "user",
          content: "Should I buy Samsung Electronics?",
          meta: "KR market / quick mode",
          createdAt: "2026-04-25T00:00:00Z",
        },
        {
          id: "msg_assistant",
          role: "assistant",
          content: "The LLM provider authentication failed. Check the saved provider key.",
          meta: "provider error",
          createdAt: "2026-04-25T00:00:01Z",
        },
      ],
    });

    render(
      <ChatShell
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "KR",
          defaultHorizon: "swing",
        }}
        copy={uiCopy.en.chat}
        onAnalysisChange={vi.fn()}
        onSendMessage={onSendMessage}
        responseLanguage="en"
      />,
    );

    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "Should I buy Samsung Electronics?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByText("provider error");
    expect(
      screen.getByText("The LLM provider authentication failed. Check the saved provider key."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/stack|trace|secret|raw key/i)).not.toBeInTheDocument();
  });

  it("renders a compact price chart on the latest assistant response", async () => {
    const onSendMessage = vi.fn().mockResolvedValue({
      conversationId: "conv_chart",
      status: "analysis_completed",
      missingInputs: [],
      analysisRequest: {
        market: "KR",
        symbol: "005930",
        stockName: "Samsung Electronics",
        horizonType: "swing",
        analysisMode: "quick",
      },
      analysisResult: null,
      marketSnapshot: {
        market: "KR",
        symbol: "005930",
        name: "Samsung Electronics",
        exchange: "KRX",
        currency: "KRW",
        lastPrice: 72400,
        previousClose: 72000,
        changePct: 0.56,
        asOfAt: "2026-04-24T15:30:00+09:00",
        source: "finance_data_reader",
        chartWindow: "1D",
        chartBars: [
          {
            timestamp: "2026-04-22T00:00:00+09:00",
            open: 70100,
            high: 71300,
            low: 69800,
            close: 71000,
            volume: 12200000,
          },
          {
            timestamp: "2026-04-23T00:00:00+09:00",
            open: 71200,
            high: 72400,
            low: 70700,
            close: 72000,
            volume: 14100000,
          },
          {
            timestamp: "2026-04-24T00:00:00+09:00",
            open: 71800,
            high: 72600,
            low: 71000,
            close: 72400,
            volume: 15500000,
          },
        ],
      },
      messages: [
        {
          id: "msg_user",
          role: "user",
          content: "Should I buy Samsung Electronics?",
          meta: "KR market / quick mode",
          createdAt: "2026-04-25T00:00:00Z",
        },
        {
          id: "msg_assistant",
          role: "assistant",
          content: "Live analysis summary.",
          meta: "live analysis",
          createdAt: "2026-04-25T00:00:01Z",
        },
      ],
    });

    render(
      <ChatShell
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "KR",
          defaultHorizon: "swing",
        }}
        copy={uiCopy.en.chat}
        onAnalysisChange={vi.fn()}
        onSendMessage={onSendMessage}
        responseLanguage="en"
      />,
    );

    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "Should I buy Samsung Electronics?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByText("Live analysis summary.");
    expect(
      screen.getByLabelText("Samsung Electronics chat price chart"),
    ).toBeInTheDocument();
    expect(screen.getByText("Samsung Electronics")).toBeInTheDocument();
    expect(screen.getByText("005930")).toBeInTheDocument();
    expect(screen.getByText("KRX")).toBeInTheDocument();
    expect(screen.getByText("2026-04-24T15:30:00+09:00")).toBeInTheDocument();
    expect(screen.getAllByText("72,400 KRW").length).toBeGreaterThanOrEqual(2);
  });

  it("refetches a US SerpApi chart when a period control is selected", async () => {
    const onFetchMarketQuote = vi.fn().mockResolvedValue({
      market: "US",
      symbol: "AAPL",
      name: "Apple Inc",
      exchange: "NASDAQ",
      currency: "USD",
      lastPrice: 280.12,
      previousClose: 270.71,
      changePct: 3.48,
      asOfAt: "2026-04-29T16:00:00-04:00",
      source: "serpapi_google_finance",
      chartWindow: "5D",
      chartBars: [
        {
          timestamp: "2026-04-24T16:00:00-04:00",
          open: 270.71,
          high: 270.71,
          low: 270.71,
          close: 270.71,
          volume: 100,
        },
        {
          timestamp: "2026-04-29T16:00:00-04:00",
          open: 280.12,
          high: 280.12,
          low: 280.12,
          close: 280.12,
          volume: 200,
        },
      ],
      keyStats: [],
      newsItems: [],
    });

    render(
      <ChatShell
        conversationSnapshot={{
          conversationId: "conv_aapl_window",
          status: "market_snapshot",
          missingInputs: [],
          analysisRequest: null,
          analysisResult: null,
          marketSnapshot: null,
          messages: [
            {
              id: "msg_assistant_aapl_window",
              role: "assistant",
              content: "Here is the market snapshot for Apple.",
              meta: "market snapshot",
              createdAt: "2026-04-29T00:00:01Z",
              marketSnapshot: {
                market: "US",
                symbol: "AAPL",
                name: "Apple Inc",
                exchange: "NASDAQ",
                currency: "USD",
                lastPrice: 270.71,
                previousClose: 267.52,
                changePct: 1.19,
                asOfAt: "2026-04-29T16:00:00-04:00",
                source: "serpapi_google_finance",
                chartWindow: "1D",
                chartBars: [
                  {
                    timestamp: "2026-04-29T09:30:00-04:00",
                    open: 267.52,
                    high: 267.52,
                    low: 267.52,
                    close: 267.52,
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
                keyStats: [],
                newsItems: [],
              },
            },
          ],
        }}
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "US",
          defaultHorizon: "swing",
        }}
        copy={uiCopy.en.chat}
        onAnalysisChange={vi.fn()}
        onFetchMarketQuote={onFetchMarketQuote}
        onSendMessage={vi.fn()}
        responseLanguage="en"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "5D" }));

    await waitFor(() => {
      expect(onFetchMarketQuote).toHaveBeenCalledWith("US", "AAPL", "5D");
    });
    expect((await screen.findAllByText("280.12 USD")).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByRole("button", { name: "5D" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("keeps earlier message charts stats and news visible after follow-up messages", async () => {
    const onSendMessage = vi.fn().mockResolvedValue({
      conversationId: "conv_aapl_history",
      status: "chat_completed",
      missingInputs: [],
      analysisRequest: null,
      analysisResult: null,
      marketSnapshot: null,
      messages: [
        {
          id: "msg_user_aapl",
          role: "user",
          content: "AAPL",
          meta: "US market / quick mode",
          createdAt: "2026-04-28T19:59:59Z",
        },
        {
          id: "msg_assistant_aapl",
          role: "assistant",
          content: "Here is the market snapshot for Apple.",
          meta: "market snapshot",
          createdAt: "2026-04-28T20:00:00Z",
          marketSnapshot: {
            market: "US",
            symbol: "AAPL",
            name: "Apple Inc",
            exchange: "NASDAQ",
            currency: "USD",
            lastPrice: 207.15,
            previousClose: 204.59,
            changePct: 1.25,
            asOfAt: "2026-04-28T16:00:00-04:00",
            source: "serpapi_google_finance",
            chartWindow: "1D",
            chartBars: [
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
            keyStats: [{ label: "Market cap", value: "$3.12T" }],
            newsItems: [
              {
                title: "Apple supplier checks improve",
                url: "https://example.com/apple-suppliers",
                source: "Market Wire",
                publishedAt: "2026-04-28T13:15:00-04:00",
                snippet: "Supplier checks pointed to stronger iPhone demand.",
              },
            ],
          },
        },
        {
          id: "msg_user_followup",
          role: "user",
          content: "Thanks",
          meta: "US market / quick mode",
          createdAt: "2026-04-28T20:00:10Z",
        },
        {
          id: "msg_assistant_followup",
          role: "assistant",
          content: "You are welcome.",
          meta: "chat",
          createdAt: "2026-04-28T20:00:11Z",
        },
      ],
    });

    render(
      <ChatShell
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "US",
          defaultHorizon: "swing",
        }}
        copy={uiCopy.en.chat}
        onAnalysisChange={vi.fn()}
        onSendMessage={onSendMessage}
        responseLanguage="en"
      />,
    );

    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "Thanks" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByText("You are welcome.");
    expect(screen.getByLabelText("Apple Inc chat price chart")).toBeInTheDocument();
    expect(screen.getByText("Market cap")).toBeInTheDocument();
    expect(screen.getByText("$3.12T")).toBeInTheDocument();
    expect(screen.getByText("Apple supplier checks improve")).toBeInTheDocument();
  });

  it("renders a news digest with linked top stories and expandable extra stories", async () => {
    render(
      <ChatShell
        conversationSnapshot={{
          conversationId: "conv_news_digest",
          status: "news_digest",
          missingInputs: [],
          analysisRequest: null,
          analysisResult: null,
          marketSnapshot: null,
          newsDigest: {
            digestId: "digest_apple",
            status: "completed",
            market: "US",
            symbol: "AAPL",
            stockName: "Apple Inc",
            query: "Apple Inc AAPL stock news",
            generatedAt: "2026-04-29T20:00:00Z",
            summary: "애플 뉴스 핵심은 실적, AI 전략, 공급망입니다.",
            keyPoints: ["Apple earnings preview highlights services growth"],
            importantArticles: [
              {
                id: "news_1",
                title: "Apple earnings preview highlights services growth",
                url: "https://example.com/apple-earnings",
                source: "Example Markets",
                publishedAt: "2026-04-29T13:00:00-04:00",
                snippet: "Investors are watching services and iPhone demand.",
                provider: "tavily_news",
                query: "Apple Inc AAPL stock news",
                rank: 0,
                category: "earnings",
                headlineKo: "오늘 Q2 2026 실적 발표 예정",
                summaryKo: "애플은 장 마감 후 실적 컨퍼런스콜을 진행합니다.",
                importanceScore: 42,
                sourceDomain: "businessinsider.com",
              },
            ],
            additionalArticles: [
              {
                id: "news_2",
                title: "Apple Arcade expands game catalog",
                url: "https://example.com/apple-arcade",
                source: "Example Search",
                publishedAt: "2026-04-27T00:00:00",
                snippet: "Apple added more services titles.",
                provider: "serpapi_google_web",
                query: "Apple Inc AAPL stock news",
                rank: 0,
                category: "product_service",
                headlineKo: "Apple Arcade 게임 카탈로그 확대",
                summaryKo: "애플은 서비스 카탈로그에 신규 타이틀을 추가했습니다.",
                importanceScore: 14,
                sourceDomain: "example.com",
              },
            ],
            providerRuns: [
              {
                provider: "tavily_news",
                query: "Apple Inc AAPL stock news",
                resultCount: 2,
                status: "completed",
                warning: null,
              },
              {
                provider: "serpapi_google_web",
                query: "Apple Inc AAPL stock news",
                resultCount: 1,
                status: "completed",
                warning: null,
              },
            ],
            warnings: [],
          },
          messages: [
            {
              id: "msg_user_news",
              role: "user",
              content: "애플 뉴스 가져와줘",
              meta: "KR market / quick mode",
              createdAt: "2026-04-29T19:59:59Z",
            },
            {
              id: "msg_assistant_news",
              role: "assistant",
              content: "Apple Inc (AAPL) 관련 최신 뉴스 핵심 1건을 정리했습니다.",
              meta: "뉴스 요약",
              createdAt: "2026-04-29T20:00:00Z",
              newsDigest: {
                digestId: "digest_apple",
                status: "completed",
                market: "US",
                symbol: "AAPL",
                stockName: "Apple Inc",
                query: "Apple Inc AAPL stock news",
                generatedAt: "2026-04-29T20:00:00Z",
                summary: "애플 뉴스 핵심은 실적, AI 전략, 공급망입니다.",
                keyPoints: ["Apple earnings preview highlights services growth"],
                importantArticles: [
                  {
                    id: "news_1",
                    title: "Apple earnings preview highlights services growth",
                    url: "https://example.com/apple-earnings",
                    source: "Example Markets",
                    publishedAt: "2026-04-29T13:00:00-04:00",
                    snippet: "Investors are watching services and iPhone demand.",
                    provider: "tavily_news",
                    query: "Apple Inc AAPL stock news",
                    rank: 0,
                    category: "earnings",
                    headlineKo: "오늘 Q2 2026 실적 발표 예정",
                    summaryKo: "애플은 장 마감 후 실적 컨퍼런스콜을 진행합니다.",
                    importanceScore: 42,
                    sourceDomain: "businessinsider.com",
                  },
                ],
                additionalArticles: [
                  {
                    id: "news_2",
                    title: "Apple Arcade expands game catalog",
                    url: "https://example.com/apple-arcade",
                    source: "Example Search",
                    publishedAt: "2026-04-27T00:00:00",
                    snippet: "Apple added more services titles.",
                    provider: "serpapi_google_web",
                    query: "Apple Inc AAPL stock news",
                    rank: 0,
                    category: "product_service",
                    headlineKo: "Apple Arcade 게임 카탈로그 확대",
                    summaryKo: "애플은 서비스 카탈로그에 신규 타이틀을 추가했습니다.",
                    importanceScore: 14,
                    sourceDomain: "example.com",
                  },
                ],
                providerRuns: [
                  {
                    provider: "tavily_news",
                    query: "Apple Inc AAPL stock news",
                    resultCount: 2,
                    status: "completed",
                    warning: null,
                  },
                  {
                    provider: "serpapi_google_web",
                    query: "Apple Inc AAPL stock news",
                    resultCount: 1,
                    status: "completed",
                    warning: null,
                  },
                ],
                warnings: [],
              },
            },
          ],
        }}
        settings={{
          provider: "openai",
          analysisMode: "quick",
          defaultMarket: "US",
          defaultHorizon: "swing",
        }}
        copy={uiCopy.ko.chat}
        onAnalysisChange={vi.fn()}
        onSendMessage={vi.fn()}
        responseLanguage="ko"
      />,
    );

    expect(screen.getByLabelText("Apple Inc news digest")).toBeInTheDocument();
    expect(screen.getByText("애플 뉴스 핵심은 실적, AI 전략, 공급망입니다.")).toBeInTheDocument();
    expect(screen.getAllByText("오늘 Q2 2026 실적 발표 예정")).toHaveLength(2);
    expect(
      screen.getAllByText("애플은 장 마감 후 실적 컨퍼런스콜을 진행합니다."),
    ).toHaveLength(2);
    expect(
      screen.getByRole("link", {
        name: "Apple earnings preview highlights services growth",
      }),
    ).toHaveAttribute("href", "https://example.com/apple-earnings");
    expect(screen.getByAltText("businessinsider.com icon")).toBeInTheDocument();
    expect(screen.getByText("earnings")).toBeInTheDocument();
    expect(screen.getByText("businessinsider.com · tavily_news")).toBeInTheDocument();
    expect(screen.getByText("검색 출처")).toBeInTheDocument();
    expect(screen.getByText("tavily_news: 2")).toBeInTheDocument();
    expect(screen.queryByText("Apple Arcade 게임 카탈로그 확대")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "나머지 기사 보기 (1)" }));

    expect(screen.getByText("Apple Arcade 게임 카탈로그 확대")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Apple Arcade expands game catalog" }),
    ).toHaveAttribute("href", "https://example.com/apple-arcade");
  });
});
