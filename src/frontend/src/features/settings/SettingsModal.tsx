import {
  FormEvent,
  KeyboardEvent,
  MouseEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import type { UiCopy } from "../../shared/i18n";
import type {
  CredentialProvider,
  ExternalCredentialProvider,
  ExternalCredentialStatus,
  LlmConnectionTestResult,
  LlmCredentialStatus,
  SaveExternalCredentialRequest,
  SaveLlmCredentialRequest,
  UiPreferences,
} from "../../shared/types";

type SettingsTab = "general" | "model" | "security";

interface SettingsModalProps {
  activeCredentialId?: string | null;
  copy: UiCopy["settingsModal"];
  credentialProfiles?: LlmCredentialStatus[];
  credentialStatus: LlmCredentialStatus;
  externalCredentialProfiles?: ExternalCredentialStatus[];
  onClearConversations: () => Promise<number>;
  onClose: () => void;
  onDeleteCredential: () => Promise<LlmCredentialStatus>;
  onDeleteExternalCredential?: (credentialId: string) => Promise<ExternalCredentialStatus>;
  onSaveCredential: (request: SaveLlmCredentialRequest) => Promise<LlmCredentialStatus>;
  onSaveExternalCredential?: (
    request: SaveExternalCredentialRequest,
  ) => Promise<ExternalCredentialStatus>;
  onSelectCredential?: (credentialId: string) => Promise<LlmCredentialStatus>;
  onSelectExternalCredential?: (credentialId: string) => Promise<ExternalCredentialStatus>;
  onTestCredential: () => Promise<LlmConnectionTestResult>;
  onUiPreferencesChange: (preferences: UiPreferences) => void;
  uiPreferences: UiPreferences;
}

const DEFAULT_PROVIDER: CredentialProvider = "cerebras";
const DEFAULT_MODEL_BY_PROVIDER: Record<CredentialProvider, string> = {
  openai: "gpt-4.1-mini",
  anthropic: "claude-3-5-sonnet-latest",
  cerebras: "llama3.1-8b",
  custom: "",
};
const DEFAULT_BASE_URL_BY_PROVIDER: Record<CredentialProvider, string> = {
  openai: "https://api.openai.com/v1",
  anthropic: "https://api.anthropic.com/v1",
  cerebras: "https://api.cerebras.ai/v1",
  custom: "",
};
const MODEL_OPTIONS_BY_PROVIDER: Partial<Record<CredentialProvider, string[]>> = {
  cerebras: ["llama3.1-8b", "qwen-3-235b-a22b-instruct-2507"],
};
const NEWS_PROVIDER_OPTIONS: ExternalCredentialProvider[] = [
  "tavily",
  "gnews",
  "serpapi",
  "eventregistry",
];
const FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "a[href]",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

export function SettingsModal({
  activeCredentialId = null,
  copy,
  credentialProfiles = [],
  credentialStatus,
  externalCredentialProfiles = [],
  onClearConversations,
  onClose,
  onDeleteCredential,
  onDeleteExternalCredential,
  onSaveCredential,
  onSaveExternalCredential,
  onSelectCredential,
  onSelectExternalCredential,
  onTestCredential,
  onUiPreferencesChange,
  uiPreferences,
}: SettingsModalProps) {
  const dialogRef = useRef<HTMLElement | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [provider, setProvider] = useState<CredentialProvider>(
    credentialStatus.provider ?? DEFAULT_PROVIDER,
  );
  const [model, setModel] = useState(
    credentialStatus.model ?? DEFAULT_MODEL_BY_PROVIDER[DEFAULT_PROVIDER],
  );
  const [baseUrl, setBaseUrl] = useState(credentialStatus.baseUrl ?? "");
  const [apiKey, setApiKey] = useState("");
  const [keyLabel, setKeyLabel] = useState(credentialStatus.label ?? "");
  const [newsProvider, setNewsProvider] = useState<ExternalCredentialProvider>("tavily");
  const [newsKeyLabel, setNewsKeyLabel] = useState("");
  const [newsApiKey, setNewsApiKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<LlmConnectionTestResult | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isClearingConversations, setIsClearingConversations] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isSavingExternal, setIsSavingExternal] = useState(false);

  useEffect(() => {
    const nextProvider = credentialStatus.provider ?? DEFAULT_PROVIDER;
    setProvider(nextProvider);
    setModel(credentialStatus.model ?? DEFAULT_MODEL_BY_PROVIDER[nextProvider]);
    setBaseUrl(credentialStatus.baseUrl ?? "");
    setKeyLabel(credentialStatus.label ?? "");
    setTestResult(null);
  }, [credentialStatus]);

  useEffect(() => {
    const previousFocus =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    closeButtonRef.current?.focus();
    return () => previousFocus?.focus();
  }, []);

  function focusableElements(): HTMLElement[] {
    return Array.from(
      dialogRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR) ?? [],
    );
  }

  function handleBackdropClick(event: MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget) {
      onClose();
    }
  }

  function handleDialogKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
      return;
    }

    if (event.key !== "Tab") {
      return;
    }

    const elements = focusableElements();
    if (elements.length === 0) {
      event.preventDefault();
      return;
    }

    const firstElement = elements[0];
    const lastElement = elements[elements.length - 1];
    const activeElement = document.activeElement;

    if (event.shiftKey && activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
      return;
    }

    if (!event.shiftKey && activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  }

  async function handleSaveCredential(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedApiKey = apiKey.trim();
    const trimmedModel = model.trim();
    if (!trimmedApiKey) {
      setError(copy.rawKeyRequired);
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      await onSaveCredential({
        credentialId: `${provider}_${Date.now().toString(36)}`,
        label: keyLabel.trim() || null,
        provider,
        model: trimmedModel || DEFAULT_MODEL_BY_PROVIDER[provider],
        baseUrl: baseUrl.trim() || null,
        apiKey: trimmedApiKey,
        makeActive: true,
      });
      setApiKey("");
    } catch {
      setError(copy.saveError);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleTestCredential() {
    setIsTesting(true);
    setError(null);
    try {
      setTestResult(await onTestCredential());
    } catch {
      setTestResult({
        configured: credentialStatus.configured,
        status: "provider_error",
        provider: credentialStatus.provider,
        model: credentialStatus.model,
        baseUrl: credentialStatus.baseUrl,
        keySource: credentialStatus.keySource,
        errorCode: null,
        message: copy.testError,
      });
    } finally {
      setIsTesting(false);
    }
  }

  async function handleDeleteCredential() {
    if (!credentialStatus.configured || !window.confirm(copy.deleteConfirm)) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    try {
      await onDeleteCredential();
      setApiKey("");
    } catch {
      setError(copy.deleteError);
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleSelectCredential(credentialId: string) {
    if (!onSelectCredential) {
      return;
    }
    setIsSaving(true);
    setError(null);
    try {
      await onSelectCredential(credentialId);
    } catch {
      setError(copy.selectKeyError);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSaveExternalCredential(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!onSaveExternalCredential) {
      return;
    }
    const trimmedApiKey = newsApiKey.trim();
    if (!trimmedApiKey) {
      setError(copy.rawKeyRequired);
      return;
    }
    setIsSavingExternal(true);
    setError(null);
    try {
      await onSaveExternalCredential({
        credentialId: `${newsProvider}_${Date.now().toString(36)}`,
        label: newsKeyLabel.trim() || null,
        provider: newsProvider,
        apiKey: trimmedApiKey,
        makeActive: true,
      });
      setNewsApiKey("");
    } catch {
      setError(copy.saveError);
    } finally {
      setIsSavingExternal(false);
    }
  }

  async function handleSelectExternalCredential(credentialId: string) {
    if (!onSelectExternalCredential) {
      return;
    }
    setIsSavingExternal(true);
    setError(null);
    try {
      await onSelectExternalCredential(credentialId);
    } catch {
      setError(copy.selectKeyError);
    } finally {
      setIsSavingExternal(false);
    }
  }

  async function handleDeleteExternalCredential(credentialId: string) {
    if (!onDeleteExternalCredential || !window.confirm(copy.deleteConfirm)) {
      return;
    }
    setIsSavingExternal(true);
    setError(null);
    try {
      await onDeleteExternalCredential(credentialId);
    } catch {
      setError(copy.deleteError);
    } finally {
      setIsSavingExternal(false);
    }
  }

  async function handleClearConversations() {
    if (!window.confirm(copy.clearConversationsConfirm)) {
      return;
    }

    setIsClearingConversations(true);
    setError(null);
    try {
      await onClearConversations();
    } catch {
      setError(copy.clearConversationsError);
    } finally {
      setIsClearingConversations(false);
    }
  }

  function defaultModelValues(): string[] {
    return Object.values(DEFAULT_MODEL_BY_PROVIDER).filter(Boolean);
  }

  function defaultBaseUrlValues(): string[] {
    return Object.values(DEFAULT_BASE_URL_BY_PROVIDER).filter(Boolean);
  }

  function handleProviderChange(nextProvider: CredentialProvider) {
    setProvider(nextProvider);
    if (!model.trim() || defaultModelValues().includes(model)) {
      setModel(DEFAULT_MODEL_BY_PROVIDER[nextProvider]);
    }
    if (!baseUrl.trim() || defaultBaseUrlValues().includes(baseUrl)) {
      setBaseUrl(DEFAULT_BASE_URL_BY_PROVIDER[nextProvider]);
    }
    setTestResult(null);
  }

  const modelOptions = MODEL_OPTIONS_BY_PROVIDER[provider] ?? [];

  return (
    <div
      className="modal-backdrop"
      data-testid="settings-backdrop"
      onClick={handleBackdropClick}
      onKeyDown={handleDialogKeyDown}
    >
      <section
        aria-label={copy.title}
        aria-modal="true"
        className="settings-dialog"
        ref={dialogRef}
        role="dialog"
      >
        <header className="settings-dialog-header">
          <h2>{copy.title}</h2>
          <button
            aria-label={copy.close}
            className="icon-button"
            onClick={onClose}
            ref={closeButtonRef}
            type="button"
          >
            x
          </button>
        </header>

        <div className="settings-dialog-body">
          <nav aria-label={copy.aria} className="settings-tabs">
            {(["general", "model", "security"] as const).map((tab) => (
              <button
                aria-pressed={activeTab === tab}
                className={activeTab === tab ? "is-active" : ""}
                key={tab}
                onClick={() => setActiveTab(tab)}
                type="button"
              >
                {copy.tabs[tab]}
              </button>
            ))}
          </nav>

          <div className="settings-pane">
            {activeTab === "general" ? (
              <section className="modal-section">
                <div className="control-group">
                  <span>{copy.language}</span>
                  <div className="segmented-control">
                    <button
                      className={uiPreferences.language === "en" ? "is-active" : ""}
                      onClick={() =>
                        onUiPreferencesChange({ ...uiPreferences, language: "en" })
                      }
                      type="button"
                    >
                      {copy.english}
                    </button>
                    <button
                      className={uiPreferences.language === "ko" ? "is-active" : ""}
                      onClick={() =>
                        onUiPreferencesChange({ ...uiPreferences, language: "ko" })
                      }
                      type="button"
                    >
                      {copy.korean}
                    </button>
                  </div>
                </div>
                <div className="control-group">
                  <span>{copy.theme}</span>
                  <div className="segmented-control">
                    <button
                      className={uiPreferences.theme === "dark" ? "is-active" : ""}
                      onClick={() =>
                        onUiPreferencesChange({ ...uiPreferences, theme: "dark" })
                      }
                      type="button"
                    >
                      {copy.dark}
                    </button>
                    <button
                      className={uiPreferences.theme === "light" ? "is-active" : ""}
                      onClick={() =>
                        onUiPreferencesChange({ ...uiPreferences, theme: "light" })
                      }
                      type="button"
                    >
                      {copy.light}
                    </button>
                  </div>
                </div>
              </section>
            ) : null}

            {activeTab === "model" ? (
              <section className="modal-section">
                <div className="credential-status" aria-live="polite">
                  <span>{credentialStatus.configured ? copy.configured : copy.notConfigured}</span>
                  {credentialStatus.apiKeyMask ? (
                    <strong>{credentialStatus.apiKeyMask}</strong>
                  ) : null}
                </div>
                {credentialProfiles.length ? (
                  <div className="credential-profile-list" aria-label={copy.savedKeys}>
                    <span>{copy.savedKeys}</span>
                    {credentialProfiles.map((profile) => (
                      <button
                        className={
                          profile.credentialId === activeCredentialId ? "is-active" : ""
                        }
                        disabled={!profile.credentialId || isSaving}
                        key={profile.credentialId ?? `${profile.provider}:${profile.model}`}
                        onClick={() =>
                          profile.credentialId
                            ? void handleSelectCredential(profile.credentialId)
                            : undefined
                        }
                        type="button"
                      >
                        <strong>{profile.label || profile.model || profile.provider}</strong>
                        <span>{profile.apiKeyMask}</span>
                      </button>
                    ))}
                  </div>
                ) : null}
                <form className="settings-form" onSubmit={handleSaveCredential}>
                  <label className="field">
                    <span>{copy.keyLabel}</span>
                    <input
                      aria-label={copy.keyLabel}
                      autoComplete="off"
                      name="key-label"
                      onChange={(event) => setKeyLabel(event.target.value)}
                      placeholder={copy.keyLabelPlaceholder}
                      value={keyLabel}
                    />
                  </label>
                  <label className="field">
                    <span>{copy.provider}</span>
                    <select
                      aria-label={copy.provider}
                      name="provider"
                      onChange={(event) =>
                        handleProviderChange(event.target.value as CredentialProvider)
                      }
                      value={provider}
                    >
                      <option value="openai">{copy.providers.openai}</option>
                      <option value="anthropic">{copy.providers.anthropic}</option>
                      <option value="cerebras">{copy.providers.cerebras}</option>
                      <option value="custom">{copy.providers.custom}</option>
                    </select>
                    {provider === "anthropic" ? (
                      <small>{copy.anthropicUnsupported}</small>
                    ) : null}
                    {provider === "cerebras" ? <small>{copy.cerebrasModelHint}</small> : null}
                  </label>
                  <label className="field">
                    <span>{copy.model}</span>
                    <input
                      aria-label={copy.model}
                      autoComplete="off"
                      list={modelOptions.length ? "llm-model-options" : undefined}
                      name="model"
                      onChange={(event) => setModel(event.target.value)}
                      placeholder={copy.modelPlaceholder}
                      spellCheck={false}
                      value={model}
                    />
                    {modelOptions.length ? (
                      <datalist id="llm-model-options">
                        {modelOptions.map((option) => (
                          <option key={option} value={option} />
                        ))}
                      </datalist>
                    ) : null}
                  </label>
                  <label className="field">
                    <span>{copy.baseUrl}</span>
                    <input
                      aria-label={copy.baseUrl}
                      autoComplete="off"
                      inputMode="url"
                      name="base-url"
                      onChange={(event) => setBaseUrl(event.target.value)}
                      placeholder={copy.baseUrlPlaceholder}
                      spellCheck={false}
                      type="url"
                      value={baseUrl}
                    />
                    <small>{copy.optionalBaseUrl}</small>
                  </label>
                  <label className="field">
                    <span>{copy.apiKey}</span>
                    <input
                      aria-label={copy.apiKey}
                      autoComplete="off"
                      name="llm-api-key"
                      onChange={(event) => setApiKey(event.target.value)}
                      placeholder={copy.apiKeyPlaceholder}
                      spellCheck={false}
                      type="password"
                      value={apiKey}
                    />
                  </label>
                  <div className="settings-actions">
                    <button disabled={isSaving} type="submit">
                      {copy.saveApiKey}
                    </button>
                    <button
                      className="secondary-action"
                      disabled={!credentialStatus.configured || isTesting}
                      onClick={() => void handleTestCredential()}
                      type="button"
                    >
                      {isTesting ? copy.testingConnection : copy.testConnection}
                    </button>
                    <button
                      className="secondary-action"
                      disabled={!credentialStatus.configured || isDeleting}
                      onClick={() => void handleDeleteCredential()}
                      type="button"
                    >
                      {copy.deleteApiKey}
                    </button>
                  </div>
                </form>
                {testResult ? (
                  <div
                    className={`connection-test-result is-${testResult.status}`}
                    role="status"
                  >
                    <strong>
                      {testResult.provider ?? "-"}
                      {testResult.model ? ` / ${testResult.model}` : ""}
                    </strong>
                    <span>{testResult.message}</span>
                  </div>
                ) : null}
                <div className="settings-subsection">
                  <div className="credential-status" aria-live="polite">
                    <span>{copy.newsKeys}</span>
                    <strong>{copy.newsKeyHint}</strong>
                  </div>
                  {externalCredentialProfiles.length ? (
                    <div className="credential-profile-list" aria-label={copy.newsSavedKeys}>
                      <span>{copy.newsSavedKeys}</span>
                      {externalCredentialProfiles.map((profile) => (
                        <button
                          className={profile.isActive ? "is-active" : ""}
                          disabled={!profile.credentialId || isSavingExternal}
                          key={profile.credentialId ?? `${profile.provider}:${profile.apiKeyMask}`}
                          onClick={() =>
                            profile.credentialId
                              ? void handleSelectExternalCredential(profile.credentialId)
                              : undefined
                          }
                          type="button"
                        >
                          <strong>{profile.label || profile.provider}</strong>
                          <span>{profile.apiKeyMask}</span>
                        </button>
                      ))}
                    </div>
                  ) : null}
                  <form className="settings-form" onSubmit={handleSaveExternalCredential}>
                    <label className="field">
                      <span>{copy.newsKeyLabel}</span>
                      <input
                        aria-label={copy.newsKeyLabel}
                        autoComplete="off"
                        name="news-key-label"
                        onChange={(event) => setNewsKeyLabel(event.target.value)}
                        placeholder={copy.newsKeyLabelPlaceholder}
                        value={newsKeyLabel}
                      />
                    </label>
                    <label className="field">
                      <span>{copy.newsProvider}</span>
                      <select
                        aria-label={copy.newsProvider}
                        name="news-provider"
                        onChange={(event) =>
                          setNewsProvider(event.target.value as ExternalCredentialProvider)
                        }
                        value={newsProvider}
                      >
                        {NEWS_PROVIDER_OPTIONS.map((option) => (
                          <option key={option} value={option}>
                            {copy.newsProviders[option]}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      <span>{copy.newsApiKey}</span>
                      <input
                        aria-label={copy.newsApiKey}
                        autoComplete="off"
                        name="news-api-key"
                        onChange={(event) => setNewsApiKey(event.target.value)}
                        placeholder={copy.newsApiKeyPlaceholder}
                        spellCheck={false}
                        type="password"
                        value={newsApiKey}
                      />
                    </label>
                    <div className="settings-actions">
                      <button disabled={isSavingExternal} type="submit">
                        {copy.saveNewsKey}
                      </button>
                      {externalCredentialProfiles
                        .filter((profile) => profile.credentialId)
                        .map((profile) => (
                          <button
                            className="secondary-action"
                            disabled={isSavingExternal}
                            key={`delete-${profile.credentialId}`}
                            onClick={() =>
                              profile.credentialId
                                ? void handleDeleteExternalCredential(profile.credentialId)
                                : undefined
                            }
                            type="button"
                          >
                            {copy.deleteNewsKey}
                          </button>
                        ))}
                    </div>
                  </form>
                </div>
                {error ? <p className="inline-error">{error}</p> : null}
              </section>
            ) : null}

            {activeTab === "security" ? (
              <section className="modal-section">
                <dl className="security-list">
                  <div>
                    <dt>{copy.credentialStorage}</dt>
                    <dd>{credentialStatus.configured ? copy.configured : copy.notConfigured}</dd>
                  </div>
                  <div>
                    <dt>{copy.currentKey}</dt>
                    <dd>{credentialStatus.apiKeyMask ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>{copy.keySource}</dt>
                    <dd>{credentialStatus.keySource ?? "-"}</dd>
                  </div>
                </dl>
                <p className="muted-copy">{copy.localOnly}</p>
                <div className="settings-actions">
                  <button
                    className="secondary-action danger-action"
                    disabled={isClearingConversations}
                    onClick={() => void handleClearConversations()}
                    type="button"
                  >
                    {isClearingConversations
                      ? copy.clearingConversations
                      : copy.clearConversations}
                  </button>
                </div>
                {error ? <p className="inline-error">{error}</p> : null}
              </section>
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}
