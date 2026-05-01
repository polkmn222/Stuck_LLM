# Implement Phase 011-020 Summary

This file is a compact index for agents. Keep the original detailed log as the source of truth.

## phase_011 - Hosted Readiness And Security Hardening

Phase Goal
- Added runtime configuration for explicit CORS origins and optional hosted API-key enforcement.
- Kept local development unauthenticated by default; hosted-style protection is enabled with `STUCK_LLM_REQUIRE_API_KEY=true` and `STUCK_LLM_API_KEY`.

Completed Work
- Added runtime configuration for explicit CORS origins and optional hosted API-key enforcement.
- Kept local development unauthenticated by default; hosted-style protection is enabled with `STUCK_LLM_REQUIRE_API_KEY=true` and `STUCK_LLM_API_KEY`.
- Added request-boundary validation for timezone-aware timestamps, conversation message size, analysis source text size, analysis document count, ingestion symbols, and backtest timestamps.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase011_hosted_readiness.py -q` failed before implementation on CORS, API-key guard, validation, and prompt-field assertions.
- RED: `cd src/frontend && npm test -- App.test.tsx SettingsPanel.test.tsx` failed before implementation on default-market quote selection and settings error display.

Next Steps
- The API-key guard is an interim hosted-mode control, not user login, per-user authorization, or role-based access control.
- Local JSON state remains unsuitable for true multi-user hosted deployment.

## phase_012 - Bilingual Theme UI Refresh

Phase Goal
- Added frontend UI copy dictionaries for English and Korean.
- Added local browser UI preferences for language and theme.

Completed Work
- Added frontend UI copy dictionaries for English and Korean.
- Added local browser UI preferences for language and theme.
- Added segmented controls for language and light/dark theme switching.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `cd src/frontend && npm test -- App.test.tsx ChatShell.test.tsx AnalysisPanel.test.tsx BacktestPanel.test.tsx SettingsPanel.test.tsx` failed before implementation because language and theme controls did not exist.
- GREEN: `cd src/frontend && npm test -- App.test.tsx ChatShell.test.tsx AnalysisPanel.test.tsx BacktestPanel.test.tsx SettingsPanel.test.tsx` passed with 10 tests.

Next Steps
- Backend-generated assistant messages remain in the backend's current English copy; this phase localizes static frontend UI only.
- Python Playwright was not installed and `agent-browser` CLI was unavailable in this environment, so visual browser automation was limited to dev-server asset checks and frontend test coverage.

## phase_014 - Conversation Language And Follow-Up Context

Phase Goal
- Added backend language detection for conversation replies based on the current user message.
- Localized backend-generated missing-stock, missing-horizon, and ready-state assistant messages for Korean and English.

Completed Work
- Added backend language detection for conversation replies based on the current user message.
- Localized backend-generated missing-stock, missing-horizon, and ready-state assistant messages for Korean and English.
- Added follow-up context recovery so a previously mentioned stock can be reused when the next user message only answers or fails to answer the horizon prompt.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase014_conversation_language.py -q` failed before implementation on typo resolution, follow-up stock context, horizon parsing, and Korean response text.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase014_conversation_language.py -q` passed with 4 tests.

Next Steps
- Conversation replies remain deterministic backend messages, not hosted LLM output.
- Stock matching is still seeded-fixture MVP behavior; broader Korean typo/fuzzy matching should be designed before live multi-stock support.

## phase_015 - Typo Confirmation Rule And Runner Auto-Open

Phase Goal
- Reviewed `review-claude/review-claude.md`; the user-facing issues in this slice were runner ergonomics and avoiding placeholder/hardcoded stock behavior.
- Removed hardcoded typo aliases for Samsung Electronics.

Completed Work
- Reviewed `review-claude/review-claude.md`; the user-facing issues in this slice were runner ergonomics and avoiding placeholder/hardcoded stock behavior.
- Removed hardcoded typo aliases for Samsung Electronics.
- Added generic fuzzy stock-candidate detection based on known seeded aliases and edit distance.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py -q` failed before implementation because typos were exact aliases, no confirmation-candidate function existed, typo+horizon recorded analysis, and `run-all.sh` had no auto-open option.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py -q` passed with 9 tests.

Next Steps
- Fuzzy stock confirmation currently works over seeded MVP aliases only; live market metadata should feed the same rule later.
- `review-claude/review-claude.md` also flags broader security and architecture items such as secret rotation, `.env` loading, LLM provider abstraction, and repository interfaces; those remain separate implementation slices.

## phase_016 - Local BYOK Credential Backend And CLI Setup

Phase Goal
- Added project-local `provider-credentials` and `stock-analysis-llm` skills under `.codex/skills`.
- Updated orchestration routing for BYOK credentials, setup flows, and live stock-analysis LLM work.

Completed Work
- Added project-local `provider-credentials` and `stock-analysis-llm` skills under `.codex/skills`.
- Updated orchestration routing for BYOK credentials, setup flows, and live stock-analysis LLM work.
- Added `.env.example` with local state, hosted guard, CORS, and credential encryption key placeholders.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase016_credentials.py src/backend/tests/test_phase011_hosted_readiness.py -q` failed before implementation on missing credential routes, missing setup script, and empty API-key guard behavior.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase016_credentials.py src/backend/tests/test_phase011_hosted_readiness.py -q` passed with 11 tests.

Next Steps
- Local generated credential keys are appropriate for local development only; hosted mode should require `STUCK_LLM_CREDENTIAL_KEY` or a secret manager.
- Credentials are single-user local records for now; login/user ownership remains a future phase.

## phase_017 - Settings Modal And Workspace Navigation

Phase Goal
- Reworked the frontend shell into a ChatGPT-style left rail with Chat, Analysis, Snapshot, and Backtest navigation.
- Kept Chat as the default workspace view and moved analysis defaults, market snapshot, and PnL/backtest into separate workspace pages.

Completed Work
- Reworked the frontend shell into a ChatGPT-style left rail with Chat, Analysis, Snapshot, and Backtest navigation.
- Kept Chat as the default workspace view and moved analysis defaults, market snapshot, and PnL/backtest into separate workspace pages.
- Added a Settings modal with General, Model, and Security categories.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `cd src/frontend && npm test -- App.test.tsx SettingsPanel.test.tsx api.test.ts` failed before implementation because the sidebar navigation, settings modal, and credential API helpers did not exist.
- GREEN: `cd src/frontend && npm test -- App.test.tsx SettingsPanel.test.tsx api.test.ts` passed with 13 tests.

Next Steps
- The frontend can now save/delete local LLM credentials, but live provider calls are still a later phase.
- Credential delete uses browser confirmation for this slice; a custom in-app confirmation dialog can replace it when settings UX expands.

## phase_018 - Live LLM Provider Analysis Integration

Phase Goal
- Added a narrow live LLM provider boundary under `src/backend/app/features/analysis/live_provider.py`.
- Added an OpenAI-compatible HTTP adapter that posts to `/chat/completions` with JSON-schema structured output.

Completed Work
- Added a narrow live LLM provider boundary under `src/backend/app/features/analysis/live_provider.py`.
- Added an OpenAI-compatible HTTP adapter that posts to `/chat/completions` with JSON-schema structured output.
- Kept the existing deterministic `/analysis/requests` path intact for local tests and fallback behavior.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py -q` failed before implementation because the live provider module did not exist.
- RED: `cd src/frontend && npm test -- AnalysisPanel.test.tsx` failed before implementation because setup/provider statuses rendered as the generic recorded state.

