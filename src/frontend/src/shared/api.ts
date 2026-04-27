import type {
  AppSettings,
  BacktestRequest,
  BacktestResult,
  ConversationSnapshot,
  DefaultMarket,
  LlmCredentialStatus,
  MarketQuote,
  SaveLlmCredentialRequest,
  SendMessageRequest,
} from "./types";

interface ApiSettings {
  provider: AppSettings["provider"];
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
  as_of_at: string;
  source: string;
}

interface ApiConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta: string;
  created_at: string;
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
  market_snapshot: ApiMarketQuote | null;
  messages: ApiConversationMessage[];
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
  provider: LlmCredentialStatus["provider"];
  model: string | null;
  base_url: string | null;
  api_key_mask: string | null;
  key_source: string | null;
  created_at: string | null;
  updated_at: string | null;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");

  const response = await fetch(`/api${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

function toSettings(settings: ApiSettings): AppSettings {
  return {
    provider: settings.provider,
    analysisMode: settings.analysis_mode,
    defaultMarket: settings.default_market,
    defaultHorizon: settings.default_horizon,
  };
}

function fromSettings(settings: AppSettings): ApiSettings {
  return {
    provider: settings.provider,
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
    asOfAt: quote.as_of_at,
    source: quote.source,
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
    marketSnapshot: snapshot.market_snapshot ? toMarketQuote(snapshot.market_snapshot) : null,
    messages: snapshot.messages.map((message) => ({
      id: message.id,
      role: message.role,
      content: message.content,
      meta: message.meta,
      createdAt: message.created_at,
    })),
  };
}

function toBacktestResult(result: ApiBacktestResult): BacktestResult {
  return {
    simulationId: result.simulation_id,
    analysisRequestId: result.analysis_request_id,
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
    provider: status.provider,
    model: status.model,
    baseUrl: status.base_url,
    apiKeyMask: status.api_key_mask,
    keySource: status.key_source,
    createdAt: status.created_at,
    updatedAt: status.updated_at,
  };
}

function fromLlmCredentialRequest(request: SaveLlmCredentialRequest) {
  return {
    provider: request.provider,
    model: request.model,
    base_url: request.baseUrl,
    api_key: request.apiKey,
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
): Promise<MarketQuote> {
  return toMarketQuote(
    await requestJson<ApiMarketQuote>(
      `/market-data/quotes/${encodeURIComponent(market)}/${encodeURIComponent(symbol)}`,
    ),
  );
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

export async function deleteLlmCredential(): Promise<LlmCredentialStatus> {
  return toLlmCredentialStatus(
    await requestJson<ApiLlmCredentialStatus>("/credentials/llm", {
      method: "DELETE",
    }),
  );
}
