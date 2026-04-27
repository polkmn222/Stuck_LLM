import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import {
  deleteLlmCredential,
  fetchLlmCredentialStatus,
  fetchMarketQuote,
  fetchSettings,
  runBacktest,
  saveLlmCredential,
  saveSettings,
  sendConversationMessage,
} from "./shared/api";

vi.mock("./shared/api", () => ({
  deleteLlmCredential: vi.fn(),
  fetchLlmCredentialStatus: vi.fn(),
  fetchMarketQuote: vi.fn(),
  fetchSettings: vi.fn(),
  runBacktest: vi.fn(),
  saveLlmCredential: vi.fn(),
  saveSettings: vi.fn(),
  sendConversationMessage: vi.fn(),
}));

const usSettings = {
  provider: "openai",
  analysisMode: "quick",
  defaultMarket: "US",
  defaultHorizon: "swing",
} as const;

const appleQuote = {
  market: "US",
  symbol: "AAPL",
  name: "Apple",
  exchange: "NASDAQ",
  currency: "USD",
  lastPrice: 207.15,
  asOfAt: "2026-04-24T16:00:00-04:00",
  source: "seeded_local_fixture",
} as const;

const emptyCredentialStatus = {
  configured: false,
  provider: null,
  model: null,
  baseUrl: null,
  apiKeyMask: null,
  keySource: null,
  createdAt: null,
  updatedAt: null,
} as const;

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
    vi.mocked(fetchLlmCredentialStatus).mockResolvedValue(emptyCredentialStatus);
    vi.mocked(fetchMarketQuote).mockResolvedValue(appleQuote);
    vi.mocked(saveLlmCredential).mockResolvedValue(emptyCredentialStatus);
    vi.mocked(deleteLlmCredential).mockResolvedValue(emptyCredentialStatus);
    vi.mocked(saveSettings).mockResolvedValue(usSettings);
    vi.mocked(sendConversationMessage).mockReset();
    vi.mocked(runBacktest).mockReset();
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
      provider: "openai",
      model: "gpt-4.1-mini",
      baseUrl: "https://api.openai.com/v1",
      apiKeyMask: "sk-...7890",
      keySource: "local_encrypted_state",
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
    fireEvent.change(screen.getByLabelText("Model"), { target: { value: "gpt-4.1-mini" } });
    fireEvent.change(screen.getByLabelText("API key"), {
      target: { value: "sk-live-secret-7890" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save API Key" }));

    await waitFor(() => {
      expect(saveLlmCredential).toHaveBeenCalledWith({
        provider: "openai",
        model: "gpt-4.1-mini",
        baseUrl: null,
        apiKey: "sk-live-secret-7890",
      });
    });
    expect(screen.getByText("sk-...7890")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Delete API Key" }));

    await waitFor(() => {
      expect(deleteLlmCredential).toHaveBeenCalledTimes(1);
    });
  });
});
