import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, cast
from uuid import uuid4

from app.features.analysis.live_provider import (
    ChatCompletionProvider,
    ChatCompletionProviderRequest,
    ChatIntentOutput,
    ChatIntentProvider,
    ChatIntentProviderRequest,
    LiveProviderError,
    LlmAnalysisProvider,
    LlmProviderConfig,
    build_chat_completion_messages,
    build_chat_intent_messages,
)
from app.features.analysis.schemas import (
    AnalysisRequestCommand,
    AnalysisResponse,
    SourceDocumentInput,
)
from app.features.analysis.service import create_live_analysis
from app.features.backtest.schemas import BacktestCommand, BacktestResponse
from app.features.backtest.service import BacktestError, run_backtest
from app.features.conversations.formatting import (
    conversation_summary as _conversation_summary,
    format_analysis_mode as _format_analysis_mode,
    format_horizon as _format_horizon,
    model_dump as _model_dump,
    new_message as _new_message,
    prediction_window_text as _prediction_window_text,
    response_language as _response_language,
)
from app.features.conversations.news_digest_formatting import (
    build_news_digest_summary_prompt as _news_digest_summary_prompt,
    digest_with_llm_output as _digest_with_llm_output,
)
from app.features.conversations.schemas import (
    AnalysisRequestSnapshot,
    ConversationCommand,
    ConversationListResponse,
    ConversationMessage,
    ConversationResponse,
    MissingInput,
    StockConfirmationSnapshot,
)
from app.features.credentials.service import get_llm_credential_secret
from app.features.ingestion.schemas import SourceAdapter, SourceCollectionCommand
from app.features.ingestion.service import DEFAULT_SOURCE_ADAPTERS, collect_sources
from app.features.market_data.schemas import MarketQuote
from app.features.market_data.service import (
    QuoteConfirmationCandidate,
    find_quote_confirmation_candidate,
    get_quote,
    get_usd_krw_rate,
    resolve_sp500_metadata_quote_from_text,
    resolve_quote_from_text,
)
from app.features.news_digest.schemas import NewsDigest
from app.features.news_digest.service import create_news_digest
from app.features.scoring.schemas import ScoreCommand, ScoringEvidenceInput
from app.features.scoring.service import score_evidence
from app.features.settings.schemas import AnalysisMode, DefaultMarket, HorizonType, Settings
from app.features.settings.service import get_settings
from app.shared.credential_crypto import CredentialCipher
from app.shared.state_store import LocalStateStore, State

UserLanguage = Literal["en", "ko"]
ANALYSIS_KEYWORDS = (
    "analyze",
    "analysis",
    "buy",
    "sell",
    "hold",
    "score",
    "probability",
    "recommend",
    "compare",
    "should i",
    "predict",
    "prediction",
    "forecast",
    "전망",
    "예측",
    "분석",
    "매수",
    "매도",
    "보유",
    "확률",
    "추천",
    "비교",
)
PREDICTION_DEFAULT_KEYWORDS = (
    "predict",
    "prediction",
    "forecast",
    "buy",
    "sell",
    "hold",
    "score",
    "probability",
    "recommend",
    "should i",
    "예측",
    "전망",
    "매수",
    "매도",
    "보유",
    "확률",
    "추천",
    "사야",
    "팔아",
)
NEWS_KEYWORDS = (
    "news",
    "headline",
    "headlines",
    "article",
    "articles",
    "latest stories",
    "뉴스",
    "기사",
    "소식",
    "보도",
)
NEWS_TYPO_KEYWORDS = (
    "뉴ㅛ",
    "뉴ㅛㅡ",
    "뉴ㅡ",
    "늇",
    "newz",
    "newss",
    "nwes",
)
SOCIAL_NEWS_KEYWORDS = (
    "sns",
    "social",
    "twitter",
    "facebook",
    "x.com",
    "트위터",
    "페이스북",
)
PNL_KEYWORDS = (
    "if i bought",
    "if i purchased",
    "bought on",
    "purchased on",
    "bought then",
    "what if i bought",
    "샀다면",
    "샀으면",
    "매수했다면",
    "매수했으면",
    "매입했다면",
)
SOURCE_HINT_ADAPTER_KEYWORDS: tuple[tuple[SourceAdapter, tuple[str, ...]], ...] = (
    ("naver_news", ("naver", "네이버")),
    ("tavily_news", ("tavily",)),
    ("gnews_news", ("gnews", "google news")),
    ("reddit", ("reddit", "r/", "레딧")),
    ("us_news", ("us news", "global news", "market news")),
    ("global_macro", ("macro", "rates", "dollar", "currency", "fx", "매크로")),
    ("polling_sentiment", ("poll", "polling", "survey")),
)
DEFAULT_USD_KRW_RATE = 1400.0
DEFAULT_PREDICTION_HORIZON: HorizonType = "swing"


def _recent_chat_context(
    existing_messages: List[ConversationMessage],
) -> List[Dict[str, str]]:
    return [
        {"role": message.role, "content": message.content[:1000]}
        for message in existing_messages[-6:]
    ]


def _chat_intent_provider(
    provider: LlmAnalysisProvider,
) -> Optional[ChatIntentProvider]:
    if isinstance(provider, ChatIntentProvider):
        return provider
    return None


def _chat_completion_provider(
    provider: LlmAnalysisProvider,
) -> Optional[ChatCompletionProvider]:
    if isinstance(provider, ChatCompletionProvider):
        return provider
    return None


