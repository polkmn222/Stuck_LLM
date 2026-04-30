import importlib
import csv
import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, cast

from app.features.market_data.schemas import (
    MarketBar,
    MarketChartWindow,
    MarketKeyStat,
    MarketNewsItem,
    MarketQuote,
)
from app.features.settings.schemas import DefaultMarket

QuoteKey = Tuple[str, str]


@dataclass(frozen=True)
class QuoteConfirmationCandidate:
    quote: MarketQuote
    canonical_name: str
    matched_alias: str
    submitted_text: str
    distance: int


@dataclass(frozen=True)
class Sp500Company:
    symbol: str
    security: str
    aliases: Tuple[str, ...]


QUOTE_FIXTURES: Dict[QuoteKey, MarketQuote] = {
    ("KR", "005930"): MarketQuote(
        market="KR",
        symbol="005930",
        name="Samsung Electronics",
        exchange="KRX",
        currency="KRW",
        last_price=72000.0,
        as_of_at="2026-04-24T15:30:00+09:00",
        source="seeded_local_fixture",
    ),
    ("US", "AAPL"): MarketQuote(
        market="US",
        symbol="AAPL",
        name="Apple",
        exchange="NASDAQ",
        currency="USD",
        last_price=207.15,
        as_of_at="2026-04-24T16:00:00-04:00",
        source="seeded_local_fixture",
    ),
    ("US", "GOOG"): MarketQuote(
        market="US",
        symbol="GOOG",
        name="Alphabet Inc Class C",
        exchange="NASDAQ",
        currency="USD",
        last_price=348.0,
        as_of_at="2026-04-24T16:00:00-04:00",
        source="seeded_local_fixture",
    ),
}

STOCK_ALIASES: Dict[str, QuoteKey] = {
    "005930": ("KR", "005930"),
    "005930.ks": ("KR", "005930"),
    "samsung": ("KR", "005930"),
    "samsung electronics": ("KR", "005930"),
    "삼성전자": ("KR", "005930"),
    "aapl": ("US", "AAPL"),
    "apple": ("US", "AAPL"),
    "apple inc": ("US", "AAPL"),
    "애플": ("US", "AAPL"),
    "goog": ("US", "GOOG"),
    "google": ("US", "GOOG"),
    "alphabet": ("US", "GOOG"),
    "alphabet inc": ("US", "GOOG"),
    "구글": ("US", "GOOG"),
    "알파벳": ("US", "GOOG"),
}

STOCK_DISPLAY_NAMES: Dict[QuoteKey, Dict[str, str]] = {
    ("KR", "005930"): {
        "en": "Samsung Electronics",
        "ko": "삼성전자",
    },
    ("US", "AAPL"): {
        "en": "Apple",
        "ko": "애플",
    },
    ("US", "GOOG"): {
        "en": "Alphabet Inc Class C",
        "ko": "구글",
    },
}

TOKEN_PUNCTUATION = ".,?!()[]{}\"'“”‘’"
SERPAPI_GOOGLE_FINANCE_SOURCE = "serpapi_google_finance"
STOCK_QUERY_FILLER_WORDS = {
    "stock",
    "stocks",
    "share",
    "shares",
    "price",
    "quote",
    "market",
    "finance",
    "주가",
    "시세",
    "가격",
    "종목",
}

SP500_LOCALIZED_ALIASES: Dict[str, Tuple[str, ...]] = {
    "AAPL": ("애플",),
    "AMZN": ("아마존",),
    "COST": ("코스트코",),
    "DIS": ("디즈니", "월트디즈니"),
    "GOOG": ("구글", "알파벳"),
    "GOOGL": ("구글", "알파벳"),
    "KO": ("코카콜라",),
    "MCD": ("맥도날드",),
    "META": ("메타",),
    "MSFT": ("마이크로소프트",),
    "NFLX": ("넷플릭스",),
    "NKE": ("나이키",),
    "NVDA": ("엔비디아",),
    "PEP": ("펩시", "펩시코"),
    "SBUX": ("스타벅스",),
    "TSLA": ("테슬라",),
    "WMT": ("월마트",),
    "XOM": ("엑슨모빌",),
}

