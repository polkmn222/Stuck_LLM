import { useEffect, useState } from "react";

import { AnalysisPanel } from "./features/analysis/AnalysisPanel";
import { BacktestPanel } from "./features/backtest/BacktestPanel";
import { ChatShell } from "./features/chat/ChatShell";
import { SettingsModal } from "./features/settings/SettingsModal";
import { SettingsPanel } from "./features/settings/SettingsPanel";
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
} from "./shared/api";
import { uiCopy } from "./shared/i18n";
import type {
  AppSettings,
  ConversationSummary,
  ConversationSnapshot,
  LlmCredentialStatus,
  SaveLlmCredentialRequest,
  UiPreferences,
} from "./shared/types";

const DEFAULT_SETTINGS: AppSettings = {
  provider: "openai",
  analysisMode: "quick",
  defaultMarket: "KR",
  defaultHorizon: null,
};

const DEFAULT_SYMBOL_BY_MARKET: Record<AppSettings["defaultMarket"], string> = {
  KR: "005930",
  US: "AAPL",
};

const DEFAULT_UI_PREFERENCES: UiPreferences = {
  language: "en",
  theme: "dark",
};

const DEFAULT_CREDENTIAL_STATUS: LlmCredentialStatus = {
  configured: false,
  provider: null,
  model: null,
  baseUrl: null,
  apiKeyMask: null,
  keySource: null,
  createdAt: null,
  updatedAt: null,
};

type ActiveView = "chat" | "analysis" | "snapshot" | "backtest";

const UI_STORAGE_KEY = "stuck_llm_ui_preferences";

function loadUiPreferences(): UiPreferences {
  try {
    const stored = window.localStorage.getItem(UI_STORAGE_KEY);
    if (!stored) {
      return DEFAULT_UI_PREFERENCES;
    }
    const parsed = JSON.parse(stored) as Partial<UiPreferences>;
    return {
      language: parsed.language === "ko" ? "ko" : "en",
      theme: parsed.theme === "light" ? "light" : "dark",
    };
  } catch {
    return DEFAULT_UI_PREFERENCES;
  }
}

function saveUiPreferences(preferences: UiPreferences) {
  window.localStorage.setItem(UI_STORAGE_KEY, JSON.stringify(preferences));
}

function seededSnapshot(quote: ConversationSnapshot["marketSnapshot"]): ConversationSnapshot {
  return {
    conversationId: "seeded_market_snapshot",
    status: "needs_input",
    missingInputs: ["horizon"],
    analysisRequest: null,
    marketSnapshot: quote,
    messages: [],
  };
}