def _coerce_chat_intent_output(value: object) -> Optional[ChatIntentOutput]:
    if isinstance(value, ChatIntentOutput):
        return value
    try:
        if hasattr(ChatIntentOutput, "model_validate"):
            return cast(ChatIntentOutput, ChatIntentOutput.model_validate(value))
        return cast(ChatIntentOutput, ChatIntentOutput.parse_obj(value))
    except (TypeError, ValueError):
        return None


def _interpret_chat_intent(
    store: LocalStateStore,
    cipher: CredentialCipher,
    provider: LlmAnalysisProvider,
    content: str,
    existing_messages: List[ConversationMessage],
    command: ConversationCommand,
    settings: Settings,
    language: UserLanguage,
) -> Optional[ChatIntentOutput]:
    intent_provider = _chat_intent_provider(provider)
    if intent_provider is None:
        return None

    credential = get_llm_credential_secret(store, cipher)
    if credential is None:
        return None

    messages = build_chat_intent_messages(
        content=content,
        recent_messages=_recent_chat_context(existing_messages),
        default_market=command.market or settings.default_market,
        default_horizon=command.horizon_type or settings.default_horizon,
        default_analysis_mode=command.analysis_mode or settings.analysis_mode,
        language=language,
    )
    try:
        output = intent_provider.interpret_chat(
            ChatIntentProviderRequest(
                config=LlmProviderConfig(
                    provider=credential.provider,
                    model=credential.model,
                    base_url=credential.base_url,
                    api_key=credential.api_key,
                ),
                messages=messages,
                language=language,
            )
        )
    except LiveProviderError:
        return None
    return _coerce_chat_intent_output(output)


def _complete_simple_chat(
    store: LocalStateStore,
    cipher: CredentialCipher,
    provider: LlmAnalysisProvider,
    content: str,
    existing_messages: List[ConversationMessage],
    language: UserLanguage,
) -> Optional[ConversationMessage]:
    chat_provider = _chat_completion_provider(provider)
    if chat_provider is None:
        return None

    credential = get_llm_credential_secret(store, cipher)
    if credential is None:
        return None

    messages = build_chat_completion_messages(
        content=content,
        recent_messages=_recent_chat_context(existing_messages),
        language=language,
    )
    try:
        output = chat_provider.complete_chat(
            ChatCompletionProviderRequest(
                config=LlmProviderConfig(
                    provider=credential.provider,
                    model=credential.model,
                    base_url=credential.base_url,
                    api_key=credential.api_key,
                ),
                messages=messages,
                language=language,
            )
        )
    except LiveProviderError:
        if language == "ko":
            return _new_message(
                "assistant",
                "LLM 제공자 호출에 실패했습니다. 설정의 저장된 API key와 모델을 확인하세요.",
                "제공자 오류",
            )
        return _new_message(
            "assistant",
            "The LLM provider failed. Check the saved API key and model in Settings.",
            "provider error",
        )

    return _new_message(
        "assistant",
        output,
        "일반 대화" if language == "ko" else "chat",
    )


def _source_adapters_from_hints(source_hints: List[str]) -> List[SourceAdapter]:
    selected: List[SourceAdapter] = []

    for adapter, keywords in SOURCE_HINT_ADAPTER_KEYWORDS:
        for hint in source_hints[:12]:
            normalized_hint = " ".join(str(hint).lower().split())
            if any(keyword in normalized_hint for keyword in keywords):
                if adapter not in selected:
                    selected.append(adapter)
                break

    return selected or list(DEFAULT_SOURCE_ADAPTERS)


def _usd_krw_rate() -> float:
    raw_rate = os.environ.get("STUCK_LLM_USD_KRW_RATE", "").strip()
    if raw_rate:
        try:
            rate = float(raw_rate.replace(",", ""))
            if rate > 0:
                return rate
        except ValueError:
            pass
    provider_rate = get_usd_krw_rate()
    if provider_rate is not None and provider_rate > 0:
        return provider_rate
    return DEFAULT_USD_KRW_RATE


def _format_usd_krw_rate(rate: float) -> str:
    if rate.is_integer():
        return f"{rate:,.0f}"
    return f"{rate:,.2f}"


