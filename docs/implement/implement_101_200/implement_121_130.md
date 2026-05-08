# Implement Phase 121-130 Summary

This file is a compact implementation index for agents. Keep the detailed source log separate when it exists.

## phase_121 - Scoring And PnL Contract Cleanup

Completed Work
- Added `test_phase121_scoring_and_pnl_contracts.py`.
- Added confidence-adjusted downside probability in `scoring/service.py`.
- Updated scoring rationale so downside probability is not presented as a raw sell-probability alias.
- Narrowed `BacktestResponse.evaluation_kind` to `Literal["pnl_simulation"]`.
- Narrowed frontend `evaluationKind` API/type mapping to the same required literal.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase121_scoring_and_pnl_contracts.py -q` failed because downside probability copied sell probability and arbitrary evaluation kinds were accepted.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase121_scoring_and_pnl_contracts.py src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase009_backtest.py src/backend/tests/test_phase110_118_llm_agent_contract.py -q` passed with 15 tests.
- Frontend focused check: `cd src/frontend && npm test -- api.test.ts` passed with 12 tests.

## phase_122 - Analysis And News UI Label Cleanup

Completed Work
- Added localized `dateLocale`, `confidenceFactorLabels`, and `operationalStateAria` copy.
- Formatted news article publication dates with `Intl.DateTimeFormat`.
- Replaced raw confidence factor keys with localized labels.
- Localized the analysis provider-state aria-label.
- Added provider-run index to React keys so repeated provider/query pairs do not collide.

Validation
- RED: `cd src/frontend && npm test -- NewsDigestView.test.tsx AnalysisPanel.test.tsx` failed on raw ISO dates, raw confidence factor keys, and hardcoded provider-state aria-label.
- GREEN: `cd src/frontend && npm test -- NewsDigestView.test.tsx AnalysisPanel.test.tsx` passed with 6 tests.

Final Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q`: passed with 178 tests and one existing urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests`: passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend`: passed.
- `cd src/frontend && npm test`: passed with 53 tests.
- `cd src/frontend && npm run typecheck`: passed.
- `cd src/frontend && npm run build`: passed.
- `cd src/frontend && npm audit --audit-level=high`: passed with 0 vulnerabilities.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `wc -l AGENTS.md docs/**/*.md`: completed.
- `git diff --check`: passed.

## phase_123 - Chat Help And Malformed Provider Fallback

Completed Work
- Added a local `/help` command in the conversation service with Korean and English guide copy.
- Added malformed-output recovery in live analysis so provider schema/source-id failures fall back to local eligible evidence and still expose `provider_error_code=malformed_output`.
- Extended the frontend request timeout from 30 seconds to 120 seconds for slow provider/news requests.
- Replaced the generic chat failure copy so users do not see a misleading local-save error for request failures.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py::test_help_command_returns_korean_capability_guide_without_provider_call src/backend/tests/test_phase018_live_llm_provider.py::test_chat_ready_request_falls_back_when_provider_returns_malformed_output src/backend/tests/test_phase034_prompt_grounding_contract.py::test_live_analysis_rejects_excluded_or_prompt_budget_source_output -q` failed before implementation.
- RED: `cd src/frontend && npm test -- ChatShell.test.tsx api.test.ts` failed before implementation on the old 30-second timeout and local-save failure copy.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py::test_help_command_returns_korean_capability_guide_without_provider_call src/backend/tests/test_phase018_live_llm_provider.py::test_chat_ready_request_falls_back_when_provider_returns_malformed_output src/backend/tests/test_phase034_prompt_grounding_contract.py::test_live_analysis_rejects_excluded_or_prompt_budget_source_output -q` passed with 3 tests and one existing urllib3 LibreSSL warning.
- GREEN: `cd src/frontend && npm test -- ChatShell.test.tsx api.test.ts` passed with 24 tests.
- Focused regression: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase034_prompt_grounding_contract.py src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase090_us_mega_cap_intent_matrix.py -q` passed with 28 tests and one existing urllib3 LibreSSL warning.
- Focused frontend regression: `cd src/frontend && npm test -- ChatShell.test.tsx api.test.ts NewsDigestView.test.tsx AnalysisPanel.test.tsx` passed with 30 tests.

