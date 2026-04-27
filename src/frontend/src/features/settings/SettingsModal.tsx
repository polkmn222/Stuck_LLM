import { FormEvent, useEffect, useState } from "react";

import type { UiCopy } from "../../shared/i18n";
import type {
  CredentialProvider,
  LlmCredentialStatus,
  SaveLlmCredentialRequest,
  UiPreferences,
} from "../../shared/types";

type SettingsTab = "general" | "model" | "security";

interface SettingsModalProps {
  copy: UiCopy["settingsModal"];
  credentialStatus: LlmCredentialStatus;
  onClose: () => void;
  onDeleteCredential: () => Promise<LlmCredentialStatus>;
  onSaveCredential: (request: SaveLlmCredentialRequest) => Promise<LlmCredentialStatus>;
  onUiPreferencesChange: (preferences: UiPreferences) => void;
  uiPreferences: UiPreferences;
}

const DEFAULT_PROVIDER: CredentialProvider = "openai";
const DEFAULT_MODEL = "gpt-4.1-mini";

export function SettingsModal({
  copy,
  credentialStatus,
  onClose,
  onDeleteCredential,
  onSaveCredential,
  onUiPreferencesChange,
  uiPreferences,
}: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [provider, setProvider] = useState<CredentialProvider>(
    credentialStatus.provider ?? DEFAULT_PROVIDER,
  );
  const [model, setModel] = useState(credentialStatus.model ?? DEFAULT_MODEL);
  const [baseUrl, setBaseUrl] = useState(credentialStatus.baseUrl ?? "");
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    setProvider(credentialStatus.provider ?? DEFAULT_PROVIDER);
    setModel(credentialStatus.model ?? DEFAULT_MODEL);
    setBaseUrl(credentialStatus.baseUrl ?? "");
  }, [credentialStatus]);

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
        provider,
        model: trimmedModel || DEFAULT_MODEL,
        baseUrl: baseUrl.trim() || null,
        apiKey: trimmedApiKey,
      });
      setApiKey("");
    } catch {
      setError(copy.saveError);
    } finally {
      setIsSaving(false);
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

  return (
    <div className="modal-backdrop" onKeyDown={(event) => event.key === "Escape" && onClose()}>
      <section aria-label={copy.title} aria-modal="true" className="settings-dialog" role="dialog">
        <header className="settings-dialog-header">
          <h2>{copy.title}</h2>
          <button aria-label={copy.close} className="icon-button" onClick={onClose} type="button">
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
                <form className="settings-form" onSubmit={handleSaveCredential}>
                  <label className="field">
                    <span>{copy.provider}</span>
                    <select
                      aria-label={copy.provider}
                      name="provider"
                      onChange={(event) =>
                        setProvider(event.target.value as CredentialProvider)
                      }
                      value={provider}
                    >
                      <option value="openai">{copy.providers.openai}</option>
                      <option value="anthropic">{copy.providers.anthropic}</option>
                      <option value="custom">{copy.providers.custom}</option>
                    </select>
                  </label>
                  <label className="field">
                    <span>{copy.model}</span>
                    <input
                      aria-label={copy.model}
                      autoComplete="off"
                      name="model"
                      onChange={(event) => setModel(event.target.value)}
                      placeholder={copy.modelPlaceholder}
                      spellCheck={false}
                      value={model}
                    />
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
                      disabled={!credentialStatus.configured || isDeleting}
                      onClick={() => void handleDeleteCredential()}
                      type="button"
                    >
                      {copy.deleteApiKey}
                    </button>
                  </div>
                </form>
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
              </section>
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}