def _parse_optional_datetime(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _price_text(quote: MarketQuote, language: UserLanguage) -> str:
    if quote.currency == "KRW":
        return f"{quote.last_price:,.0f} {quote.currency}"
    base_text = f"{quote.last_price:,.2f} {quote.currency}"
    if language == "ko" and quote.currency == "USD":
        rate = _usd_krw_rate()
        converted_price = quote.last_price * rate
        return (
            f"{base_text} (약 {converted_price:,.0f} KRW, "
            f"USD/KRW {_format_usd_krw_rate(rate)} 기준)"
        )
    return base_text


def _eligible_chart_closes(quote: MarketQuote) -> List[float]:
    cutoff = _parse_optional_datetime(quote.as_of_at)
    closes: List[float] = []
    for bar in quote.chart_bars:
        bar_time = _parse_optional_datetime(bar.timestamp)
        if cutoff is not None and bar_time is not None and bar_time > cutoff:
            continue
        closes.append(float(bar.close))
    return closes


def _market_data_source_document(quote: MarketQuote) -> SourceDocumentInput:
    parts = [
        (
            f"Latest market snapshot for {quote.name} ({quote.symbol}) on "
            f"{quote.exchange}: last price {quote.last_price:.2f} {quote.currency} "
            f"as of {quote.as_of_at} from {quote.source}."
        )
    ]
    if quote.previous_close is not None:
        parts.append(f"Previous close was {quote.previous_close:.2f} {quote.currency}.")
    if quote.change_pct is not None:
        parts.append(f"Latest session change was {quote.change_pct:.2f}%.")

    closes = _eligible_chart_closes(quote)
    if len(closes) >= 2:
        start_close = closes[0]
        latest_close = closes[-1]
        if start_close:
            chart_return = (latest_close - start_close) / start_close * 100
            parts.append(
                (
                    f"Chart window {quote.chart_window} has {len(closes)} eligible bars; "
                    f"close-to-close return is {chart_return:.2f}%."
                )
            )
        parts.append(
            (
                f"Eligible chart close range is {min(closes):.2f} to "
                f"{max(closes):.2f} {quote.currency}."
            )
        )
    else:
        parts.append("No eligible multi-bar chart trend was available in the snapshot.")

    return SourceDocumentInput(
        source_type="market_data",
        source_name="Market data snapshot",
        url=None,
        title=f"Market data and chart context for {quote.name}",
        published_at=quote.as_of_at,
        fetched_at=quote.as_of_at,
        content_text=" ".join(parts),
        language="en",
        adapter="market_data",
        relevance_score=0.72,
        safety_flags=["market_data", "derived_snapshot"],
    )


def _stock_confirmation_snapshot(
    candidate: QuoteConfirmationCandidate,
    source: Literal["fuzzy_alias", "llm_intent"],
) -> StockConfirmationSnapshot:
    return StockConfirmationSnapshot(
        market=candidate.quote.market,
        symbol=candidate.quote.symbol,
        name=candidate.quote.name,
        exchange=candidate.quote.exchange,
        source=source,
        submitted_text=candidate.submitted_text,
    )


def _candidate_from_stock_confirmation(
    snapshot: StockConfirmationSnapshot,
) -> Optional[QuoteConfirmationCandidate]:
    quote = get_quote(snapshot.market, snapshot.symbol)
    if quote is None:
        return None
    return QuoteConfirmationCandidate(
        quote=quote,
        canonical_name=snapshot.name,
        matched_alias=snapshot.symbol,
        submitted_text=snapshot.submitted_text,
        distance=0 if snapshot.source == "llm_intent" else 1,
    )


def _llm_stock_candidate(
    *,
    content: str,
    exact_quote: Optional[MarketQuote],
    intent: Optional[ChatIntentOutput],
    intent_quote: Optional[MarketQuote],
) -> Optional[QuoteConfirmationCandidate]:
    if exact_quote is not None or intent is None or intent_quote is None:
        return None
    if intent.intent not in {"market_snapshot", "news_digest"}:
        return None
    if intent.stock_query is None:
        return None
    return QuoteConfirmationCandidate(
        quote=intent_quote,
        canonical_name=intent_quote.name,
        matched_alias=intent.stock_query,
        submitted_text=content,
        distance=0,
    )


def _evidence_summary_text(analysis_result: AnalysisResponse, language: UserLanguage) -> str:
    if not analysis_result.evidence_items:
        return ""
    evidence_summaries = "; ".join(
        item.summary for item in analysis_result.evidence_items[:3]
    )
    if language == "ko":
        return f" 근거 요약: {evidence_summaries}."
    return f" Evidence: {evidence_summaries}."


def _score_summary_text(
    analysis_result: AnalysisResponse,
    horizon_type: HorizonType,
    language: UserLanguage,
) -> str:
    score = analysis_result.score_result
    if score is None or score.status != "scored":
        return ""
    window = _prediction_window_text(horizon_type, language)
    if language == "ko":
        return (
            f" {window} 기준 확률은 매수 {score.buy_probability:.1f}%, "
            f"보유 {score.hold_probability:.1f}%, 매도 {score.sell_probability:.1f}%입니다. "
            f"예상 수익률 범위는 {score.expected_return_min_pct:+.1f}%~"
            f"{score.expected_return_max_pct:+.1f}%, "
            f"하락 위험은 {score.downside_probability:.1f}%입니다. "
            f"유사 이벤트 baseline은 표본 {score.similar_event_sample_count}개, "
            f"상승 승률 {score.similar_event_win_rate:.1f}%, "
            f"중앙 수익률 {score.similar_event_median_return_pct:+.1f}%입니다. "
            f"신뢰도는 {score.confidence_score:.2f}입니다."
        )
    return (
        f" For {window}, probabilities are buy {score.buy_probability:.1f}%, "
        f"hold {score.hold_probability:.1f}%, sell {score.sell_probability:.1f}%. "
        f"Expected return range is {score.expected_return_min_pct:+.1f}% to "
        f"{score.expected_return_max_pct:+.1f}%, with downside risk "
        f"{score.downside_probability:.1f}%. "
        f"Similar-event baseline uses {score.similar_event_sample_count} samples, "
        f"{score.similar_event_win_rate:.1f}% win rate, and "
        f"{score.similar_event_median_return_pct:+.1f}% median return. "
        f"Confidence is {score.confidence_score:.2f}."
    )


def _analysis_keywords_requested(content: str) -> bool:
    normalized = content.lower()
    return any(keyword in normalized for keyword in ANALYSIS_KEYWORDS)


def _prediction_default_requested(
    content: str,
    intent: Optional[ChatIntentOutput],
) -> bool:
    if intent is not None and intent.horizon_type is not None:
        return False
    normalized = content.lower()
    return any(keyword in normalized for keyword in PREDICTION_DEFAULT_KEYWORDS)


def _news_keywords_requested(content: str) -> bool:
    normalized = content.lower()
    return any(keyword in normalized for keyword in NEWS_KEYWORDS)


def _news_typo_requested(content: str) -> bool:
    normalized = " ".join(content.lower().split())
    if any(keyword in normalized for keyword in NEWS_TYPO_KEYWORDS):
        return True
    compact = re.sub(r"\s+", "", normalized)
    return any(keyword in compact for keyword in NEWS_TYPO_KEYWORDS)


def _social_news_requested(content: str) -> bool:
    normalized = content.lower()
    return any(keyword in normalized for keyword in SOCIAL_NEWS_KEYWORDS)


def _pnl_keywords_requested(content: str) -> bool:
    normalized = content.lower()
    return any(keyword in normalized for keyword in PNL_KEYWORDS)


def _market_close_timestamp_for_date(entry_date: datetime, market: DefaultMarket) -> str:
    if market == "KR":
        return f"{entry_date.date().isoformat()}T15:30:00+09:00"
    return f"{entry_date.date().isoformat()}T16:00:00-04:00"


def _parse_entry_date(content: str, quote: MarketQuote) -> Optional[str]:
    as_of = _parse_optional_datetime(quote.as_of_at)
    reference_year = as_of.year if as_of is not None else datetime.now(timezone.utc).year

    iso_match = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", content)
    if iso_match:
        year, month, day = (int(value) for value in iso_match.groups())
        try:
            return _market_close_timestamp_for_date(
                datetime(year, month, day),
                quote.market,
            )
        except ValueError:
            return None

    korean_match = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", content)
    if korean_match:
        month, day = (int(value) for value in korean_match.groups())
        try:
            return _market_close_timestamp_for_date(
                datetime(reference_year, month, day),
                quote.market,
            )
        except ValueError:
            return None

    english_match = re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\s+(\d{1,2})\b",
        content,
        flags=re.IGNORECASE,
    )
    if english_match:
        month_lookup = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        month = month_lookup[english_match.group(1)[:3].lower()]
        day = int(english_match.group(2))
        try:
            return _market_close_timestamp_for_date(
                datetime(reference_year, month, day),
                quote.market,
            )
        except ValueError:
            return None

    return None


