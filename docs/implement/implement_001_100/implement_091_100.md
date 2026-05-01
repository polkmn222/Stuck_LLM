# Implement Phase 091-100 Summary

This file is a compact index for agents. Keep the original detailed log as the source of truth.

## phase_091 - Workflow Docs And Unit Test Policy Hardening

Phase Goal
- Updated code-authoring workflow docs with stock-universe rules, matrix-test expectations, cache key requirements, source adapter cache safety, and prediction artifact invalidation rules.
- Updated validation workflow docs to require representative `symbol x intent x language` tests, provider fakes, cache hit/miss checks, `as_of_at` cutoff checks, and secret-leak checks.

Completed Work
- Updated code-authoring workflow docs with stock-universe rules, matrix-test expectations, cache key requirements, source adapter cache safety, and prediction artifact invalidation rules.
- Updated validation workflow docs to require representative `symbol x intent x language` tests, provider fakes, cache hit/miss checks, `as_of_at` cutoff checks, and secret-leak checks.
- Updated orchestration workflow docs with external repo audit guidance and a clear separation between KV cache acceleration and normalized processing/audit records.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase092_sp500_stock_universe.py src/backend/tests/test_phase093_news_cache_processing_store.py src/backend/tests/test_phase094_sp500_query_templates.py src/backend/tests/test_phase095_prediction_artifact_store.py src/backend/tests/test_phase096_ai_capabilities.py -q` passed with 7 tests and one local urllib3 LibreSSL warning after one query-template test fix.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py src/backend/tests/test_phase090_us_mega_cap_intent_matrix.py src/backend/tests/test_phase092_sp500_stock_universe.py src/backend/tests/test_phase093_news_cache_processing_store.py src/backend/tests/test_phase094_sp500_query_templates.py src/backend/tests/test_phase095_prediction_artifact_store.py src/backend/tests/test_phase096_ai_capabilities.py -q` passed with 20 tests and one local urllib3 LibreSSL warning.

Next Steps
- No new skill installation was needed. Existing project-local skills covered architecture, database design, backend implementation, stock-analysis LLM behavior, workflow docs, and validation.

## phase_092 - S&P 500 Stock Universe Boundary

Phase Goal
- Extended the S&P 500 CSV loader to expose sector and sub-industry metadata in `Sp500Company`.
- Added public helpers to list S&P 500 companies, resolve a company by symbol, build Google Finance candidate queries, and create metadata-only quotes for news lookup.

Completed Work
- Extended the S&P 500 CSV loader to expose sector and sub-industry metadata in `Sp500Company`.
- Added public helpers to list S&P 500 companies, resolve a company by symbol, build Google Finance candidate queries, and create metadata-only quotes for news lookup.
- Conversation news routing can now use a metadata-only S&P 500 quote when live quote data is unavailable, while chart and prediction paths still require real or fixture market data.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase092_sp500_stock_universe.py -q` passed as part of the phase_092 through phase_096 targeted run.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py src/backend/tests/test_phase090_us_mega_cap_intent_matrix.py src/backend/tests/test_phase092_sp500_stock_universe.py src/backend/tests/test_phase093_news_cache_processing_store.py src/backend/tests/test_phase094_sp500_query_templates.py src/backend/tests/test_phase095_prediction_artifact_store.py src/backend/tests/test_phase096_ai_capabilities.py -q` passed with 20 tests and one local urllib3 LibreSSL warning.

Next Steps
- Metadata-only quotes intentionally have no price/chart data and are used only to construct news digests.

## phase_093 - News KV Cache And Processing Records

Phase Goal
- Added a `processing_cache` feature with deterministic cache keys, TTL-based JSON KV entries, news processing run records, evidence hashing, and prediction artifact helpers.
- Extended the local state-store DB shape with `kv_cache`, `news_processing_runs`, and `prediction_artifacts`.

