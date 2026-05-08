# Implement Phase 141-150 Summary

This file is a compact implementation index for agents. Keep the detailed source log separate when it exists.

## phase_141 - Claude Review Documentation Integrity

Completed Work
- Added phase 138-140 entries to plan/task/implementation range READMEs.
- Added new compact summaries for phases 141-150 and routed the top-level README pointers to the new range.
- Added `EVENTREGISTRY_API_KEY` to `.env.example`.
- Clarified cache-version bump, live market-data test isolation, and local-only env fallback workflow guidance.

Validation
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `git diff --check`: passed.
- `wc -l AGENTS.md docs/plan/README.md docs/task/README.md docs/implement/README.md docs/plan/plan_101_200/README.md docs/task/task_101_200/README.md docs/implement/implement_101_200/README.md docs/plan/plan_101_200/plan_141_150.md docs/task/task_101_200/task_141_150.md docs/implement/implement_101_200/implement_141_150.md docs/agent-workflows/code-authoring.md docs/agent-workflows/code-validation.md docs/agent-workflows/orchestration.md`: completed.

## phase_142 - Market Data Test Isolation

Completed Work
- Added `src/backend/tests/conftest.py` with an autouse fixture that blocks unmocked `FinanceDataReader` reads.
- Verified tests that intentionally monkeypatch `_read_finance_data` can still exercise deterministic live-provider parsing.

Validation
- Focused drift/provider validation passed: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py::test_seeded_market_data_quote_is_available src/backend/tests/test_phase014_conversation_language.py::test_horizon_follow_up_records_previous_stock_context src/backend/tests/test_phase026_generative_chat_orchestration.py src/backend/tests/test_phase077_prediction_probabilities.py::test_prediction_without_horizon_defaults_to_five_trading_day_probabilities src/backend/tests/test_phase080_pnl_chat.py::test_korean_if_bought_date_returns_separate_pnl_simulation src/backend/tests/test_phase019_live_market_and_news.py::test_finance_data_reader_quote_includes_snapshot_and_chart -q`: passed with 10 tests.

## phase_143 - News Provider Robustness Cleanup

Completed Work
- Changed EventRegistry calls to `https://www.eventregistry.org/api/v1/article`.
- Changed Reddit public search to `old.reddit.com`, added rate-limit early stop, and added `partial_provider_error`.
- Replaced the social query suffix with neutral public-post/investor-reaction terms.
- Bumped news provider cache version to `phase_143_news_provider_v2`.

Validation
- RED: focused phase 132/133 tests failed on host, status, rate-limit, and cache-version expectations before implementation.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase132_eventregistry_news_provider.py src/backend/tests/test_phase133_reddit_public_search_provider.py -q`: passed with 9 tests.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend/app/features/news_digest/service.py src/backend/app/features/news_digest/schemas.py src/backend/app/shared/provider_status.py src/backend/tests/test_phase132_eventregistry_news_provider.py src/backend/tests/test_phase133_reddit_public_search_provider.py`: passed.

## phase_144 - News Evidence Timestamp Clamp

Completed Work
- Added `test_phase144_news_evidence_timestamp_clamp.py`.
- Clamped missing-article-date fallback timestamps to quote `as_of_at` and added a safety flag when the clamp occurs.
- Preserved actual future article dates so downstream evidence normalization can exclude them.

Validation
- RED: phase 144 focused test failed because missing article dates fell back to future digest generation time.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase144_news_evidence_timestamp_clamp.py -q`: passed with 2 tests.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend/app/features/conversations/service.py src/backend/tests/test_phase144_news_evidence_timestamp_clamp.py`: passed.

## phase_145 - News Digest Card Privacy Cleanup

Completed Work
- Made the localized headline the single link target for news cards.
- Removed Google favicon URL construction and rendered local domain glyphs instead.
- Added frontend coverage for single-title links and absence of remote favicon URLs.
- Added frontend support for `partial_provider_error` news run status.

