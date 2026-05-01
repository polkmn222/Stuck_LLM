from app.features.market_data import service as market_data_service
from app.features.news_digest import service as news_digest_service


def _queries_for(symbol: str) -> tuple[str, ...]:
    quote = market_data_service.sp500_metadata_quote(symbol)
    assert quote is not None
    return news_digest_service._build_news_queries(quote, f"{symbol} 뉴스")


def test_sp500_symbol_and_sector_query_templates_cover_representative_companies() -> None:
    expectations = {
        "AAPL": ("Apple Intelligence", "iPhone services", "App Store"),
        "GOOG": ("Google Cloud", "Gemini", "antitrust"),
        "NVDA": ("GPU AI data center", "Blackwell", "semiconductor"),
        "TSLA": ("EV deliveries", "autonomous driving", "battery"),
        "JPM": ("net interest income", "credit losses", "capital markets"),
        "XOM": ("oil gas production", "commodity prices", "capex"),
        "LLY": ("FDA clinical trial", "drug pipeline", "reimbursement"),
        "WMT": ("consumer demand", "pricing margins", "supply chain"),
    }

    for symbol, fragments in expectations.items():
        joined_queries = "\n".join(_queries_for(symbol))
        assert symbol in joined_queries
        for fragment in fragments:
            assert fragment in joined_queries

