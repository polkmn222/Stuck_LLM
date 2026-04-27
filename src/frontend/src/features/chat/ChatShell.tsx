import { FormEvent, useState } from "react";

import type {
  AppSettings,
  ConversationMessage,
  ConversationSnapshot,
  SendMessageRequest,
} from "../../shared/types";
import type { UiCopy } from "../../shared/i18n";

interface ChatShellProps {
  copy: UiCopy["chat"];
  settings: AppSettings;
  onAnalysisChange: (snapshot: ConversationSnapshot) => void;
  onSendMessage: (request: SendMessageRequest) => Promise<ConversationSnapshot>;
}

function messageClassName(message: ConversationMessage): string {
  return `message message-${message.role}`;
}

export function ChatShell({ copy, settings, onAnalysisChange, onSendMessage }: ChatShellProps) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || isSending) {
      return;
    }

    setIsSending(true);
    setError(null);

    try {
      const snapshot = await onSendMessage({
        content,
        conversationId,
        market: settings.defaultMarket,
        horizonType: settings.defaultHorizon,
        analysisMode: settings.analysisMode,
      });
      setConversationId(snapshot.conversationId);
      setMessages(snapshot.messages);
      setDraft("");
      onAnalysisChange(snapshot);
    } catch {
      setError(copy.error);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="chat-shell" aria-label={copy.aria}>
      <header className="chat-header">
        <div>
          <p className="eyebrow">{copy.eyebrow}</p>
          <h1>{copy.title}</h1>
        </div>
        <span className="status-pill">
          {settings.defaultMarket} / {settings.analysisMode}
        </span>
      </header>

      <div className="message-list">
        {messages.length === 0 ? (
          <article className="message message-assistant">
            <span>{copy.emptyMeta}</span>
            <p>{copy.emptyText}</p>
          </article>
        ) : (
          messages.map((message) => (
            <article className={messageClassName(message)} key={message.id}>
              <span>{message.meta}</span>
              <p>{message.content}</p>
            </article>
          ))
        )}
        {error ? <p className="inline-error">{error}</p> : null}
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <input
          aria-label={copy.messageLabel}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={copy.placeholder}
          value={draft}
        />
        <button disabled={isSending} type="submit">
          {copy.send}
        </button>
      </form>
    </section>
  );
}
