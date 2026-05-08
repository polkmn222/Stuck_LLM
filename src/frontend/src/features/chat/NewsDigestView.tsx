import { useState } from "react";

import type { UiCopy } from "../../shared/i18n";
import type { NewsArticle, NewsDigest, NewsSearchRun } from "../../shared/types";

type NewsDigestCopy = UiCopy["chat"]["newsDigest"];
type AggregatedProviderRun = {
  provider: NewsSearchRun["provider"];
  status: NewsSearchRun["status"];
  resultCount: number;
  queryCount: number;
};

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

function formatPublishedAt(value: string, locale: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function articleSummary(article: NewsArticle, copy: NewsDigestCopy): string | null {
  if (article.summaryKo) {
    return article.summaryKo;
  }
  if (copy.dateLocale.startsWith("en")) {
    return article.snippet;
  }
  return null;
}

function aggregateProviderRuns(runs: NewsSearchRun[]): AggregatedProviderRun[] {
  const statusPriority: Record<NewsSearchRun["status"], number> = {
    provider_error: 0,
    partial_provider_error: 1,
    missing_credential: 2,
    completed: 3,
  };
  const byProvider = new Map<NewsSearchRun["provider"], AggregatedProviderRun>();
  for (const run of runs) {
    const existing = byProvider.get(run.provider);
    if (existing == null) {
      byProvider.set(run.provider, {
        provider: run.provider,
        status: run.status,
        resultCount: run.resultCount,
        queryCount: 1,
      });
      continue;
    }
    existing.resultCount += run.resultCount;
    existing.queryCount += 1;
    if (statusPriority[run.status] < statusPriority[existing.status]) {
      existing.status = run.status;
    }
  }
  return Array.from(byProvider.values());
}

function NewsArticleList({
  articles,
  copy,
}: {
  articles: NewsArticle[];
  copy: NewsDigestCopy;
}) {
  return (
    <div className="news-card-list">
      {articles.map((article) => {
        const headline = article.headlineKo || article.title;
        return (
          <article className="news-card" key={article.id}>
            <div className="news-card-icon" aria-hidden="true">
              <span>{articleDomain(article).slice(0, 1).toUpperCase()}</span>
            </div>
            <div className="news-card-body">
              <div className="news-card-meta">
                <span>{articleDomain(article)}</span>
                <span className="news-provider-badge">{article.provider}</span>
                <span>{article.category}</span>
              </div>
              {article.publishedAt ? (
                <p className="news-card-date">
                  {formatPublishedAt(article.publishedAt, copy.dateLocale)}
                </p>
              ) : null}
              {article.url ? (
                <a href={article.url} rel="noreferrer" target="_blank">
                  {headline}
                </a>
              ) : (
                <strong>{headline}</strong>
              )}
              {articleSummary(article, copy) ? (
                <p className="news-card-summary">{articleSummary(article, copy)}</p>
              ) : null}
            </div>
          </article>
        );
      })}
    </div>
  );
}

export function NewsDigestView({
  copy,
  digest,
}: {
  copy: NewsDigestCopy;
  digest: NewsDigest;
}) {
  const [expanded, setExpanded] = useState(false);
  const providerRuns = aggregateProviderRuns(digest.providerRuns);
  const toggleLabel = expanded
    ? copy.collapse
    : `${copy.additional} (${digest.additionalArticles.length})`;

  return (
    <section
      aria-label={`${digest.stockName} news digest`}
      className="news-digest"
    >
      <p className="news-digest-summary">{digest.summary}</p>
      <NewsArticleList articles={digest.importantArticles} copy={copy} />
      {digest.additionalArticles.length ? (
        <>
          <button
            className="news-digest-toggle"
            onClick={() => setExpanded((current) => !current)}
            type="button"
          >
            {toggleLabel}
          </button>
          {expanded ? <NewsArticleList articles={digest.additionalArticles} copy={copy} /> : null}
        </>
      ) : null}
      <div className="news-digest-sources">
        <strong>{copy.searchSources}</strong>
        <div>
          {providerRuns.map((run) => (
            <span key={run.provider}>
              {run.provider}: {run.status} · {run.resultCount}
              {run.queryCount > 1 ? ` (${run.queryCount} queries)` : ""}
            </span>
          ))}
        </div>
        {digest.warnings.length ? (
          <p>
            {copy.warnings}: {digest.warnings.join(", ")}
          </p>
        ) : null}
      </div>
    </section>
  );
}
