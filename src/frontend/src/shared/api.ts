import type {
  AnalysisEvidenceItem,
  AnalysisResult,
  AnalysisSourceDocument,
  AppSettings,
  BacktestRequest,
  BacktestResult,
  ConversationSnapshot,
  ConversationSummary,
  DefaultMarket,
  LlmConnectionTestResult,
  LlmCredentialProfileList,
  LlmCredentialStatus,
  MarketChartWindow,
  NewsArticle,
  NewsCategory,
  EvaluationKind,
  ExternalCredentialProfileList,
  ExternalCredentialStatus,
  NewsDigest,
  NewsProvider,
  NewsSearchRun,
  MarketQuote,
  SaveExternalCredentialRequest,
  SaveLlmCredentialRequest,
  SendMessageRequest,
} from "./types";

interface ApiSettings {
  analysis_mode: AppSettings["analysisMode"];
  default_market: AppSettings["defaultMarket"];
  default_horizon: AppSettings["defaultHorizon"];
}

interface ApiMarketQuote {
  market: MarketQuote["market"];
  symbol: string;
  name: string;
  exchange: string;
  currency: string;
  last_price: number;
  previous_close: number | null;
  change_pct: number | null;
  as_of_at: string;
  source: string;
  chart_window?: MarketChartWindow;
  chart_bars: ApiMarketBar[];
  key_stats?: ApiMarketKeyStat[];
  news_items?: ApiMarketNewsItem[];
}

interface ApiMarketBar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface ApiMarketKeyStat {
  label: string;
  value: string;
}

interface ApiMarketNewsItem {
  title: string;
  url: string | null;
  source: string | null;
  published_at: string | null;
  snippet: string | null;
}

interface ApiNewsSearchRun {
  provider: NewsProvider;
  query: string;
  result_count: number;
  status: NewsSearchRun["status"];
  warning: string | null;
}

interface ApiNewsArticle {
  id: string;
  title: string;
  url: string | null;
  source: string | null;
  published_at: string | null;
  snippet: string | null;
  provider: NewsProvider;
  query: string;
  rank: number;
  category: NewsCategory;
  headline_ko: string | null;
  summary_ko: string | null;
  importance_score: number;
  source_domain: string | null;
}

interface ApiNewsDigest {
  digest_id: string;
  status: NewsDigest["status"];
  market: DefaultMarket;
  symbol: string;
  stock_name: string;
  query: string;
  generated_at: string;
  summary: string;
  key_points: string[];
  important_articles: ApiNewsArticle[];
  additional_articles: ApiNewsArticle[];
  provider_runs: ApiNewsSearchRun[];
  warnings: string[];
}

interface ApiConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta: string;
  created_at: string;
  market_snapshot?: ApiMarketQuote | null;
  news_digest?: ApiNewsDigest | null;
  backtest_result?: ApiBacktestResult | null;
}

interface ApiConversationSummary {
  conversation_id: string;
  title: string;
  status: ConversationSnapshot["status"];
  updated_at: string;
  last_message: string;
}

interface ApiConversationList {
  conversations: ApiConversationSummary[];
}

interface ApiDeleteResponse {
  deleted_count: number;
}

interface ApiConversationSnapshot {
  conversation_id: string;
  status: ConversationSnapshot["status"];
  missing_inputs: ConversationSnapshot["missingInputs"];
  analysis_request: null | {
    market: DefaultMarket;
    symbol: string;
    stock_name: string;
    horizon_type: NonNullable<AppSettings["defaultHorizon"]>;
    analysis_mode: AppSettings["analysisMode"];
  };
  analysis_result: ApiAnalysisResult | null;
  market_snapshot: ApiMarketQuote | null;
  news_digest?: ApiNewsDigest | null;
  backtest_result?: ApiBacktestResult | null;
  messages: ApiConversationMessage[];
}

interface ApiAnalysisSourceDocument {
  id: string;
  source_type: string;
  source_name: string;
  url: string | null;
  title: string;
  published_at: string;
  fetched_at?: string | null;
  included_in_analysis: boolean;
  exclusion_reason: string | null;
  language?: string | null;
  adapter?: string | null;
  relevance_score?: number | null;
  safety_flags?: string[];
}