Final Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q`: passed with 179 tests and one existing urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests`: passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend`: passed.
- `cd src/frontend && npm test`: passed with 54 tests.
- `cd src/frontend && npm run typecheck`: passed.
- `cd src/frontend && npm run build`: passed.
- `cd src/frontend && npm audit --audit-level=high`: passed with 0 vulnerabilities.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `wc -l AGENTS.md docs/**/*.md`: completed.
- `git diff --check`: passed.

## phase_124 - Help Command Credential-Free Regression

Completed Work
- Added `test_help_command_does_not_require_saved_credentials`.
- Proved `/도움말` is handled locally before provider intent, chat completion, or analysis calls.

Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py::test_help_command_does_not_require_saved_credentials -q`: passed.

## phase_125 - Chat News Query Fanout Cap

Completed Work
- Added `test_chat_news_digest_caps_provider_query_fanout_for_responsiveness`.
- Added optional `query_limit` support to `create_news_digest`.
- Capped chat-triggered news digest query templates at two, limiting the default four-provider chat path to at most eight provider runs.
- Kept direct `create_news_digest` behavior uncapped by default.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_chat_news_digest_caps_provider_query_fanout_for_responsiveness -q` failed with 36 provider runs.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_chat_news_digest_caps_provider_query_fanout_for_responsiveness -q` passed.
- Regression: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_news_digest_collects_providers_dedupes_and_tracks_transparency -q` passed.

Final Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase034_prompt_grounding_contract.py -q`: passed with 29 tests and one existing urllib3 LibreSSL warning.
- `cd src/frontend && npm test -- ChatShell.test.tsx api.test.ts NewsDigestView.test.tsx`: passed with 25 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q`: passed with 181 tests and one existing urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests`: passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend`: passed.
- `cd src/frontend && npm test`: passed with 54 tests.
- `cd src/frontend && npm run typecheck`: passed.
- `cd src/frontend && npm run build`: passed.
- `cd src/frontend && npm audit --audit-level=high`: passed with 0 vulnerabilities.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `wc -l AGENTS.md docs/**/*.md`: completed.
- `git diff --check`: passed.

## phase_126 - LLM Runtime Execution Documentation

Completed Work
- Added `docs/product/llm-runtime-execution.md` with execution boundaries for intent routing, news digest, prediction, chart/graph data, caches, artifacts, and validation.
- Documented that `docs/product/llm-agent-phase-roadmap.md` is retired and should be replaced by compact phase summaries for phase history.
- Updated `README.md`, `docs/product/README.md`, `docs/product/llm-agent-spec.md`, and workflow docs to route agents to the runtime execution document.
- Updated compact phase indexes and latest-range pointers for `phase_126`.

Validation
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `rg -n "llm-agent-phase-roadmap.md" README.md docs/agent-workflows`: passed with no active roadmap references.
- `test ! -e docs/product/llm-agent-phase-roadmap.md`: passed.
- `wc -l README.md docs/product/README.md docs/product/llm-agent-spec.md docs/product/llm-runtime-execution.md docs/agent-workflows/code-authoring.md docs/agent-workflows/orchestration.md docs/plan/README.md docs/task/README.md docs/implement/README.md docs/plan/plan_101_200/README.md docs/task/task_101_200/README.md docs/implement/implement_101_200/README.md docs/plan/plan_101_200/plan_121_130.md docs/task/task_101_200/task_121_130.md docs/implement/implement_101_200/implement_121_130.md`: completed.
- `git diff --check`: passed.

## phase_127 - Analysis And News Output Trust Cleanup

Completed Work
- Added `rule_based_fallback` to `ScoreCommand` and capped rule-based fallback confidence at `0.5`.
- Added `llm_unavailable` confidence-factor handling and localized frontend labels.
- Passed malformed-output fallback state from conversation analysis scoring to the scoring service.
- Suppressed duplicate fallback evidence summary text and assembled live analysis messages as paragraph-separated content.
- Stopped seeding `NewsArticle.summary_ko` from raw snippets, leaving untranslated snippets out of Korean summaries unless an LLM fills the localized field.
- Removed duplicate news key-point rendering, aggregated provider runs by provider, and kept Korean article cards from falling back to English snippets.
- Localized analysis provider error codes and preserved message paragraph breaks in chat rendering.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase008_scoring.py::test_rule_based_fallback_scoring_caps_confidence_and_flags_llm_unavailable src/backend/tests/test_phase018_live_llm_provider.py::test_chat_ready_request_falls_back_when_provider_returns_malformed_output src/backend/tests/test_phase064_069_news_digest.py::test_news_article_does_not_seed_korean_summary_with_english_snippet -q` failed on uncapped fallback confidence, duplicate fallback evidence text, and snippet-backed `summary_ko`.
- RED: `cd src/frontend && npm test -- NewsDigestView.test.tsx AnalysisPanel.test.tsx` failed on duplicate headline rendering, unaggregated provider chips, raw `llm_unavailable`, raw `malformed_output`, and Korean snippet fallback.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase008_scoring.py::test_rule_based_fallback_scoring_caps_confidence_and_flags_llm_unavailable src/backend/tests/test_phase018_live_llm_provider.py::test_chat_ready_request_falls_back_when_provider_returns_malformed_output src/backend/tests/test_phase064_069_news_digest.py::test_news_article_does_not_seed_korean_summary_with_english_snippet -q` passed with 3 tests and one existing urllib3 LibreSSL warning.
- GREEN: `cd src/frontend && npm test -- NewsDigestView.test.tsx AnalysisPanel.test.tsx` passed with 8 tests.
- Focused regression: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase110_118_llm_agent_contract.py src/backend/tests/e2e/test_phase118_validation_matrix.py -q` passed with 33 tests and one existing urllib3 LibreSSL warning.
- Focused frontend regression: `cd src/frontend && npm test -- ChatShell.test.tsx api.test.ts NewsDigestView.test.tsx AnalysisPanel.test.tsx` passed with 32 tests after updating the ChatShell expectation for single news-card rendering.

