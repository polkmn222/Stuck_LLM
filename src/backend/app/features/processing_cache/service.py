import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Mapping, Optional, cast
from uuid import uuid4

from app.features.processing_cache.schemas import (
    CacheBucketStatus,
    CacheInvalidationResponse,
    ProcessingCacheStatus,
)
from app.shared.state_store import LocalStateStore, State

PROCESSING_CACHE_VERSION = "phase_093_v1"
PREDICTION_ARTIFACT_VERSION = "phase_095_v1"


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso_now() -> str:
    return _now().isoformat().replace("+00:00", "Z")


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def cache_key(namespace: str, components: Mapping[str, Any]) -> str:
    return f"{namespace}:{stable_hash({'version': PROCESSING_CACHE_VERSION, **dict(components)})}"


def get_cached_json(
    store: LocalStateStore,
    namespace: str,
    components: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    key = cache_key(namespace, components)
    state = store.read()
    entry = state.get("kv_cache", {}).get(key)
    if not isinstance(entry, dict):
        return None

    expires_at = _parse_datetime(entry.get("expires_at"))
    if expires_at is not None and expires_at <= _now():
        def mutate(state: State) -> None:
            state["kv_cache"].pop(key, None)

        store.update(mutate)
        return None

    payload = entry.get("payload")
    return cast(Dict[str, Any], payload) if isinstance(payload, dict) else None


def set_cached_json(
    store: LocalStateStore,
    namespace: str,
    components: Mapping[str, Any],
    payload: Mapping[str, Any],
    *,
    ttl_seconds: int,
) -> str:
    key = cache_key(namespace, components)
    created_at = _now()
    expires_at = created_at + timedelta(seconds=ttl_seconds)

    def mutate(state: State) -> str:
        state["kv_cache"][key] = {
            "namespace": namespace,
            "key": key,
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "payload": dict(payload),
        }
        return key

    return store.update(mutate)


def _cache_bucket_status(entries: Mapping[str, Any]) -> CacheBucketStatus:
    namespaces: Dict[str, int] = {}
    expired_entries = 0

    for key, raw_entry in entries.items():
        namespace = ""
        expires_at = None
        if isinstance(raw_entry, dict):
            namespace = str(raw_entry.get("namespace") or "")
            expires_at = _parse_datetime(raw_entry.get("expires_at"))
        if not namespace:
            namespace = key.split(":", 1)[0]
        namespaces[namespace] = namespaces.get(namespace, 0) + 1
        if expires_at is not None and expires_at <= _now():
            expired_entries += 1

    return CacheBucketStatus(
        total_entries=len(entries),
        expired_entries=expired_entries,
        namespaces=namespaces,
    )


def get_processing_cache_status(store: LocalStateStore) -> ProcessingCacheStatus:
    state = store.read()
    kv_cache = state.get("kv_cache", {})
    news_processing_runs = state.get("news_processing_runs", {})
    prediction_artifacts = state.get("prediction_artifacts", {})
    return ProcessingCacheStatus(
        kv_cache=_cache_bucket_status(kv_cache if isinstance(kv_cache, dict) else {}),
        news_processing_runs=len(news_processing_runs)
        if isinstance(news_processing_runs, dict)
        else 0,
        prediction_artifacts=len(prediction_artifacts)
        if isinstance(prediction_artifacts, dict)
        else 0,
    )


def invalidate_cached_json(
    store: LocalStateStore,
    key: str,
) -> CacheInvalidationResponse:
    def mutate(state: State) -> bool:
        return state["kv_cache"].pop(key, None) is not None

    return CacheInvalidationResponse(key=key, removed=store.update(mutate))


def record_news_processing_run(
    store: LocalStateStore,
    *,
    digest_payload: Mapping[str, Any],
    cache_hits: int,
    cache_misses: int,
    query_templates: Iterable[str],
) -> str:
    run_id = f"news_process_{uuid4().hex}"
    provider_runs = digest_payload.get("provider_runs", [])
    important_articles = digest_payload.get("important_articles", [])
    additional_articles = digest_payload.get("additional_articles", [])

    def mutate(state: State) -> str:
        state["news_processing_runs"][run_id] = {
            "id": run_id,
            "digest_id": digest_payload.get("digest_id"),
            "market": digest_payload.get("market"),
            "symbol": digest_payload.get("symbol"),
            "stock_name": digest_payload.get("stock_name"),
            "generated_at": digest_payload.get("generated_at"),
            "recorded_at": _iso_now(),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "query_templates": list(query_templates),
            "provider_runs": provider_runs,
            "important_article_count": len(important_articles)
            if isinstance(important_articles, list)
            else 0,
            "additional_article_count": len(additional_articles)
            if isinstance(additional_articles, list)
            else 0,
        }
        return run_id

    return store.update(mutate)


def evidence_set_hash(documents: Iterable[Any]) -> str:
    payload = []
    for document in documents:
        payload.append(
            {
                "source_type": getattr(document, "source_type", None),
                "source_name": getattr(document, "source_name", None),
                "url": getattr(document, "url", None),
                "title": getattr(document, "title", None),
                "published_at": getattr(document, "published_at", None),
                "content_text": getattr(document, "content_text", None),
                "language": getattr(document, "language", None),
                "adapter": getattr(document, "adapter", None),
                "relevance_score": getattr(document, "relevance_score", None),
                "safety_flags": getattr(document, "safety_flags", []),
            }
        )
    return stable_hash(payload)


def prediction_artifact_key(
    *,
    market: str,
    symbol: str,
    horizon_type: str,
    analysis_mode: str,
    as_of_at: str,
    provider: str,
    model: str,
    base_url: Optional[str],
    prompt_version: str,
    evidence_hash: str,
) -> str:
    return cache_key(
        "prediction_artifact",
        {
            "artifact_version": PREDICTION_ARTIFACT_VERSION,
            "market": market,
            "symbol": symbol,
            "horizon_type": horizon_type,
            "analysis_mode": analysis_mode,
            "as_of_at": as_of_at,
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "prompt_version": prompt_version,
            "evidence_hash": evidence_hash,
        },
    )


def get_prediction_artifact(
    store: LocalStateStore,
    artifact_key: str,
) -> Optional[Dict[str, Any]]:
    state = store.read()
    artifact = state.get("prediction_artifacts", {}).get(artifact_key)
    return cast(Dict[str, Any], artifact) if isinstance(artifact, dict) else None


def store_prediction_artifact(
    store: LocalStateStore,
    artifact_key: str,
    *,
    market: str,
    symbol: str,
    as_of_at: str,
    provider: str,
    model: str,
    prompt_version: str,
    evidence_hash: str,
    summary: str,
    evidence_items: Iterable[Mapping[str, Any]],
) -> str:
    def mutate(state: State) -> str:
        state["prediction_artifacts"][artifact_key] = {
            "key": artifact_key,
            "artifact_version": PREDICTION_ARTIFACT_VERSION,
            "market": market,
            "symbol": symbol,
            "as_of_at": as_of_at,
            "provider": provider,
            "model": model,
            "prompt_version": prompt_version,
            "evidence_hash": evidence_hash,
            "summary": summary,
            "evidence_items": [dict(item) for item in evidence_items],
            "created_at": _iso_now(),
        }
        return artifact_key

    return store.update(mutate)
