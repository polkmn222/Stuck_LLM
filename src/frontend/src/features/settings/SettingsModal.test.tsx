import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { vi } from "vitest";

import { SettingsModal } from "./SettingsModal";
import { uiCopy } from "../../shared/i18n";

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

function renderSettingsModal(onClose = vi.fn()) {
  return {
    onClose,
    ...render(
      <SettingsModal
        copy={uiCopy.en.settingsModal}
        credentialStatus={emptyCredentialStatus}
        onClearConversations={vi.fn()}
        onClose={onClose}
        onDeleteCredential={vi.fn()}
        onSaveCredential={vi.fn()}
        onTestCredential={vi.fn()}
        onUiPreferencesChange={vi.fn()}
        uiPreferences={{ language: "en", theme: "dark" }}
      />,
    ),
  };
}

describe("SettingsModal", () => {
  it("closes from backdrop clicks but not inside dialog clicks", () => {
    const { onClose } = renderSettingsModal();

    fireEvent.click(screen.getByRole("dialog", { name: "Settings" }));
    expect(onClose).not.toHaveBeenCalled();

    fireEvent.click(screen.getByTestId("settings-backdrop"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("traps focus through keyboard navigation and restores prior focus on cleanup", () => {
    const opener = document.createElement("button");
    opener.textContent = "Open settings";
    document.body.appendChild(opener);
    opener.focus();

    const onClose = vi.fn();
    const { unmount } = renderSettingsModal(onClose);
    const dialog = screen.getByRole("dialog", { name: "Settings" });
    const closeButton = screen.getByRole("button", { name: "Close settings" });
    const lastFocusable = screen.getByRole("button", { name: "Light" });

    expect(closeButton).toHaveFocus();

    fireEvent.keyDown(dialog, { key: "Tab", shiftKey: true });
    expect(lastFocusable).toHaveFocus();

    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(closeButton).toHaveFocus();

    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);

    unmount();
    expect(opener).toHaveFocus();
    opener.remove();
  });

  it("defaults model credentials to Cerebras while preserving provider selection", () => {
    renderSettingsModal();

    fireEvent.click(screen.getByRole("button", { name: "Model" }));

    expect(screen.getByLabelText("Provider")).toHaveValue("cerebras");
    expect(
      within(screen.getByLabelText("Provider")).getAllByRole("option").map((option) => option.textContent),
    ).toEqual([
      "OpenAI",
      "Anthropic",
      "Cerebras",
      "Custom",
    ]);
    fireEvent.change(screen.getByLabelText("Provider"), {
      target: { value: "openai" },
    });
    expect(screen.getByLabelText("Provider")).toHaveValue("openai");
  });

  it("saves Cerebras credentials by default", async () => {
    const onSaveCredential = vi.fn().mockResolvedValue({
      configured: true,
      provider: "cerebras",
      model: "llama3.1-8b",
      baseUrl: "https://api.cerebras.ai/v1",
      apiKeyMask: "csk-...alue",
      keySource: "local_encrypted_state",
      createdAt: "2026-04-28T09:00:00+09:00",
      updatedAt: "2026-04-28T09:00:00+09:00",
    });

    render(
      <SettingsModal
        copy={uiCopy.en.settingsModal}
        credentialStatus={emptyCredentialStatus}
        onClearConversations={vi.fn()}
        onClose={vi.fn()}
        onDeleteCredential={vi.fn()}
        onSaveCredential={onSaveCredential}
        onTestCredential={vi.fn()}
        onUiPreferencesChange={vi.fn()}
        uiPreferences={{ language: "en", theme: "dark" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Model" }));
    fireEvent.change(screen.getByLabelText("API key"), {
      target: { value: "csk-phase035-secret-value" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save API Key" }));

    await waitFor(() => {
      expect(onSaveCredential).toHaveBeenCalledWith(expect.objectContaining({
        provider: "cerebras",
        model: "llama3.1-8b",
        baseUrl: null,
        apiKey: "csk-phase035-secret-value",
        makeActive: true,
      }));
    });
  });

  it("creates a new LLM profile when saving a new key with an active profile", async () => {
    const onSaveCredential = vi.fn().mockResolvedValue({
      configured: true,
      credentialId: "cerebras_new",
      label: "Second Cerebras key",
      provider: "cerebras",
      model: "llama3.1-8b",
      baseUrl: "https://api.cerebras.ai/v1",
      apiKeyMask: "csk-...cond",
      keySource: "local_encrypted_state",
      isActive: true,
      createdAt: "2026-05-08T09:00:00+09:00",
      updatedAt: "2026-05-08T09:00:00+09:00",
    });

    render(
      <SettingsModal
        activeCredentialId="cerebras_fast"
        copy={uiCopy.en.settingsModal}
        credentialProfiles={[
          {
            configured: true,
            credentialId: "cerebras_fast",
            label: "Cerebras fast",
            provider: "cerebras",
            model: "llama3.1-8b",
            baseUrl: "https://api.cerebras.ai/v1",
            apiKeyMask: "csk-...irst",
            keySource: "local_encrypted_state",
            isActive: true,
            createdAt: "2026-05-06T09:00:00Z",
            updatedAt: "2026-05-06T09:00:00Z",
          },
        ]}
        credentialStatus={{
          configured: true,
          credentialId: "cerebras_fast",
          label: "Cerebras fast",
          provider: "cerebras",
          model: "llama3.1-8b",
          baseUrl: "https://api.cerebras.ai/v1",
          apiKeyMask: "csk-...irst",
          keySource: "local_encrypted_state",
          isActive: true,
          createdAt: "2026-05-06T09:00:00Z",
          updatedAt: "2026-05-06T09:00:00Z",
        }}
        onClearConversations={vi.fn()}
        onClose={vi.fn()}
        onDeleteCredential={vi.fn()}
        onSaveCredential={onSaveCredential}
        onTestCredential={vi.fn()}
        onUiPreferencesChange={vi.fn()}
        uiPreferences={{ language: "en", theme: "dark" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Model" }));
    fireEvent.change(screen.getByLabelText("Key label"), {
      target: { value: "Second Cerebras key" },
    });
    fireEvent.change(screen.getByLabelText("API key"), {
      target: { value: "csk-second-secret-value" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save API Key" }));

    await waitFor(() => {
      expect(onSaveCredential).toHaveBeenCalledTimes(1);
    });
    const request = onSaveCredential.mock.calls[0][0];
    expect(request.credentialId).toMatch(/^cerebras_/);
    expect(request.credentialId).not.toBe("cerebras_fast");
    expect(request.label).toBe("Second Cerebras key");
  });

  it("tests the saved provider connection and renders safe diagnostic copy", async () => {
    const onTestCredential = vi.fn().mockResolvedValue({
      configured: true,
      status: "provider_error",
      provider: "cerebras",
      model: "llama3.1-8b",
      baseUrl: "https://api.cerebras.ai/v1",
      keySource: "local_encrypted_state",
      errorCode: "auth_error",
      message: "Authentication failed. Check the saved provider key.",
    });

    render(
      <SettingsModal
        copy={uiCopy.en.settingsModal}
        credentialStatus={{
          configured: true,
          credentialId: "cerebras_fast",
          label: "Cerebras fast",
          provider: "cerebras",
          model: "llama3.1-8b",
          baseUrl: "https://api.cerebras.ai/v1",
          apiKeyMask: "csk-...alue",
          keySource: "local_encrypted_state",
          isActive: true,
          createdAt: "2026-04-28T09:00:00+09:00",
          updatedAt: "2026-04-28T09:00:00+09:00",
        }}
        onClearConversations={vi.fn()}
        onClose={vi.fn()}
        onDeleteCredential={vi.fn()}
        onSaveCredential={vi.fn()}
        onTestCredential={onTestCredential}
        onUiPreferencesChange={vi.fn()}
        uiPreferences={{ language: "en", theme: "dark" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Model" }));
    fireEvent.click(screen.getByRole("button", { name: "Test connection" }));

    expect(await screen.findByText("Authentication failed. Check the saved provider key."))
      .toBeInTheDocument();
    expect(document.body.textContent).not.toContain(["csk", "phase025-auth-secret"].join("-"));
    expect(onTestCredential).toHaveBeenCalledTimes(1);
  });

  it("renders saved key profiles and selects the active profile", async () => {
    const onSelectCredential = vi.fn().mockResolvedValue({
      configured: true,
      credentialId: "openai_research",
      label: "OpenAI research",
      provider: "openai",
      model: "gpt-4.1-mini",
      baseUrl: "https://api.openai.com/v1",
      apiKeyMask: "sk-o...cret",
      keySource: "generated_local",
      isActive: true,
      createdAt: "2026-05-06T09:00:00Z",
      updatedAt: "2026-05-06T09:00:00Z",
    });

    render(
      <SettingsModal
        activeCredentialId="cerebras_fast"
        copy={uiCopy.en.settingsModal}
        credentialProfiles={[
          {
            configured: true,
            credentialId: "openai_research",
            label: "OpenAI research",
            provider: "openai",
            model: "gpt-4.1-mini",
            baseUrl: "https://api.openai.com/v1",
            apiKeyMask: "sk-o...cret",
            keySource: "generated_local",
            isActive: false,
            createdAt: "2026-05-06T09:00:00Z",
            updatedAt: "2026-05-06T09:00:00Z",
          },
          {
            configured: true,
            credentialId: "cerebras_fast",
            label: "Cerebras fast",
            provider: "cerebras",
            model: "llama3.1-8b",
            baseUrl: "https://api.cerebras.ai/v1",
            apiKeyMask: "csk-...cret",
            keySource: "generated_local",
            isActive: true,
            createdAt: "2026-05-06T09:01:00Z",
            updatedAt: "2026-05-06T09:01:00Z",
          },
        ]}
        credentialStatus={emptyCredentialStatus}
        onClearConversations={vi.fn()}
        onClose={vi.fn()}
        onDeleteCredential={vi.fn()}
        onSaveCredential={vi.fn()}
        onSelectCredential={onSelectCredential}
        onTestCredential={vi.fn()}
        onUiPreferencesChange={vi.fn()}
        uiPreferences={{ language: "en", theme: "dark" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Model" }));
    fireEvent.click(screen.getByRole("button", { name: /OpenAI research/ }));

    await waitFor(() => {
      expect(onSelectCredential).toHaveBeenCalledWith("openai_research");
    });
    expect(document.body.textContent).not.toContain("phase129");
  });

  it("saves and selects news provider credentials from the model tab", async () => {
    const onSaveExternalCredential = vi.fn().mockResolvedValue({
      configured: true,
      credentialId: "eventregistry_news",
      label: "EventRegistry news",
      provider: "eventregistry",
      apiKeyMask: "evre...cret",
      keySource: "local_encrypted_state",
      isActive: true,
      createdAt: "2026-05-06T09:00:00Z",
      updatedAt: "2026-05-06T09:00:00Z",
    });
    const onSelectExternalCredential = vi.fn().mockResolvedValue({
      configured: true,
      credentialId: "tavily_news",
      label: "Tavily news",
      provider: "tavily",
      apiKeyMask: "tvly...cret",
      keySource: "local_encrypted_state",
      isActive: true,
      createdAt: "2026-05-06T09:00:00Z",
      updatedAt: "2026-05-06T09:00:00Z",
    });

    render(
      <SettingsModal
        copy={uiCopy.en.settingsModal}
        credentialStatus={emptyCredentialStatus}
        externalCredentialProfiles={[
          {
            configured: true,
            credentialId: "tavily_news",
            label: "Tavily news",
            provider: "tavily",
            apiKeyMask: "tvly...cret",
            keySource: "local_encrypted_state",
            isActive: true,
            createdAt: "2026-05-06T09:00:00Z",
            updatedAt: "2026-05-06T09:00:00Z",
          },
        ]}
        onClearConversations={vi.fn()}
        onClose={vi.fn()}
        onDeleteCredential={vi.fn()}
        onSaveCredential={vi.fn()}
        onSaveExternalCredential={onSaveExternalCredential}
        onSelectExternalCredential={onSelectExternalCredential}
        onTestCredential={vi.fn()}
        onUiPreferencesChange={vi.fn()}
        uiPreferences={{ language: "en", theme: "dark" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Model" }));
    fireEvent.click(screen.getByRole("button", { name: /Tavily news/ }));
    await waitFor(() => {
      expect(onSelectExternalCredential).toHaveBeenCalledWith("tavily_news");
    });

    fireEvent.change(screen.getByLabelText("News provider"), {
      target: { value: "eventregistry" },
    });
    fireEvent.change(screen.getByLabelText("News key label"), {
      target: { value: "EventRegistry news" },
    });
    fireEvent.change(screen.getByLabelText("News API key"), {
      target: { value: "eventregistry-phase136-secret" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save News Key" }));

    await waitFor(() => {
      expect(onSaveExternalCredential).toHaveBeenCalledWith({
        credentialId: expect.stringMatching(/^eventregistry_/),
        label: "EventRegistry news",
        provider: "eventregistry",
        apiKey: "eventregistry-phase136-secret",
        makeActive: true,
      });
    });
    expect(document.body.textContent).not.toContain("eventregistry-phase136-secret");
  });

  it("renders delete actions for every saved news provider key", async () => {
    const onDeleteExternalCredential = vi.fn().mockResolvedValue({
      configured: false,
      credentialId: null,
      label: null,
      provider: null,
      apiKeyMask: null,
      keySource: null,
      isActive: false,
      createdAt: null,
      updatedAt: null,
    });
    Object.defineProperty(window, "confirm", {
      configurable: true,
      value: vi.fn(() => true),
    });

    render(
      <SettingsModal
        copy={uiCopy.en.settingsModal}
        credentialStatus={emptyCredentialStatus}
        externalCredentialProfiles={[
          {
            configured: true,
            credentialId: "tavily_news",
            label: "Tavily news",
            provider: "tavily",
            apiKeyMask: "tvly...cret",
            keySource: "local_encrypted_state",
            isActive: true,
            createdAt: "2026-05-06T09:00:00Z",
            updatedAt: "2026-05-06T09:00:00Z",
          },
          {
            configured: true,
            credentialId: "gnews_news",
            label: "GNews",
            provider: "gnews",
            apiKeyMask: "gnew...cret",
            keySource: "local_encrypted_state",
            isActive: true,
            createdAt: "2026-05-06T09:01:00Z",
            updatedAt: "2026-05-06T09:01:00Z",
          },
        ]}
        onClearConversations={vi.fn()}
        onClose={vi.fn()}
        onDeleteCredential={vi.fn()}
        onDeleteExternalCredential={onDeleteExternalCredential}
        onSaveCredential={vi.fn()}
        onTestCredential={vi.fn()}
        onUiPreferencesChange={vi.fn()}
        uiPreferences={{ language: "en", theme: "dark" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Model" }));
    const deleteButtons = screen.getAllByRole("button", { name: "Delete News Key" });
    expect(deleteButtons).toHaveLength(2);

    fireEvent.click(deleteButtons[1]);

    await waitFor(() => {
      expect(onDeleteExternalCredential).toHaveBeenCalledWith("gnews_news");
    });
  });


  it("clears all conversations from the security tab after confirmation", async () => {
    const onClearConversations = vi.fn().mockResolvedValue(2);
    Object.defineProperty(window, "confirm", {
      configurable: true,
      value: vi.fn(() => true),
    });

    render(
      <SettingsModal
        copy={uiCopy.en.settingsModal}
        credentialStatus={emptyCredentialStatus}
        onClearConversations={onClearConversations}
        onClose={vi.fn()}
        onDeleteCredential={vi.fn()}
        onSaveCredential={vi.fn()}
        onTestCredential={vi.fn()}
        onUiPreferencesChange={vi.fn()}
        uiPreferences={{ language: "en", theme: "dark" }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Security" }));
    fireEvent.click(screen.getByRole("button", { name: "Clear chat history" }));

    await waitFor(() => {
      expect(onClearConversations).toHaveBeenCalledTimes(1);
    });
  });
});
