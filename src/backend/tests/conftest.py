import pytest

from app.features.market_data import service as market_data_service


@pytest.fixture(autouse=True)
def block_unmocked_finance_data_reader(monkeypatch) -> None:
    """Keep tests on seeded/fake market data unless a test opts in explicitly."""

    def blocked_finance_data_reader(symbol: str, start_date: str, end_date: str):
        raise RuntimeError(
            "Tests must monkeypatch FinanceDataReader data instead of using live market data."
        )

    monkeypatch.setattr(
        market_data_service,
        "_read_finance_data",
        blocked_finance_data_reader,
    )