US_GOOGLE_FINANCE_EXCHANGES: Dict[str, str] = {
    "AAPL": "NASDAQ",
    "ADBE": "NASDAQ",
    "AMD": "NASDAQ",
    "AMZN": "NASDAQ",
    "AVGO": "NASDAQ",
    "BAC": "NYSE",
    "BRK.B": "NYSE",
    "COST": "NASDAQ",
    "CRM": "NYSE",
    "DIS": "NYSE",
    "GOOG": "NASDAQ",
    "GOOGL": "NASDAQ",
    "HD": "NYSE",
    "IBM": "NYSE",
    "INTC": "NASDAQ",
    "JNJ": "NYSE",
    "JPM": "NYSE",
    "KO": "NYSE",
    "LLY": "NYSE",
    "MA": "NYSE",
    "META": "NASDAQ",
    "MSFT": "NASDAQ",
    "NFLX": "NASDAQ",
    "NVDA": "NASDAQ",
    "ORCL": "NYSE",
    "PEP": "NASDAQ",
    "PG": "NYSE",
    "QCOM": "NASDAQ",
    "SBUX": "NASDAQ",
    "TSLA": "NASDAQ",
    "UNH": "NYSE",
    "V": "NYSE",
    "WMT": "NYSE",
    "XOM": "NYSE",
}


class MarketDataProviderError(Exception):
    pass


def normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized.endswith(".KS"):
        return normalized[:-3]
    return normalized


def _normalize_lookup_text(text: str) -> str:
    normalized = text.lower()
    normalized = re.sub(r"[:/\\|,?!()[\]{}\"'“”‘’]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    tokens = [
        token
        for token in normalized.split()
        if token not in STOCK_QUERY_FILLER_WORDS
    ]
    return " ".join(tokens)


