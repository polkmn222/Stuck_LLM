# Implementation Log

Newest phases go first. Record concrete implementation notes, commands, validation, and unresolved risks for each phase.

## phase_018 - Live LLM Provider Analysis Integration Handoff

Status: planned, not implemented in this handoff.

Next agent brief:

- Start from the completed phase_016 credential backend and phase_017 settings UI.
- Use `stock-analysis-llm`, `llm-application-dev`, `provider-credentials`, `security-auditor`, `test-driven-development`, and `lint-and-validate`.
- Implement the first production-oriented live LLM path without removing deterministic local tests/fallbacks.
- Prefer a narrow provider interface before vendor-specific implementation.
- OpenAI-compatible provider support should be first; preserve Anthropic/custom boundaries already represented by the credential schema.
- If no credential is configured, return a setup-needed assistant message in Korean or English rather than falling back silently to fake analysis.
- Decrypt and pass raw API keys only inside the provider-call edge; never log, serialize, or return raw keys.
- Keep strict `as_of_at` filtering: include `published_at == as_of_at`, exclude anything after it, and never include PnL/backtest data in the prompt.
- Treat source documents as untrusted evidence and validate structured output before scoring handoff.

Suggested validation targets for phase_018:

- RED first: missing credentials, mocked provider success, provider auth/rate-limit/timeout failure, malformed structured output, Korean/English setup text, and cutoff equality.
- Backend: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py -q`.
- Backend full: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q`.
- Frontend affected tests: `cd src/frontend && npm test -- ChatShell.test.tsx App.test.tsx`.
- Frontend full: `cd src/frontend && npm test && npm run typecheck && npm run build`.
- Secret check: grep/log review should confirm no raw test API key appears in state files, responses, snapshots, or logs.

## phase_017 - Settings Modal And Workspace Navigation

Implementation notes:

- Reworked the frontend shell into a ChatGPT-style left rail with Chat, Analysis, Snapshot, and Backtest navigation.
- Kept Chat as the default workspace view and moved analysis defaults, market snapshot, and PnL/backtest into separate workspace pages.
- Added a Settings modal with General, Model, and Security categories.
- Moved language and theme controls into General settings.
- Added a Model settings form for local BYOK provider, model, optional base URL, and API key entry.
- Connected the frontend to `GET`, `PUT`, and `DELETE /credentials/llm` through typed API helpers.
- Kept raw API keys write-only from the frontend perspective; status rendering uses masked key metadata only.
- Added Security settings that show local credential storage state, masked key, and key-source metadata.
- Updated analysis settings so provider routing is no longer mixed with analysis mode, market, and horizon defaults.
- Adjusted UI copy for English and Korean labels in the new navigation and modal flow.

Validation:

- RED: `cd src/frontend && npm test -- App.test.tsx SettingsPanel.test.tsx api.test.ts` failed before implementation because the sidebar navigation, settings modal, and credential API helpers did not exist.
- GREEN: `cd src/frontend && npm test -- App.test.tsx SettingsPanel.test.tsx api.test.ts` passed with 13 tests.
- `cd src/frontend && npm test` passed with 17 tests across 6 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 40 tests.
- `cd src/frontend && npm audit --audit-level=high` passed after rerun with network access; the initial sandboxed run could not resolve `registry.npmjs.org`.
- `BACKEND_PORT=8012 FRONTEND_PORT=5176 AUTO_OPEN_BROWSER=0 ./run-all.sh` started backend `http://127.0.0.1:8012` and frontend `http://127.0.0.1:5176`.
- Verified backend health, frontend-proxied health, frontend HTML, and credential status responses with `curl`.
- Stopped the validation servers after smoke testing.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/frontend/src` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 1648 total lines.

Risks and follow-ups:

- The frontend can now save/delete local LLM credentials, but live provider calls are still a later phase.
- Credential delete uses browser confirmation for this slice; a custom in-app confirmation dialog can replace it when settings UX expands.
- The view state is local React state for now; URL-deep-linked workspace tabs can be added later if team usage requires shareable state.

## phase_016 - Local BYOK Credential Backend And CLI Setup

Implementation notes:

- Added project-local `provider-credentials` and `stock-analysis-llm` skills under `.codex/skills`.
- Updated orchestration routing for BYOK credentials, setup flows, and live stock-analysis LLM work.
- Added `.env.example` with local state, hosted guard, CORS, and credential encryption key placeholders.
- Added a backend `credentials` feature slice with `GET`, `PUT`, and `DELETE /credentials/llm`.
- Added OpenAI, Anthropic, and OpenAI-compatible custom provider config support.
- Added encrypted at-rest API-key storage using `cryptography` Fernet.
- Added `STUCK_LLM_CREDENTIAL_KEY` support with generated local development key fallback at the state-file directory.
- Added redacted credential responses that include provider metadata, masked key text, and key source only.
- Added `scripts/setup_credentials.py` for interactive or non-interactive developer BYOK setup.
- Normalized empty `STUCK_LLM_API_KEY` to unauthenticated so hosted guard cannot be bypassed with an empty key.
- Added `cryptography>=42.0.0` as a backend dependency.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase016_credentials.py src/backend/tests/test_phase011_hosted_readiness.py -q` failed before implementation on missing credential routes, missing setup script, and empty API-key guard behavior.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase016_credentials.py src/backend/tests/test_phase011_hosted_readiness.py -q` passed with 11 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 40 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests scripts/setup_credentials.py` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend scripts/setup_credentials.py` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app scripts/setup_credentials.py` passed.

