from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.features.market_data.schemas import MarketQuote
from app.features.settings.schemas import AnalysisMode, DefaultMarket, HorizonType

ConversationStatus = Literal["needs_input", "ready_for_analysis"]
MessageRole = Literal["user", "assistant"]
MissingInput = Literal["stock", "stock_confirmation", "horizon"]


class AnalysisRequestSnapshot(BaseModel):
    market: DefaultMarket
    symbol: str
    stock_name: str
    horizon_type: HorizonType
    analysis_mode: AnalysisMode


class ConversationMessage(BaseModel):
    id: str
    role: MessageRole
    content: str
    meta: str
    created_at: str


class ConversationCommand(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    market: Optional[DefaultMarket] = None
    horizon_type: Optional[HorizonType] = None
    analysis_mode: Optional[AnalysisMode] = None


class ConversationResponse(BaseModel):
    conversation_id: str
    status: ConversationStatus
    missing_inputs: List[MissingInput]
    analysis_request: Optional[AnalysisRequestSnapshot]
    market_snapshot: Optional[MarketQuote]
    messages: List[ConversationMessage]