Completed Work
- Added a `processing_cache` feature with deterministic cache keys, TTL-based JSON KV entries, news processing run records, evidence hashing, and prediction artifact helpers.
- Extended the local state-store DB shape with `kv_cache`, `news_processing_runs`, and `prediction_artifacts`.
- Updated news provider collection to cache completed provider/query results for 15 minutes and record cache hits/misses plus provider-run transparency.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase093_news_cache_processing_store.py -q` passed as part of the phase_092 through phase_096 targeted run.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py src/backend/tests/test_phase090_us_mega_cap_intent_matrix.py src/backend/tests/test_phase092_sp500_stock_universe.py src/backend/tests/test_phase093_news_cache_processing_store.py src/backend/tests/test_phase094_sp500_query_templates.py src/backend/tests/test_phase095_prediction_artifact_store.py src/backend/tests/test_phase096_ai_capabilities.py -q` passed with 20 tests and one local urllib3 LibreSSL warning.

Next Steps
- The current DB boundary is the existing local JSON state store. A later PostgreSQL migration should map the same keys and records into real tables.

## phase_094 - S&P 500 Query Templates

Phase Goal
- Added symbol-specific query profiles for Apple, Google/Alphabet, Nvidia, Tesla, and Walmart.
- Added sector-aware query profiles for S&P 500 GICS sectors including financials, energy, health care, information technology, consumer, industrials, utilities, real estate, materials, and communication services.

Completed Work
- Added symbol-specific query profiles for Apple, Google/Alphabet, Nvidia, Tesla, and Walmart.
- Added sector-aware query profiles for S&P 500 GICS sectors including financials, energy, health care, information technology, consumer, industrials, utilities, real estate, materials, and communication services.
- Kept baseline company-event queries for earnings, leadership, regulation, analyst consensus, and S&P Global Market Intelligence research.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase094_sp500_query_templates.py -q` passed as part of the phase_092 through phase_096 targeted run.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py src/backend/tests/test_phase090_us_mega_cap_intent_matrix.py src/backend/tests/test_phase092_sp500_stock_universe.py src/backend/tests/test_phase093_news_cache_processing_store.py src/backend/tests/test_phase094_sp500_query_templates.py src/backend/tests/test_phase095_prediction_artifact_store.py src/backend/tests/test_phase096_ai_capabilities.py -q` passed with 20 tests and one local urllib3 LibreSSL warning.

Next Steps
- The templates are rule-based. Later phases can enrich S&P 500 company metadata from a DB table with exchange, sector aliases, and localized Korean company names.

## phase_095 - Prediction Artifact Store

Phase Goal
- Added deterministic source-document IDs for analysis decisions based on source content and order, enabling safe artifact replay across repeated identical requests.
- Added prediction artifact storage in the local state-store DB boundary, keyed by market, symbol, horizon, analysis mode, `as_of_at`, provider, model, base URL, prompt version, and evidence hash.

Completed Work
- Added deterministic source-document IDs for analysis decisions based on source content and order, enabling safe artifact replay across repeated identical requests.
- Added prediction artifact storage in the local state-store DB boundary, keyed by market, symbol, horizon, analysis mode, `as_of_at`, provider, model, base URL, prompt version, and evidence hash.
- Cached artifacts store summary and structured evidence items only. They do not store raw credentials, hidden system instructions, or full prompt context.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase095_prediction_artifact_store.py -q` passed as part of the phase_092 through phase_096 targeted run.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py src/backend/tests/test_phase090_us_mega_cap_intent_matrix.py src/backend/tests/test_phase092_sp500_stock_universe.py src/backend/tests/test_phase093_news_cache_processing_store.py src/backend/tests/test_phase094_sp500_query_templates.py src/backend/tests/test_phase095_prediction_artifact_store.py src/backend/tests/test_phase096_ai_capabilities.py -q` passed with 20 tests and one local urllib3 LibreSSL warning.

Next Steps
- Artifact reuse is local-state based in this phase. PostgreSQL migration should add a unique index on artifact key and an index on `(symbol, as_of_at, prompt_version, model_provider, model_name)`.

## phase_096 - AI Capability And Prompt Inventory Diagnostics

Phase Goal
- Added an `/ai/capabilities` backend route with a static provider capability matrix for OpenAI, Cerebras, custom OpenAI-compatible providers, and a future local-model slot.
- Added a prompt inventory that records current prompt/artifact version names without returning prompt bodies, API keys, or decrypted credentials.

Completed Work
- Added an `/ai/capabilities` backend route with a static provider capability matrix for OpenAI, Cerebras, custom OpenAI-compatible providers, and a future local-model slot.
- Added a prompt inventory that records current prompt/artifact version names without returning prompt bodies, API keys, or decrypted credentials.
- Registered the route in the FastAPI app and covered it with a secret-leak unit test.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase096_ai_capabilities.py -q` passed as part of the phase_092 through phase_096 targeted run.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend/app src/backend/tests` passed.