Next Steps
- Anthropic credentials are preserved in the credential schema but live Anthropic calls intentionally return an unsupported-provider status in this phase.
- The first live provider path uses seeded offline source collection from the existing ingestion MVP; real source collection policy and rate limits remain future work.

## phase_019 - Live Market Data And Search Ingestion

Phase Goal
- Added `MarketBar` data and extended market quotes with previous close, change percent, and daily chart bars.
- Added a FinanceDataReader-backed market-data path for latest available daily OHLCV data with seeded fixture fallback.

Completed Work
- Added `MarketBar` data and extended market quotes with previous close, change percent, and daily chart bars.
- Added a FinanceDataReader-backed market-data path for latest available daily OHLCV data with seeded fixture fallback.
- Preserved seeded quote behavior for offline/local deterministic tests when FinanceDataReader is absent or unavailable.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase019_live_market_and_news.py -q` failed before implementation on seeded-only market data and unsupported live adapters.
- RED: `cd src/frontend && npm test -- AnalysisPanel.test.tsx ChatShell.test.tsx` failed before implementation because chart rendering did not exist.

Next Steps
- FinanceDataReader is best-effort and may fail under network/provider changes; the app falls back to seeded fixtures rather than blocking chat.
- External news/search adapters are API-backed only. Reddit/X/SNS scraping remains intentionally deferred pending official API and policy review.

## phase_020 - Review-Filtered Security, Concurrency, A11y, And CI Hardening

Phase Goal
- Accepted only the verified Claude-review findings for this phase and left overstated findings out of scope.
- Hardened live LLM prompt context so each eligible source is emitted as escaped JSON inside explicit untrusted-source delimiters.

Completed Work
- Accepted only the verified Claude-review findings for this phase and left overstated findings out of scope.
- Hardened live LLM prompt context so each eligible source is emitted as escaped JSON inside explicit untrusted-source delimiters.
- Added provider base URL validation before OpenAI-compatible endpoint assembly. Non-HTTPS, loopback, private, link-local, metadata, `.local`, `.internal`, and credential-bearing URLs are rejected without calling the HTTP client.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase020_security_and_concurrency.py -q` failed on unsafe provider URLs calling the HTTP client, unescaped source delimiters, and stale concurrent append overwrites.
- RED: `cd src/frontend && npm test -- SettingsModal.test.tsx AnalysisPanel.test.tsx api.test.ts` failed on missing modal backdrop/focus behavior, missing chart data table, and missing request abort timeout.

Next Steps
- Provider base URL validation is intentionally conservative. Local/private custom LLM endpoints are rejected by default; an explicit opt-in policy should be designed if local custom providers need to return.
- Provider URL validation does not resolve public hostnames to detect private DNS answers; hosted deployment should add egress allowlists or network policy.
