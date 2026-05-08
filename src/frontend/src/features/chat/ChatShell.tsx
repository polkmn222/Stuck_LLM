import { FormEvent, ReactNode, useEffect, useRef, useState } from "react";

import type {
  AppSettings,
  ConversationMessage,
  ConversationSnapshot,
  LlmCredentialStatus,
  MarketChartWindow,
  MarketQuote,
  SendMessageRequest,
  UiLanguage,
} from "../../shared/types";
import type { UiCopy } from "../../shared/i18n";
import { MarketChart } from "../analysis/MarketChart";
import { NewsDigestView } from "./NewsDigestView";

interface ChatShellProps {
  activeCredentialId?: string | null;
  copy: UiCopy["chat"];
  conversationSnapshot?: ConversationSnapshot | null;
  credentialProfiles?: LlmCredentialStatus[];
  settings: AppSettings;
  onAnalysisChange: (snapshot: ConversationSnapshot) => void;
  onConversationChange?: (snapshot: ConversationSnapshot) => void;
  onCredentialChange?: (credentialId: string) => void;
  onFetchMarketQuote?: (
    market: MarketQuote["market"],
    symbol: string,
    window: MarketChartWindow,
  ) => Promise<MarketQuote>;
  onSendMessage: (request: SendMessageRequest) => Promise<ConversationSnapshot>;
  responseLanguage: UiLanguage;
}

const CHART_WINDOWS: MarketChartWindow[] = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "MAX"];

function messageClassName(message: ConversationMessage, needsApiKey: boolean): string {
  return [
    "message",
    `message-${message.role}`,
    needsApiKey ? "message-needs-api-key" : "",
  ]
    .filter(Boolean)
    .join(" ");
}

function renderInlineMarkdown(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const linkPattern = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = linkPattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }
    nodes.push(
      <a href={match[2]} key={`${match[2]}:${match.index}`} rel="noreferrer" target="_blank">
        {match[1]}
      </a>,
    );
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }
  return nodes;
}

function MessageContent({ content }: { content: string }) {
  return (
    <div className="message-content">
      {content.split("\n").map((line, index) => (
        <p className={line.startsWith("- ") ? "message-bullet-line" : undefined} key={index}>
          {renderInlineMarkdown(line)}
        </p>
      ))}
    </div>
  );
}

