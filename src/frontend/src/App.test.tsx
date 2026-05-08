import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import {
  clearConversations,
  deleteConversation,
  deleteExternalCredentialProfile,
  deleteLlmCredential,
  fetchConversation,
  fetchConversations,
  fetchExternalCredentialProfiles,
  fetchLlmCredentialProfiles,
  fetchLlmCredentialStatus,
  fetchMarketQuote,
  fetchSettings,
  runBacktest,
  saveExternalCredential,
  saveLlmCredential,
  saveSettings,
  selectExternalCredentialProfile,
  selectLlmCredentialProfile,
  sendConversationMessage,
  testLlmCredential,
} from "./shared/api";
import type { MarketQuote } from "./shared/types";

vi.mock("./shared/api", () => ({
  clearConversations: vi.fn(),
  deleteConversation: vi.fn(),
  deleteExternalCredentialProfile: vi.fn(),
  deleteLlmCredential: vi.fn(),
  fetchConversation: vi.fn(),
  fetchConversations: vi.fn(),
  fetchExternalCredentialProfiles: vi.fn(),
  fetchLlmCredentialProfiles: vi.fn(),
  fetchLlmCredentialStatus: vi.fn(),
  fetchMarketQuote: vi.fn(),
  fetchSettings: vi.fn(),
  runBacktest: vi.fn(),
  saveExternalCredential: vi.fn(),
  saveLlmCredential: vi.fn(),
  saveSettings: vi.fn(),
  selectExternalCredentialProfile: vi.fn(),
  selectLlmCredentialProfile: vi.fn(),
  sendConversationMessage: vi.fn(),
  testLlmCredential: vi.fn(),
}));

const usSettings = {
  analysisMode: "quick",
  defaultMarket: "US",
  defaultHorizon: "swing",
} as const;

const appleQuote: MarketQuote = {
  market: "US",
  symbol: "AAPL",
  name: "Apple",
  exchange: "NASDAQ",
  currency: "USD",
  lastPrice: 207.15,
  previousClose: null,
  changePct: null,
  asOfAt: "2026-04-24T16:00:00-04:00",
  source: "seeded_local_fixture",
  chartWindow: "1D",
  chartBars: [],
  keyStats: [],
  newsItems: [],
};

const emptyCredentialStatus = {
  configured: false,
  credentialId: null,
  label: null,
  provider: null,
  model: null,
  baseUrl: null,
  apiKeyMask: null,
  keySource: null,
  isActive: false,
  createdAt: null,
  updatedAt: null,
} as const;

const emptyExternalCredentialProfiles = {
  activeCredentialIds: {},
  credentials: [],
};

function installMemoryStorage() {
  const store = new Map<string, string>();
  const storage: Storage = {
    get length() {
      return store.size;
    },
    clear: () => store.clear(),
    getItem: (key: string) => store.get(key) ?? null,
    key: (index: number) => Array.from(store.keys())[index] ?? null,
    removeItem: (key: string) => {
      store.delete(key);
    },
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
  };

  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: storage,
  });
}

