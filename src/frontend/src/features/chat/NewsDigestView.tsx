import { useState } from "react";

import type { NewsArticle, NewsDigest, UiLanguage } from "../../shared/types";

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

export function NewsDigestView({
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
