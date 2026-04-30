import { FormEvent, useEffect, useRef, useState } from "react";

import type {
  AppSettings,
  ConversationMessage,
  ConversationSnapshot,
  MarketChartWindow,
  MarketQuote,
  NewsArticle,
  NewsDigest,
  SendMessageRequest,
  UiLanguage,
} from "../../shared/types";
import type { UiCopy } from "../../shared/i18n";
import { MarketChart } from "../analysis/MarketChart";

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

function articleDomain(article: NewsArticle): string {
  if (article.sourceDomain) {
    return article.sourceDomain;
  }
  if (!article.url) {
    return article.source ?? article.provider;
  }
  try {
    return new URL(article.url).hostname.replace(/^www\./, "");
  } catch {
    return article.source ?? article.provider;
  }
}

function articleIconUrl(article: NewsArticle): string | null {
  if (!article.url) {
    return null;
  }
  return `https://www.google.com/s2/favicons?sz=32&domain_url=${encodeURIComponent(article.url)}`;
}

function NewsArticleList({ articles }: { articles: NewsArticle[] }) {
  return (
    <div className="news-card-list">
      {articles.map((article) => (
        <article className="news-card" key={article.id}>
          <div className="news-card-icon" aria-hidden={articleIconUrl(article) ? undefined : true}>
            {articleIconUrl(article) ? (
              <img
                alt={`${articleDomain(article)} icon`}
                src={articleIconUrl(article) ?? undefined}
              />
            ) : (
              <span>{articleDomain(article).slice(0, 1).toUpperCase()}</span>
            )}
          </div>
          <div className="news-card-body">
            <div className="news-card-meta">
              <span>{articleDomain(article)} · {article.provider}</span>
              <span>{article.category}</span>
            </div>
            <strong>{article.headlineKo || article.title}</strong>
            {article.summaryKo || article.snippet ? (
              <p className="news-card-summary">{article.summaryKo || article.snippet}</p>
            ) : null}
            {article.url ? (
              <a href={article.url} rel="noreferrer" target="_blank">
                {article.title}
              </a>
            ) : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function NewsKeyPoints({ articles }: { articles: NewsArticle[] }) {
  return (
    <ol className="news-key-points">
      {articles.map((article) => (
        <li key={`key-${article.id}`}>
          <strong>{article.headlineKo || article.title}</strong>
          {article.summaryKo || article.snippet ? (
            <p>{article.summaryKo || article.snippet}</p>
          ) : null}
        </li>
      ))}
    </ol>
  );
}

function NewsDigestView({
  digest,
  language,
}: {
  digest: NewsDigest;
  language: UiLanguage;
}) {
  const [expanded, setExpanded] = useState(false);
  const labels =
    language === "ko"
      ? {
          additional: "나머지 기사 보기",
          collapse: "나머지 기사 접기",
          searchSources: "검색 출처",
          warnings: "경고",
        }
      : {
          additional: "Show more articles",
          collapse: "Hide extra articles",
          searchSources: "Search sources",
          warnings: "Warnings",
        };
  const toggleLabel = expanded
    ? labels.collapse
    : `${labels.additional} (${digest.additionalArticles.length})`;

  return (
    <section
      aria-label={`${digest.stockName} news digest`}
      className="news-digest"
    >
      <p className="news-digest-summary">{digest.summary}</p>
      <NewsKeyPoints articles={digest.importantArticles} />
      <NewsArticleList articles={digest.importantArticles} />
      {digest.additionalArticles.length ? (
        <>
          <button
            className="news-digest-toggle"
            onClick={() => setExpanded((current) => !current)}
            type="button"
          >
            {toggleLabel}
          </button>
          {expanded ? <NewsArticleList articles={digest.additionalArticles} /> : null}
        </>
      ) : null}
      <div className="news-digest-sources">
        <strong>{labels.searchSources}</strong>
        <div>
          {digest.providerRuns.map((run) => (
            <span key={`${run.provider}:${run.query}`}>
              {run.provider}: {run.resultCount}
            </span>
          ))}
        </div>
        {digest.warnings.length ? (
          <p>
            {labels.warnings}: {digest.warnings.join(", ")}
          </p>
        ) : null}
      </div>
    </section>
  );
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
                    digest={message.newsDigest}
                    language={responseLanguage}
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
