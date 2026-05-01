import { FormEvent, useEffect, useRef, useState } from "react";

import type {
  AppSettings,
  ConversationMessage,
  ConversationSnapshot,
  MarketChartWindow,
  MarketQuote,
  SendMessageRequest,
  UiLanguage,
} from "../../shared/types";
import type { UiCopy } from "../../shared/i18n";
import { MarketChart } from "../analysis/MarketChart";
import { NewsDigestView } from "./NewsDigestView";

interface ChatShellProps {
  copy: UiCopy["chat"];
  conversationSnapshot?: ConversationSnapshot | null;
  settings: AppSettings;
  onAnalysisChange: (snapshot: ConversationSnapshot) => void;
  onConversationChange?: (snapshot: ConversationSnapshot) => void;
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

export function ChatShell({
  copy,
  conversationSnapshot = null,
  settings,
  onAnalysisChange,
  onConversationChange,
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
  const activeSnapshot = conversationSnapshot ?? latestSnapshot;
  const messages = activeSnapshot?.messages ?? internalMessages;
  const activeConversationId = activeSnapshot?.conversationId ?? conversationId;

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView?.({ block: "end", behavior: "smooth" });
  }, [messages.length, isSending]);

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
                <p>{message.content}</p>
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
