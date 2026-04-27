from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.features.settings.schemas import AnalysisMode, DefaultMarket, HorizonType
from app.shared.validation import require_timezone_datetime

AnalysisStatus = Literal["completed", "needs_evidence"]
EvidenceStance = Literal["bullish", "neutral", "bearish"]


class SourceDocumentInput(BaseModel):
    source_type: str = Field(min_length=1, max_length=64)
    source_name: str = Field(min_length=1, max_length=160)
    url: Optional[str] = Field(default=None, max_length=2048)
    title: str = Field(min_length=1, max_length=240)
    author: Optional[str] = None
    published_at: str
    fetched_at: Optional[str] = None
    content_text: str = Field(min_length=1, max_length=8000)
    language: Optional[str] = None

    @field_validator("published_at", "fetched_at")
    @classmethod
    def require_aware_timestamp(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return require_timezone_datetime(value)


class SourceDocumentDecision(SourceDocumentInput):
    id: str
    included_in_analysis: bool
    exclusion_reason: Optional[str] = None


class EvidenceItem(BaseModel):
    source_document_id: str
    stance: EvidenceStance
    weight: float
    summary: str
    quote_excerpt: str


class AnalysisRequestCommand(BaseModel):
    market: DefaultMarket
    symbol: str = Field(min_length=1, max_length=32)
    stock_name: str = Field(min_length=1, max_length=160)
    horizon_type: HorizonType
    analysis_mode: AnalysisMode
    as_of_at: str
    source_documents: List[SourceDocumentInput] = Field(max_length=50)

    @field_validator("as_of_at")
    @classmethod
    def require_aware_as_of_at(cls, value: str) -> str:
        return require_timezone_datetime(value)


class AnalysisResponse(BaseModel):
    analysis_request_id: str
    status: AnalysisStatus
    market: DefaultMarket
    symbol: str
    stock_name: str
    horizon_type: HorizonType
    analysis_mode: AnalysisMode
    as_of_at: str
    included_document_count: int
    excluded_document_count: int
    source_documents: List[SourceDocumentDecision]
    evidence_items: List[EvidenceItem]
    summary: str


class StoredAnalysisRecord(AnalysisResponse):
    system_instructions: str
    prompt_context: str
