export type AnalysisMode = "quick" | "deep";
export type DefaultMarket = "KR" | "US";
export type HorizonType = "intraday" | "swing" | "long_term";
export type Provider = "openai" | "claude" | "gemini";
export type CredentialProvider = "openai" | "anthropic" | "custom";
export type UiLanguage = "en" | "ko";
export type UiTheme = "dark" | "light";

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
  asOfAt: string;
  source: string;
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
}

export interface ConversationSnapshot {
  conversationId: string;
  status: "needs_input" | "ready_for_analysis";
  missingInputs: Array<"stock" | "horizon" | "stock_confirmation">;
  analysisRequest: AnalysisRequestSnapshot | null;
  marketSnapshot: MarketQuote | null;
  messages: ConversationMessage[];
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
