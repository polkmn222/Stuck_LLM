from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.features.analysis.schemas import AnalysisResponse
from app.features.backtest.schemas import BacktestResponse
from app.features.market_data.schemas import MarketQuote
from app.features.news_digest.schemas import NewsDigest
from app.features.settings.schemas import AnalysisMode, DefaultMarket, HorizonType

ConversationStatus = Literal[
    "needs_input",
    "ready_for_analysis",
    "analysis_completed",
    "setup_needed",
    "provider_error",
    "chat_completed",
    "market_snapshot",
    "news_digest",
    "pnl_simulation",
]
MessageRole = Literal["user", "assistant"]
MissingInput = Literal["stock", "stock_confirmation", "horizon"]
ResponseLanguage = Literal["en", "ko"]


class AnalysisRequestSnapshot(BaseModel):
    market: DefaultMarket
    symbol: str
    stock_name: str
    horizon_type: HorizonType
    analysis_mode: AnalysisMode


class StockConfirmationSnapshot(BaseModel):
    market: DefaultMarket
    symbol: str
    name: str
    exchange: str
    source: Literal["fuzzy_alias", "llm_intent"]
    submitted_text: str


class ConversationMessage(BaseModel):
    id: str
    role: MessageRole
    content: str
    meta: str
    created_at: str
    market_snapshot: Optional[MarketQuote] = None
    stock_confirmation: Optional[StockConfirmationSnapshot] = None
    news_digest: Optional[NewsDigest] = None
    backtest_result: Optional[BacktestResponse] = None


class ConversationCommand(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    market: Optional[DefaultMarket] = None
    horizon_type: Optional[HorizonType] = None
    analysis_mode: Optional[AnalysisMode] = None
    response_language: Optional[ResponseLanguage] = None


class ConversationResponse(BaseModel):
    conversation_id: str
    status: ConversationStatus
    missing_inputs: List[MissingInput]
    analysis_request: Optional[AnalysisRequestSnapshot]
    analysis_result: Optional[AnalysisResponse] = None
    market_snapshot: Optional[MarketQuote]
    news_digest: Optional[NewsDigest] = None
    backtest_result: Optional[BacktestResponse] = None
    messages: List[ConversationMessage]


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    status: ConversationStatus
    updated_at: str
    last_message: str


class ConversationListResponse(BaseModel):
    conversations: List[ConversationSummary]


class ConversationDeleteResponse(BaseModel):
    deleted_count: int