interface ApiAnalysisEvidenceItem {
  source_document_id: string;
  stance: AnalysisEvidenceItem["stance"];
  weight: number;
  summary: string;
  quote_excerpt: string;
}

interface ApiScoreDriver {
  source_document_id: string;
  stance: AnalysisEvidenceItem["stance"];
  weight: number;
  probability_impact: "supports_buy" | "supports_hold" | "supports_sell";
  summary: string;
}

interface ApiScoreResult {
  score_id: string;
  analysis_request_id: string;
  status: NonNullable<AnalysisResult["scoreResult"]>["status"];
  buy_probability: number;
  hold_probability: number;
  sell_probability: number;
  confidence_score: number;
  expected_return_min_pct?: number;
  expected_return_max_pct?: number;
  downside_probability?: number;
  similar_event_sample_count?: number;
  similar_event_win_rate?: number;
  similar_event_median_return_pct?: number;
  confidence_factors?: string[];
  drivers: ApiScoreDriver[];
  rationale: string;
}

interface ApiAnalysisResult {
  analysis_request_id: string;
  status: AnalysisResult["status"];
  included_document_count: number;
  excluded_document_count: number;
  source_audit?: {
    source_warnings?: string[];
    included_by_source_type?: Record<string, number>;
    excluded_by_reason?: Record<string, number>;
    prompt_document_ids?: string[];
  };
  source_documents: ApiAnalysisSourceDocument[];
  evidence_items: ApiAnalysisEvidenceItem[];
  summary: string;
  score_result?: ApiScoreResult | null;
  provider: string | null;
  model: string | null;
  provider_error_code: string | null;
}

interface ApiEquityPoint {
  timestamp: string;
  price: number;
  value: number;
  return_pct: number;
}

interface ApiBacktestResult {
  simulation_id: string;
  analysis_request_id: string | null;
  evaluation_kind: EvaluationKind;
  market: DefaultMarket;
  symbol: string;
  entry_at: string;
  exit_at: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  gross_return_pct: number;
  gross_pnl: number;
  max_drawdown_pct: number;
  equity_curve: ApiEquityPoint[];
  source: string;
}

interface ApiLlmCredentialStatus {
  configured: boolean;
  credential_id?: string | null;
  label?: string | null;
  provider: LlmCredentialStatus["provider"];
  model: string | null;
  base_url: string | null;
  api_key_mask: string | null;
  key_source: string | null;
  is_active?: boolean;
  created_at: string | null;
  updated_at: string | null;
}

interface ApiLlmCredentialProfileList {
  active_credential_id: string | null;
  credentials: ApiLlmCredentialStatus[];
}

interface ApiLlmConnectionTestResult {
  configured: boolean;
  status: LlmConnectionTestResult["status"];
  provider: LlmConnectionTestResult["provider"];
  model: string | null;
  base_url: string | null;
  key_source: string | null;
  error_code: string | null;
  message: string;
}

interface ApiExternalCredentialStatus {
  configured: boolean;
  credential_id?: string | null;
  label?: string | null;
  provider: ExternalCredentialStatus["provider"];
  api_key_mask: string | null;
  key_source: string | null;
  is_active?: boolean;
  created_at: string | null;
  updated_at: string | null;
}

interface ApiExternalCredentialProfileList {
  active_credential_ids: ExternalCredentialProfileList["activeCredentialIds"];
  credentials: ApiExternalCredentialStatus[];
}