describe("App", () => {
  beforeEach(() => {
    installMemoryStorage();
    vi.mocked(fetchSettings).mockResolvedValue(usSettings);
    vi.mocked(fetchConversations).mockResolvedValue([]);
    vi.mocked(fetchConversation).mockReset();
    vi.mocked(deleteConversation).mockResolvedValue(1);
    vi.mocked(clearConversations).mockResolvedValue(0);
    vi.mocked(fetchLlmCredentialStatus).mockResolvedValue(emptyCredentialStatus);
    vi.mocked(fetchLlmCredentialProfiles).mockResolvedValue({
      activeCredentialId: null,
      credentials: [],
    });
    vi.mocked(fetchExternalCredentialProfiles).mockResolvedValue(emptyExternalCredentialProfiles);
    vi.mocked(fetchMarketQuote).mockResolvedValue(appleQuote);
    vi.mocked(saveLlmCredential).mockResolvedValue(emptyCredentialStatus);
    vi.mocked(deleteLlmCredential).mockResolvedValue(emptyCredentialStatus);
    vi.mocked(selectLlmCredentialProfile).mockResolvedValue(emptyCredentialStatus);
    vi.mocked(saveExternalCredential).mockReset();
    vi.mocked(deleteExternalCredentialProfile).mockReset();
    vi.mocked(selectExternalCredentialProfile).mockReset();
    vi.mocked(saveSettings).mockResolvedValue(usSettings);
    vi.mocked(sendConversationMessage).mockReset();
    vi.mocked(runBacktest).mockReset();
    vi.mocked(testLlmCredential).mockResolvedValue({
      configured: false,
      status: "setup_needed",
      provider: null,
      model: null,
      baseUrl: null,
      keySource: null,
      errorCode: null,
      message: "Save an LLM provider key before testing the connection.",
    });
  });

  it("loads the initial quote for the configured default market", async () => {
    render(<App />);

    await waitFor(() => {
      expect(fetchMarketQuote).toHaveBeenCalledWith("US", "AAPL");
    });
  });

  it("surfaces settings save failures", async () => {
    vi.mocked(saveSettings).mockRejectedValueOnce(new Error("network failed"));

    render(<App />);

    await screen.findByRole("heading", { name: "Stock Analysis Agent" });
    fireEvent.click(screen.getByRole("button", { name: "Analysis" }));
    await screen.findByDisplayValue("US");
    fireEvent.click(screen.getByRole("button", { name: "Save settings" }));

    await waitFor(() => {
      expect(screen.getByText("Settings could not be saved.")).toBeInTheDocument();
    });
  });

  it("switches between English and Korean UI copy", async () => {
    render(<App />);

    await screen.findByRole("heading", { name: "Stock Analysis Agent" });
    fireEvent.click(screen.getByRole("button", { name: "Settings" }));
    fireEvent.click(screen.getByRole("button", { name: "한국어" }));

    expect(screen.getByRole("heading", { name: "주식 분석 에이전트" })).toBeInTheDocument();
    expect(screen.getByLabelText("메시지")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "전송" })).toBeInTheDocument();
  });

  it("sends the active UI language with chat messages", async () => {
    vi.mocked(sendConversationMessage).mockResolvedValueOnce({
      conversationId: "conv_language",
      status: "needs_input",
      missingInputs: ["horizon"],
      analysisRequest: null,
      analysisResult: null,
      marketSnapshot: null,
      messages: [
        {
          id: "msg_user",
          role: "user",
          content: "Should I buy Samsung Electronics?",
          meta: "KR market / quick mode",
          createdAt: "2026-04-28T00:00:00Z",
        },
        {
          id: "msg_assistant",
          role: "assistant",
          content: "어떤 투자 기간을 사용할까요?",
          meta: "기간 필요",
          createdAt: "2026-04-28T00:00:01Z",
        },
      ],
    });

    render(<App />);

    await screen.findByRole("heading", { name: "Stock Analysis Agent" });
    fireEvent.click(screen.getByRole("button", { name: "Settings" }));
    fireEvent.click(screen.getByRole("button", { name: "한국어" }));
    fireEvent.change(screen.getByLabelText("메시지"), {
      target: { value: "Should I buy Samsung Electronics?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "전송" }));

    await waitFor(() => {
      expect(sendConversationMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          content: "Should I buy Samsung Electronics?",
          responseLanguage: "ko",
        }),
      );
    });
  });

  it("switches between dark and light themes", async () => {
    render(<App />);

    const shell = await screen.findByRole("main");
    expect(shell).toHaveAttribute("data-theme", "dark");

    fireEvent.click(screen.getByRole("button", { name: "Settings" }));
    fireEvent.click(screen.getByRole("button", { name: "Light" }));

    expect(shell).toHaveAttribute("data-theme", "light");
  });

  it("uses sidebar navigation for analysis snapshot and backtest views", async () => {
    render(<App />);

    await screen.findByRole("heading", { name: "Stock Analysis Agent" });

    expect(screen.getByRole("button", { name: "Chat" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analysis" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Snapshot" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Backtest" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Analysis" }));
    expect(screen.getByRole("heading", { name: "Analysis defaults" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Snapshot" }));
    expect(screen.getByRole("heading", { name: "Market snapshot" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Backtest" }));
    expect(screen.getByRole("heading", { name: "PnL curve" })).toBeInTheDocument();
  });

  it("loads previous conversations from the left rail", async () => {
    vi.mocked(fetchConversations).mockResolvedValueOnce([
      {
        conversationId: "conv_aapl",
        title: "AAPL",
        status: "market_snapshot",
        updatedAt: "2026-04-28T20:00:00Z",
        lastMessage: "Here is the market snapshot for Apple.",
      },
    ]);
    vi.mocked(fetchConversation).mockResolvedValueOnce({
      conversationId: "conv_aapl",
      status: "market_snapshot",
      missingInputs: [],
      analysisRequest: null,
      analysisResult: null,
      marketSnapshot: null,
      messages: [
        {
          id: "msg_assistant",
          role: "assistant",
          content: "Loaded AAPL snapshot.",
          meta: "market snapshot",
          createdAt: "2026-04-28T20:00:00Z",
        },
      ],
    });

    render(<App />);

    await screen.findByRole("button", { name: "AAPL" });
    fireEvent.click(screen.getByRole("button", { name: "AAPL" }));

    await screen.findByText("Loaded AAPL snapshot.");
    expect(fetchConversation).toHaveBeenCalledWith("conv_aapl");
  });

  it("opens a fresh empty chat when New chat is clicked", async () => {
    vi.mocked(sendConversationMessage).mockResolvedValueOnce({
      conversationId: "conv_sent",
      status: "market_snapshot",
      missingInputs: [],
      analysisRequest: null,
      analysisResult: null,
      marketSnapshot: null,
      messages: [
        {
          id: "msg_user_sent",
          role: "user",
          content: "AAPL",
          meta: "US market / quick mode",
          createdAt: "2026-04-29T00:00:00Z",
        },
        {
          id: "msg_assistant_sent",
          role: "assistant",
          content: "Loaded AAPL snapshot.",
          meta: "market snapshot",
          createdAt: "2026-04-29T00:00:01Z",
        },
      ],
    });

    render(<App />);

    await screen.findByRole("heading", { name: "Stock Analysis Agent" });
    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "AAPL" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(
        within(screen.getByLabelText("Conversation")).getByText("Loaded AAPL snapshot."),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "New chat" }));

    await waitFor(() => {
      expect(
        within(screen.getByLabelText("Conversation")).queryByText("Loaded AAPL snapshot."),
      ).not.toBeInTheDocument();
    });
    expect(
      within(screen.getByLabelText("Conversation")).getByText(
        "Samsung Electronics and AAPL are ready as seeded market-data fixtures.",
      ),
    ).toBeInTheDocument();
  });

  it("deletes a previous conversation from the left rail", async () => {
    vi.mocked(fetchConversations).mockResolvedValueOnce([
      {
        conversationId: "conv_aapl",
        title: "AAPL",
        status: "market_snapshot",
        updatedAt: "2026-04-28T20:00:00Z",
        lastMessage: "Here is the market snapshot for Apple.",
      },
    ]);

    render(<App />);

    await screen.findByRole("button", { name: "AAPL" });
    fireEvent.click(screen.getByRole("button", { name: "Delete AAPL" }));

    await waitFor(() => {
      expect(deleteConversation).toHaveBeenCalledWith("conv_aapl");
    });
    expect(screen.queryByRole("button", { name: /^AAPL/ })).not.toBeInTheDocument();
    expect(screen.getByText("No saved conversations")).toBeInTheDocument();
  });

  it("clears all conversations from settings", async () => {
    vi.mocked(fetchConversations).mockResolvedValueOnce([
      {
        conversationId: "conv_aapl",
        title: "AAPL",
        status: "market_snapshot",
        updatedAt: "2026-04-28T20:00:00Z",
        lastMessage: "Here is the market snapshot for Apple.",
      },
    ]);
    vi.mocked(clearConversations).mockResolvedValueOnce(1);
    Object.defineProperty(window, "confirm", {
      configurable: true,
      value: vi.fn(() => true),
    });

    render(<App />);

    await screen.findByRole("button", { name: "AAPL" });
    fireEvent.click(screen.getByRole("button", { name: "Settings" }));
    fireEvent.click(screen.getByRole("button", { name: "Security" }));
    fireEvent.click(screen.getByRole("button", { name: "Clear chat history" }));

    await waitFor(() => {
      expect(clearConversations).toHaveBeenCalledTimes(1);
    });
    expect(screen.queryByRole("button", { name: /^AAPL/ })).not.toBeInTheDocument();
  });

  it("opens a settings modal for general model and security settings", async () => {
    render(<App />);

    await screen.findByRole("heading", { name: "Stock Analysis Agent" });
    fireEvent.click(screen.getByRole("button", { name: "Settings" }));

    expect(screen.getByRole("dialog", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "General" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Model" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Security" })).toBeInTheDocument();
    expect(screen.getByText("Language")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Model" }));
    expect(screen.getByLabelText("Provider")).toBeInTheDocument();
    expect(screen.getByLabelText("API key")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Security" }));
    expect(screen.getByText("Credential storage")).toBeInTheDocument();
  });

  it("saves and deletes local LLM credentials from the model settings", async () => {
    const configuredStatus = {
      configured: true,
      credentialId: "cerebras_fast",
      label: "Cerebras fast",
      provider: "cerebras",
      model: "llama3.1-8b",
      baseUrl: "https://api.cerebras.ai/v1",
      apiKeyMask: "csk-...7890",
      keySource: "local_encrypted_state",
      isActive: true,
      createdAt: "2026-04-27T12:00:00+09:00",
      updatedAt: "2026-04-27T12:00:00+09:00",
    } as const;
    vi.mocked(saveLlmCredential).mockResolvedValueOnce(configuredStatus);
    vi.mocked(deleteLlmCredential).mockResolvedValueOnce(emptyCredentialStatus);
    Object.defineProperty(window, "confirm", {
      configurable: true,
      value: vi.fn(() => true),
    });

    render(<App />);

    await screen.findByRole("heading", { name: "Stock Analysis Agent" });
    fireEvent.click(screen.getByRole("button", { name: "Settings" }));
    fireEvent.click(screen.getByRole("button", { name: "Model" }));
    fireEvent.change(screen.getByLabelText("API key"), {
      target: { value: "csk-live-secret-7890" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save API Key" }));

    await waitFor(() => {
      expect(saveLlmCredential).toHaveBeenCalledWith(expect.objectContaining({
        provider: "cerebras",
        model: "llama3.1-8b",
        baseUrl: null,
        apiKey: "csk-live-secret-7890",
        makeActive: true,
      }));
    });
    expect(screen.getByText("csk-...7890")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Delete API Key" }));

    await waitFor(() => {
      expect(deleteLlmCredential).toHaveBeenCalledTimes(1);
    });
  });
});