def _wants_stock_analysis(
    content: str,
    intent: Optional[ChatIntentOutput],
    *,
    continuing_with_horizon: bool,
) -> bool:
    if intent is not None and intent.intent == "stock_analysis":
        return True
    if _analysis_keywords_requested(content):
        return True
    return continuing_with_horizon


def _wants_news_digest(content: str, intent: Optional[ChatIntentOutput]) -> bool:
    if intent is not None and intent.intent == "news_digest":
        return True
    return (
        _news_keywords_requested(content)
        or _news_typo_requested(content)
        or _social_news_requested(content)
    )


def _market_snapshot_requested(
    content: str,
    quote: Optional[MarketQuote],
    intent: Optional[ChatIntentOutput],
) -> bool:
    if quote is None:
        return False
    if intent is not None and intent.intent == "market_snapshot":
        return True
    if _analysis_keywords_requested(content):
        return False
    normalized = " ".join(content.lower().strip(".,?!()[]{} ").split())
    symbol = quote.symbol.lower()
    name = quote.name.lower()
    return normalized in {symbol, name, f"{symbol}:{quote.exchange.lower()}"} or symbol in {
        token.strip(".,?!()[]{}").lower() for token in content.split()
    }


def _market_snapshot_reply(quote: MarketQuote, language: UserLanguage) -> ConversationMessage:
    news_count = len(quote.news_items)
    if language == "ko":
        news_text = f" 관련 뉴스 {news_count}건도 함께 가져왔습니다." if news_count else ""
        return _new_message(
            "assistant",
            (
                f"{quote.name} ({quote.symbol}) 스냅샷입니다. "
                f"현재가는 {_price_text(quote, language)}이고 "
                f"기준 시각은 {quote.as_of_at}입니다."
                f"{news_text}"
            ),
            "시장 스냅샷",
            market_snapshot=quote,
        )
    news_text = f" I also found {news_count} related news item(s)." if news_count else ""
    return _new_message(
        "assistant",
        (
            f"Here is the market snapshot for {quote.name} ({quote.symbol}): "
            f"{_price_text(quote, language)} as of {quote.as_of_at}.{news_text}"
        ),
        "market snapshot",
        market_snapshot=quote,
    )


def _news_digest_reply(
    quote: MarketQuote,
    digest: NewsDigest,
    language: UserLanguage,
) -> ConversationMessage:
    if language == "ko":
        content = (
            f"{quote.name} ({quote.symbol}) 관련 최신 뉴스 핵심 "
            f"{len(digest.important_articles)}건을 정리했습니다. "
            "출처와 링크는 아래 카드에서 확인할 수 있습니다."
        )
        return _new_message(
            "assistant",
            content,
            "뉴스 요약",
            news_digest=digest,
        )
    content = (
        f"I summarized the top {len(digest.important_articles)} recent news item(s) "
        f"for {quote.name} ({quote.symbol}). Links and search sources are shown below."
    )
    return _new_message(
        "assistant",
        content,
        "news digest",
        news_digest=digest,
    )