const REQUEST_TIMEOUT_MS = 120_000;

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");

  const controller = new AbortController();
  let timedOut = false;
  const timeoutId = window.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  const abortFromCaller = () => controller.abort();

  if (init?.signal?.aborted) {
    controller.abort();
  } else {
    init?.signal?.addEventListener("abort", abortFromCaller, { once: true });
  }

  try {
    const response = await fetch(`/api${path}`, {
      ...init,
      headers,
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error(timedOut ? "Request timed out." : "Request was aborted.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
    init?.signal?.removeEventListener("abort", abortFromCaller);
  }
}

function toSettings(settings: ApiSettings): AppSettings {
  return {
    analysisMode: settings.analysis_mode,
    defaultMarket: settings.default_market,
    defaultHorizon: settings.default_horizon,
  };
}

function fromSettings(settings: AppSettings): ApiSettings {
  return {
    analysis_mode: settings.analysisMode,
    default_market: settings.defaultMarket,
    default_horizon: settings.defaultHorizon,
  };
}

function toMarketQuote(quote: ApiMarketQuote): MarketQuote {
  return {
    market: quote.market,
    symbol: quote.symbol,
    name: quote.name,
    exchange: quote.exchange,
    currency: quote.currency,
    lastPrice: quote.last_price,
    previousClose: quote.previous_close ?? null,
    changePct: quote.change_pct ?? null,
    asOfAt: quote.as_of_at,
    source: quote.source,
    chartWindow: quote.chart_window ?? "1D",
    chartBars: (quote.chart_bars ?? []).map((bar) => ({
      timestamp: bar.timestamp,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
      volume: bar.volume,
    })),
    keyStats: (quote.key_stats ?? []).map((stat) => ({
      label: stat.label,
      value: stat.value,
    })),
    newsItems: (quote.news_items ?? []).map((item) => ({
      title: item.title,
      url: item.url,
      source: item.source,
      publishedAt: item.published_at,
      snippet: item.snippet,
    })),
  };
}

function toAnalysisSourceDocument(document: ApiAnalysisSourceDocument): AnalysisSourceDocument {
  return {
    id: document.id,
    sourceType: document.source_type,
    sourceName: document.source_name,
    url: document.url,
    title: document.title,
    publishedAt: document.published_at,
    fetchedAt: document.fetched_at ?? null,
    includedInAnalysis: document.included_in_analysis,
    exclusionReason: document.exclusion_reason,
    language: document.language ?? null,
    adapter: document.adapter ?? null,
    relevanceScore: document.relevance_score ?? null,
    safetyFlags: document.safety_flags ?? [],
  };
}

function toAnalysisEvidenceItem(item: ApiAnalysisEvidenceItem): AnalysisEvidenceItem {
  return {
    sourceDocumentId: item.source_document_id,
    stance: item.stance,
    weight: item.weight,
    summary: item.summary,
    quoteExcerpt: item.quote_excerpt,
  };
}

function toScoreResult(result: ApiScoreResult): NonNullable<AnalysisResult["scoreResult"]> {
  return {
    scoreId: result.score_id,
    analysisRequestId: result.analysis_request_id,
    status: result.status,
    buyProbability: result.buy_probability,
    holdProbability: result.hold_probability,
    sellProbability: result.sell_probability,
    confidenceScore: result.confidence_score,
    expectedReturnMinPct: result.expected_return_min_pct ?? 0,
    expectedReturnMaxPct: result.expected_return_max_pct ?? 0,
    downsideProbability: result.downside_probability ?? 0,
    similarEventSampleCount: result.similar_event_sample_count ?? 0,
    similarEventWinRate: result.similar_event_win_rate ?? 0,
    similarEventMedianReturnPct: result.similar_event_median_return_pct ?? 0,
    confidenceFactors: result.confidence_factors ?? [],
    drivers: result.drivers.map((driver) => ({
      sourceDocumentId: driver.source_document_id,
      stance: driver.stance,
      weight: driver.weight,
      probabilityImpact: driver.probability_impact,
      summary: driver.summary,
    })),
    rationale: result.rationale,
  };
}

function toAnalysisResult(result: ApiAnalysisResult): AnalysisResult {
  return {
    analysisRequestId: result.analysis_request_id,
    status: result.status,
    includedDocumentCount: result.included_document_count,
    excludedDocumentCount: result.excluded_document_count,
    sourceAudit: {
      sourceWarnings: result.source_audit?.source_warnings ?? [],
      includedBySourceType: result.source_audit?.included_by_source_type ?? {},
      excludedByReason: result.source_audit?.excluded_by_reason ?? {},
      promptDocumentIds: result.source_audit?.prompt_document_ids ?? [],
    },
    sourceDocuments: result.source_documents.map(toAnalysisSourceDocument),
    evidenceItems: result.evidence_items.map(toAnalysisEvidenceItem),
    summary: result.summary,
    scoreResult: result.score_result ? toScoreResult(result.score_result) : null,
    provider: result.provider,
    model: result.model,
    providerErrorCode: result.provider_error_code,
  };
}

function toNewsArticle(article: ApiNewsArticle): NewsArticle {
  return {
    id: article.id,
    title: article.title,
    url: article.url,
    source: article.source,
    publishedAt: article.published_at,
    snippet: article.snippet,
    provider: article.provider,
    query: article.query,
    rank: article.rank,
    category: article.category,
    headlineKo: article.headline_ko,
    summaryKo: article.summary_ko,
    importanceScore: article.importance_score,
    sourceDomain: article.source_domain,
  };
}

function toNewsSearchRun(run: ApiNewsSearchRun): NewsSearchRun {
  return {
    provider: run.provider,
    query: run.query,
    resultCount: run.result_count,
    status: run.status,
    warning: run.warning,
  };
}

function toNewsDigest(digest: ApiNewsDigest): NewsDigest {
  return {
    digestId: digest.digest_id,
    status: digest.status,
    market: digest.market,
    symbol: digest.symbol,
    stockName: digest.stock_name,
    query: digest.query,
    generatedAt: digest.generated_at,
    summary: digest.summary,
    keyPoints: digest.key_points,
    importantArticles: digest.important_articles.map(toNewsArticle),
    additionalArticles: digest.additional_articles.map(toNewsArticle),
    providerRuns: digest.provider_runs.map(toNewsSearchRun),
    warnings: digest.warnings,
  };
}

function toConversationSnapshot(snapshot: ApiConversationSnapshot): ConversationSnapshot {
  return {
    conversationId: snapshot.conversation_id,
    status: snapshot.status,
    missingInputs: snapshot.missing_inputs,
    analysisRequest: snapshot.analysis_request
      ? {
          market: snapshot.analysis_request.market,
          symbol: snapshot.analysis_request.symbol,
          stockName: snapshot.analysis_request.stock_name,
          horizonType: snapshot.analysis_request.horizon_type,
          analysisMode: snapshot.analysis_request.analysis_mode,
        }
      : null,
    analysisResult: snapshot.analysis_result ? toAnalysisResult(snapshot.analysis_result) : null,
    marketSnapshot: snapshot.market_snapshot ? toMarketQuote(snapshot.market_snapshot) : null,
    newsDigest: snapshot.news_digest ? toNewsDigest(snapshot.news_digest) : null,
    backtestResult: snapshot.backtest_result ? toBacktestResult(snapshot.backtest_result) : null,
    messages: snapshot.messages.map((message) => ({
      id: message.id,
      role: message.role,
      content: message.content,
      meta: message.meta,
      createdAt: message.created_at,
      marketSnapshot: message.market_snapshot ? toMarketQuote(message.market_snapshot) : null,
      newsDigest: message.news_digest ? toNewsDigest(message.news_digest) : null,
      backtestResult: message.backtest_result ? toBacktestResult(message.backtest_result) : null,
    })),
  };
}

function toConversationSummary(summary: ApiConversationSummary): ConversationSummary {
  return {
    conversationId: summary.conversation_id,
    title: summary.title,
    status: summary.status,
    updatedAt: summary.updated_at,
    lastMessage: summary.last_message,
  };
}

function toBacktestResult(result: ApiBacktestResult): BacktestResult {
  return {
    simulationId: result.simulation_id,
    analysisRequestId: result.analysis_request_id,
    evaluationKind: result.evaluation_kind,
    market: result.market,
    symbol: result.symbol,
    entryAt: result.entry_at,
    exitAt: result.exit_at,
    entryPrice: result.entry_price,
    exitPrice: result.exit_price,
    quantity: result.quantity,
    grossReturnPct: result.gross_return_pct,
    grossPnl: result.gross_pnl,
    maxDrawdownPct: result.max_drawdown_pct,
    source: result.source,
    equityCurve: result.equity_curve.map((point) => ({
      timestamp: point.timestamp,
      price: point.price,
      value: point.value,
      returnPct: point.return_pct,
    })),
  };
}

function toLlmCredentialStatus(status: ApiLlmCredentialStatus): LlmCredentialStatus {
  return {
    configured: status.configured,
    credentialId: status.credential_id ?? null,
    label: status.label ?? null,
    provider: status.provider,
    model: status.model,
    baseUrl: status.base_url,
    apiKeyMask: status.api_key_mask,
    keySource: status.key_source,
    isActive: status.is_active ?? false,
    createdAt: status.created_at,
    updatedAt: status.updated_at,
  };
}

function toLlmCredentialProfileList(
  response: ApiLlmCredentialProfileList,
): LlmCredentialProfileList {
  return {
    activeCredentialId: response.active_credential_id,
    credentials: response.credentials.map(toLlmCredentialStatus),
  };
}

function toLlmConnectionTestResult(
  result: ApiLlmConnectionTestResult,
): LlmConnectionTestResult {
  return {
    configured: result.configured,
    status: result.status,
    provider: result.provider,
    model: result.model,
    baseUrl: result.base_url,
    keySource: result.key_source,
    errorCode: result.error_code,
    message: result.message,
  };
}

function toExternalCredentialStatus(
  status: ApiExternalCredentialStatus,
): ExternalCredentialStatus {
  return {
    configured: status.configured,
    credentialId: status.credential_id ?? null,
    label: status.label ?? null,
    provider: status.provider,
    apiKeyMask: status.api_key_mask,
    keySource: status.key_source,
    isActive: status.is_active ?? false,
    createdAt: status.created_at,
    updatedAt: status.updated_at,
  };
}

function toExternalCredentialProfileList(
  response: ApiExternalCredentialProfileList,
): ExternalCredentialProfileList {
  return {
    activeCredentialIds: response.active_credential_ids ?? {},
    credentials: response.credentials.map(toExternalCredentialStatus),
  };
}

function fromLlmCredentialRequest(request: SaveLlmCredentialRequest) {
  return {
    credential_id: request.credentialId,
    label: request.label,
    provider: request.provider,
    model: request.model,
    base_url: request.baseUrl,
    api_key: request.apiKey,
    make_active: request.makeActive ?? true,
  };
}

function fromExternalCredentialRequest(request: SaveExternalCredentialRequest) {
  return {
    credential_id: request.credentialId,
    label: request.label,
    provider: request.provider,
    api_key: request.apiKey,
    make_active: request.makeActive ?? true,
  };
}

export async function fetchSettings(): Promise<AppSettings> {
  return toSettings(await requestJson<ApiSettings>("/settings"));
}

export async function saveSettings(settings: AppSettings): Promise<AppSettings> {
  return toSettings(
    await requestJson<ApiSettings>("/settings", {
      method: "PATCH",
      body: JSON.stringify(fromSettings(settings)),
    }),
  );
}

export async function fetchMarketQuote(
  market: DefaultMarket,
  symbol: string,
  window: MarketChartWindow = "1D",
): Promise<MarketQuote> {
  const path = [
    `/market-data/quotes/${encodeURIComponent(market)}/${encodeURIComponent(symbol)}`,
    `window=${encodeURIComponent(window)}`,
  ].join("?");
  return toMarketQuote(
    await requestJson<ApiMarketQuote>(path),
  );
}

export async function fetchConversations(): Promise<ConversationSummary[]> {
  const response = await requestJson<ApiConversationList>("/conversations");
  return response.conversations.map(toConversationSummary);
}

export async function fetchConversation(conversationId: string): Promise<ConversationSnapshot> {
  return toConversationSnapshot(
    await requestJson<ApiConversationSnapshot>(
      `/conversations/${encodeURIComponent(conversationId)}`,
    ),
  );
}

export async function deleteConversation(conversationId: string): Promise<number> {
  const response = await requestJson<ApiDeleteResponse>(
    `/conversations/${encodeURIComponent(conversationId)}`,
    {
      method: "DELETE",
    },
  );
  return response.deleted_count;
}

export async function clearConversations(): Promise<number> {
  const response = await requestJson<ApiDeleteResponse>("/conversations", {
    method: "DELETE",
  });
  return response.deleted_count;
}

export async function sendConversationMessage(
  request: SendMessageRequest,
): Promise<ConversationSnapshot> {
  const path = request.conversationId
    ? `/conversations/${encodeURIComponent(request.conversationId)}/messages`
    : "/conversations";

  const snapshot = await requestJson<ApiConversationSnapshot>(path, {
    method: "POST",
    body: JSON.stringify({
      content: request.content,
      market: request.market,
      horizon_type: request.horizonType,
      analysis_mode: request.analysisMode,
      response_language: request.responseLanguage,
      llm_credential_id: request.llmCredentialId,
    }),
  });

  return toConversationSnapshot(snapshot);
}

export async function runBacktest(request: BacktestRequest): Promise<BacktestResult> {
  const result = await requestJson<ApiBacktestResult>("/backtests/simulations", {
    method: "POST",
    body: JSON.stringify({
      analysis_request_id: request.analysisRequestId,
      market: request.market,
      symbol: request.symbol,
      entry_at: request.entryAt,
      exit_at: request.exitAt,
      quantity: request.quantity,
    }),
  });

  return toBacktestResult(result);
}

export async function fetchLlmCredentialStatus(): Promise<LlmCredentialStatus> {
  return toLlmCredentialStatus(await requestJson<ApiLlmCredentialStatus>("/credentials/llm"));
}

export async function fetchLlmCredentialProfiles(): Promise<LlmCredentialProfileList> {
  return toLlmCredentialProfileList(
    await requestJson<ApiLlmCredentialProfileList>("/credentials/llm/profiles"),
  );
}

export async function saveLlmCredential(
  request: SaveLlmCredentialRequest,
): Promise<LlmCredentialStatus> {
  return toLlmCredentialStatus(
    await requestJson<ApiLlmCredentialStatus>("/credentials/llm", {
      method: "PUT",
      body: JSON.stringify(fromLlmCredentialRequest(request)),
    }),
  );
}

export async function selectLlmCredentialProfile(
  credentialId: string,
): Promise<LlmCredentialStatus> {
  return toLlmCredentialStatus(
    await requestJson<ApiLlmCredentialStatus>(
      `/credentials/llm/profiles/${encodeURIComponent(credentialId)}/active`,
      {
        method: "PATCH",
      },
    ),
  );
}

export async function deleteLlmCredential(): Promise<LlmCredentialStatus> {
  return toLlmCredentialStatus(
    await requestJson<ApiLlmCredentialStatus>("/credentials/llm", {
      method: "DELETE",
    }),
  );
}

export async function testLlmCredential(): Promise<LlmConnectionTestResult> {
  return toLlmConnectionTestResult(
    await requestJson<ApiLlmConnectionTestResult>("/credentials/llm/test", {
      method: "POST",
    }),
  );
}

export async function fetchExternalCredentialProfiles(): Promise<ExternalCredentialProfileList> {
  return toExternalCredentialProfileList(
    await requestJson<ApiExternalCredentialProfileList>("/credentials/external/profiles"),
  );
}

export async function saveExternalCredential(
  request: SaveExternalCredentialRequest,
): Promise<ExternalCredentialStatus> {
  return toExternalCredentialStatus(
    await requestJson<ApiExternalCredentialStatus>("/credentials/external/profiles", {
      method: "POST",
      body: JSON.stringify(fromExternalCredentialRequest(request)),
    }),
  );
}

export async function selectExternalCredentialProfile(
  credentialId: string,
): Promise<ExternalCredentialStatus> {
  return toExternalCredentialStatus(
    await requestJson<ApiExternalCredentialStatus>(
      `/credentials/external/profiles/${encodeURIComponent(credentialId)}/active`,
      {
        method: "PATCH",
      },
    ),
  );
}

export async function deleteExternalCredentialProfile(
  credentialId: string,
): Promise<ExternalCredentialStatus> {
  return toExternalCredentialStatus(
    await requestJson<ApiExternalCredentialStatus>(
      `/credentials/external/profiles/${encodeURIComponent(credentialId)}`,
      {
        method: "DELETE",
      },
    ),
  );
}