Final Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q`: passed with 183 tests and one existing urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests`: passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend`: passed.
- `cd src/frontend && npm test`: passed with 56 tests.
- `cd src/frontend && npm run typecheck`: passed.
- `cd src/frontend && npm run build`: passed.
- `cd src/frontend && npm audit --audit-level=high`: passed with 0 vulnerabilities.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `wc -l AGENTS.md docs/**/*.md`: completed.
- `git diff --check`: passed.

## phase_128 - Malformed Output Provider Error Boundary

Completed Work
- Removed the `malformed_output` branch that converted included documents into local fallback evidence with `status="completed"`.
- Changed malformed provider output to return `status="provider_error"` with `provider_error_code="malformed_output"` and no `score_result`.
- Removed `rule_based_fallback` from `ScoreCommand` and removed `llm_unavailable` confidence-factor handling.
- Updated Korean and English malformed-output labels to avoid rule-based fallback wording.
- Updated product runtime docs to prohibit local prediction synthesis after malformed provider output.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py::test_chat_ready_request_maps_malformed_output_to_provider_error_without_fallback src/backend/tests/test_phase034_prompt_grounding_contract.py::test_live_analysis_rejects_excluded_or_prompt_budget_source_output -q` failed because malformed output still returned completed fallback analysis.
- RED: `cd src/frontend && npm test -- AnalysisPanel.test.tsx` failed because the malformed-output label still said rule-based fallback.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py::test_chat_ready_request_maps_malformed_output_to_provider_error_without_fallback src/backend/tests/test_phase034_prompt_grounding_contract.py::test_live_analysis_rejects_excluded_or_prompt_budget_source_output src/backend/tests/test_phase008_scoring.py -q` passed with 5 tests and one existing urllib3 LibreSSL warning.
- GREEN: `cd src/frontend && npm test -- AnalysisPanel.test.tsx` passed with 6 tests.
- Focused regression: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase034_prompt_grounding_contract.py src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase110_118_llm_agent_contract.py src/backend/tests/e2e/test_phase118_validation_matrix.py -q` passed with 24 tests and one existing urllib3 LibreSSL warning.
- Focused frontend regression: `cd src/frontend && npm test -- AnalysisPanel.test.tsx ChatShell.test.tsx api.test.ts` passed with 30 tests.

