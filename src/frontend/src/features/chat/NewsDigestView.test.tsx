import { fireEvent, render, screen } from "@testing-library/react";

import { NewsDigestView } from "./NewsDigestView";
import type { NewsDigest } from "../../shared/types";

const digest: NewsDigest = {
  digestId: "digest_test",
  status: "completed",
  market: "US",
  symbol: "AAPL",
  stockName: "Apple Inc",
  query: "Apple news",
  generatedAt: "2026-04-29T20:00:00Z",
  summary: "애플 뉴스 핵심 요약입니다.",
  keyPoints: [],
  importantArticles: [
    {
      id: "news_1",
      title: "Apple earnings preview",
      url: "https://example.com/apple",
      source: "Example Markets",
      publishedAt: "2026-04-29T13:00:00-04:00",
      snippet: "Investors watch services.",
      provider: "tavily_news",
      query: "Apple news",
      rank: 0,
      category: "earnings",
      headlineKo: "애플 실적 미리보기",
      summaryKo: "서비스 매출이 주목됩니다.",
      importanceScore: 42,
      sourceDomain: "example.com",
    },
  ],
  additionalArticles: [
    {
      id: "news_2",
      title: "Apple services update",
      url: "https://example.com/services",
      source: "Example Search",
      publishedAt: "2026-04-28T13:00:00-04:00",
      snippet: "Services update.",
      provider: "serpapi_google_web",
      query: "Apple news",
      rank: 1,
      category: "product_service",
      headlineKo: "서비스 업데이트",
      summaryKo: "서비스 카탈로그가 확대됐습니다.",
      importanceScore: 12,
      sourceDomain: "example.com",
    },
  ],
  providerRuns: [
    {
      provider: "tavily_news",
      query: "Apple news",
      resultCount: 1,
      status: "completed",
      warning: null,
    },
  ],
  warnings: [],
};

it("renders news digest key articles and expands additional articles", () => {
  render(<NewsDigestView digest={digest} language="ko" />);

  expect(screen.getByLabelText("Apple Inc news digest")).toBeInTheDocument();
  expect(screen.getAllByText("애플 실적 미리보기")).toHaveLength(2);
  expect(screen.queryByText("서비스 업데이트")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "나머지 기사 보기 (1)" }));

  expect(screen.getByText("서비스 업데이트")).toBeInTheDocument();
});