Next Steps
- The matrix is intentionally static in this phase. A later frontend/provider diagnostics phase can attach live provider availability checks.

## phase_097 - In-Flight Work Landing And Cache Surface

Phase Goal
- Added `processing_cache` schemas and router endpoints for cache status inspection and single-key KV invalidation.
- Registered the processing-cache router in the FastAPI app alongside the existing AI capability diagnostics route.

Completed Work
- Added `processing_cache` schemas and router endpoints for cache status inspection and single-key KV invalidation.
- Registered the processing-cache router in the FastAPI app alongside the existing AI capability diagnostics route.
- Extended the phase_093 cache test coverage to verify `/processing-cache/status` namespace counts and `/processing-cache/invalidate` removal behavior.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase093_news_cache_processing_store.py -q` failed before implementation because `/processing-cache/status` returned 404.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase093_news_cache_processing_store.py -q` passed with 2 tests.

Next Steps
- Invalidation is intentionally scoped to KV cache entries only. Prediction artifact deletion and broader cache lifecycle policy should be handled in the storage split phase.
- The local state store remains the backing persistence boundary until the planned storage split and later database migration.

## phase_098 - Conversation Formatting Extraction

Phase Goal
- Added `conversations/formatting.py` for model dumping, message creation, language detection, horizon/mode labels, prediction-window copy, and conversation summaries.
- Updated `conversations/service.py` to import those helpers, reducing the first slice of formatting responsibility from the large service file.

Completed Work
- Added `conversations/formatting.py` for model dumping, message creation, language detection, horizon/mode labels, prediction-window copy, and conversation summaries.
- Updated `conversations/service.py` to import those helpers, reducing the first slice of formatting responsibility from the large service file.
- Added direct helper coverage for Korean language detection, horizon labeling, and summary generation.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase098_conversation_formatting.py -q` failed before implementation because `conversations.formatting` did not exist.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase098_conversation_formatting.py -q` passed.

Next Steps
- This is only the first decomposition slice. Intent routing, analysis orchestration, and response assembly remain in `conversations/service.py`.

## phase_099 - Provider Warning Helper

Phase Goal
- Added `app.shared.provider_status` for provider run statuses and warning string construction.
- Replaced duplicate warning string construction in ingestion and news digest flows with the shared helper.

Completed Work
- Added `app.shared.provider_status` for provider run statuses and warning string construction.
- Replaced duplicate warning string construction in ingestion and news digest flows with the shared helper.
- Kept current public warning strings unchanged: `missing_credential:<provider>` and `provider_error:<provider>`.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase099_provider_status.py -q` failed before implementation because `app.shared.provider_status` did not exist.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase099_provider_status.py src/backend/tests/test_phase010_ingestion_adapters.py src/backend/tests/test_phase064_069_news_digest.py -q` passed with 15 tests.

Next Steps
- This phase standardizes warning construction only. Provider fallback orchestration remains feature-local and can be consolidated later.

## phase_100 - Split Local Cache Storage Domains

Phase Goal
- Added sidecar persistence for `kv_cache`, `news_processing_runs`, and `prediction_artifacts` under `state.json.d/`.
- Kept `LocalStateStore.read()`, `write()`, and `update()` APIs unchanged and merged sidecar data transparently on read.

Completed Work
- Added sidecar persistence for `kv_cache`, `news_processing_runs`, and `prediction_artifacts` under `state.json.d/`.
- Kept `LocalStateStore.read()`, `write()`, and `update()` APIs unchanged and merged sidecar data transparently on read.
- Main state JSON now keeps split cache/artifact domains empty after writes, reducing growth pressure on the core settings/conversation file.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_local_state_store.py -q` failed before implementation because cache/artifact values were still stored in the main state file.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_local_state_store.py src/backend/tests/test_phase093_news_cache_processing_store.py src/backend/tests/test_phase095_prediction_artifact_store.py -q` passed with 5 tests and one local urllib3 LibreSSL warning.

Next Steps
- This is a local file split, not a database migration. PostgreSQL or another DB-backed repository remains the target for hosted/team mode.
