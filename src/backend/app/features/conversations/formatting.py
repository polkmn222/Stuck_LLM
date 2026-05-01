from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, cast
from uuid import uuid4

from pydantic import BaseModel

from app.features.backtest.schemas import BacktestResponse
from app.features.conversations.schemas import (
    ConversationMessage,
    ConversationSummary,
    MessageRole,
    StockConfirmationSnapshot,
)
from app.features.market_data.schemas import MarketQuote
from app.features.news_digest.schemas import NewsDigest
from app.features.settings.schemas import AnalysisMode, HorizonType

UserLanguage = Literal["en", "ko"]


def model_dump(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return cast(Dict[str, Any], model.model_dump())
    return cast(Dict[str, Any], model.dict())


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_message(
    role: MessageRole,
    content: str,
    meta: str,
    market_snapshot: Optional[MarketQuote] = None,
    stock_confirmation: Optional[StockConfirmationSnapshot] = None,
    news_digest: Optional[NewsDigest] = None,
    backtest_result: Optional[BacktestResponse] = None,
) -> ConversationMessage:
    return ConversationMessage(
        id=f"msg_{uuid4().hex}",
        role=role,
        content=content,
        meta=meta,
        created_at=now_iso(),
        market_snapshot=market_snapshot,
        stock_confirmation=stock_confirmation,
        news_digest=news_digest,
        backtest_result=backtest_result,
    )


def detect_language(content: str) -> UserLanguage:
    if any("\uac00" <= character <= "\ud7a3" for character in content):
        return "ko"
    return "en"


def response_language(
    content: str,
    explicit_language: Optional[UserLanguage],
) -> UserLanguage:
    return explicit_language or detect_language(content)


def format_horizon(horizon_type: HorizonType, language: UserLanguage) -> str:
    english_labels = {
        "intraday": "intraday",
        "swing": "swing",
        "long_term": "long-term",
    }
    korean_labels = {
        "intraday": "장중",
        "swing": "스윙",
        "long_term": "장기",
    }
    return korean_labels[horizon_type] if language == "ko" else english_labels[horizon_type]


def prediction_window_text(horizon_type: HorizonType, language: UserLanguage) -> str:
    if horizon_type == "swing":
        return "향후 5거래일" if language == "ko" else "the next 5 trading days"
    return format_horizon(horizon_type, language)


def format_analysis_mode(analysis_mode: AnalysisMode, language: UserLanguage) -> str:
    if language == "ko":
        return "빠른" if analysis_mode == "quick" else "심층"
    return analysis_mode


def conversation_summary(conversation_id: str, stored: Dict[str, Any]) -> ConversationSummary:
    messages = [
        ConversationMessage(**message) for message in stored.get("messages", [])
    ]
    first_user = next((message for message in messages if message.role == "user"), None)
    last_message = messages[-1] if messages else None
    title = first_user.content.strip() if first_user is not None else "Untitled conversation"
    if len(title) > 64:
        title = f"{title[:61]}..."
    return ConversationSummary(
        conversation_id=conversation_id,
        title=title,
        status=stored.get("status", "ready_for_analysis"),
        updated_at=last_message.created_at if last_message is not None else "",
        last_message=last_message.content if last_message is not None else "",
    )
