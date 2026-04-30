import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { SettingsModal } from "./SettingsModal";
import { uiCopy } from "../../shared/i18n";

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
    expect(screen.getAllByRole("option").map((option) => option.textContent)).toEqual([
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
      expect(onSaveCredential).toHaveBeenCalledWith({
        provider: "cerebras",
        model: "llama3.1-8b",
        baseUrl: null,
        apiKey: "csk-phase035-secret-value",
      });
    });
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
          provider: "cerebras",
          model: "llama3.1-8b",
          baseUrl: "https://api.cerebras.ai/v1",
          apiKeyMask: "csk-...alue",
          keySource: "local_encrypted_state",
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
