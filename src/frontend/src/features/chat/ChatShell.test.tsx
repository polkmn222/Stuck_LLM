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
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(onSendMessage).not.toHaveBeenCalled());
  });
});