def _strip_common_company_suffixes(name: str) -> str:
    normalized = _normalize_lookup_text(name)
    suffix_pattern = (
        r"\b(inc|incorporated|corp|corporation|company|co|plc|ltd|limited|"
        r"class a|class b|class c|common stock)\b"
    )
    normalized = re.sub(suffix_pattern, " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _sp500_aliases_for(symbol: str, security: str) -> Tuple[str, ...]:
    aliases: List[str] = []

    def add(value: str) -> None:
        normalized = _normalize_lookup_text(value)
        if normalized and normalized not in aliases:
            aliases.append(normalized)

    add(symbol)
    add(security)
    stripped_security = _strip_common_company_suffixes(security)
    if stripped_security:
        add(stripped_security)
    for alias in SP500_LOCALIZED_ALIASES.get(symbol, ()):
        add(alias)
    return tuple(aliases)


@lru_cache(maxsize=1)
def _sp500_companies() -> Tuple[Sp500Company, ...]:
    csv_path = Path(__file__).with_name("sp500_constituents.csv")
    if not csv_path.exists():
        return ()

    companies: List[Sp500Company] = []
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            raw_symbol = str(row.get("Symbol", "")).strip().upper()
            security = _clean_market_text(row.get("Security"))
            if not raw_symbol or not security:
                continue
            symbol = raw_symbol.replace("/", ".")
            companies.append(
                Sp500Company(
                    symbol=symbol,
                    security=security,
                    aliases=_sp500_aliases_for(symbol, security),
                )
            )
    return tuple(companies)


@lru_cache(maxsize=1)
def _sp500_symbol_set() -> frozenset[str]:
    return frozenset(company.symbol for company in _sp500_companies())


def _sp500_alias_matches(company: Sp500Company, lowered_text: str, normalized_text: str) -> Optional[str]:
    for alias in company.aliases:
        if normalized_text == alias:
            return alias
        if _has_hangul(alias) and alias in lowered_text:
            return alias
        if not _has_hangul(alias) and _english_alias_matches(alias, lowered_text):
            return alias
    return None


def _resolve_sp500_quote_from_text(text: str, normalized_text: str) -> Optional[MarketQuote]:
    lowered_text = text.lower()
    for company in _sp500_companies():
        if _sp500_alias_matches(company, lowered_text, normalized_text) is None:
            continue
        return get_quote("US", company.symbol)
    return None


def _english_alias_matches(alias: str, text: str) -> bool:
    escaped_alias = re.escape(alias.lower())
    return re.search(rf"(?<![a-z0-9.]){escaped_alias}(?![a-z0-9.])", text) is not None


def _alias_matches_text(alias: str, lowered_text: str, normalized_text: str) -> bool:
    normalized_alias = _normalize_lookup_text(alias)
    if not normalized_alias:
        return False
    if normalized_text == normalized_alias:
        return True
    if _has_hangul(alias):
        return alias in lowered_text
    return _english_alias_matches(alias, lowered_text)


def _market_timezone_suffix(market: str) -> str:
    return "+09:00" if market == "KR" else "-04:00"


def _market_close_time(market: str) -> str:
    return "15:30:00" if market == "KR" else "16:00:00"


def _date_from_value(value: Any) -> date:
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        raise MarketDataProviderError("Missing FinanceDataReader date value.")
    return datetime.fromisoformat(text[:10]).date()


def _bar_timestamp(value: Any, market: str) -> str:
    bar_date = _date_from_value(value)
    return f"{bar_date.isoformat()}T00:00:00{_market_timezone_suffix(market)}"


def _quote_as_of_at(value: Any, market: str) -> str:
    bar_date = _date_from_value(value)
    return (
        f"{bar_date.isoformat()}T{_market_close_time(market)}"
        f"{_market_timezone_suffix(market)}"
    )


def _coerce_float(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _coerce_price(value: Any) -> Optional[float]:
    number = _coerce_float(value)
    if number is not None:
        return number
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if match is None:
        return None
    return _coerce_float(match.group(0))


def get_usd_krw_rate() -> Optional[float]:
    api_key = _serpapi_api_key()
    if api_key is None:
        return None

    for query in ("USD-KRW", "USD/KRW", "USDKRW"):
        try:
            payload = _search_serpapi_google_finance(
                query,
                api_key,
                window="1D",
                timeout_seconds=10,
            )
        except (MarketDataProviderError, OSError, KeyError, TypeError, ValueError):
            continue
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            continue
        rate = _coerce_price(summary.get("extracted_price") or summary.get("price"))
        if rate is not None and rate > 0:
            return rate
    return None


def _frame_records(frame: Any) -> List[Dict[str, Any]]:
    if frame is None:
        return []
    if hasattr(frame, "empty") and bool(frame.empty):
        return []
    if hasattr(frame, "reset_index"):
        frame = frame.reset_index()
    if hasattr(frame, "to_dict"):
        return cast(List[Dict[str, Any]], frame.to_dict("records"))
    if isinstance(frame, list):
        return cast(List[Dict[str, Any]], frame)
    return []


def _read_finance_data(symbol: str, start_date: str, end_date: str) -> Any:
    finance_data_reader = importlib.import_module("FinanceDataReader")
    return finance_data_reader.DataReader(symbol, start_date, end_date)


def _serpapi_api_key() -> Optional[str]:
    api_key = os.environ.get("SERPAPI_API_KEY", "").strip()
    return api_key or None


def _google_finance_exchange(symbol: str) -> str:
    return US_GOOGLE_FINANCE_EXCHANGES.get(symbol.upper(), "NASDAQ")


def _serpapi_google_finance_query(symbol: str) -> str:
    return _serpapi_google_finance_queries(symbol)[0]


def _serpapi_google_finance_queries(symbol: str) -> List[str]:
    symbol_key = symbol.strip().upper()
    candidates: List[str] = []

    def add_candidate(value: str) -> None:
        candidate = value.strip().upper()
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    if ":" in symbol_key:
        ticker, exchange = symbol_key.split(":", 1)
        add_candidate(symbol_key)
        add_candidate(f"{exchange}:{ticker}")
        add_candidate(ticker)
        return candidates

    primary_exchange = _google_finance_exchange(symbol_key)
    add_candidate(f"{symbol_key}:{primary_exchange}")
    if symbol_key in US_GOOGLE_FINANCE_EXCHANGES:
        add_candidate(f"{primary_exchange}:{symbol_key}")
    for exchange in ("NASDAQ", "NYSE"):
        add_candidate(f"{symbol_key}:{exchange}")
    add_candidate(symbol_key)
    return candidates


def _search_serpapi_google_finance(
    query: str,
    api_key: str,
    *,
    window: str = "1D",
    timeout_seconds: int = 10,
) -> Dict[str, Any]:
    params = {
        "engine": "google_finance",
        "q": query,
        "window": window,
        "api_key": api_key,
    }
    url = f"https://serpapi.com/search.json?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Stuck_LLM market-data provider",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (
        TimeoutError,
        urllib.error.HTTPError,
        urllib.error.URLError,
        OSError,
        ValueError,
    ):
        raise MarketDataProviderError("SerpApi Google Finance request failed.") from None
    if not isinstance(payload, dict):
        raise MarketDataProviderError("SerpApi Google Finance response was malformed.")
    return cast(Dict[str, Any], payload)


def _finance_symbol(market: str, symbol: str) -> str:
    if market == "KR":
        return symbol.zfill(6) if symbol.isdigit() else symbol
    return symbol.upper()


def _bar_from_record(record: Dict[str, Any], market: str) -> Optional[MarketBar]:
    date_value = record.get("Date") or record.get("index") or record.get("datetime")
    open_price = _coerce_float(record.get("Open"))
    high_price = _coerce_float(record.get("High"))
    low_price = _coerce_float(record.get("Low"))
    close_price = _coerce_float(record.get("Close"))
    volume = _coerce_float(record.get("Volume")) or 0.0
    if (
        date_value is None
        or open_price is None
        or high_price is None
        or low_price is None
        or close_price is None
    ):
        return None
    return MarketBar(
        timestamp=_bar_timestamp(date_value, market),
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=volume,
    )


def _change_pct_from_records(
    records: List[Dict[str, Any]],
    bars: List[MarketBar],
) -> Optional[float]:
    if not bars:
        return None
    raw_change = _coerce_float(records[-1].get("Change"))
    if raw_change is not None:
        normalized = raw_change * 100 if abs(raw_change) <= 1 else raw_change
        return round(normalized, 2)
    if len(bars) < 2 or bars[-2].close == 0:
        return None
    return round(((bars[-1].close - bars[-2].close) / bars[-2].close) * 100, 2)


def _parse_serpapi_datetime(value: Any) -> Optional[str]:
    if isinstance(value, datetime):
        return value.isoformat()
    text = re.sub(r"\s+", " ", str(value).strip())
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).isoformat()
    except ValueError:
        pass
    for date_format in (
        "%b %d %Y, %I:%M:%S %p UTC%z",
        "%b %d %Y, %I:%M %p UTC%z",
    ):
        try:
            return datetime.strptime(text, date_format).isoformat()
        except ValueError:
            continue
    return None


def _serpapi_previous_close(
    payload: Dict[str, Any],
    summary: Dict[str, Any],
    last_price: float,
) -> Optional[float]:
    knowledge_graph = payload.get("knowledge_graph")
    if isinstance(knowledge_graph, dict):
        key_stats = knowledge_graph.get("key_stats")
        if isinstance(key_stats, dict):
            stats = key_stats.get("stats")
            if isinstance(stats, list):
                for stat in stats:
                    if not isinstance(stat, dict):
                        continue
                    label = str(stat.get("label", "")).strip().lower()
                    if "previous close" in label or "prev close" in label:
                        return _coerce_price(stat.get("value"))

    movement = summary.get("price_movement")
    if not isinstance(movement, dict):
        return None
    movement_value = _coerce_price(movement.get("value"))
    movement_direction = str(movement.get("movement", "")).strip().lower()
    if movement_value is None:
        return None
    if movement_direction == "up":
        return round(last_price - movement_value, 4)
    if movement_direction == "down":
        return round(last_price + movement_value, 4)
    return None


def _serpapi_change_pct(summary: Dict[str, Any], previous_close: Optional[float]) -> Optional[float]:
    movement = summary.get("price_movement")
    if isinstance(movement, dict):
        percentage = _coerce_price(movement.get("percentage"))
        if percentage is not None:
            return round(percentage, 2)
    last_price = _coerce_price(summary.get("extracted_price") or summary.get("price"))
    if last_price is None or previous_close is None or previous_close == 0:
        return None
    return round(((last_price - previous_close) / previous_close) * 100, 2)


def _serpapi_chart_bars(payload: Dict[str, Any]) -> List[MarketBar]:
    graph = payload.get("graph")
    if not isinstance(graph, list):
        return []

    bars: List[MarketBar] = []
    for point in graph:
        if not isinstance(point, dict):
            continue
        price = _coerce_price(point.get("price"))
        timestamp = _parse_serpapi_datetime(point.get("date") or point.get("time"))
        if price is None or timestamp is None:
            continue
        volume = _coerce_price(point.get("volume")) or 0.0
        # SerpApi graph points are quote-line data, not real OHLC candles.
        bars.append(
            MarketBar(
                timestamp=timestamp,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=volume,
            )
        )
    return bars


def _serpapi_key_stats(payload: Dict[str, Any]) -> List[MarketKeyStat]:
    knowledge_graph = payload.get("knowledge_graph")
    if not isinstance(knowledge_graph, dict):
        return []
    key_stats = knowledge_graph.get("key_stats")
    if not isinstance(key_stats, dict):
        return []
    stats = key_stats.get("stats")
    if not isinstance(stats, list):
        return []

    parsed_stats: List[MarketKeyStat] = []
    for stat in stats[:12]:
        if not isinstance(stat, dict):
            continue
        label = _clean_market_text(stat.get("label"))
        value = _clean_market_text(stat.get("value"))
        if not label or not value:
            continue
        if "previous close" in label.lower() or "prev close" in label.lower():
            continue
        parsed_stats.append(MarketKeyStat(label=label, value=value))
    return parsed_stats


def _clean_market_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _serpapi_news_records(raw_news: List[Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for item in raw_news:
        if not isinstance(item, dict):
            continue
        nested_items = item.get("items")
        if isinstance(nested_items, list):
            records.extend(
                cast(
                    List[Dict[str, Any]],
                    [entry for entry in nested_items if isinstance(entry, dict)],
                )
            )
            continue
        records.append(item)
    return records


def _serpapi_news_items(payload: Dict[str, Any]) -> List[MarketNewsItem]:
    raw_news = payload.get("news_results") or payload.get("news")
    if not isinstance(raw_news, list):
        return []

    news_items: List[MarketNewsItem] = []
    for item in _serpapi_news_records(raw_news)[:8]:
        title = _clean_market_text(item.get("title") or item.get("snippet"))
        if not title:
            continue
        raw_source = item.get("source")
        source = None
        if isinstance(raw_source, dict):
            source = _clean_market_text(raw_source.get("name"))
        else:
            source = _clean_market_text(raw_source)
        news_items.append(
            MarketNewsItem(
                title=title,
                url=_clean_market_text(item.get("link") or item.get("url")) or None,
                source=source or None,
                published_at=_parse_serpapi_datetime(item.get("date") or item.get("published_at")),
                snippet=_clean_market_text(item.get("snippet") or item.get("summary")) or None,
            )
        )
    return news_items


def _quote_from_serpapi_payload(
    symbol: str,
    payload: Dict[str, Any],
    *,
    window: MarketChartWindow = "1D",
) -> Optional[MarketQuote]:
    if payload.get("error"):
        return None
    metadata = payload.get("search_metadata")
    if isinstance(metadata, dict):
        status = str(metadata.get("status", "")).strip().lower()
        if status and status != "success":
            return None

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return None

    last_price = _coerce_price(summary.get("extracted_price") or summary.get("price"))
    if last_price is None:
        return None

    chart_bars = _serpapi_chart_bars(payload)
    as_of_at = _parse_serpapi_datetime(summary.get("date") or summary.get("market_time"))
    if as_of_at is None and chart_bars:
        as_of_at = chart_bars[-1].timestamp
    if as_of_at is None:
        return None

    quote_symbol = str(summary.get("stock") or symbol).strip().upper() or symbol
    name = str(summary.get("title") or summary.get("name") or quote_symbol).strip()
    exchange = str(summary.get("exchange") or _google_finance_exchange(quote_symbol)).strip()
    currency = str(summary.get("currency") or "USD").strip().upper() or "USD"
    previous_close = _serpapi_previous_close(payload, summary, last_price)

    return MarketQuote(
        market="US",
        symbol=quote_symbol,
        name=name or quote_symbol,
        exchange=exchange.upper() or _google_finance_exchange(quote_symbol),
        currency=currency,
        last_price=last_price,
        previous_close=previous_close,
        change_pct=_serpapi_change_pct(summary, previous_close),
        as_of_at=as_of_at,
        source=SERPAPI_GOOGLE_FINANCE_SOURCE,
        chart_window=window,
        chart_bars=chart_bars,
        key_stats=_serpapi_key_stats(payload),
        news_items=_serpapi_news_items(payload),
    )


def _quote_from_serpapi_google_finance(
    symbol: str,
    window: MarketChartWindow = "1D",
) -> Optional[MarketQuote]:
    api_key = _serpapi_api_key()
    if api_key is None:
        return None

    fallback_quote: Optional[MarketQuote] = None
    for query in _serpapi_google_finance_queries(symbol):
        try:
            payload = _search_serpapi_google_finance(
                query,
                api_key,
                window=window,
                timeout_seconds=10,
            )
            quote = _quote_from_serpapi_payload(symbol, payload, window=window)
        except (MarketDataProviderError, ImportError, OSError, KeyError, TypeError, ValueError):
            continue
        if quote is not None:
            if quote.chart_bars:
                return quote
            if fallback_quote is None:
                fallback_quote = quote
    return fallback_quote


def _quote_from_finance_data_reader(market: str, symbol: str) -> Optional[MarketQuote]:
    today = date.today()
    start_date = (today - timedelta(days=60)).isoformat()
    end_date = today.isoformat()
    market_symbol = _finance_symbol(market, symbol)

    try:
        frame = _read_finance_data(market_symbol, start_date, end_date)
    except Exception:
        return None

    records = _frame_records(frame)
    bar_records: List[Tuple[Dict[str, Any], MarketBar]] = []
    for record in records:
        try:
            bar = _bar_from_record(record, market)
        except (MarketDataProviderError, ValueError):
            continue
        if bar is not None:
            bar_records.append((record, bar))

    valid_records = [record for record, _ in bar_records]
    bars = [bar for _, bar in bar_records]
    if not bars:
        return None

    key = (market, symbol)
    seeded_quote = QUOTE_FIXTURES.get(key)
    if seeded_quote is not None:
        name = seeded_quote.name
        exchange = seeded_quote.exchange
        currency = seeded_quote.currency
    else:
        name = symbol
        exchange = "KRX" if market == "KR" else "US"
        currency = "KRW" if market == "KR" else "USD"

    last_record = bar_records[-1][0]
    previous_close = bars[-2].close if len(bars) > 1 else None
    return MarketQuote(
        market=cast(DefaultMarket, market),
        symbol=symbol,
        name=name,
        exchange=exchange,
        currency=currency,
        last_price=bars[-1].close,
        previous_close=previous_close,
        change_pct=_change_pct_from_records(valid_records, bars),
        as_of_at=_quote_as_of_at(
            last_record.get("Date") or last_record.get("index") or last_record.get("datetime"),
            market,
        ),
        source="finance_data_reader",
        chart_bars=bars[-30:],
    )


def get_quote(
    market: str,
    symbol: str,
    window: MarketChartWindow = "1D",
) -> Optional[MarketQuote]:
    market_key = market.strip().upper()
    symbol_key = normalize_symbol(symbol)
    if market_key == "US":
        serpapi_quote = _quote_from_serpapi_google_finance(symbol_key, window=window)
        if serpapi_quote is not None:
            return serpapi_quote
    if market_key in {"KR", "US"}:
        live_quote = _quote_from_finance_data_reader(market_key, symbol_key)
        if live_quote is not None:
            return live_quote
    return QUOTE_FIXTURES.get((market_key, symbol_key))


def resolve_quote_from_text(text: str, default_market: DefaultMarket) -> Optional[MarketQuote]:
    lowered_text = text.lower()
    normalized_text = _normalize_lookup_text(text)
    for alias, key in STOCK_ALIASES.items():
        if _alias_matches_text(alias, lowered_text, normalized_text):
            return get_quote(*key)

    sp500_quote = _resolve_sp500_quote_from_text(text, normalized_text)
    if sp500_quote is not None:
        return sp500_quote

    tokens = [token.strip(".,?!()[]{}") for token in normalized_text.split()]
    for token in tokens:
        normalized_token = normalize_symbol(token)
        if normalized_token in _sp500_symbol_set() or normalized_token in US_GOOGLE_FINANCE_EXCHANGES:
            quote = get_quote("US", normalized_token)
            if quote is not None:
                return quote
        quote = get_quote(default_market, token)
        if quote is not None:
            return quote
    return None


def _has_hangul(text: str) -> bool:
    return any("\uac00" <= character <= "\ud7a3" for character in text)


def _display_name_for_alias(alias: str, key: QuoteKey) -> str:
    language = "ko" if _has_hangul(alias) else "en"
    names = STOCK_DISPLAY_NAMES.get(key)
    if names is None:
        return QUOTE_FIXTURES[key].name
    return names[language]


def _clean_token(token: str) -> str:
    return token.strip(TOKEN_PUNCTUATION).lower()


def _text_windows(text: str, word_count: int) -> Iterable[str]:
    tokens = [_clean_token(token) for token in text.split()]
    tokens = [token for token in tokens if token]
    if word_count <= 1:
        return tokens
    return [
        " ".join(tokens[index : index + word_count])
        for index in range(0, len(tokens) - word_count + 1)
    ]


def _fuzzy_aliases() -> Iterable[Tuple[str, QuoteKey]]:
    for alias, key in STOCK_ALIASES.items():
        comparable_alias = alias.replace(" ", "")
        if len(comparable_alias) < 4 or comparable_alias.replace(".", "").isdigit():
            continue
        yield alias, key


def _max_typo_distance(alias: str) -> int:
    return 2 if len(alias.replace(" ", "")) >= 8 else 1


def _edit_distance(left: str, right: str, max_distance: int) -> int:
    if abs(len(left) - len(right)) > max_distance:
        return max_distance + 1

    previous_row: List[int] = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current_row = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            insertion = current_row[right_index - 1] + 1
            deletion = previous_row[right_index] + 1
            substitution = previous_row[right_index - 1] + (
                0 if left_character == right_character else 1
            )
            current_row.append(min(insertion, deletion, substitution))
        if min(current_row) > max_distance:
            return max_distance + 1
        previous_row = current_row
    return previous_row[-1]


def find_quote_confirmation_candidate(
    text: str,
    default_market: DefaultMarket,
) -> Optional[QuoteConfirmationCandidate]:
    if resolve_quote_from_text(text, default_market) is not None:
        return None

    best_candidate: Optional[QuoteConfirmationCandidate] = None
    best_score: Optional[Tuple[int, int]] = None

    for alias, key in _fuzzy_aliases():
        max_distance = _max_typo_distance(alias)
        word_count = len(alias.split())
        for submitted_text in _text_windows(text, word_count):
            distance = _edit_distance(submitted_text, alias, max_distance)
            if distance == 0 or distance > max_distance:
                continue

            score = (distance, -len(alias))
            if best_score is not None and score >= best_score:
                continue

            best_score = score
            best_candidate = QuoteConfirmationCandidate(
                quote=QUOTE_FIXTURES[key],
                canonical_name=_display_name_for_alias(alias, key),
                matched_alias=alias,
                submitted_text=submitted_text,
                distance=distance,
            )

    return best_candidate
