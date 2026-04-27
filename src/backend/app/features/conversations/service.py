from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, cast
from uuid import uuid4

from pydantic import BaseModel

from app.features.conversations.schemas import (
    AnalysisRequestSnapshot,
    ConversationCommand,
    ConversationMessage,
    ConversationResponse,
    MessageRole,
    MissingInput,
)
from app.features.market_data.schemas import MarketQuote
from app.features.market_data.service import (
    QuoteConfirmationCandidate,
    find_quote_confirmation_candidate,
    resolve_quote_from_text,
)
from app.features.settings.schemas import AnalysisMode, DefaultMarket, HorizonType, Settings
from app.features.settings.service import get_settings
from app.shared.state_store import LocalStateStore, State

UserLanguage = Literal["en", "ko"]


def _model_dump(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return cast(Dict[str, Any], model.model_dump())
    return cast(Dict[str, Any], model.dict())


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_message(role: MessageRole, content: str, meta: str) -> ConversationMessage:
    return ConversationMessage(
        id=f"msg_{uuid4().hex}",
        role=role,
        content=content,
        meta=meta,
        created_at=_now(),
    )


def _detect_language(content: str) -> UserLanguage:
    if any("\uac00" <= character <= "\ud7a3" for character in content):
        return "ko"
    return "en"


def _format_horizon(horizon_type: HorizonType, language: UserLanguage) -> str:
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


def _format_analysis_mode(analysis_mode: AnalysisMode, language: UserLanguage) -> str:
    if language == "ko":
        return "빠른" if analysis_mode == "quick" else "심층"
    return analysis_mode


def _price_text(quote: MarketQuote) -> str:
    if quote.currency == "KRW":
        return f"{quote.last_price:,.0f} {quote.currency}"
    return f"{quote.last_price:,.2f} {quote.currency}"


def _assistant_reply(
    missing_inputs: List[MissingInput],
    quote: Optional[MarketQuote],
    stock_candidate: Optional[QuoteConfirmationCandidate],
    horizon_type: Optional[HorizonType],
    analysis_mode: AnalysisMode,
    language: UserLanguage,
) -> ConversationMessage:
    if "stock_confirmation" in missing_inputs:
        if stock_candidate is None:
            return _new_message(
                role="assistant",
                content="Which stock should I analyze? Include a ticker or company name.",
                meta="missing stock",
            )
        if language == "ko":
            return _new_message(
                role="assistant",
                content=(
                    f"{stock_candidate.canonical_name} ({stock_candidate.quote.symbol}) "
                    "말씀이신가요? 맞으면 '네'라고 답하고, 아니면 정확한 티커나 "
                    "회사명을 알려주세요."
                ),
                meta="종목 확인 필요",
            )
        return _new_message(
            role="assistant",
            content=(
                f"Did you mean {stock_candidate.canonical_name} "
                f"({stock_candidate.quote.symbol})? Reply yes to confirm, or send the "
                "exact ticker or company name."
            ),
            meta="confirm stock",
        )

    if "stock" in missing_inputs:
        if language == "ko":
            return _new_message(
                role="assistant",
                content="어떤 종목을 분석할까요? 티커나 회사명을 알려주세요.",
                meta="종목 필요",
            )
        return _new_message(
            role="assistant",
            content="Which stock should I analyze? Include a ticker or company name.",
            meta="missing stock",
        )

    if "horizon" in missing_inputs:
        if language == "ko":
            return _new_message(
                role="assistant",
                content="매수, 보유, 매도 확률을 계산하기 전에 어떤 투자 기간을 사용할까요?",
                meta="기간 필요",
            )
        return _new_message(
            role="assistant",
            content=(
                "Which investment horizon should I use before I score buy, hold, "
                "and sell probabilities?"
            ),
            meta="missing horizon",
        )

    if quote is None or horizon_type is None:
        raise ValueError("A complete request requires a quote and horizon.")

    if language == "ko":
        return _new_message(
            role="assistant",
            content=(
                f"{quote.name} ({quote.symbol})에 대한 "
                f"{_format_analysis_mode(analysis_mode, language)} 분석 요청을 "
                f"{_format_horizon(horizon_type, language)} 기간으로 기록했습니다. "
                f"최신 시드 시장 스냅샷은 {quote.as_of_at} 기준 "
                f"{_price_text(quote)}입니다. LLM 분석은 아직 연결되지 않았습니다. "
                "따라서 매수/보유/매도 확률은 대기 상태입니다."
            ),
            meta="시장 스냅샷 기록",
        )

    return _new_message(
        role="assistant",
        content=(
            f"I recorded a {analysis_mode} request for {quote.name} ({quote.symbol}) "
            f"over a {_format_horizon(horizon_type, language)} horizon. Latest seeded market "
            f"snapshot is {_price_text(quote)} as of {quote.as_of_at}. "
            "LLM analysis is not connected yet, so buy/hold/sell probabilities remain pending."
        ),
        meta="market snapshot recorded",
    )


def _resolve_horizon_from_text(text: str) -> Optional[HorizonType]:
    lowered_text = text.lower()
    if any(keyword in lowered_text for keyword in ["intraday", "day trade", "today"]):
        return "intraday"
    if any(keyword in text for keyword in ["당일", "장중", "단타", "오늘"]):
        return "intraday"
    if any(keyword in lowered_text for keyword in ["swing", "short term", "short-term"]):
        return "swing"
    if any(keyword in text for keyword in ["스윙", "중기"]):
        return "swing"
    if any(keyword in lowered_text for keyword in ["long term", "long-term", "longterm"]):
        return "long_term"
    if any(keyword in text for keyword in ["장기", "장투"]):
        return "long_term"
    return None


def _is_affirmative_confirmation(text: str) -> bool:
    normalized = text.strip().lower().strip(".,?! ")

    def starts_with_standalone_term(term: str) -> bool:
        if normalized == term:
            return True
        if not normalized.startswith(term):
            return False
        next_character = normalized[len(term) : len(term) + 1]
        return next_character in {" ", ",", ".", "!", "?", "，"}

    english_terms = {"yes", "y", "yeah", "yep", "correct", "right"}
    if any(starts_with_standalone_term(term) for term in english_terms):
        return True

    korean_terms = ["네", "예", "응", "맞아", "맞아요", "맞습니다", "맞음", "그래"]
    return any(starts_with_standalone_term(term) for term in korean_terms)


def _resolve_confirmed_stock_candidate(
    existing_messages: List[ConversationMessage],
    market: DefaultMarket,
) -> Optional[QuoteConfirmationCandidate]:
    for message in reversed(existing_messages):
        if message.role != "user":
            continue
        candidate = find_quote_confirmation_candidate(message.content, market)
        if candidate is not None:
            return candidate
    return None


def _resolve_previous_quote(
    existing_messages: List[ConversationMessage],
    market: DefaultMarket,
) -> Optional[MarketQuote]:
    for message in reversed(existing_messages):
        if message.role != "user":
            continue
        quote = resolve_quote_from_text(message.content, market)
        if quote is not None:
            return quote
    return None


def _build_response(
    conversation_id: str,
    existing_messages: List[ConversationMessage],
    command: ConversationCommand,
    settings: Settings,
) -> ConversationResponse:
    content = command.content.strip()
    language = _detect_language(content)
    market: DefaultMarket = command.market or settings.default_market
    analysis_mode: AnalysisMode = command.analysis_mode or settings.analysis_mode
    horizon_type = (
        command.horizon_type or _resolve_horizon_from_text(content) or settings.default_horizon
    )
    exact_quote = resolve_quote_from_text(content, market)
    confirmed_candidate = (
        _resolve_confirmed_stock_candidate(existing_messages, market)
        if _is_affirmative_confirmation(content)
        else None
    )
    stock_candidate = (
        find_quote_confirmation_candidate(content, market)
        if exact_quote is None and confirmed_candidate is None
        else None
    )
    quote = exact_quote or (
        confirmed_candidate.quote if confirmed_candidate is not None else None
    )
    if quote is None and stock_candidate is None:
        quote = _resolve_previous_quote(existing_messages, market)

    missing_inputs: List[MissingInput] = []
    if stock_candidate is not None:
        missing_inputs = ["stock_confirmation"]
    elif quote is None:
        missing_inputs = ["stock"]
    elif horizon_type is None:
        missing_inputs = ["horizon"]

    user_message = _new_message(
        role="user",
        content=content,
        meta=f"{market} market / {analysis_mode} mode",
    )
    assistant_message = _assistant_reply(
        missing_inputs,
        quote,
        stock_candidate,
        horizon_type,
        analysis_mode,
        language,
    )

    analysis_request: Optional[AnalysisRequestSnapshot] = None
    market_snapshot: Optional[MarketQuote] = None
    if not missing_inputs and quote is not None and horizon_type is not None:
        analysis_request = AnalysisRequestSnapshot(
            market=quote.market,
            symbol=quote.symbol,
            stock_name=quote.name,
            horizon_type=horizon_type,
            analysis_mode=analysis_mode,
        )
        market_snapshot = quote

    return ConversationResponse(
        conversation_id=conversation_id,
        status="needs_input" if missing_inputs else "ready_for_analysis",
        missing_inputs=missing_inputs,
        analysis_request=analysis_request,
        market_snapshot=market_snapshot,
        messages=[*existing_messages, user_message, assistant_message],
    )


def create_conversation(store: LocalStateStore, command: ConversationCommand) -> ConversationResponse:
    settings = get_settings(store)
    conversation_id = f"conv_{uuid4().hex}"
    response = _build_response(conversation_id, [], command, settings)

    def mutate(state: State) -> ConversationResponse:
        state["conversations"][conversation_id] = _model_dump(response)
        return response

    return store.update(mutate)


def append_message(
    store: LocalStateStore,
    conversation_id: str,
    command: ConversationCommand,
) -> Optional[ConversationResponse]:
    settings = get_settings(store)

    def mutate(state: State) -> Optional[ConversationResponse]:
        stored = state["conversations"].get(conversation_id)
        if stored is None:
            return None

        existing_messages = [
            ConversationMessage(**message) for message in stored.get("messages", [])
        ]
        response = _build_response(conversation_id, existing_messages, command, settings)
        state["conversations"][conversation_id] = _model_dump(response)
        return response

    return store.update(mutate)


def get_conversation(store: LocalStateStore, conversation_id: str) -> Optional[ConversationResponse]:
    stored = store.read()["conversations"].get(conversation_id)
    if stored is None:
        return None
    return ConversationResponse(**stored)