def _pnl_reply(
    quote: MarketQuote,
    result: BacktestResponse,
    language: UserLanguage,
) -> ConversationMessage:
    if language == "ko":
        content = (
            f"{quote.name} ({quote.symbol})를 {result.entry_at}에 1주 샀다면 "
            f"{result.exit_at} 기준 수익률은 {result.gross_return_pct:+.2f}%이고 "
            f"손익은 {result.gross_pnl:+,.2f} {quote.currency}입니다. "
            f"최대 낙폭은 {result.max_drawdown_pct:.2f}%입니다. "
            "이 값은 별도 PnL 시뮬레이션이며 과거 시점의 LLM 분석 근거에는 "
            "미래 가격을 섞지 않습니다."
        )
        return _new_message(
            "assistant",
            content,
            "손익 시뮬레이션",
            market_snapshot=quote,
            backtest_result=result,
        )
    content = (
        f"If you bought 1 share of {quote.name} ({quote.symbol}) at {result.entry_at}, "
        f"the return as of {result.exit_at} is {result.gross_return_pct:+.2f}% "
        f"with PnL {result.gross_pnl:+,.2f} {quote.currency}. "
        f"Max drawdown is {result.max_drawdown_pct:.2f}%. "
        "This is a separate PnL simulation and does not feed future prices into "
        "historical LLM evidence analysis."
    )
    return _new_message(
        "assistant",
        content,
        "PnL simulation",
        market_snapshot=quote,
        backtest_result=result,
    )


def _pnl_error_reply(
    quote: MarketQuote,
    language: UserLanguage,
) -> ConversationMessage:
    if language == "ko":
        return _new_message(
            "assistant",
            f"{quote.name} ({quote.symbol})의 요청한 기간에 사용할 가격 데이터가 부족합니다.",
            "손익 시뮬레이션 실패",
            market_snapshot=quote,
        )
    return _new_message(
        "assistant",
        f"Not enough price data is available for {quote.name} ({quote.symbol}) in that range.",
        "PnL simulation failed",
        market_snapshot=quote,
    )


def _complete_news_digest_summary(
    store: LocalStateStore,
    cipher: CredentialCipher,
    provider: LlmAnalysisProvider,
    digest: NewsDigest,
    content: str,
    language: UserLanguage,
) -> NewsDigest:
    chat_provider = _chat_completion_provider(provider)
    if chat_provider is None or not digest.important_articles:
        return digest

    credential = get_llm_credential_secret(store, cipher)
    if credential is None:
        return digest

    try:
        output = chat_provider.complete_chat(
            ChatCompletionProviderRequest(
                config=LlmProviderConfig(
                    provider=credential.provider,
                    model=credential.model,
                    base_url=credential.base_url,
                    api_key=credential.api_key,
                ),
                messages=_news_digest_summary_prompt(digest, content, language),
                language=language,
            )
        ).strip()
    except LiveProviderError:
        return digest
    if not output:
        return digest
    return _digest_with_llm_output(digest, output)


