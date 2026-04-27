from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from app.features.market_data.schemas import MarketQuote
from app.features.settings.schemas import DefaultMarket

QuoteKey = Tuple[str, str]


@dataclass(frozen=True)
class QuoteConfirmationCandidate:
    quote: MarketQuote
    canonical_name: str
    matched_alias: str
    submitted_text: str
    distance: int

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
}

STOCK_ALIASES: Dict[str, QuoteKey] = {
    "005930": ("KR", "005930"),
    "005930.ks": ("KR", "005930"),
    "samsung": ("KR", "005930"),
    "samsung electronics": ("KR", "005930"),
    "삼성전자": ("KR", "005930"),
    "aapl": ("US", "AAPL"),
    "apple": ("US", "AAPL"),
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
}

TOKEN_PUNCTUATION = ".,?!()[]{}\"'“”‘’"


def normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized.endswith(".KS"):
        return normalized[:-3]
    return normalized


def get_quote(market: str, symbol: str) -> Optional[MarketQuote]:
    market_key = market.strip().upper()
    symbol_key = normalize_symbol(symbol)
    return QUOTE_FIXTURES.get((market_key, symbol_key))


def resolve_quote_from_text(text: str, default_market: DefaultMarket) -> Optional[MarketQuote]:
    lowered_text = text.lower()
    for alias, key in STOCK_ALIASES.items():
        if alias in lowered_text:
            return QUOTE_FIXTURES[key]

    tokens = [token.strip(".,?!()[]{}") for token in text.split()]
    for token in tokens:
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