export function App() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [snapshot, setSnapshot] = useState<ConversationSnapshot | null>(null);
  const [activeConversation, setActiveConversation] = useState<ConversationSnapshot | null>(null);
  const [chatSessionKey, setChatSessionKey] = useState(0);
  const [conversationSummaries, setConversationSummaries] = useState<ConversationSummary[]>([]);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [hasSettingsError, setHasSettingsError] = useState(false);
  const [activeView, setActiveView] = useState<ActiveView>("chat");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [credentialStatus, setCredentialStatus] = useState<LlmCredentialStatus>(
    DEFAULT_CREDENTIAL_STATUS,
  );
  const [uiPreferences, setUiPreferences] = useState<UiPreferences>(loadUiPreferences);
  const copy = uiCopy[uiPreferences.language];

  useEffect(() => {
    let isCurrent = true;

    async function loadInitialState() {
      const credentialStatusPromise = fetchLlmCredentialStatus().catch(
        () => DEFAULT_CREDENTIAL_STATUS,
      );
      const conversationsPromise = fetchConversations().catch(() => []);
      try {
        const loadedSettings = await fetchSettings();
        const [loadedCredentialStatus, loadedConversations, quote] = await Promise.all([
          credentialStatusPromise,
          conversationsPromise,
          fetchMarketQuote(
            loadedSettings.defaultMarket,
            DEFAULT_SYMBOL_BY_MARKET[loadedSettings.defaultMarket],
          ),
        ]);
        if (isCurrent) {
          setSettings(loadedSettings);
          setCredentialStatus(loadedCredentialStatus);
          setConversationSummaries(loadedConversations);
          setSnapshot(seededSnapshot(quote));
        }
      } catch {
        if (isCurrent) {
          const [loadedCredentialStatus, loadedConversations] = await Promise.all([
            credentialStatusPromise,
            conversationsPromise,
          ]);
          setCredentialStatus(loadedCredentialStatus);
          setConversationSummaries(loadedConversations);
          setSettings(DEFAULT_SETTINGS);
        }
      }
    }

    void loadInitialState();
    return () => {
      isCurrent = false;
    };
  }, []);

  async function handleSaveSettings(nextSettings: AppSettings) {
    setIsSavingSettings(true);
    setHasSettingsError(false);
    try {
      setSettings(await saveSettings(nextSettings));
    } catch {
      setHasSettingsError(true);
    } finally {
      setIsSavingSettings(false);
    }
  }

  function updateUiPreferences(nextPreferences: UiPreferences) {
    setUiPreferences(nextPreferences);
    saveUiPreferences(nextPreferences);
  }

  async function handleSaveCredential(request: SaveLlmCredentialRequest) {
    const nextStatus = await saveLlmCredential(request);
    setCredentialStatus(nextStatus);
    return nextStatus;
  }

  async function handleDeleteCredential() {
    const nextStatus = await deleteLlmCredential();
    setCredentialStatus(nextStatus);
    return nextStatus;
  }

  function mergeConversationSummary(nextSnapshot: ConversationSnapshot) {
    const latestMessage = nextSnapshot.messages[nextSnapshot.messages.length - 1];
    const firstUser = nextSnapshot.messages.find((message) => message.role === "user");
    if (!latestMessage) {
      return;
    }

    const nextSummary: ConversationSummary = {
      conversationId: nextSnapshot.conversationId,
      title: firstUser?.content.slice(0, 64) || nextSnapshot.conversationId,
      status: nextSnapshot.status,
      updatedAt: latestMessage.createdAt,
      lastMessage: latestMessage.content,
    };
    setConversationSummaries((current) => [
      nextSummary,
      ...current.filter((summary) => summary.conversationId !== nextSnapshot.conversationId),
    ]);
  }

  async function handleSendConversationMessage(
    request: Parameters<typeof sendConversationMessage>[0],
  ) {
    const nextSnapshot = await sendConversationMessage(request);
    setActiveConversation(nextSnapshot);
    setSnapshot(nextSnapshot);
    mergeConversationSummary(nextSnapshot);
    return nextSnapshot;
  }

  async function handleSelectConversation(conversationId: string) {
    const loadedConversation = await fetchConversation(conversationId);
    setActiveConversation(loadedConversation);
    setSnapshot(loadedConversation);
    setActiveView("chat");
  }

  function handleNewConversation() {
    setActiveConversation(null);
    setSnapshot(null);
    setChatSessionKey((current) => current + 1);
    setActiveView("chat");
  }

  async function handleDeleteConversation(conversationId: string) {
    await deleteConversation(conversationId);
    setConversationSummaries((current) =>
      current.filter((summary) => summary.conversationId !== conversationId),
    );
    if (activeConversation?.conversationId === conversationId) {
      setActiveConversation(null);
      setSnapshot(null);
    }
  }

  async function handleClearConversations() {
    const deletedCount = await clearConversations();
    setConversationSummaries([]);
    setActiveConversation(null);
    setSnapshot(null);
    setActiveView("chat");
    return deletedCount;
  }

  const navItems: Array<{ view: ActiveView; label: string; icon: string }> = [
    { view: "chat", label: copy.app.navChat, icon: "C" },
    { view: "analysis", label: copy.app.navAnalysis, icon: "A" },
    { view: "snapshot", label: copy.app.navSnapshot, icon: "S" },
    { view: "backtest", label: copy.app.navBacktest, icon: "B" },
  ];

  function renderActiveView() {
    if (activeView === "analysis") {
      return (
        <div className="workspace-page">
          <SettingsPanel
            copy={copy.settings}
            errorMessage={hasSettingsError ? copy.app.settingsError : null}
            isSaving={isSavingSettings}
            onSave={(nextSettings) => void handleSaveSettings(nextSettings)}
            settings={settings}
          />
        </div>
      );
    }

    if (activeView === "snapshot") {
      return (
        <div className="workspace-page">
          <AnalysisPanel copy={copy.analysis} snapshot={snapshot} />
        </div>
      );
    }

    if (activeView === "backtest") {
      return (
        <div className="workspace-page">
          <BacktestPanel copy={copy.backtest} onRunBacktest={runBacktest} />
        </div>
      );
    }

    return (
      <ChatShell
        key={`${chatSessionKey}:${activeConversation?.conversationId ?? "new"}`}
        conversationSnapshot={activeConversation}
        copy={copy.chat}
        onAnalysisChange={setSnapshot}
        onConversationChange={setActiveConversation}
        onFetchMarketQuote={fetchMarketQuote}
        onSendMessage={handleSendConversationMessage}
        responseLanguage={uiPreferences.language}
        settings={settings}
      />
    );
  }

  return (
    <main
      className="app-shell"
      data-language={uiPreferences.language}
      data-theme={uiPreferences.theme}
    >
      <aside className="side-rail" aria-label={copy.app.sidebarAria}>
        <section className="sidebar-brand" aria-label={copy.app.brandTitle}>
          <span className="brand-mark">S</span>
          <div>
            <strong>{copy.app.brandTitle}</strong>
            <p>{copy.app.brandSubtitle}</p>
          </div>
        </section>

        <nav className="rail-nav" aria-label={copy.app.sidebarAria}>
          {navItems.map((item) => (
            <button
              aria-pressed={activeView === item.view}
              className={activeView === item.view ? "rail-button is-active" : "rail-button"}
              key={item.view}
              onClick={() => setActiveView(item.view)}
              type="button"
            >
              <span aria-hidden="true" className="rail-icon">
                {item.icon}
              </span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <section className="conversation-rail" aria-label={copy.app.previousChats}>
          <div className="conversation-rail-heading">
            <span>{copy.app.previousChats}</span>
            <button onClick={handleNewConversation} type="button">
              {copy.app.newChat}
            </button>
          </div>
          <div className="conversation-list">
            {conversationSummaries.length ? (
              conversationSummaries.map((summary) => (
                <div className="conversation-list-item" key={summary.conversationId}>
                  <button
                    aria-label={summary.title}
                    aria-pressed={activeConversation?.conversationId === summary.conversationId}
                    className={
                      activeConversation?.conversationId === summary.conversationId
                        ? "conversation-button is-active"
                        : "conversation-button"
                    }
                    onClick={() => void handleSelectConversation(summary.conversationId)}
                    type="button"
                  >
                    <strong>{summary.title}</strong>
                    <span>{summary.lastMessage}</span>
                  </button>
                  <button
                    aria-label={`${copy.app.deleteChat} ${summary.title}`}
                    className="conversation-delete-button"
                    onClick={() => void handleDeleteConversation(summary.conversationId)}
                    type="button"
                  >
                    x
                  </button>
                </div>
              ))
            ) : (
              <p>{copy.app.noConversations}</p>
            )}
          </div>
        </section>

        <footer className="sidebar-footer">
          <button className="rail-button" onClick={() => setIsSettingsOpen(true)} type="button">
            <span aria-hidden="true" className="rail-icon">
              G
            </span>
            <span>{copy.app.settings}</span>
          </button>
        </footer>
      </aside>

      <section className="workspace" aria-label={copy.app.workspaceAria}>
        {renderActiveView()}
      </section>

      {isSettingsOpen ? (
        <SettingsModal
          copy={copy.settingsModal}
          credentialStatus={credentialStatus}
          onClearConversations={handleClearConversations}
          onClose={() => setIsSettingsOpen(false)}
          onDeleteCredential={handleDeleteCredential}
          onSaveCredential={handleSaveCredential}
          onTestCredential={testLlmCredential}
          onUiPreferencesChange={updateUiPreferences}
          uiPreferences={uiPreferences}
        />
      ) : null}
    </main>
  );
}