def _assistant_reply(
    missing_inputs: List[MissingInput],
    quote: Optional[MarketQuote],
    stock_candidate: Optional[QuoteConfirmationCandidate],
    horizon_type: Optional[HorizonType],
    analysis_mode: AnalysisMode,
    language: UserLanguage,
    analysis_result: Optional[AnalysisResponse],
    follow_up_question: Optional[str] = None,
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
                stock_confirmation=_stock_confirmation_snapshot(
                    stock_candidate,
                    "llm_intent" if stock_candidate.distance == 0 else "fuzzy_alias",
                ),
            )
        return _new_message(
            role="assistant",
            content=(
                f"Did you mean {stock_candidate.canonical_name} "
                f"({stock_candidate.quote.symbol})? Reply yes to confirm, or send the "
                "exact ticker or company name."
            ),
            meta="confirm stock",
            stock_confirmation=_stock_confirmation_snapshot(
                stock_candidate,
                "llm_intent" if stock_candidate.distance == 0 else "fuzzy_alias",
            ),
        )

    if follow_up_question is not None and missing_inputs:
        return _new_message(
            role="assistant",
            content=follow_up_question,
            meta="확인 필요" if language == "ko" else "needs clarification",
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

    if analysis_result is not None:
        if analysis_result.status == "setup_needed":
            return _new_message(
                role="assistant",
                content=analysis_result.summary,
                meta="설정 필요" if language == "ko" else "setup needed",
            )
        if analysis_result.status == "provider_error":
            return _new_message(
                role="assistant",
                content=analysis_result.summary,
                meta="제공자 오류" if language == "ko" else "provider error",
            )
        if analysis_result.status == "needs_evidence":
            if language == "ko":
                return _new_message(
                    role="assistant",
                    content="요청 시점에 사용할 수 있는 적격 근거가 없어 분석을 완료하지 못했습니다.",
                    meta="근거 필요",
                )
            return _new_message(
                role="assistant",
                content="No eligible evidence was available for the requested analysis time.",
                meta="needs evidence",
            )

        if language == "ko":
            return _new_message(
                role="assistant",
                content=(
                    f"{analysis_result.summary}"
                    f"{_score_summary_text(analysis_result, horizon_type, language)}"
                    f"{_evidence_summary_text(analysis_result, language)}"
                ),
                meta="라이브 분석",
                market_snapshot=quote,
            )
        return _new_message(
            role="assistant",
            content=(
                f"{analysis_result.summary}"
                f"{_score_summary_text(analysis_result, horizon_type, language)}"
                f"{_evidence_summary_text(analysis_result, language)}"
            ),
            meta="live analysis",
            market_snapshot=quote,
        )

    if language == "ko":
        return _new_message(
            role="assistant",
            content=(
                f"{quote.name} ({quote.symbol})에 대한 "
                f"{_format_analysis_mode(analysis_mode, language)} 분석 요청을 "
                f"{_format_horizon(horizon_type, language)} 기간으로 기록했습니다. "
                f"최신 시드 시장 스냅샷은 {quote.as_of_at} 기준 "
                f"{_price_text(quote, language)}입니다. LLM 분석은 아직 연결되지 않았습니다. "
                "따라서 매수/보유/매도 확률은 대기 상태입니다."
            ),
            meta="시장 스냅샷 기록",
            market_snapshot=quote,
        )

    return _new_message(
        role="assistant",
        content=(
            f"I recorded a {analysis_mode} request for {quote.name} ({quote.symbol}) "
            f"over a {_format_horizon(horizon_type, language)} horizon. Latest seeded market "
            f"snapshot is {_price_text(quote, language)} as of {quote.as_of_at}. "
            "LLM analysis is not connected yet, so buy/hold/sell probabilities remain pending."
        ),
        meta="market snapshot recorded",
        market_snapshot=quote,
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
        if message.role != "assistant" or message.stock_confirmation is None:
            continue
        candidate = _candidate_from_stock_confirmation(message.stock_confirmation)
        if candidate is not None:
            return candidate

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


def _create_chat_live_analysis(
    store: LocalStateStore,
    cipher: CredentialCipher,
    provider: LlmAnalysisProvider,
    quote: MarketQuote,
    horizon_type: HorizonType,
    analysis_mode: AnalysisMode,
    language: UserLanguage,
    source_adapters: List[SourceAdapter],
) -> AnalysisResponse:
    collection = collect_sources(
        store,
        SourceCollectionCommand(
            market=quote.market,
            symbol=quote.symbol,
            stock_name=quote.name,
            as_of_at=quote.as_of_at,
            analysis_mode=analysis_mode,
            source_adapters=source_adapters,
        ),
    )
    command = AnalysisRequestCommand(
        market=quote.market,
        symbol=quote.symbol,
        stock_name=quote.name,
        horizon_type=horizon_type,
        analysis_mode=analysis_mode,
        as_of_at=quote.as_of_at,
        source_warnings=collection.warnings,
        source_documents=[
            SourceDocumentInput(**_model_dump(document))
            for document in collection.documents
        ]
        + [_market_data_source_document(quote)],
    )
    return create_live_analysis(
        store=store,
        cipher=cipher,
        command=command,
        provider=provider,
        language=language,
    )


def _analysis_with_score(
    store: LocalStateStore,
    analysis_result: AnalysisResponse,
) -> AnalysisResponse:
    if analysis_result.status != "completed":
        return analysis_result
    score = score_evidence(
        store,
        ScoreCommand(
            analysis_request_id=analysis_result.analysis_request_id,
            evidence_items=[
                ScoringEvidenceInput(**_model_dump(item))
                for item in analysis_result.evidence_items
            ],
            excluded_document_count=analysis_result.excluded_document_count,
        ),
    )
    payload = _model_dump(analysis_result)
    payload["score_result"] = _model_dump(score)
    return AnalysisResponse(**payload)


def _build_response(
    store: LocalStateStore,
    cipher: CredentialCipher,
    provider: LlmAnalysisProvider,
    conversation_id: str,
    existing_messages: List[ConversationMessage],
    command: ConversationCommand,
    settings: Settings,
) -> ConversationResponse:
    content = command.content.strip()
    language = _response_language(content, command.response_language)
    parsed_horizon = _resolve_horizon_from_text(content)
    intent = _interpret_chat_intent(
        store,
        cipher,
        provider,
        content,
        existing_messages,
        command,
        settings,
        language,
    )
    intent_market = intent.market if intent is not None else None
    intent_analysis_mode = intent.analysis_mode if intent is not None else None
    intent_horizon_type = intent.horizon_type if intent is not None else None
    market: DefaultMarket = command.market or intent_market or settings.default_market
    analysis_mode: AnalysisMode = (
        command.analysis_mode or intent_analysis_mode or settings.analysis_mode
    )
    horizon_type = (
        command.horizon_type
        or parsed_horizon
        or intent_horizon_type
        or settings.default_horizon
    )
    exact_quote = resolve_quote_from_text(content, market)
    intent_quote = None
    if exact_quote is None and intent is not None and intent.stock_query:
        intent_quote = resolve_quote_from_text(
            intent.stock_query,
            intent.market or market,
        )
    intent_stock_candidate = _llm_stock_candidate(
        content=content,
        exact_quote=exact_quote,
        intent=intent,
        intent_quote=intent_quote,
    )
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
    if (
        stock_candidate is None
        and exact_quote is None
        and confirmed_candidate is None
        and intent_stock_candidate is not None
    ):
        stock_candidate = intent_stock_candidate
    quote = exact_quote or (
        confirmed_candidate.quote if confirmed_candidate is not None else None
    )
    if quote is None and stock_candidate is None:
        quote = intent_quote
    continuing_with_horizon = (
        (quote is None and stock_candidate is None and parsed_horizon is not None)
        or (quote is not None and parsed_horizon is not None)
    )
    wants_analysis = _wants_stock_analysis(
        content,
        intent,
        continuing_with_horizon=continuing_with_horizon,
    )
    wants_news = _wants_news_digest(content, intent)
    wants_pnl = _pnl_keywords_requested(content)
    if quote is None and stock_candidate is None and wants_news:
        quote = resolve_sp500_metadata_quote_from_text(content)
    if (
        wants_analysis
        and not wants_pnl
        and horizon_type is None
        and _prediction_default_requested(content, intent)
    ):
        horizon_type = DEFAULT_PREDICTION_HORIZON
    intent_follow_up_question = (
        intent.follow_up_question.strip()
        if intent is not None and intent.needs_follow_up and intent.follow_up_question
        else None
    )

    simple_chat_message: Optional[ConversationMessage] = None
    if (
        quote is None
        and stock_candidate is None
        and not wants_analysis
        and not wants_news
        and not wants_pnl
        and intent_follow_up_question is None
    ):
        simple_chat_message = _complete_simple_chat(
            store,
            cipher,
            provider,
            content,
            existing_messages,
            language,
        )

    if simple_chat_message is None and quote is None and stock_candidate is None and wants_analysis:
        quote = _resolve_previous_quote(existing_messages, market)

    snapshot_requested = (
        confirmed_candidate is not None
        and confirmed_candidate.distance == 0
        and parsed_horizon is None
        and not wants_analysis
        and not wants_news
        and not wants_pnl
    ) or _market_snapshot_requested(content, quote, intent)
    if (
        quote is not None
        and stock_candidate is None
        and not wants_analysis
        and not wants_news
        and not wants_pnl
    ):
        snapshot_requested = True

    missing_inputs: List[MissingInput] = []
    if simple_chat_message is not None:
        missing_inputs = []
    elif stock_candidate is not None:
        missing_inputs = ["stock_confirmation"]
    elif intent_follow_up_question is not None and quote is None:
        missing_inputs = ["stock"]
    elif quote is None:
        missing_inputs = ["stock"]
    elif wants_analysis and not wants_pnl and horizon_type is None:
        missing_inputs = ["horizon"]

    user_message = _new_message(
        role="user",
        content=content,
        meta=f"{market} market / {analysis_mode} mode",
    )

    analysis_request: Optional[AnalysisRequestSnapshot] = None
    market_snapshot: Optional[MarketQuote] = None
    analysis_result: Optional[AnalysisResponse] = None
    if simple_chat_message is not None:
        assistant_message = simple_chat_message
        simple_status: Literal[
            "needs_input",
            "ready_for_analysis",
            "analysis_completed",
            "setup_needed",
            "provider_error",
            "chat_completed",
            "market_snapshot",
            "news_digest",
            "pnl_simulation",
        ] = (
            "chat_completed"
            if simple_chat_message.meta not in {"provider error", "제공자 오류"}
            else "provider_error"
        )
        return ConversationResponse(
            conversation_id=conversation_id,
            status=simple_status,
            missing_inputs=[],
            analysis_request=None,
            analysis_result=None,
            market_snapshot=None,
            news_digest=None,
            backtest_result=None,
            messages=[*existing_messages, user_message, assistant_message],
        )

    if snapshot_requested and quote is not None and not wants_analysis:
        assistant_message = _market_snapshot_reply(quote, language)
        return ConversationResponse(
            conversation_id=conversation_id,
            status="market_snapshot",
            missing_inputs=[],
            analysis_request=None,
            analysis_result=None,
            market_snapshot=quote,
            news_digest=None,
            backtest_result=None,
            messages=[*existing_messages, user_message, assistant_message],
        )

    if wants_pnl and quote is not None and stock_candidate is None:
        entry_at = _parse_entry_date(content, quote)
        if entry_at is None:
            assistant_message = _new_message(
                "assistant",
                "매수일을 알려주세요. 예: 2026-04-01 또는 4월 1일"
                if language == "ko"
                else "Please include the buy date, for example 2026-04-01 or April 1.",
                "매수일 필요" if language == "ko" else "entry date needed",
                market_snapshot=quote,
            )
            return ConversationResponse(
                conversation_id=conversation_id,
                status="needs_input",
                missing_inputs=[],
                analysis_request=None,
                analysis_result=None,
                market_snapshot=quote,
                news_digest=None,
                backtest_result=None,
                messages=[*existing_messages, user_message, assistant_message],
            )
        try:
            backtest_result = run_backtest(
                store,
                BacktestCommand(
                    analysis_request_id=None,
                    market=quote.market,
                    symbol=quote.symbol,
                    entry_at=entry_at,
                    exit_at=quote.as_of_at,
                    quantity=1.0,
                ),
            )
            assistant_message = _pnl_reply(quote, backtest_result, language)
            return ConversationResponse(
                conversation_id=conversation_id,
                status="pnl_simulation",
                missing_inputs=[],
                analysis_request=None,
                analysis_result=None,
                market_snapshot=quote,
                news_digest=None,
                backtest_result=backtest_result,
                messages=[*existing_messages, user_message, assistant_message],
            )
        except BacktestError:
            assistant_message = _pnl_error_reply(quote, language)
            return ConversationResponse(
                conversation_id=conversation_id,
                status="pnl_simulation",
                missing_inputs=[],
                analysis_request=None,
                analysis_result=None,
                market_snapshot=quote,
                news_digest=None,
                backtest_result=None,
                messages=[*existing_messages, user_message, assistant_message],
            )

    if wants_news and quote is not None and stock_candidate is None:
        news_digest = create_news_digest(
            quote,
            requested_query=content,
            language=language,
            store=store,
        )
        news_digest = _complete_news_digest_summary(
            store,
            cipher,
            provider,
            news_digest,
            content,
            language,
        )
        assistant_message = _news_digest_reply(quote, news_digest, language)
        return ConversationResponse(
            conversation_id=conversation_id,
            status="news_digest",
            missing_inputs=[],
            analysis_request=None,
            analysis_result=None,
            market_snapshot=None,
            news_digest=news_digest,
            backtest_result=None,
            messages=[*existing_messages, user_message, assistant_message],
        )

    if not missing_inputs and quote is not None and horizon_type is not None:
        analysis_request = AnalysisRequestSnapshot(
            market=quote.market,
            symbol=quote.symbol,
            stock_name=quote.name,
            horizon_type=horizon_type,
            analysis_mode=analysis_mode,
        )
        market_snapshot = quote
        analysis_result = _create_chat_live_analysis(
            store,
            cipher,
            provider,
            quote,
            horizon_type,
            analysis_mode,
            language,
            _source_adapters_from_hints(intent.source_hints if intent else []),
        )
        analysis_result = _analysis_with_score(store, analysis_result)

    assistant_message = _assistant_reply(
        missing_inputs,
        quote,
        stock_candidate,
        horizon_type,
        analysis_mode,
        language,
        analysis_result,
        follow_up_question=intent_follow_up_question,
    )

    status: Literal[
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
    if missing_inputs:
        status = "needs_input"
    elif analysis_result is None:
        status = "ready_for_analysis"
    elif analysis_result.status == "completed":
        status = "analysis_completed"
    elif analysis_result.status == "setup_needed":
        status = "setup_needed"
    elif analysis_result.status == "provider_error":
        status = "provider_error"
    else:
        status = "ready_for_analysis"

    return ConversationResponse(
        conversation_id=conversation_id,
        status=status,
        missing_inputs=missing_inputs,
        analysis_request=analysis_request,
        analysis_result=analysis_result,
        market_snapshot=market_snapshot,
        news_digest=None,
        backtest_result=None,
        messages=[*existing_messages, user_message, assistant_message],
    )


def create_conversation(
    store: LocalStateStore,
    cipher: CredentialCipher,
    provider: LlmAnalysisProvider,
    command: ConversationCommand,
) -> ConversationResponse:
    settings = get_settings(store)
    conversation_id = f"conv_{uuid4().hex}"
    response = _build_response(
        store,
        cipher,
        provider,
        conversation_id,
        [],
        command,
        settings,
    )

    def mutate(state: State) -> ConversationResponse:
        state["conversations"][conversation_id] = _model_dump(response)
        return response

    return store.update(mutate)


def append_message(
    store: LocalStateStore,
    cipher: CredentialCipher,
    provider: LlmAnalysisProvider,
    conversation_id: str,
    command: ConversationCommand,
) -> Optional[ConversationResponse]:
    settings = get_settings(store)
    stored = store.read()["conversations"].get(conversation_id)
    if stored is None:
        return None

    existing_messages = [
        ConversationMessage(**message) for message in stored.get("messages", [])
    ]
    response = _build_response(
        store,
        cipher,
        provider,
        conversation_id,
        existing_messages,
        command,
        settings,
    )
    new_messages = response.messages[len(existing_messages) :]

    def mutate(state: State) -> Optional[ConversationResponse]:
        current = state["conversations"].get(conversation_id)
        if current is None:
            return None
        current_messages = [
            ConversationMessage(**message) for message in current.get("messages", [])
        ]
        merged_response = ConversationResponse(
            **{
                **_model_dump(response),
                "messages": [
                    *[_model_dump(message) for message in current_messages],
                    *[_model_dump(message) for message in new_messages],
                ],
            }
        )
        state["conversations"][conversation_id] = _model_dump(merged_response)
        return merged_response

    return store.update(mutate)


def get_conversation(store: LocalStateStore, conversation_id: str) -> Optional[ConversationResponse]:
    stored = store.read()["conversations"].get(conversation_id)
    if stored is None:
        return None
    return ConversationResponse(**stored)


def delete_conversation(store: LocalStateStore, conversation_id: str) -> bool:
    def mutate(state: State) -> bool:
        return state["conversations"].pop(conversation_id, None) is not None

    return store.update(mutate)


def clear_conversations(store: LocalStateStore) -> int:
    def mutate(state: State) -> int:
        deleted_count = len(state["conversations"])
        state["conversations"].clear()
        return deleted_count

    return store.update(mutate)


def list_conversations(store: LocalStateStore) -> ConversationListResponse:
    summaries = [
        _conversation_summary(conversation_id, stored)
        for conversation_id, stored in store.read()["conversations"].items()
    ]
    summaries.sort(key=lambda summary: summary.updated_at, reverse=True)
    return ConversationListResponse(conversations=summaries)
