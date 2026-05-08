import pytest
from pydantic import BaseModel

from app.features.analysis import service as analysis_service
from app.shared.datetime_utils import parse_aware_datetime, parse_optional_aware_datetime
from app.shared.pydantic_compat import model_dump


class CompatModel(BaseModel):
    name: str
    count: int


def test_shared_model_dump_supports_pydantic_models() -> None:
    assert model_dump(CompatModel(name="sample", count=2)) == {
        "name": "sample",
        "count": 2,
    }


def test_shared_datetime_utils_require_timezone_and_allow_optional_parse() -> None:
    parsed = parse_aware_datetime("2026-04-29T16:00:00-04:00")

    assert parsed.utcoffset() is not None
    assert parse_optional_aware_datetime("not-a-date") is None
    with pytest.raises(ValueError):
        parse_aware_datetime("2026-04-29T16:00:00")


def test_analysis_service_no_longer_exposes_legacy_normalization_helpers() -> None:
    legacy_names = {
        "_parse_datetime",
        "_quote_excerpt",
        "_escaped_prompt_json",
        "_source_document_id",
        "_stance_for",
        "_document_decisions",
        "_safe_source_warnings",
        "_source_audit",
        "_evidence_items",
        "_prompt_document_payload",
        "_prompt_context",
        "_with_inclusion",
        "_apply_live_prompt_budget",
        "BULLISH_TERMS",
        "BEARISH_TERMS",
        "SAFE_WARNING_CODE_RE",
    }

    assert not (legacy_names & set(vars(analysis_service)))