Validation
- RED: `cd src/frontend && npm test -- NewsDigestView.test.tsx` failed before the headline-link/favicon cleanup.
- GREEN: `cd src/frontend && npm test -- NewsDigestView.test.tsx`: passed with 2 tests.
- `cd src/frontend && npm run typecheck`: passed.

## phase_146 - Settings Provider Type Cleanup

Completed Work
- Removed stale backend settings `provider` literal and default-state field.
- Removed frontend `Provider`/`AppSettings.provider`, API mapping fields, default settings value, and stale test fixtures.
- Kept LLM provider selection on credential profile types and UI.

Validation
- RED: backend settings focused test failed while `/settings` still returned `provider`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py::test_settings_update_persists_across_app_instances src/backend/tests/test_local_state_store.py::test_local_state_store_persists_state_and_merges_defaults -q`: passed with 2 tests.
- `cd src/frontend && npm test -- api.test.ts SettingsPanel.test.tsx App.test.tsx ChatShell.test.tsx NewsDigestView.test.tsx`: passed with 44 tests.
- `cd src/frontend && npm run typecheck`: passed.

## Validation Through phase_146

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q`: passed with 203 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests`: passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend`: passed.
- `cd src/frontend && npm test`: passed with 62 tests.
- `cd src/frontend && npm run typecheck`: passed.
- `cd src/frontend && npm run build`: passed.
- `cd src/frontend && npm audit --audit-level=high`: passed with 0 vulnerabilities after network approval.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `git diff --check`: passed.

## phase_147 - Crawl URL Safety Boundary

Completed Work
- Added `test_phase147_crawl_url_safety.py` with regressions for DNS-resolved private hosts, malformed ports, unsafe redirect targets, and unsupported response content types.
- Added resolved-host validation to direct crawl URLs before `urlopen`.
- Reused the same validation for final redirect URLs before reading the body.
- Fixed unsupported content-type handling so binary/PDF responses are rejected while missing content type remains explicitly allowed.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase147_crawl_url_safety.py -q` failed with 3 expected failures.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase147_crawl_url_safety.py -q`: passed with 4 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase130_crawl_and_scenario_prediction.py -q`: passed with 2 tests.

## phase_148 - Settings Credential Profile Actions

Completed Work
- Added focused SettingsModal coverage for new LLM profile creation and per-profile external key delete actions.
- Changed LLM key saves from Settings to generate a new profile id for newly entered keys.
- Rendered a delete button for each saved external news/search key.

Validation
- RED: `cd src/frontend && npm test -- SettingsModal.test.tsx` failed on active-profile overwrite and single delete-button rendering.
- GREEN: `cd src/frontend && npm test -- SettingsModal.test.tsx`: passed with 10 tests.

## phase_149 - Analysis External Credential Source Collection

Completed Work
- Added `test_phase149_analysis_external_source_credentials.py` to prove stock-analysis source collection uses the selected Tavily key.
- Added selected external credential map support to ingestion collectors for Tavily, GNews, and SerpApi.
- Passed active external credentials from conversation analysis orchestration into `collect_sources`.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase149_analysis_external_source_credentials.py -q` failed because Tavily source documents were absent.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase149_analysis_external_source_credentials.py -q`: passed with 1 test.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase135_external_provider_credential_selection.py -q`: passed with 2 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase019_live_market_and_news.py::test_ingestion_missing_external_credentials_returns_safe_warnings -q`: passed with 1 test.

## Final Validation Through phase_149

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase147_crawl_url_safety.py src/backend/tests/test_phase130_crawl_and_scenario_prediction.py src/backend/tests/test_phase149_analysis_external_source_credentials.py src/backend/tests/test_phase135_external_provider_credential_selection.py src/backend/tests/test_phase019_live_market_and_news.py::test_ingestion_missing_external_credentials_returns_safe_warnings -q`: passed with 10 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q`: passed with 208 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests`: passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend`: passed.
- `cd src/frontend && npm test -- SettingsModal.test.tsx`: passed with 10 tests.
- `cd src/frontend && npm test`: passed with 64 tests.
- `cd src/frontend && npm run typecheck`: passed.
- `cd src/frontend && npm run build`: passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `git diff --check`: passed.