Final Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q`: passed with 182 tests and one existing urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests`: passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend`: passed.
- `cd src/frontend && npm test`: passed with 56 tests.
- `cd src/frontend && npm run typecheck`: passed.
- `cd src/frontend && npm run build`: passed.
- `cd src/frontend && npm audit --audit-level=high`: passed with 0 vulnerabilities.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `wc -l AGENTS.md docs/**/*.md`: completed.
- `git diff --check`: passed.

## phase_129 - Multi Credential Selection Boundary

Completed Work
- Added profile-aware LLM credential schemas, service functions, and `/credentials/llm/profiles` endpoints while preserving the existing `/credentials/llm` active-status path.
- Added `active_llm_credential_id` to local state and made active-profile fallback backward-compatible with the existing `default` credential record.
- Added `llm_credential_id` to conversation commands and threaded it through chat intent, generic chat completion, news digest LLM summaries, and live analysis.
- Added Settings modal saved-key selection and a chat-header LLM key selector.
- Updated frontend API/type mapping for credential profile lists and active selection.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase129_multi_provider_credentials.py -q` failed on missing profile endpoints.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase129_multi_provider_credentials.py -q` passed with 2 tests and one existing urllib3 LibreSSL warning.
- RED: `cd src/frontend && npm test -- api.test.ts ChatShell.test.tsx` failed on missing profile API mapping and missing chat key selector.
- GREEN: `cd src/frontend && npm test -- api.test.ts ChatShell.test.tsx SettingsModal.test.tsx App.test.tsx` passed with 45 tests.
- Focused regression: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase129_multi_provider_credentials.py src/backend/tests/test_phase016_credentials.py src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase026_generative_chat_orchestration.py -q` passed with 21 tests and one existing urllib3 LibreSSL warning.
- Frontend typecheck: `cd src/frontend && npm run typecheck` passed.

## phase_130 - Crawl-Backed News And Scenario Prediction

Completed Work
- Added `web_crawl` and `reddit_crawl` news provider run types.
- Added direct URL extraction, safety checks for unsupported schemes, credentialed URLs, localhost/private literal IPs, redirect targets, response type, and response-size limits.
- Added direct article extraction from crawlable HTML titles, publication metadata, and article text.
- Added Reddit search URL conversion to Reddit search JSON and normalized result articles.
- Added crawled/news digest article conversion into live prediction source documents.
- Changed routing so prediction terms win over incidental URL path terms like `/article/`.
- Added Korean and English scenario-style prediction copy while keeping probability, expected-range, downside, baseline, and confidence details.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase130_crawl_and_scenario_prediction.py -q` failed before crawl/news-to-prediction implementation.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase130_crawl_and_scenario_prediction.py -q` passed with 2 tests and one existing urllib3 LibreSSL warning.
- Focused regression: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase130_crawl_and_scenario_prediction.py src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py src/backend/tests/test_phase090_us_mega_cap_intent_matrix.py -q` passed with 17 tests and one existing urllib3 LibreSSL warning.
- Backend lint: `PYTHONPATH=src/backend python3 -m ruff check src/backend` passed.
- Frontend typecheck: `cd src/frontend && npm run typecheck` passed.
