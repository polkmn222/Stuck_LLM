from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.features.scoring.schemas import ScoreResponse
from app.features.settings.schemas import AnalysisMode, DefaultMarket, HorizonType
from app.shared.validation import require_timezone_datetime

AnalysisStatus = Literal["completed", "needs_evidence", "setup_needed", "provider_error"]
EvidenceStance = Literal["bullish", "neutral", "bearish"]
ProviderErrorCode = Literal[
    "auth_error",
    "rate_limited",
    "timeout",
    "malformed_output",
    "unsupported_provider",
    "invalid_base_url",
    "provider_error",
]


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
    adapter: Optional[str] = Field(default=None, max_length=64)
    relevance_score: Optional[float] = Field(default=None, ge=0, le=1)
    safety_flags: List[str] = Field(default_factory=list, max_length=12)

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


class SourceAuditSummary(BaseModel):
    source_warnings: List[str] = Field(default_factory=list, max_length=20)
    included_by_source_type: Dict[str, int] = Field(default_factory=dict)
    excluded_by_reason: Dict[str, int] = Field(default_factory=dict)
    prompt_document_ids: List[str] = Field(default_factory=list, max_length=50)


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
    source_warnings: List[str] = Field(default_factory=list, max_length=20)
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
    source_audit: SourceAuditSummary
    source_documents: List[SourceDocumentDecision]
    evidence_items: List[EvidenceItem]
    summary: str
    score_result: Optional[ScoreResponse] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    provider_error_code: Optional[ProviderErrorCode] = None


class StoredAnalysisRecord(AnalysisResponse):
    system_instructions: str
    prompt_context: str
