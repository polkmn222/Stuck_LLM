export type AnalysisMode = "quick" | "deep";
export type DefaultMarket = "KR" | "US";
export type HorizonType = "intraday" | "swing" | "long_term";
export type Provider = "openai" | "claude" | "gemini";
export type CredentialProvider = "openai" | "anthropic" | "cerebras" | "custom";
export type UiLanguage = "en" | "ko";
export type UiTheme = "dark" | "light";
export type MarketChartWindow = "1D" | "5D" | "1M" | "6M" | "YTD" | "1Y" | "5Y" | "MAX";
export type NewsProvider =
  | "tavily_news"
  | "naver_news"
  | "gnews_news"
  | "serpapi_google_news"
  | "serpapi_google_web"
  | "serpapi_social_web";
export type NewsCategory =
  | "official"
  | "earnings"
  | "core_business"
  | "controversy"
  | "market_reaction"
  | "product_service"
  | "quote_page"
  | "other";

export interface UiPreferences {
  language: UiLanguage;
  theme: UiTheme;
}

export interface AppSettings {
  provider: Provider;
  analysisMode: AnalysisMode;
  defaultMarket: DefaultMarket;
  defaultHorizon: HorizonType | null;
}

export interface MarketQuote {
  market: DefaultMarket;
  symbol: string;
  name: string;
  exchange: string;
  currency: string;
  lastPrice: number;
  previousClose: number | null;
  changePct: number | null;
  asOfAt: string;
  source: string;
  chartWindow: MarketChartWindow;
  chartBars: MarketBar[];
  keyStats: MarketKeyStat[];
  newsItems: MarketNewsItem[];
}

export interface MarketBar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketKeyStat {
  label: string;
  value: string;
}

export interface MarketNewsItem {
  title: string;
  url: string | null;
  source: string | null;
  publishedAt: string | null;
  snippet: string | null;
}

export interface AnalysisRequestSnapshot {
  market: DefaultMarket;
  symbol: string;
  stockName: string;
  horizonType: HorizonType;
  analysisMode: AnalysisMode;
}

export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta: string;
  createdAt: string;
  marketSnapshot?: MarketQuote | null;
  newsDigest?: NewsDigest | null;
  backtestResult?: BacktestResult | null;
}

export interface NewsSearchRun {
  provider: NewsProvider;
  query: string;
  resultCount: number;
  status: "completed" | "missing_credential" | "provider_error";
  warning: string | null;
}

export interface NewsArticle {
  id: string;
  title: string;
  url: string | null;
  source: string | null;
  publishedAt: string | null;
  snippet: string | null;
  provider: NewsProvider;
  query: string;
  rank: number;
  category: NewsCategory;
  headlineKo: string | null;
  summaryKo: string | null;
  importanceScore: number;
  sourceDomain: string | null;
}

export interface NewsDigest {
  digestId: string;
  status: "completed" | "partial" | "empty";
  market: DefaultMarket;
  symbol: string;
  stockName: string;
  query: string;
  generatedAt: string;
  summary: string;
  keyPoints: string[];
  importantArticles: NewsArticle[];
  additionalArticles: NewsArticle[];
  providerRuns: NewsSearchRun[];
  warnings: string[];
}

export interface AnalysisSourceDocument {
  id: string;
  sourceType: string;
  sourceName: string;
  url: string | null;
  title: string;
  publishedAt: string;
  fetchedAt: string | null;
  includedInAnalysis: boolean;
  exclusionReason: string | null;
  language: string | null;
  adapter: string | null;
  relevanceScore: number | null;
  safetyFlags: string[];
}

export interface AnalysisEvidenceItem {
  sourceDocumentId: string;
  stance: "bullish" | "neutral" | "bearish";
  weight: number;
  summary: string;
  quoteExcerpt: string;
}

export interface ScoreDriver {
  sourceDocumentId: string;
  stance: AnalysisEvidenceItem["stance"];
  weight: number;
  probabilityImpact: "supports_buy" | "supports_hold" | "supports_sell";
  summary: string;
}

export interface ScoreResult {
  scoreId: string;
  analysisRequestId: string;
  status: "scored" | "needs_evidence";
  buyProbability: number;
  holdProbability: number;
  sellProbability: number;
  confidenceScore: number;
  expectedReturnMinPct: number;
  expectedReturnMaxPct: number;
  downsideProbability: number;
  similarEventSampleCount: number;
  similarEventWinRate: number;
  similarEventMedianReturnPct: number;
  confidenceFactors?: string[];
  drivers: ScoreDriver[];
  rationale: string;
}

export interface AnalysisResult {
  analysisRequestId: string;
  status: "completed" | "needs_evidence" | "setup_needed" | "provider_error";
  includedDocumentCount: number;
  excludedDocumentCount: number;
  sourceAudit: AnalysisSourceAudit;
  sourceDocuments: AnalysisSourceDocument[];
  evidenceItems: AnalysisEvidenceItem[];
  summary: string;
  scoreResult?: ScoreResult | null;
  provider: string | null;
  model: string | null;
  providerErrorCode: string | null;
}

export interface AnalysisSourceAudit {
  sourceWarnings: string[];
  includedBySourceType: Record<string, number>;
  excludedByReason: Record<string, number>;
  promptDocumentIds: string[];
}

export interface ConversationSnapshot {
  conversationId: string;
  status:
    | "needs_input"
    | "ready_for_analysis"
    | "analysis_completed"
    | "setup_needed"
    | "provider_error"
    | "chat_completed"
    | "market_snapshot"
    | "news_digest"
    | "pnl_simulation";
  missingInputs: Array<"stock" | "horizon" | "stock_confirmation">;
  analysisRequest: AnalysisRequestSnapshot | null;
  analysisResult?: AnalysisResult | null;
  marketSnapshot: MarketQuote | null;
  newsDigest?: NewsDigest | null;
  backtestResult?: BacktestResult | null;
  messages: ConversationMessage[];
}

export interface ConversationSummary {
  conversationId: string;
  title: string;
  status: ConversationSnapshot["status"];
  updatedAt: string;
  lastMessage: string;
}

export interface LlmCredentialStatus {
  configured: boolean;
  provider: CredentialProvider | null;
  model: string | null;
  baseUrl: string | null;
  apiKeyMask: string | null;
  keySource: string | null;
  createdAt: string | null;
  updatedAt: string | null;
}

export interface LlmConnectionTestResult {
  configured: boolean;
  status: "ok" | "setup_needed" | "provider_error";
  provider: CredentialProvider | null;
  model: string | null;
  baseUrl: string | null;
  keySource: string | null;
  errorCode: string | null;
  message: string;
}

export interface SaveLlmCredentialRequest {
  provider: CredentialProvider;
  model: string;
  baseUrl: string | null;
  apiKey: string;
}

export interface SendMessageRequest {
  content: string;
  conversationId: string | null;
  market: DefaultMarket;
  horizonType: HorizonType | null;
  analysisMode: AnalysisMode;
  responseLanguage: UiLanguage;
}

export interface BacktestRequest {
  analysisRequestId: string | null;
  market: DefaultMarket;
  symbol: string;
  entryAt: string;
  exitAt: string;
  quantity: number;
}

export interface EquityPoint {
  timestamp: string;
  price: number;
  value: number;
  returnPct: number;
}

export interface BacktestResult {
  simulationId: string;
  analysisRequestId: string | null;
  evaluationKind?: string;
  market: DefaultMarket;
  symbol: string;
  entryAt: string;
  exitAt: string;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  grossReturnPct: number;
  grossPnl: number;
  maxDrawdownPct: number;
  equityCurve: EquityPoint[];
  source: string;
}