Risks and follow-ups:

- Local generated credential keys are appropriate for local development only; hosted mode should require `STUCK_LLM_CREDENTIAL_KEY` or a secret manager.
- Credentials are single-user local records for now; login/user ownership remains a future phase.
- Live provider calls are intentionally deferred to the next LLM phase.

## phase_015 - Typo Confirmation Rule And Runner Auto-Open

Implementation notes:

- Reviewed `review-claude/review-claude.md`; the user-facing issues in this slice were runner ergonomics and avoiding placeholder/hardcoded stock behavior.
- Removed hardcoded typo aliases for Samsung Electronics.
- Added generic fuzzy stock-candidate detection based on known seeded aliases and edit distance.
- Added a `stock_confirmation` missing-input state so likely typos ask for explicit user confirmation before analysis is recorded.
- Added affirmative follow-up handling for confirmed typo candidates, including Korean `네` and English `yes`.
- Guarded against non-affirmative Korean text such as `네이버` accidentally confirming a prior typo candidate.
- Kept exact stock names on the existing direct flow.
- Updated `run-all.sh` to open the frontend URL automatically by default after startup, with `AUTO_OPEN_BROWSER=0` available for automation and validation.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py -q` failed before implementation because typos were exact aliases, no confirmation-candidate function existed, typo+horizon recorded analysis, and `run-all.sh` had no auto-open option.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py -q` passed with 9 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 34 tests.
- `bash -n run-all.sh` passed.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `AUTO_OPEN_BROWSER=0 ./run-all.sh` started backend `http://127.0.0.1:8010` and frontend `http://127.0.0.1:5174`.
- Verified backend health, frontend-proxied health, and frontend HTML responses with `curl`.
- Stopped the smoke-test servers after validation.

Risks and follow-ups:

- Fuzzy stock confirmation currently works over seeded MVP aliases only; live market metadata should feed the same rule later.
- `review-claude/review-claude.md` also flags broader security and architecture items such as secret rotation, `.env` loading, LLM provider abstraction, and repository interfaces; those remain separate implementation slices.

## phase_014 - Conversation Language And Follow-Up Context

Implementation notes:

- Added backend language detection for conversation replies based on the current user message.
- Localized backend-generated missing-stock, missing-horizon, and ready-state assistant messages for Korean and English.
- Added follow-up context recovery so a previously mentioned stock can be reused when the next user message only answers or fails to answer the horizon prompt.
- Added lightweight horizon parsing for English and Korean text such as `swing`, `장중`, `스윙`, and `장기`.
- Initially added seeded Samsung Electronics aliases for common Korean typo inputs; phase_015 later replaced this with an explicit confirmation rule.
- Kept the ready-state response explicit that hosted LLM analysis is still not connected.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase014_conversation_language.py -q` failed before implementation on typo resolution, follow-up stock context, horizon parsing, and Korean response text.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase014_conversation_language.py -q` passed with 4 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase014_conversation_language.py -q` passed with 9 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 29 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.

Risks and follow-ups:

- Conversation replies remain deterministic backend messages, not hosted LLM output.
- Stock matching is still seeded-fixture MVP behavior; broader Korean typo/fuzzy matching should be designed before live multi-stock support.

## phase_012 - Bilingual Theme UI Refresh

Implementation notes:

- Added frontend UI copy dictionaries for English and Korean.
- Added local browser UI preferences for language and theme.
- Added segmented controls for language and light/dark theme switching.
- Reworked the layout into a ChatGPT-like left sidebar with central conversation workspace and bottom composer.
- Updated chat, settings, analysis snapshot, and backtest panels to consume localized copy.
- Replaced the old beige dashboard styling with dark and light CSS variable themes.

Validation:

- RED: `cd src/frontend && npm test -- App.test.tsx ChatShell.test.tsx AnalysisPanel.test.tsx BacktestPanel.test.tsx SettingsPanel.test.tsx` failed before implementation because language and theme controls did not exist.
- GREEN: `cd src/frontend && npm test -- App.test.tsx ChatShell.test.tsx AnalysisPanel.test.tsx BacktestPanel.test.tsx SettingsPanel.test.tsx` passed with 10 tests.
- `cd src/frontend && npm test` passed with 13 tests across 6 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 25 tests.
- `cd src/frontend && npm audit --audit-level=high` passed after rerun with network access; the initial sandboxed run could not resolve `registry.npmjs.org`.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/frontend/src backups/phase_012/manifest.md` returned no matches.
- `git diff --check` passed.
- Dev server assets were reachable from `http://127.0.0.1:5174/`.

Risks and follow-ups:

- Backend-generated assistant messages remain in the backend's current English copy; this phase localizes static frontend UI only.
- Python Playwright was not installed and `agent-browser` CLI was unavailable in this environment, so visual browser automation was limited to dev-server asset checks and frontend test coverage.

## phase_011 - Hosted Readiness And Security Hardening

Implementation notes:

- Added runtime configuration for explicit CORS origins and optional hosted API-key enforcement.
- Kept local development unauthenticated by default; hosted-style protection is enabled with `STUCK_LLM_REQUIRE_API_KEY=true` and `STUCK_LLM_API_KEY`.
- Added request-boundary validation for timezone-aware timestamps, conversation message size, analysis source text size, analysis document count, ingestion symbols, and backtest timestamps.
- Split public `AnalysisResponse` from stored analysis records so `system_instructions` and `prompt_context` stay server-side.
- Updated the frontend to load the initial quote from the persisted default market instead of always using Samsung Electronics.
- Added visible settings-save failure feedback in the settings panel.
- Aligned the Vite config port with the root runner default.
- Added `mypy` to backend dev dependencies because validation docs require it.
- Shortened project-local `.codex/skills` and `.agents/skills` descriptions to prevent Codex skills context budget truncation warnings.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase011_hosted_readiness.py -q` failed before implementation on CORS, API-key guard, validation, and prompt-field assertions.
- RED: `cd src/frontend && npm test -- App.test.tsx SettingsPanel.test.tsx` failed before implementation on default-market quote selection and settings error display.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase011_hosted_readiness.py src/backend/tests/test_phase007_analysis_pipeline.py -q` passed with 8 tests.
- GREEN: `cd src/frontend && npm test -- App.test.tsx SettingsPanel.test.tsx` passed with 4 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 25 tests.
- `cd src/frontend && npm test` passed with 11 tests across 6 files.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed after rerun with network access; the initial sandboxed run could not resolve `registry.npmjs.org`.
- `bash -n run-all.sh` passed.
- `./run-all.sh` started backend `http://127.0.0.1:8010` and frontend `http://127.0.0.1:5174`.
- Verified backend health, frontend-proxied health, and frontend HTML responses with `curl`.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src` returned no matches.
- `git diff --check` and `git diff --cached --check` passed.

Risks and follow-ups:

- The API-key guard is an interim hosted-mode control, not user login, per-user authorization, or role-based access control.
- Local JSON state remains unsuitable for true multi-user hosted deployment.
- Full deployment, database, rate limiting, and real identity provider selection move to `phase_012`.

## phase_010 - Global Source Adapter MVP

Implementation notes:

- Added the backend `ingestion` feature slice.
- Added `POST /ingestion/collect` for global source collection.
- Added seed-backed offline adapters for Reddit, US news, polling/sentiment, and global macro sources.
- Added adapter registry behavior through typed `source_adapters` request validation.
- Returned analysis-compatible source documents with source metadata, timestamps, URLs, adapter names, relevance scores, and safety flags.
- Preserved post-`as_of_at` documents as collected source material, leaving inclusion/exclusion to the analysis layer.
- Extended local JSON state with `source_collections`.
- Kept live network fetch, arbitrary URL fetch, crawler execution, credentials, and paid external calls out of this phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase010_ingestion_adapters.py -q` failed with 404 before the ingestion route existed.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase010_ingestion_adapters.py -q` passed with 4 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 20 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.

Risks and follow-ups:

- Source adapters are seeded offline fixtures only; no live Reddit, news, polling, or macro API is connected.
- Legal, rate-limit, credential, and robots/source policy review remains required before replacing seeded adapters with live collectors.
- The server was not started for final smoke testing per user preference; run `./run-all.sh` manually when interactive verification is needed.

## phase_009 - Backtest And PnL Graph Service

Implementation notes:

- Added the backend `backtest` feature slice.
- Added `POST /backtests/simulations` for seeded PnL simulations.
- Added seeded Samsung Electronics and Apple price-bar paths for local simulation.
- Calculated entry price, exit price, gross return, gross PnL, max drawdown, and equity curve.
- Stored backtest results under a separate local `backtests` state area.
- Added a frontend `BacktestPanel` with a compact SVG equity curve.
- Added frontend API mapping for backtest request/response shapes.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase009_backtest.py -q` failed with 404 before the backtest route existed.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase009_backtest.py -q` passed with 3 tests.
- RED: `npm test` failed before frontend implementation because `BacktestPanel` and `runBacktest` did not exist.
- GREEN: `npm test` passed with 8 frontend tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 16 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `npm run typecheck` passed.
- `npm run build` passed.
- `npm audit --audit-level=high` reported 0 vulnerabilities.
- `bash -n run-all.sh` passed.
- `./run-all.sh` started backend `http://127.0.0.1:8010` and frontend `http://127.0.0.1:5174`.
- Verified backend health, frontend-proxied health, analysis, scoring, backtest, and frontend HTML responses with `curl`.