export function ChatShell({
  activeCredentialId = null,
  copy,
  conversationSnapshot = null,
  credentialProfiles = [],
  settings,
  onAnalysisChange,
  onConversationChange,
  onCredentialChange,
  onFetchMarketQuote,
  onSendMessage,
  responseLanguage,
}: ChatShellProps) {
  const scrollAnchorRef = useRef<HTMLDivElement | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [chartOverrides, setChartOverrides] = useState<Record<string, MarketQuote>>({});
  const [loadingChartKey, setLoadingChartKey] = useState<string | null>(null);
  const [chartErrorMessageId, setChartErrorMessageId] = useState<string | null>(null);
  const [latestSnapshot, setLatestSnapshot] = useState<ConversationSnapshot | null>(null);
  const [internalMessages, setInternalMessages] = useState<ConversationMessage[]>([]);
  const [selectedCredentialId, setSelectedCredentialId] = useState<string | null>(
    activeCredentialId,
  );
  const activeSnapshot = conversationSnapshot ?? latestSnapshot;
  const messages = activeSnapshot?.messages ?? internalMessages;
  const activeConversationId = activeSnapshot?.conversationId ?? conversationId;
  const selectedCredential = credentialProfiles.find(
    (profile) => profile.credentialId === selectedCredentialId,
  );
  const selectedCredentialText = selectedCredential
    ? `${selectedCredential.label || selectedCredential.provider || copy.unknownModelKey} · ${
        selectedCredential.model || copy.unknownModelKey
      }`
    : null;

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView?.({ block: "end", behavior: "smooth" });
  }, [messages.length, isSending]);

  useEffect(() => {
    setSelectedCredentialId(activeCredentialId);
  }, [activeCredentialId]);

  function handleCredentialChange(nextCredentialId: string) {
    setSelectedCredentialId(nextCredentialId || null);
    if (nextCredentialId) {
      onCredentialChange?.(nextCredentialId);
    }
  }

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
        conversationId: activeConversationId,
        market: settings.defaultMarket,
        horizonType: settings.defaultHorizon,
        analysisMode: settings.analysisMode,
        responseLanguage,
        llmCredentialId: selectedCredentialId,
      });
      setConversationId(snapshot.conversationId);
      setLatestSnapshot(snapshot);
      setInternalMessages(snapshot.messages);
      setChartOverrides({});
      setChartErrorMessageId(null);
      setDraft("");
      onAnalysisChange(snapshot);
      onConversationChange?.(snapshot);
    } catch {
      setError(copy.error);
    } finally {
      setIsSending(false);
    }
  }

  const latestAssistantMessageId = [...messages]
    .reverse()
    .find((message) => message.role === "assistant")?.id;

  function quoteForMessage(message: ConversationMessage): MarketQuote | null {
    return (
      chartOverrides[message.id]
      ?? message.marketSnapshot
      ?? (message.id === latestAssistantMessageId
        ? activeSnapshot?.marketSnapshot ?? null
        : null)
    );
  }

  function canRefetchChart(quote: MarketQuote): boolean {
    return (
      Boolean(onFetchMarketQuote)
      && quote.market === "US"
      && quote.source === "serpapi_google_finance"
    );
  }

  async function handleChartWindowSelect(
    messageId: string,
    quote: MarketQuote,
    window: MarketChartWindow,
  ) {
    if (!onFetchMarketQuote || loadingChartKey !== null || quote.chartWindow === window) {
      return;
    }

    setLoadingChartKey(`${messageId}:${window}`);
    setChartErrorMessageId(null);
    try {
      const nextQuote = await onFetchMarketQuote(quote.market, quote.symbol, window);
      setChartOverrides((current) => ({
        ...current,
        [messageId]: nextQuote,
      }));
    } catch {
      setChartErrorMessageId(messageId);
    } finally {
      setLoadingChartKey(null);
    }
  }

  return (
    <section className="chat-shell" aria-label={copy.aria}>
      <header className="chat-header">
        <div>
          <p className="eyebrow">{copy.eyebrow}</p>
          <h1>{copy.title}</h1>
        </div>
        <div className="chat-header-controls">
          {credentialProfiles.length ? (
            <label className="compact-select">
              <span>{copy.modelKeyLabel}</span>
              <select
                aria-label={copy.modelKeyLabel}
                onChange={(event) => handleCredentialChange(event.target.value)}
                value={selectedCredentialId ?? ""}
              >
                {credentialProfiles.map((profile) => (
                  <option
                    key={profile.credentialId ?? `${profile.provider}:${profile.model}`}
                    value={profile.credentialId ?? ""}
                  >
                    {profile.label || profile.model || profile.provider || copy.unknownModelKey}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          {selectedCredentialText ? (
            <span className="status-pill credential-pill">{selectedCredentialText}</span>
          ) : null}
          <span className="status-pill">
            {settings.defaultMarket} / {settings.analysisMode}
          </span>
        </div>
      </header>

      <div className="message-list">
        {messages.length === 0 ? (
          <article className="message message-assistant">
            <span>{copy.emptyMeta}</span>
            <p>{copy.emptyText}</p>
          </article>
        ) : (
          messages.map((message) => {
            const quote = message.role === "assistant" ? quoteForMessage(message) : null;
            const chartIsLoading = Boolean(
              loadingChartKey?.startsWith(`${message.id}:`),
            );
            return (
              <article
                className={messageClassName(
                  message,
                    message.id === latestAssistantMessageId
                    && activeSnapshot?.status === "setup_needed",
                )}
                key={message.id}
              >
                <span>{message.meta}</span>
                <MessageContent content={message.content} />
                {message.newsDigest ? (
                  <NewsDigestView
                    copy={copy.newsDigest}
                    digest={message.newsDigest}
                  />
                ) : null}
                {quote ? (
                  <>
                    <MarketChart
                      activeWindow={quote.chartWindow}
                      ariaLabel={`${quote.name} chat price chart`}
                      availableWindows={canRefetchChart(quote) ? CHART_WINDOWS : []}
                      isWindowLoading={chartIsLoading}
                      onWindowSelect={(window) =>
                        void handleChartWindowSelect(message.id, quote, window)
                      }
                      quote={quote}
                      variant="compact"
                    />
                    {chartErrorMessageId === message.id ? (
                      <p className="inline-error">{copy.chartWindowError}</p>
                    ) : null}
                  </>
                ) : null}
              </article>
            );
          })
        )}
        {error ? <p className="inline-error">{error}</p> : null}
        {isSending ? (
          <article aria-live="polite" className="message message-assistant activity-message">
            <span>{copy.thinking}</span>
            <ul>
              {copy.activityItems.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        ) : null}
        <div aria-hidden="true" ref={scrollAnchorRef} />
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