Risks and follow-ups:

- Backtests use seeded local fixtures only; no live market data provider is connected.
- The simulation is gross PnL only and does not include transaction costs, tax, slippage, dividends, or FX.
- PnL data is deliberately separate from historical analysis evidence and must not feed `as_of_at` analysis prompts.

## phase_008 - Scoring Probabilities And Confidence

Implementation notes:

- Added the backend `scoring` feature slice.
- Added `POST /scoring/evaluate` to convert evidence stance weights into buy, hold, and sell probabilities.
- Added score drivers so each probability impact links back to a source document.
- Added confidence scoring based on evidence count, total eligible evidence weight, and excluded-source penalty.
- Added `needs_evidence` behavior for empty evidence so the API does not fabricate probabilities.
- Extended local JSON state with `scores`.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase008_scoring.py -q` failed with 404 before the scoring route existed.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase008_scoring.py -q` passed with 3 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 13 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.

Risks and follow-ups:

- The probability model is a deterministic MVP heuristic, not a calibrated financial model.
- Confidence is a source-quality proxy based on local inputs only; it is not a statistical forecast confidence interval.
- Later phases should evaluate scoring calibration against historical outcomes and richer source quality metadata.

## phase_007 - Historical Analysis Pipeline

Implementation notes:

- Added the backend `analysis` feature slice.
- Added `POST /analysis/requests` for source-grounded local analysis requests.
- Enforced `as_of_at` filtering before prompt context or summaries are built.
- Added source-document inclusion/exclusion decisions and evidence items.
- Added a local deterministic analysis provider that classifies evidence stance without calling an external LLM.
- Added prompt-boundary text that treats source documents as untrusted evidence and keeps source instructions out of system instructions.
- Extended local JSON state with `analysis_requests`.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase007_analysis_pipeline.py -q` failed with 404 before the analysis route existed.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase007_analysis_pipeline.py -q` passed with 3 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 10 tests.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.

Risks and follow-ups:

- This phase does not call a hosted LLM provider; it creates a deterministic local pipeline for cutoff, prompt-boundary, and evidence-linking behavior.
- Source ingestion remains manual/user-supplied for now.
- Buy, hold, and sell probabilities remain a `phase_008` responsibility.

## phase_006 - Chat Settings And Market Data MVP

Implementation notes:

- Added a file-backed local JSON state store for settings and conversations.
- Added backend feature slices for settings, conversations, and seeded market-data quotes.
- Added shared backend store dependency wiring through FastAPI app state.
- Added settings persistence through `GET /settings` and `PATCH /settings`.
- Added conversation creation, append, and fetch endpoints.
- Added a seeded quote endpoint for Samsung Electronics and Apple MVP fixtures.
- Connected the React shell to `/api/*` through a shared frontend API mapper.
- Replaced static probability values with a market snapshot and pending probability state.
- Added unit tests for backend settings, conversations, market data, local state storage, frontend chat, settings, analysis panel, and API mapping.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py -q` failed before implementation because `create_app` did not accept `state_path`.
- RED: `npm test` failed before frontend implementation because the new chat/settings/analysis component contracts did not exist yet.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py -q` passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 7 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `npm test` passed with 6 frontend tests.
- `npm run typecheck` passed.
- `npm run build` passed.
- `npm audit --audit-level=high` reported 0 vulnerabilities.
- `bash -n run-all.sh` passed.
- `./run-all.sh` started backend `http://127.0.0.1:8010` and frontend `http://127.0.0.1:5174`.
- Verified backend health, frontend-proxied health, settings, seeded market quote, and missing-horizon conversation responses with `curl`.

Risks and follow-ups:

- Local state is a development JSON file at `.local/stuck_llm_state.json` unless `STUCK_LLM_STATE_PATH` is set; it is not a concurrent multi-user database.
- Market data is seeded fixture data only and is not live market data.
- Conversation responses do not call an LLM yet; buy/hold/sell probabilities intentionally remain pending until later scoring and analysis phases.
- Source ingestion, strict `as_of_at` filtering, and persistent database migrations remain future phase work.

## phase_005 - Unified Runner And Atomic Test Policy

Implementation notes:

- Started a phase for root-level unified dev execution and mandatory unit-test policy.
- Added `run-all.sh` to start backend and frontend together from the repository root.
- Added Vite proxy support so `/api/*` on the frontend dev server routes to the backend.
- Added frontend unit test infrastructure with Vitest, jsdom, and Testing Library.
- Added a colocated unit test for `src/frontend/src/features/chat/ChatShell.tsx`.
- Added `src/README.md` for backend/frontend feature folder conventions.
- Updated docs and `AGENTS.md` to make feature folders and unit tests mandatory.
- Initialized a local git repository so `review-claude` can review diffs.

Validation:

- `npm install` completed in `src/frontend` and reported 0 vulnerabilities.
- `npm test` passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed.
- `npm run typecheck` passed.
- `npm run build` passed.
- `npm audit --audit-level=high` reported 0 vulnerabilities.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `bash -n run-all.sh` passed.
- `./run-all.sh` was verified with backend `http://127.0.0.1:8010/health`, frontend `http://127.0.0.1:5174/`, and proxied API `http://127.0.0.1:5174/api/health`.
- `git diff --check 4b825dc642cb6eb9a060e54bf8d69288fbee4904` passed after local git initialization.
- `review-claude` was submitted as background job `claude-20260425-173217-Stuck_LLM-45795`.

Risks and follow-ups:

- The root runner starts two local processes and should clean both up on interrupt.
- The current dev server is intended for local development only.
- `review-claude` requires git; this repository was initialized locally during the phase.
- Claude review results have not been collected yet; run the recorded collect command when ready.

## phase_004 - Source Scaffold And Foundation Slice

Implementation notes:

- Started the first code phase with `src/backend` and `src/frontend` as the application roots.
- Added the backend `health` feature with a test-first workflow.
- Added a Vite, React, and TypeScript frontend shell with `chat`, `settings`, and `analysis` feature folders.
- Updated validation docs from the earlier `apps/` assumption to the `src/` layout.
- Updated the plan to make `src/backend` and `src/frontend` the implementation roots.
- Added generated-artifact ignore rules to `.gitignore`.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_health.py -q` failed before implementation with `ModuleNotFoundError: No module named 'app'`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_health.py -q` passed after implementation.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `cd src/frontend && npm install` completed and reported 0 vulnerabilities.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` reported 0 vulnerabilities.
- Ruff and MyPy were installed into `/tmp/stuck_llm_backend_dev` for validation without changing project runtime files.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- Final validation rerun passed for backend tests, compileall, Ruff, MyPy, frontend typecheck, frontend build, frontend audit, and placeholder search.
- `backups/phase_004/manifest.md` records source/documentation backups and intentionally excluded generated artifacts.

Risks and follow-ups:

- No database, conversation persistence, LLM provider integration, or backend/frontend API connection exists yet.
- Frontend build output and caches are generated artifacts and should not be treated as source.

## phase_003 - Skill Installation And Routing Policy

Implementation notes:

- Copied selected local/global source skills into `.codex/skills/`.
- Installed selected external skills with `npx --yes skills add -y ...`.
- Synchronized external `.agents/skills/*` installs into `.codex/skills/*` so project-local `SKILL.md` verification succeeds.
- Expanded `docs/agent-workflows/orchestration.md` with situation-based skill routing.
- Updated `AGENTS.md` with install/run permission and docs-change policy.
- Updated `.find-skills/stock-analysis-agent/index.md` installation status.

Installed project-local skills:

- `agent-browser`, `apify-ultimate-scraper`, `backend-development`, `backtest`, `backtesting-trading-strategies`, `database-design`, `firecrawl`, `llm-application-dev`, `openai-docs`, `optimize`, `plugin-creator`, `quant-backtest`, `quick-stats`, `setup`, `shadcn`, `skill-creator`, `skill-installer`, `strategy-compare`, `supabase-postgres-best-practices`, `vectorbt-expert`, `vercel-react-best-practices`, `web-design-guidelines`, `webapp-testing`.

Validation:

- `find .codex/skills -maxdepth 2 -name SKILL.md -print | sort` shows 41 project-local skill files.
- `find backups/phase_003/.codex/skills -maxdepth 2 -name SKILL.md -print | sort` shows all phase-installed project-local skill backups.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs .find-skills/stock-analysis-agent/index.md backups/phase_003` returned no placeholder matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md .find-skills/stock-analysis-agent/index.md backups/phase_003/manifest.md` completed; `AGENTS.md` is 41 lines.

Risks and follow-ups:

- External scraper/browser skills can run with broad local permissions; use them only with source/legal/security context.
- `agent-browser` and `apify-ultimate-scraper` reported medium-risk or alert-bearing external install summaries; review before using on authenticated or sensitive sites.
- External API-backed skills may require API keys, credits, or separate CLI installation.
- Restart Codex after this turn so newly installed project-local skills are loaded automatically.

## phase_002 - Skill Discovery Checklist And Index

Implementation notes:

- Created `docs/checklist-001.md` for the `find-skills` gate.
- Broadened the checklist to favor recall across direct-fit, adjacent, and later-phase skills.
- Generated `.find-skills/stock-analysis-agent/index.md` after the user requested index generation.
- Ranked project-local skills, global/home source skills, and external candidates separately.
- Did not install or copy any additional skills.

Validation:

- `rg -n "TO[D]O|TB[D]|FIX[M]E" docs/checklist-001.md docs/task.md docs/implement.md .find-skills/stock-analysis-agent/index.md backups/phase_002` returned no placeholder matches.
- `wc -l docs/checklist-001.md docs/task.md docs/implement.md .find-skills/stock-analysis-agent/index.md backups/phase_002/docs/checklist-001.md backups/phase_002/docs/task.md backups/phase_002/docs/implement.md backups/phase_002/.find-skills/stock-analysis-agent/index.md backups/phase_002/manifest.md` completed.

Risks and follow-ups:

- External candidates still require source, license, portability, dependency, and install-path validation.
- Global/home-level skills may be useful sources but do not count as project-local installs.

## phase_001 - Planning And Workflow Documentation

Implementation notes:

- Created durable planning docs for the stock-analysis AI agent.
- Kept `AGENTS.md` short and redirected detailed workflow rules to `docs/agent-workflows/`.
- Added phase tracking rules for `docs/task.md`, `docs/implement.md`, and `backups/`.
- Recorded local and external skill/tool candidates without installing new external skills.

Validation:

- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs` returned no placeholder matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` completed; `AGENTS.md` is 35 lines.
- `git status --short` could not run because this directory is not currently a git repository.
- No application code exists yet, so no Python or TypeScript test suite is available.

Risks and follow-ups:

- External skill candidates require license and dependency review before project-local installation.
- Data-source legality and stability must be reviewed per source before crawler implementation.
- API key encryption design is not finalized.
- The scoring method is not finalized and must be validated separately from LLM prose quality.

## Future Phase Template

```text
## phase_00x - Title

Implementation notes:
- ...

Validation:
- ...

Risks and follow-ups:
- ...
```
