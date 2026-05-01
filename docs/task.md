# Task Log

Newest phases go first. Every implementation phase must use a `phase_00x` identifier and update this file before final handoff.

## phase_103 - Chat News Digest Component Split

Status: completed

Objective:

- Reduce `ChatShell` surface area by moving the news digest rendering subtree into a focused React component without changing UI behavior.

Acceptance criteria:

- `NewsDigestView` renders key articles, provider runs, warnings, and expandable additional articles independently.
- `ChatShell` imports and uses the extracted component.
- Existing chat news digest behavior and frontend validation continue to pass.

Files changed:

- `src/frontend/src/features/chat/ChatShell.tsx`
- `src/frontend/src/features/chat/NewsDigestView.tsx`
- `src/frontend/src/features/chat/NewsDigestView.test.tsx`
- `docs/agent-workflows/code-validation.md`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_102 - Backend E2E Chat-To-Analysis Slice

Status: completed

Objective:

- Add a focused backend E2E-style test slice for the persisted `/conversations` chat-to-prediction-analysis path.

Acceptance criteria:

- A deterministic provider can drive `/conversations` through credential setup, stock prediction, scoring, and conversation retrieval.
- The E2E test verifies source audit prompt IDs and raw-key non-exposure.
- The helper is isolated under `src/backend/tests/e2e`.

Files changed:

- `src/backend/tests/e2e/__init__.py`
- `src/backend/tests/e2e/helpers.py`
- `src/backend/tests/e2e/test_chat_to_analysis.py`
- `docs/agent-workflows/code-validation.md`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_101 - External Provider Credential Boundary

Status: completed

Objective:

- Centralize environment-backed search/news/market-data provider credential lookup so feature services no longer read provider API-key environment variables directly.

Acceptance criteria:

- Tavily, GNews, SerpApi, and Naver credentials are loaded through one credentials helper.
- Credential objects do not leak raw secrets through `repr`.
- Ingestion, news digest, and market-data provider code use the shared helper while preserving missing-credential warnings.

Files changed:

- `src/backend/app/features/credentials/external_providers.py`
- `src/backend/app/features/ingestion/service.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/app/features/news_digest/service.py`
- `src/backend/tests/test_phase101_external_provider_credentials.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_100 - Split Local Cache Storage Domains

Status: completed

Objective:

- Move cache and prediction-artifact domains out of the main local state JSON file while keeping the existing `LocalStateStore` API stable.

Acceptance criteria:

- `kv_cache`, `news_processing_runs`, and `prediction_artifacts` are written to `state.json.d/*.json` sidecar files.
- `LocalStateStore.read()` merges sidecar domains transparently.
- Existing cache, artifact, and conversation flows continue to pass.

Files changed:

- `src/backend/app/shared/state_store.py`
- `src/backend/tests/test_local_state_store.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_099 - Provider Warning Helper

Status: completed

Objective:

- Share provider status-to-warning behavior across ingestion and news digest provider flows.

Acceptance criteria:

- Missing credential and provider error warnings are built by a shared helper.
- Duplicate warnings are deduplicated consistently.
- Ingestion and news digest tests continue to pass.

Files changed:

- `src/backend/app/features/ingestion/service.py`
- `src/backend/app/features/news_digest/service.py`
- `src/backend/app/shared/provider_status.py`
- `src/backend/tests/test_phase099_provider_status.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_098 - Conversation Formatting Extraction

Status: completed

Objective:

- Start decomposing `conversations/service.py` by extracting message, language, horizon, and summary formatting helpers.

Acceptance criteria:

- Conversation formatting helpers live in a dedicated module.
- `conversations/service.py` uses the extracted helpers without changing chat behavior.
- New helper tests and existing backend tests pass.

Files changed:

- `src/backend/app/features/conversations/formatting.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase098_conversation_formatting.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_097 - In-Flight Work Landing And Cache Surface

Status: completed

Objective:

- Land the in-flight AI capability and processing-cache work into a more observable backend surface while addressing immediate repo hygiene findings from external reviews.

Acceptance criteria:

- `processing_cache` exposes a minimal status endpoint for KV cache, news processing run, and prediction artifact counts.
- `processing_cache` exposes a secret-safe invalidation endpoint for a single KV cache key.
- The processing-cache route is registered in the FastAPI app and covered by backend unit tests.
- Review scratch directories ignore `review-gpt` consistently with existing `review-claude` and `review-gemini` entries.

Files changed:

- `.gitignore`
- `src/backend/app/features/processing_cache/router.py`
- `src/backend/app/features/processing_cache/schemas.py`
- `src/backend/app/features/processing_cache/service.py`
- `src/backend/app/main.py`
- `src/backend/tests/test_phase093_news_cache_processing_store.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_096 - AI Capability And Prompt Inventory Diagnostics

Status: completed

Objective:

- Add a lightweight, secret-safe AI capability matrix and prompt inventory endpoint inspired by the WealthOS assistant audit.

Acceptance criteria:

- `/ai/capabilities` returns provider capability levels for chat, intent routing, stock analysis, news summary, and prediction-artifact caching.
- The prompt inventory lists the active prompt/artifact versions used by conversation, news, analysis, and processing-cache paths.
- The capability response does not expose API keys, decrypted credentials, or hidden prompt text.

Files changed:

- `src/backend/app/features/ai_capabilities/__init__.py`
- `src/backend/app/features/ai_capabilities/router.py`
- `src/backend/app/features/ai_capabilities/schemas.py`
- `src/backend/app/features/ai_capabilities/service.py`
- `src/backend/app/main.py`
- `src/backend/tests/test_phase096_ai_capabilities.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_095 - Prediction Artifact Store

Status: completed

Objective:

- Persist and reuse live prediction outputs when the evidence set, prompt version, provider, model, horizon, and `as_of_at` match.

Acceptance criteria:

- Live analysis assigns deterministic source-document IDs from evidence content.
- Completed live prediction output is stored as a prediction artifact without raw credentials or hidden system prompt text.
- Repeating the same prediction request reuses the artifact instead of recalling the live provider.
- Artifact reuse remains scoped to provider/model, prompt version, horizon, `as_of_at`, and evidence hash.

Files changed:

- `src/backend/app/features/analysis/service.py`
- `src/backend/app/features/processing_cache/__init__.py`
- `src/backend/app/features/processing_cache/service.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/tests/test_phase095_prediction_artifact_store.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_094 - S&P 500 Query Templates

Status: completed

Objective:

- Apply symbol-specific and sector-aware news query templates to S&P 500 companies, not only Apple and Google.

Acceptance criteria:

- Apple, Google/Alphabet, Nvidia, Tesla, JPMorgan, Exxon Mobil, Eli Lilly, and Walmart receive relevant query fragments.
- Generic US news queries still include earnings, leadership, regulation, analyst, and S&P Global research coverage.
- Existing news digest ranking and provider transparency tests continue to pass.

Files changed:

- `src/backend/app/features/news_digest/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`
- `src/backend/tests/test_phase094_sp500_query_templates.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_093 - News KV Cache And Processing Records

Status: completed

Objective:

- Add DB-backed KV cache behavior for news provider results and record news processing runs for audit/replay.

Acceptance criteria:

- Repeated news provider queries within TTL reuse the cached provider payload.
- News processing runs record cache hits, misses, provider runs, query templates, and article counts.
- Cache and processing records do not store API keys or provider secrets.

Files changed:

- `src/backend/app/features/news_digest/service.py`
- `src/backend/app/features/processing_cache/__init__.py`
- `src/backend/app/features/processing_cache/service.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/tests/test_phase093_news_cache_processing_store.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_092 - S&P 500 Stock Universe Boundary

Status: completed

Objective:

- Promote the local S&P 500 CSV into a reusable stock-universe boundary so news and query templates can resolve all S&P 500 symbols consistently.

Acceptance criteria:

- The S&P 500 universe exposes company name, sector, sub-industry, aliases, and Google Finance candidate queries.
- Metadata-only S&P 500 quotes can support news lookup when live quote data is unavailable.
- Representative S&P 500 symbols resolve through the same market-data boundary used by Apple and Google.

Files changed:

- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase092_sp500_stock_universe.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_091 - Workflow Docs And Unit Test Policy Hardening

Status: completed

Objective:

- Update agent workflow docs for external repo audits, S&P 500 matrix testing, cache/processing DB policy, and unit-test rigor.

Acceptance criteria:

- Code-authoring docs describe stock universe rules, cache keys, source adapter cache safety, and prediction artifact invalidation.
- Validation docs require matrix tests, provider fakes, cache hit/miss tests, and secret-leak checks for affected features.
- Orchestration docs route cache/processing DB work through database design and separate KV cache from normalized audit records.

Files changed:

- `docs/agent-workflows/code-authoring.md`
- `docs/agent-workflows/code-validation.md`
- `docs/agent-workflows/orchestration.md`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_090 - US Mega-Cap Intent Matrix Regression

Status: completed

Objective:

- Tighten unit coverage for Korean user requests about Apple, Google, Nvidia, and Tesla across news, stock chart, and prediction paths.

Acceptance criteria:

- `애플`, `구글`, `엔비디아`, and `테슬라` route to US symbols `AAPL`, `GOOG`, `NVDA`, and `TSLA`.
- Korean news requests for all four symbols return `news_digest` without requiring an analysis horizon.
- Korean stock chart requests for all four symbols return `market_snapshot` with Google Finance chart bars.
- Korean prediction requests for all four symbols return `analysis_completed` with default `swing` horizon probabilities.
- The matrix does not rely on successful LLM intent classification and does not leak LLM or search provider secrets.

Files changed:

- `src/backend/tests/test_phase090_us_mega_cap_intent_matrix.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_089 - News Review Routing And Test Isolation

Status: completed

Objective:

- Review the `phase_086` onward news/prediction continuation work and patch issues found during validation.

Acceptance criteria:

- Korean social-reaction requests such as `애플 SNS 반응` route to a news digest without relying on LLM intent classification.
- Social-reaction news requests include the public SerpApi social web provider when `SERPAPI_API_KEY` is configured.
- News digest tests remain stable when developer-local Naver credentials are present in the environment.
- Backend lint, type, compile, and test validation passes.

Files changed:

- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_088 - News Source Validation, Docs, And Push Prep

Status: completed

Objective:

- Validate `phase_083` through `phase_087`, record final implementation notes, preserve documentation backups, and prepare the git push requested by the user.

Acceptance criteria:

- Full backend tests, frontend tests/typecheck/build, Python lint/type checks, security audit, and whitespace checks pass.
- Documentation is updated after validation, with newest phases first.
- Modified docs are backed up under `backups/phase_088/`.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_087 - Korean Prediction Intent Fallback

Status: completed

Objective:

- Make Korean prediction phrases such as `애플 예측` route to live analysis even when the LLM intent classifier returns `other`.

Acceptance criteria:

- `예측` is treated as a stock-analysis keyword, not a market snapshot request.
- No-horizon prediction requests still default to the five-trading-day `swing` horizon.
- The conversation path returns scored buy/hold/sell probabilities when evidence analysis completes.

Files changed:

- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase077_prediction_probabilities.py`

## phase_086 - Naver And Public Social News Sources

Status: completed

Objective:

- Add optional domestic Naver News and public SNS search coverage to the news digest pipeline without direct logged-in social crawling.

Acceptance criteria:

- `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET` enable a `naver_news` provider.
- SNS coverage uses public SerpApi Google Web queries restricted to `x.com`, `twitter.com`, and `facebook.com`.
- Provider runs and articles preserve transparency while avoiding API-key leakage.

Files changed:

- `src/backend/app/features/news_digest/schemas.py`
- `src/backend/app/features/news_digest/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`
- `src/frontend/src/shared/types.ts`

## phase_085 - Diverse News Selection

Status: completed

Objective:

- Prevent the top news digest articles from being dominated by one source domain or one event type.

Acceptance criteria:

- Important articles are selected with category and source-domain caps before fallback fill.
- Quote pages remain deprioritized.
- Keyword classification avoids broad false positives such as matching `ai` inside unrelated words.

Files changed:

- `src/backend/app/features/news_digest/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_084 - News Query Diversification

Status: completed

Objective:

- Stop Apple news collection from over-targeting only quarterly earnings by generating diversified company-event queries.

Acceptance criteria:

- US news digest collection runs distinct queries for earnings, product/AI strategy, leadership, regulation/controversy, analyst/research context, and S&P Global research.
- Provider transparency records the query actually used for each run.
- Existing news digest routing continues to work for normal and typo-recovered Korean requests.

Files changed:

- `src/backend/app/features/news_digest/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_083 - Typo And News Intent Recovery

Status: completed

Objective:

- Recover common news-intent typos such as `애플 뉴ㅛㅡ` so users get the intended news digest instead of an unrelated market snapshot.

Acceptance criteria:

- `애플 뉴ㅛㅡ` routes to `news_digest` without requiring horizon input.
- The recovered request preserves the resolved stock and normal news digest payload.
- Generic stock prediction and market snapshot routing are not regressed.

Files changed:

- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_082 - Prediction Docs, Backups, And Full Validation

Status: completed

Objective:

- Record prediction phases `phase_077` through `phase_081`, preserve final backups, and run full validation after code and tests were complete.

Validation:

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 141 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `python3 -m ruff check src/backend/app src/backend/tests` passed.
- `python3 -m mypy src/backend/app` passed with 53 source files.
- `cd src/frontend && npm test` passed with 51 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after approved network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_081 - Similar Event Calibration Baseline

Status: completed

Objective:

- Add a replaceable similar-event calibration slot to scored predictions.

Acceptance criteria:

- Score responses include similar-event sample count, win rate, and median return fields.
- Chat and analysis UI expose the baseline without presenting it as a fully calibrated forecast.

Files changed:

- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/scoring/schemas.py`
- `src/backend/app/features/scoring/service.py`
- `src/backend/tests/test_phase008_scoring.py`
- `src/backend/tests/test_phase077_prediction_probabilities.py`
- `src/frontend/src/features/analysis/AnalysisPanel.test.tsx`
- `src/frontend/src/features/analysis/AnalysisPanel.tsx`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/shared/types.ts`

## phase_080 - Historical Buy-Date PnL Chat

Status: completed

Objective:

- Let users ask what would have happened if they bought a stock on a prior date, while keeping PnL separate from historical LLM evidence.

Acceptance criteria:

- Korean buy-date questions such as `4월 1일에 샀다면` return `pnl_simulation`.
- PnL responses include a `backtest_result` payload and do not create an analysis request.
- The assistant states that future prices are not mixed into historical LLM evidence.

Files changed:

- `src/backend/app/features/backtest/service.py`
- `src/backend/app/features/conversations/schemas.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase080_pnl_chat.py`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/types.ts`

## phase_079 - Expected Return And Downside Risk

Status: completed

Objective:

- Extend scored predictions beyond action probabilities with a rough five-trading-day expected return range and downside risk.

Acceptance criteria:

- Score responses include expected return min/max percentages and downside probability.
- Korean and English chat responses include the expected return range and downside risk.
- The analysis panel renders the new score metadata.

Files changed:

- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/scoring/schemas.py`
- `src/backend/app/features/scoring/service.py`
- `src/backend/tests/test_phase008_scoring.py`
- `src/backend/tests/test_phase077_prediction_probabilities.py`
- `src/frontend/src/features/analysis/AnalysisPanel.test.tsx`
- `src/frontend/src/features/analysis/AnalysisPanel.tsx`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/shared/types.ts`

## phase_078 - Market Data Evidence Bundle

Status: completed

Objective:

- Add current market snapshot and chart context as eligible `as_of_at` evidence for prediction prompts.

Acceptance criteria:

- Live analysis receives a `market_data` source document alongside news/source-adapter documents.
- Source audit counts market-data evidence explicitly.
- Market data evidence uses the quote `as_of_at` and excludes chart bars after that timestamp.

Files changed:

- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase026_generative_chat_orchestration.py`
- `src/backend/tests/test_phase077_prediction_probabilities.py`

## phase_077 - Five Trading Day Prediction Probabilities

Status: completed

Objective:

- Make no-horizon prediction requests default to a five-trading-day swing view and return scored buy/hold/sell probabilities in chat and UI.

Acceptance criteria:

- Prediction phrases such as `애플 예측해줘` default to `horizon_type=swing`.
- Completed live analysis attaches a `score_result` with buy/hold/sell probabilities.
- Chat responses and the analysis panel display the probability result.

Files changed:

- `src/backend/app/features/analysis/schemas.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase006_chat_settings_market_data.py`
- `src/backend/tests/test_phase014_conversation_language.py`
- `src/backend/tests/test_phase020_security_and_concurrency.py`
- `src/backend/tests/test_phase077_prediction_probabilities.py`
- `src/frontend/src/features/analysis/AnalysisPanel.test.tsx`
- `src/frontend/src/features/analysis/AnalysisPanel.tsx`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/styles.css`

## phase_076 - News Polish Docs, Backups, And Validation

Status: completed

Objective:

- Record phases `phase_070` through `phase_076`, preserve documentation backups, and run full validation.

Validation:

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 139 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `python3 -m ruff check src/backend/app src/backend/tests` passed.
- `python3 -m mypy src/backend/app` passed with 53 source files.
- `cd src/frontend && npm test` passed with 49 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after approved network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_075 - Korean News Digest Cards

Status: completed

Objective:

- Make news digest messages look closer to the ChatGPT reference: Korean headline bullets, compact article cards, source icons, and overflow-safe copy.

Acceptance criteria:

- Important articles render Korean headline/summary text when available.
- Article cards show favicon-style icons, source domain, provider, category, original linked title, and clipped summary.
- Long snippets are constrained within the chat message box.

Files changed:

- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/features/chat/ChatShell.tsx`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/styles.css`

## phase_074 - LLM Korean News Metadata

Status: completed

Objective:

- Let the LLM return structured Korean news summary metadata while retaining deterministic fallback behavior.

Acceptance criteria:

- The LLM prompt asks for compact JSON with digest summary and per-article `headline_ko`, `summary_ko`, and `category`.
- Valid JSON updates the digest and article metadata.
- Plain-text LLM responses still update only the digest summary.

Files changed:

- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_073 - News Importance Categories

Status: completed

Objective:

- Add explicit news categories and importance scores to support better story ordering.

Acceptance criteria:

- Articles can be categorized as official, earnings, core business, controversy, market reaction, product/service, quote page, or other.
- Official, earnings, core business, controversy, and major issue stories rank above generic quote/history pages.

Files changed:

- `src/backend/app/features/news_digest/schemas.py`
- `src/backend/app/features/news_digest/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_072 - News Query And Quote Page Demotion

Status: completed

Objective:

- Stop news search from over-targeting stock-price pages and reduce noisy snippets from finance portal navigation pages.

Acceptance criteria:

- US news queries use latest company news, earnings, official, business, and controversy terms instead of stock-price wording.
- Google Finance/Yahoo Finance quote/history pages are classified as `quote_page` and receive negative importance scores.
- Long provider snippets are normalized and truncated before display.

Files changed:

- `src/backend/app/features/news_digest/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_071 - Joint Dev Server Shutdown

Status: completed

Objective:

- Make `run-all.sh` terminate backend and frontend together when Ctrl+C is pressed on macOS.

Acceptance criteria:

- Ctrl+C/SIGTERM uses an explicit `shutdown` trap.
- Backend/frontend background processes are started with `exec` so tracked PIDs point at server processes.
- Cleanup waits for both child processes after sending termination signals.

Files changed:

- `run-all.sh`
- `src/backend/tests/test_phase015_runner_and_typo_confirmation.py`

## phase_070 - Ruff And MyPy Install

Status: completed

Objective:

- Install local backend validation tooling requested by the user.

Acceptance criteria:

- `python3 -m ruff --version` reports `ruff 0.15.12`.
- `python3 -m mypy --version` reports `mypy 1.19.1`.
- Backend validation uses these tools successfully.

Files changed:

- None. The backend `pyproject.toml` already listed `ruff` and `mypy` under dev optional dependencies.

## phase_069 - News Digest Docs, Backups, And Validation

Status: completed

Objective:

- Record the news digest implementation phases, preserve modified-file backups, and run full validation.

Validation:

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 135 tests and one local urllib3 LibreSSL warning.
- `cd src/frontend && npm test` passed with 49 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after approved network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_068 - Chat News Digest UI

Status: completed

Objective:

- Render news digest responses like a compact ChatGPT-style answer with source links and expandable extra stories.

Acceptance criteria:

- The assistant message shows a summary, linked important articles, provider result counts, and warnings.
- Additional articles are hidden behind a button and expand up to the backend limit.
- Frontend API mapping preserves top-level and message-level `newsDigest` payloads.

Files changed:

- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/features/chat/ChatShell.tsx`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/styles.css`

## phase_067 - Chat News Request Routing

Status: completed

Objective:

- Let requests such as `애플 뉴스 가져와줘` and `AAPL latest news` return a news digest without requiring an investment horizon.

Acceptance criteria:

- News requests return `status=news_digest`.
- Stock analysis is not invoked for news-only requests.
- Missing stock information still produces a focused clarification path.

Files changed:

- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/app/features/conversations/schemas.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_066 - LLM News Summary Fallback

Status: completed

Objective:

- Use the saved LLM provider for a concise source-grounded news overview when available, with deterministic fallback otherwise.

Acceptance criteria:

- LLM prompts include only fetched article metadata and never source credentials.
- Provider errors or missing LLM credentials keep the deterministic summary instead of failing the digest.

Files changed:

- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_065 - News Query Ranking And Dedupe

Status: completed

Objective:

- Normalize company/ticker news queries, merge duplicate provider results, and split important versus additional articles.

Acceptance criteria:

- Apple/AAPL news queries normalize to a finance-news query.
- Duplicate URLs are canonicalized and shown once.
- The digest returns up to 5 important articles and up to 10 additional articles.

Files changed:

- `src/backend/app/features/news_digest/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_064 - News Digest Provider Contract

Status: completed

Objective:

- Add a structured news digest provider contract for Tavily, GNews, SerpApi Google News, and SerpApi Google Web.

Acceptance criteria:

- Provider runs expose provider name, query, result count, status, and warnings.
- Articles preserve title, link, source, published time, snippet, provider, and query.
- `backups/phase_064/` records implementation-file backups and `backups/phase_069/` records documentation backups.

Files changed:

- `src/backend/app/features/news_digest/__init__.py`
- `src/backend/app/features/news_digest/schemas.py`
- `src/backend/app/features/news_digest/service.py`
- `src/backend/tests/test_phase064_069_news_digest.py`

## phase_063 - Provider USD/KRW Conversion Rate

Status: completed

Objective:

- Stop Korean US-stock snapshot copy from relying on the stale fallback `USD/KRW 1,400` whenever a live market-data provider key is available.
- Keep deterministic env override behavior for tests and local operator control.

Scope note:

- This phase uses the existing SerpApi Google Finance request path to query `USD-KRW`. It does not add a separate FX vendor or persist historical FX rates.

Skills used:

- `test-driven-development` for RED backend conversion-rate coverage.
- `backend-development` for provider-rate integration.
- `lint-and-validate` for backend and full-project validation.

Acceptance criteria:

- If `STUCK_LLM_USD_KRW_RATE` is set, Korean US-stock copy uses that configured rate.
- If the env rate is absent and `SERPAPI_API_KEY` is present, Korean US-stock copy uses a provider `USD-KRW` rate.
- If neither is available, the existing local fallback remains.
- `backups/phase_063/` records modified non-backup files for this phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed because Korean US-stock conversion still used `USD/KRW 1,400`.
- GREEN: same command passed with 6 tests and one local urllib3 LibreSSL warning.
- Full validation is recorded in `docs/implement.md` under `phase_063`.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app src/backend/tests src/frontend/src backups/phase_060 backups/phase_061 backups/phase_062 backups/phase_063` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 5228 total lines.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase026_generative_chat_orchestration.py`
- `src/backend/tests/test_phase055_058_market_chat.py`

## phase_062 - S&P 500 Symbol Directory Routing

Status: completed

Objective:

- Prevent S&P 500 tickers and company names such as WMT/Walmart/월마트 from falling through to KR market lookup when the default market is KR.
- Add a local S&P 500 symbol directory as the first broader US-stock resolution layer beyond hand-written Apple/Google aliases.

Scope note:

- The S&P 500 constituent CSV is local app data seeded from the public `datasets/s-and-p-500-companies` constituents CSV. It is not a live membership update job.

Skills used:

- `test-driven-development` for RED resolver/chat coverage.
- `backend-development` for market-data resolver changes.
- `llm-application-dev` for deterministic resolver behavior before asking the LLM to disambiguate.
- `lint-and-validate` for backend and full-project validation.

Acceptance criteria:

- `월마트 주가` resolves to US `WMT`, not a KRW `WMT` fallback.
- Direct S&P 500 tickers typed while default market is KR route to US quote lookup.
- Existing Apple/Google deterministic aliases continue to work.
- `backups/phase_062/` records modified non-backup files for this phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed because `월마트 주가` returned `needs_input`.
- GREEN: same command passed after the S&P 500 directory resolver.
- Full validation is recorded in `docs/implement.md` under `phase_063`.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/market_data/service.py`
- `src/backend/app/features/market_data/sp500_constituents.csv`
- `src/backend/tests/test_phase055_058_market_chat.py`

## phase_061 - Chat Auto Scroll To Latest

Status: completed

Objective:

- Make the chat behave like GPT-style conversation UIs by scrolling to the newest content after message updates and while request activity is shown.

Scope note:

- This phase only changes the chat scroll anchor behavior. It does not add streaming responses.

Skills used:

- `test-driven-development` for RED frontend scroll coverage.
- `frontend-design` for predictable GPT-style conversation ergonomics.
- `systematic-debugging` for jsdom/browser scroll compatibility.
- `lint-and-validate` for frontend and full-project validation.

Acceptance criteria:

- After a message response arrives, the conversation scroll anchor is brought into view.
- During pending activity, the newest activity content can stay visible.
- Tests remain compatible with environments where `scrollIntoView` is not implemented.
- `backups/phase_061/` records modified non-backup files for this phase.

Validation:

- RED: `cd src/frontend && npm test -- ChatShell.test.tsx` failed because no scroll behavior occurred.
- GREEN: same command passed with 10 tests.
- Full validation is recorded in `docs/implement.md` under `phase_063`.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/features/chat/ChatShell.tsx`

## phase_060 - Chart Hover Tooltip And Thinner Directional Line

Status: completed

Objective:

- Add Google Finance-style hover feedback to the chart.
- Keep line color directional by selected chart window: green when the displayed window ends above its first value, red when it ends below.
- Reduce the plotted line stroke so dense intraday charts are easier to read.

Scope note:

- This remains the existing SVG chart. It adds pointer interaction without adding a charting dependency.

Skills used:

- `test-driven-development` for RED chart hover and selected-window color tests.
- `frontend-design` for chart tooltip and stroke tuning.
- `systematic-debugging` for interaction behavior in tests.
- `lint-and-validate` for frontend and full-project validation.

Acceptance criteria:

- Hovering over the chart shows the nearest point date/time and price.
- A selected window's first and last chart bars drive red/green line color.
- The visual line is thinner than the prior thick stroke.
- `backups/phase_060/` records modified non-backup files for this phase.

Validation:

- RED: `cd src/frontend && npm test -- MarketChart.test.tsx` failed because tooltip and selected-window behavior were absent.
- GREEN: same command passed with 3 tests.
- Full validation is recorded in `docs/implement.md` under `phase_063`.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/frontend/src/features/analysis/MarketChart.test.tsx`
- `src/frontend/src/features/analysis/MarketChart.tsx`
- `src/frontend/src/styles.css`

## phase_059 - Readable Finance Chart And Fresh New Chat

Status: completed

Objective:

- Bring the `gpt-coding/finance_app.py` chart behavior into the React app as a readable finance chart.
- Make the chat chart large enough to interpret without guessing what the line represents.
- Ensure `New chat` opens a genuinely fresh empty conversation view.

Scope note:

- The Streamlit/Plotly implementation was translated into the existing React SVG chart instead of adding a new Plotly dependency.
- This phase is frontend-only; the backend quote and alias behavior from phases 055-058 remains unchanged.

Skills used:

- `test-driven-development` for chart and new-chat regression coverage.
- `frontend-design` for readable chart dimensions, stable axes, and compact finance UI layout.
- `systematic-debugging` for the stale conversation state and chart readability symptoms.
- `lint-and-validate` for frontend and backend regression validation.

Acceptance criteria:

- Chat and analysis charts render a larger finance-style plot with y-axis price labels, x-axis time/date labels, start reference line, and latest marker.
- USD charts display USD labels while KR charts display KRW labels.
- `New chat` clears the active conversation and remounts the chat shell so old messages are not shown.
- `backups/phase_059/` records modified non-backup files for this phase.

Validation:

- `cd src/frontend && npm test -- MarketChart.test.tsx App.test.tsx ChatShell.test.tsx AnalysisPanel.test.tsx` passed with 25 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm test` passed with 44 tests.
- `cd src/frontend && npm run build` passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 131 tests and one local urllib3 LibreSSL warning.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app src/backend/tests src/frontend/src backups/phase_059` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 4959 total lines.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/App.tsx`
- `src/frontend/src/features/analysis/AnalysisPanel.test.tsx`
- `src/frontend/src/features/analysis/MarketChart.test.tsx`
- `src/frontend/src/features/analysis/MarketChart.tsx`
- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/styles.css`

## phase_058 - Google Finance Style Chart Context

Status: completed

Objective:

- Bring the current React market chart closer to the useful `gpt-coding` Google Finance graph behavior.
- Show the selected window, start reference, latest marker, and exchange-local axis labels in the chart card.

Scope note:

- This remains the existing lightweight SVG chart component. It does not add Plotly or a new charting dependency.

Skills used:

- `test-driven-development` for RED frontend chart tests before implementation.
- `frontend-design` for stable, compact chart context aligned with `DESIGN.md`.
- `lint-and-validate` for frontend and full-project validation.

Acceptance criteria:

- Windowed US snapshots show the active window value even when period controls are not rendered.
- Charts show a start-price reference label and latest-price marker label.
- Date axis labels preserve the provider/exchange-local date instead of shifting through browser-local timezone conversion.
- `backups/phase_058/` records modified non-backup files for this phase.

Validation:

- RED: `cd src/frontend && npm test -- MarketChart.test.tsx` failed because start/latest/window/date context was absent.
- GREEN: same command passed.
- Full validation is recorded in `docs/implement.md` under `phase_058`.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/frontend/src/features/analysis/MarketChart.test.tsx`
- `src/frontend/src/features/analysis/MarketChart.tsx`
- `src/frontend/src/styles.css`

## phase_057 - US Snapshot Currency Display Policy

Status: completed

Objective:

- Keep US market snapshots and graphs in USD.
- In Korean chat copy, add a KRW conversion for US prices instead of mislabeling US stocks as KRW.

Scope note:

- This phase adds deterministic display conversion using `STUCK_LLM_USD_KRW_RATE` when present and a local fallback rate otherwise. It does not add a live FX provider.

Skills used:

- `test-driven-development` for RED backend conversation tests before implementation.
- `backend-development` for conversation response formatting.
- `lint-and-validate` for backend and full-project validation.

Acceptance criteria:

- `구글 주가` resolves to a US `GOOG` market snapshot when the Google Finance provider is available.
- US snapshot payloads keep `currency="USD"`.
- Korean assistant snapshot text includes USD and an approximate KRW conversion.
- `backups/phase_057/` records modified non-backup files for this phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed because `구글 주가` returned `needs_input` and no KRW conversion.
- GREEN: same command passed.
- Full validation is recorded in `docs/implement.md` under `phase_057`.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase055_058_market_chat.py`

## phase_056 - Search-Style US Ticker Normalization

Status: completed

Objective:

- Accept realistic quote-search phrases such as `apple`, `aapl stock`, `애플 주가`, `구글 주가`, and `google stock`.
- Prefer SerpApi Google Finance candidates with graph data before falling back to graphless summary data.

Scope note:

- This phase adds focused Apple and Google/Alphabet aliases plus generic quote filler stripping. It does not attempt a full global symbol directory.

Skills used:

- `test-driven-development` for RED backend market-data and chat tests before implementation.
- `backend-development` for market-data resolver changes.
- `llm-application-dev` for intent prompt guidance around search-style phrases and ambiguity.
- `lint-and-validate` for backend and full-project validation.

Acceptance criteria:

- Apple and Google localized/common-name inputs route to US tickers even when the active default market is KR.
- The provider tries the next Google Finance query candidate if the first candidate has no graph for a requested chart window.
- LLM intent instructions classify search-style quote requests as `market_snapshot` unless the user asks for analysis/scoring.
- `backups/phase_056/` records modified non-backup files for this phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed because Google did not resolve and graphless candidates were accepted.
- GREEN: same command passed.
- Full validation is recorded in `docs/implement.md` under `phase_056`.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase026_generative_chat_orchestration.py`
- `src/backend/tests/test_phase055_058_market_chat.py`

## phase_055 - Ambiguous Chat Follow-Up And Snapshot Guard

Status: completed

Objective:

- Stop stock-only inputs such as `apple` from producing a `/conversations` 500.
- Use the LLM intent follow-up question when the user asks an ambiguous stock question.

Scope note:

- This phase fixes chat orchestration behavior only. It does not change the live analysis evidence or scoring pipeline.

Skills used:

- `test-driven-development` for RED backend conversation tests before implementation.
- `backend-development` for conversation state and response behavior.
- `llm-application-dev` for structured follow-up handling.
- `lint-and-validate` for backend and full-project validation.

Acceptance criteria:

- `apple` returns a market snapshot, not a 500 or a horizon prompt.
- LLM `needs_follow_up` with `follow_up_question` is surfaced to the user as the assistant response.
- Stock confirmation follow-ups with a horizon still proceed to analysis instead of snapshot-only behavior.
- `backups/phase_055/` records modified non-backup files for this phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed with the existing 500, generic follow-up, and missing snapshot behavior.
- GREEN: same command passed.
- Full validation is recorded in `docs/implement.md` under `phase_055`.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase055_058_market_chat.py`

## phase_052 - Conversation Deletion And Fixed Settings Rail

Status: completed

Objective:

- Add saved-conversation deletion from the left rail.
- Add a Settings action that clears all saved chat history.
- Keep the Settings button independent at the bottom of the left rail while conversation history scrolls separately.

Scope note:

- This phase deletes local saved conversations from the current state store. It does not add undo or archival recovery.

Skills used:

- `test-driven-development` for RED backend and frontend tests before implementation.
- `backend-development` for conversation deletion API/service changes.
- `frontend-design` for left-rail layout and settings modal UX.
- `lint-and-validate` for focused validation.

Acceptance criteria:

- `DELETE /conversations/{conversation_id}` deletes one saved conversation and returns `deleted_count`.
- `DELETE /conversations` clears all saved conversations and returns `deleted_count`.
- Missing conversation deletion returns 404.
- Each left-rail conversation has an accessible delete control.
- Settings Security tab has a confirm-gated clear-history action.
- The left rail keeps Settings in a bottom footer while the conversation list scrolls independently.
- `backups/phase_052/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase052_conversation_delete.py -q` failed because conversation DELETE endpoints returned 405.
- GREEN: same command passed with 3 tests and one local urllib3 LibreSSL warning.
- RED: `cd src/frontend && npm test -- api.test.ts App.test.tsx SettingsModal.test.tsx` failed because the delete API helpers, left-rail delete button, and Settings clear-history action did not exist.
- GREEN: same command passed with 27 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 127 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `cd src/frontend && npm test` passed with 42 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after approved network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app src/backend/tests src/frontend/src backups/phase_049 backups/phase_050 backups/phase_051 backups/phase_052` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 4600 total lines.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/conversations/router.py`
- `src/backend/app/features/conversations/schemas.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase052_conversation_delete.py`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/App.tsx`
- `src/frontend/src/features/settings/SettingsModal.test.tsx`
- `src/frontend/src/features/settings/SettingsModal.tsx`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/styles.css`

## phase_051 - Frontend Chart Period Controls

Status: completed

Objective:

- Let users switch US Google Finance graph windows from the chat market snapshot card.
- Keep period switching message-local so older conversation charts remain stable unless the user changes that chart.

Scope note:

- This phase adds graph period controls only for US `serpapi_google_finance` market snapshots.
- It does not prefetch every period and does not add news UI changes.

Skills used:

- `test-driven-development` for RED frontend tests before implementation.
- `frontend-design` for compact segmented chart controls.
- `lint-and-validate` for focused frontend validation.

Acceptance criteria:

- Frontend API mapping accepts `chart_window` and returns `chartWindow`.
- `fetchMarketQuote("US", "AAPL", "5D")` calls `/market-data/quotes/US/AAPL?window=5D`.
- US SerpApi chart cards show period controls for `1D`, `5D`, `1M`, `6M`, `YTD`, `1Y`, `5Y`, and `MAX`.
- Selecting a period refetches that message's quote and updates the rendered graph/price.
- `backups/phase_051/` records every non-backup file modified in the phase.

Validation:

- RED: `cd src/frontend && npm test -- api.test.ts ChatShell.test.tsx` failed because `chartWindow` was not mapped and the chat chart had no period buttons.
- GREEN: same command passed with 18 tests.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/App.tsx`
- `src/frontend/src/features/analysis/AnalysisPanel.test.tsx`
- `src/frontend/src/features/analysis/MarketChart.tsx`
- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/features/chat/ChatShell.tsx`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/styles.css`

## phase_050 - US Google Finance Chart Window Contract

Status: completed

Objective:

- Expose SerpApi Google Finance graph windows through the backend market-data API for US quotes.
- Improve Google Finance query fallback for exchange-qualified inputs such as `AAPL:NASDAQ`.

Scope note:

- This phase is backend-only. Frontend period controls are implemented in phase_051.
- The new window contract is limited to the existing market-data quote endpoint and SerpApi Google Finance path.

Skills used:

- `test-driven-development` for RED backend tests before implementation.
- `backend-development` for API/schema/service changes.
- `lint-and-validate` for focused backend validation.

Acceptance criteria:

- `GET /market-data/quotes/US/AAPL?window=5D` passes `window=5D` to SerpApi Google Finance.
- `MarketQuote` responses include the selected `chart_window`.
- `AAPL:NASDAQ` style inputs try the original candidate, then the reversed `NASDAQ:AAPL` candidate, before falling back.
- Existing SerpApi key handling remains environment-only and API responses do not leak `SERPAPI_API_KEY`.
- `backups/phase_050/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py::test_us_quote_endpoint_passes_requested_chart_window_to_serpapi src/backend/tests/test_phase022_us_market_data_provider.py::test_colon_us_quote_tries_reversed_google_finance_exchange_candidate -q` failed because the backend always passed `window=1D` and did not try `NASDAQ:AAPL`.
- GREEN: same command passed with 2 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py -q` passed with 6 tests.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/market_data/router.py`
- `src/backend/app/features/market_data/schemas.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase006_chat_settings_market_data.py`
- `src/backend/tests/test_phase022_us_market_data_provider.py`

## phase_049 - Google Finance Runtime Comparison

Status: completed

Objective:

- Compare the standalone `gpt-coding` Google Finance Streamlit apps with the current local FastAPI/React structure before implementing the remaining graph UX phases.
- Confirm which pieces should be brought into the app first for US-only graph support.

Scope note:

- This phase does not change production code. It records the runtime comparison and implementation constraints for phases 050 through 052.
- Live SerpApi calls were not executed because the current shell environment does not contain `SERPAPI_API_KEY`.

Skills used:

- `webapp-testing` for local runtime feasibility checks.
- `frontend-design` for mapping the standalone graph UX into the current chat workspace.
- `lint-and-validate` for non-production validation commands.

Acceptance criteria:

- The standalone Streamlit finance files are syntax-checked in the repository workspace.
- The comparison identifies the useful chart behavior: query candidates, SerpApi `window`, and graph-first retrieval.
- The comparison identifies current app gaps: no API-level `window`, no frontend period controls, no independent bottom settings rail, and no conversation deletion.
- `backups/phase_049/` records every non-backup file modified in the phase.

Validation:

- `python3 -m streamlit --version` passed and reported Streamlit 1.50.0.
- `python3 -m py_compile gpt-coding/finance_app.py gpt-coding/finance_news_app.py` initially failed because Python tried to write bytecode under the macOS user cache outside the sandbox.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m py_compile gpt-coding/finance_app.py gpt-coding/finance_news_app.py` passed.
- `python3 -c "import os; print('SERPAPI_API_KEY=set' if os.environ.get('SERPAPI_API_KEY') else 'SERPAPI_API_KEY=missing')"` reported `SERPAPI_API_KEY=missing`.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_054 - Chat Request Activity Indicator

Status: completed

Objective:

- Show ChatGPT-style in-flight activity while the app is waiting for LLM/provider and market-data work to finish.
- Keep the status short and specific enough to tell the user whether the app is checking LLM intent or market data APIs.

Scope note:

- This phase adds frontend request-status copy only; it does not add true backend streaming or server-sent progress events.

Skills used:

- `test-driven-development` for RED frontend tests before implementation.
- `frontend-design` for compact status UI inside the chat workspace.
- `lint-and-validate` for frontend validation.

Acceptance criteria:

- While a chat request is pending, the message list shows `Thinking...` in English and `생각중...` in Korean.
- The pending status includes short activity lines for LLM intent/provider work and market-data API checks.
- The send button remains disabled while the pending status is visible.
- The status disappears when the request completes.
- `backups/phase_054/` records every non-backup file modified in the phase.

Validation:

- RED: `cd src/frontend && npm test -- ChatShell.test.tsx` failed because pending requests did not render `Thinking...` or `생각중...` activity copy.
- GREEN: same command passed with 8 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 122 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app/features/analysis/live_provider.py src/backend/app/features/conversations src/backend/tests/test_phase026_generative_chat_orchestration.py` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `cd src/frontend && npm test` passed with 36 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after approved network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app src/backend/tests src/frontend/src backups/phase_053 backups/phase_054` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 4280 total lines.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/features/chat/ChatShell.tsx`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/styles.css`

## phase_053 - LLM Confirmed Korean US Ticker Snapshot

Status: completed

Objective:

- Let a Korean company-name input such as `애플` resolve to a US ticker snapshot through LLM intent, without adding a hard-coded Korean alias.
- Ask the user to confirm the LLM-inferred stock before fetching the graph.

Scope note:

- This phase focuses on graph/market snapshot retrieval only.
- News expansion and richer chart window controls remain out of scope for this phase.

Skills used:

- `test-driven-development` for RED backend tests before implementation.
- `llm-application-dev` for structured intent handling.
- `stock-analysis-llm` for keeping LLM stock inference separate from evidence analysis.
- `backend-development` for conversation schema and service changes.
- `lint-and-validate` for final validation.

Acceptance criteria:

- The chat intent prompt tells the LLM to infer localized company names into canonical stock queries when confident.
- If a user sends `애플` and the saved LLM intent maps it to `AAPL` in `US`, the assistant asks for confirmation instead of immediately fetching.
- A Korean affirmative follow-up such as `네` confirms the pending LLM stock candidate and returns a US market snapshot with chart bars.
- No hard-coded `애플` alias is added to market-data aliases.
- Raw LLM keys and `SERPAPI_API_KEY` remain absent from responses.
- `backups/phase_053/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase026_generative_chat_orchestration.py::test_llm_inferred_korean_us_stock_requires_confirmation_before_snapshot -q` failed because LLM-inferred `애플` was immediately returned as a market snapshot instead of requiring confirmation.
- GREEN: same command passed with one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase026_generative_chat_orchestration.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py -q` passed with 13 tests and one local urllib3 LibreSSL warning.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/app/features/conversations/schemas.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase026_generative_chat_orchestration.py`

## phase_048 - SerpApi Google News Ingestion Adapter

Status: completed

Objective:

- Add a selectable ingestion adapter that uses `SERPAPI_API_KEY` with SerpApi Google News and converts results into source documents.

Scope note:

- This phase adds source collection support only; market snapshot chart/news UI behavior remains covered by phases 046 and 047.

Skills used:

- `test-driven-development` for RED backend tests before implementation.
- `backend-development` for ingestion adapter and schema changes.
- `security-auditor` for external source text and secret-handling checks.
- `lint-and-validate` for backend validation.

Acceptance criteria:

- `source_adapters` accepts `serpapi_google_news`.
- The adapter calls SerpApi with `engine=google_news`, a stock news query, and `SERPAPI_API_KEY`.
- Flat Google News items and grouped `stories` become source documents with safe metadata and untrusted-source safety flags.
- Missing `SERPAPI_API_KEY` returns a safe `missing_credential:serpapi_google_news` warning.
- Raw SerpApi keys are not returned in API responses.
- `backups/phase_048/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase019_live_market_and_news.py::test_ingestion_collects_serpapi_google_news_without_leaking_key src/backend/tests/test_phase019_live_market_and_news.py::test_ingestion_missing_serpapi_google_news_key_returns_safe_warning -q` failed because `serpapi_google_news` was not accepted by the ingestion schema.
- GREEN: same command passed with 2 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase019_live_market_and_news.py src/backend/tests/test_phase010_ingestion_adapters.py -q` passed with 10 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 121 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app/features/market_data/service.py src/backend/app/features/ingestion src/backend/tests/test_phase019_live_market_and_news.py src/backend/tests/test_phase022_us_market_data_provider.py src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app src/backend/tests backups/phase_046 backups/phase_047 backups/phase_048` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 4118 total lines.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/ingestion/schemas.py`
- `src/backend/app/features/ingestion/service.py`
- `src/backend/tests/test_phase019_live_market_and_news.py`

## phase_047 - Nested Google Finance News Snapshot Parsing

Status: completed

Objective:

- Preserve related news when SerpApi Google Finance returns nested news sections instead of a flat `news_results` list.

Scope note:

- This phase only changes market snapshot parsing; it does not add a Google News search adapter.

Skills used:

- `test-driven-development` for RED backend tests before implementation.
- `backend-development` for market-data service parsing changes.
- `security-auditor` for treating provider news text as untrusted display/evidence metadata.
- `lint-and-validate` for backend validation.

Acceptance criteria:

- Google Finance `news_results[].items` entries become `MarketNewsItem` values.
- Nested news keeps source, link, published timestamp, and snippet when present.
- Existing flat Google Finance news parsing continues to work.
- `backups/phase_047/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py::test_ticker_snapshot_flattens_nested_google_finance_news_items -q` failed because the parser returned the wrapper title `In the news` instead of the nested article.
- GREEN: same command passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py src/backend/tests/test_phase022_us_market_data_provider.py -q` passed with 7 tests and one local urllib3 LibreSSL warning.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py`

## phase_046 - SerpApi Google Finance Query Candidate Fallback

Status: completed

Objective:

- Improve US ticker snapshot resolution by trying SerpApi Google Finance query candidates when the preferred exchange mapping has no usable quote.

Scope note:

- This phase only changes Google Finance market snapshot lookup; it does not add a separate news search adapter or frontend UI.

Skills used:

- `test-driven-development` for RED backend tests before implementation.
- `backend-development` for market-data service changes.
- `security-auditor` for keeping SerpApi key handling and response data boundaries safe.
- `lint-and-validate` for backend validation.

Acceptance criteria:

- Unknown US tickers try `SYMBOL:NASDAQ`, then `SYMBOL:NYSE`, then bare `SYMBOL` without duplicating candidates.
- A malformed or quote-less candidate response falls through to the next candidate.
- SerpApi API keys remain environment-only and are not returned in API responses.
- `backups/phase_046/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py::test_serpapi_google_finance_tries_exchange_candidates_until_quote_found -q` failed because only `ACME:NASDAQ` was tried and the route returned 404.
- GREEN: same command passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py -q` passed with 4 tests.

Files changed:

- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase022_us_market_data_provider.py`

## phase_041 - Agent Harness Foundation

Status: completed

Objective:

- Add a project-local harness entrypoint that agents can run to execute validation profiles from one command.
- Produce agent-readable JSON and Markdown reports under ignored harness artifacts.
- Keep phase_042 through phase_045 as documented future harness phases only.

Scope note:

- This phase adds command orchestration and reports; it does not add browser automation, eval corpus CLI, observability traces, or structural garbage-collection lint yet.

Skills used:

- `test-driven-development` for RED harness contract tests before implementation.
- `agent-workflow-docs` for workflow documentation updates.
- `lint-and-validate` for final validation.

Acceptance criteria:

- A root harness command supports dry-run profile inspection without executing expensive checks.
- Harness profiles cover docs, backend, frontend, provider-focused, quick, and full validation command sets.
- Each harness run writes `report.json` and `report.md` with profile, command, status, cwd, duration, and stdout/stderr tail data.
- Generated harness reports are ignored by git.
- Docs record `phase_042` through `phase_045` as future planned harness work, without implementing those phases.
- `backups/phase_041/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase041_agent_harness.py -q` failed because `scripts/harness/run_harness.py` did not exist.
- GREEN: same command passed with 2 tests.
- `./run-harness.sh --profile docs --dry-run --run-id phase041-dry-run` passed and wrote report artifacts.
- `./run-harness.sh --profile docs --run-id phase041-docs-check` passed.
- `./run-harness.sh --profile quick --run-id phase041-quick` passed.
- `./run-harness.sh --profile backend --run-id phase041-backend` passed.
- `./run-harness.sh --profile frontend --run-id phase041-frontend` passed.
- `./run-harness.sh --profile provider --run-id phase041-provider` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check scripts/harness src/backend/tests/test_phase041_agent_harness.py` passed.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q scripts/harness src/backend/tests/test_phase041_agent_harness.py` passed.
- Final `./run-harness.sh --profile docs --run-id phase041-docs-after-log` passed.
- Final `git diff --check` passed.
- Final `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_041` returned no matches.
- Final `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 3909 total lines.

Files changed:

- `.gitignore`
- `AGENTS.md`
- `docs/agent-workflows/code-validation.md`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`
- `run-harness.sh`
- `scripts/harness/run_harness.py`
- `src/backend/tests/test_phase041_agent_harness.py`

## phase_040 - Agent Workflow Provider Validation Policy

Status: completed

Objective:

- Patch `docs/agent-workflows` so future provider/API-key work validates real user conversation paths, not only connection tests.
- Clarify the split between LLM provider credentials and search/market-data provider keys.
- Require separate acceptance criteria for simple chat, follow-up chat, stock analysis, and rich market snapshots.
- Update `AGENTS.md` so agents proactively patch `docs/agent-workflows` when workflow behavior is not applying correctly.

Scope note:

- This phase updates agent-facing workflow policy only; implementation behavior is covered by `phase_038` and `phase_039`.

Skills used:

- `agent-workflow-docs` for workflow documentation changes.
- `agents-md` for concise root agent instructions.
- `lint-and-validate` for documentation validation.

Acceptance criteria:

- Workflow docs state that API-key work must verify `/conversations`, repeated follow-ups, and saved conversation behavior.
- Workflow docs distinguish LLM provider keys from search/news/market-data keys such as `SERPAPI_API_KEY`.
- Workflow docs require rich snapshot schema/UI when users expect Google Finance-style data beyond `MarketQuote`.
- `AGENTS.md` tells agents to proactively patch `docs/agent-workflows` when workflow docs need correction.
- `backups/phase_040/` records every non-backup file modified in the phase.

Validation:

- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_038 backups/phase_039 backups/phase_040` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 3952 total lines.

Files changed:

- `AGENTS.md`
- `docs/agent-workflows/code-authoring.md`
- `docs/agent-workflows/code-validation.md`
- `docs/agent-workflows/orchestration.md`
- `docs/implement.md`
- `docs/plan.md`
- `docs/task.md`

## phase_039 - ChatGPT-Style Conversation Workspace

Status: completed

Objective:

- Make the chat workspace behave like a ChatGPT-style conversation surface with internal message scrolling, a stable composer, and previous conversations selectable from the left rail.
- Preserve message-level market charts, news, and stats across follow-up messages instead of replacing earlier content with only the latest snapshot.
- Render ticker snapshots in chat when a user searches a symbol such as `AAPL`.

Scope note:

- This phase consumes the `phase_038` conversation list and message-level snapshot API; it does not add streaming or browser push updates.

Skills used:

- `frontend-design` for the ChatGPT-style workspace aligned with `DESIGN.md`.
- `test-driven-development` for RED frontend tests before UI/API changes.
- `lint-and-validate` for frontend validation.

Acceptance criteria:

- The left rail lists previous conversations and can load a selected conversation by ID.
- The chat message list scrolls independently while the composer remains visible.
- Earlier assistant charts/news/stats remain attached to their original messages after later messages are sent.
- `AAPL` snapshot responses render price chart, key stats, and related news in the chat message.
- `backups/phase_039/` records every non-backup file modified in the phase.

Validation:

- RED: `cd src/frontend && npm test -- ChatShell.test.tsx App.test.tsx api.test.ts` failed on missing conversation API mapping, missing left-rail history, and missing message-level snapshot rendering.
- GREEN: same command passed with 23 tests.
- `cd src/frontend && npm test` passed with 34 tests across 7 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after approved network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.

Files changed:

- `docs/task.md`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/App.tsx`
- `src/frontend/src/features/analysis/AnalysisPanel.test.tsx`
- `src/frontend/src/features/analysis/MarketChart.tsx`
- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/features/chat/ChatShell.tsx`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/styles.css`

## phase_038 - Persistent LLM Chat And Rich Ticker Snapshots

Status: completed

Objective:

- Let a saved LLM API key support simple conversational replies through the real `/conversations` user path, not only connection diagnostics or stock-analysis structured outputs.
- Persist and reload conversations with message-level market snapshot attachments so earlier charts/news remain visible after follow-up messages.
- Return a market snapshot with chart/news/key stats when the user enters a stock ticker such as `AAPL`, without requiring a horizon first.
- Expose a conversation list endpoint for previous-chat selection in the frontend.

Scope note:

- This phase keeps LLM credentials saved-user-key first; LLM environment variables remain non-fallback.
- This phase does not add streaming, multi-user login, or full portfolio memory.

Skills used:

- `test-driven-development` for RED backend tests before behavior changes.
- `provider-credentials` for saved-key use and raw-secret non-exposure.
- `stock-analysis-llm` for keeping stock-analysis prompts separate from generic chat and evidence cutoff rules.
- `backend-development` for conversation and market-data API changes.
- `lint-and-validate` for backend validation.

Acceptance criteria:

- Generic chat with a saved Cerebras/OpenAI-compatible key calls the provider through `/conversations`, stores the assistant reply, and includes recent conversation context on follow-up.
- Conversation summaries can be listed newest-first and loaded by ID without exposing raw keys.
- A ticker-only request such as `AAPL` returns a market snapshot instead of asking for a swing/intraday/long-term horizon.
- SerpApi Google Finance parsing captures chart bars, key stats, and news items without leaking `SERPAPI_API_KEY`.
- Assistant messages can carry their own `market_snapshot` so previous charts/news survive later messages.
- `backups/phase_038/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py -q` failed because generic chat returned `needs_input` and ticker-only `AAPL` asked for a horizon.
- GREEN: same command passed with 2 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase022_us_market_data_provider.py src/backend/tests/test_phase026_generative_chat_orchestration.py -q` passed with 14 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 115 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `git diff --check` passed.

Files changed:

- `docs/task.md`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/app/features/conversations/router.py`
- `src/backend/app/features/conversations/schemas.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/market_data/schemas.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase006_chat_settings_market_data.py`
- `src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py`

## phase_037 - Cerebras Provider Header Compatibility

Status: completed

Objective:

- Compare the working `cerebras-test` SDK call, DeepTutor provider utilities, and Stuck_LLM's direct HTTP provider path.
- Apply the minimal DeepTutor-inspired provider-header pattern needed for Cerebras compatibility.
- Confirm Stuck_LLM's saved Cerebras credential can send a real prompt and receive a response.

Scope note:

- This phase does not copy DeepTutor's full LLM architecture, model catalog, env-fallback policy, streaming stack, or telemetry system.
- This phase preserves Stuck_LLM's current saved-credential-first policy; LLM environment variables remain non-fallback for runtime credentials.

Skills used:

- `provider-credentials` for saved-key boundaries and raw-secret non-exposure.
- `llm-application-dev` for provider-call compatibility.
- `backend-development` for the backend provider implementation.
- `test-driven-development` for RED header-contract tests before implementation.
- `lint-and-validate` for backend validation.

Acceptance criteria:

- Cerebras/OpenAI-compatible provider calls send explicit `Accept: application/json` and a non-urllib `User-Agent`.
- Analyze, chat intent, and connection-test calls share the same provider header builder.
- Existing raw-key non-exposure tests remain passing.
- Saved Cerebras credential connection test succeeds against the real provider.
- `backups/phase_037/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase024_cerebras_provider.py::test_cerebras_provider_uses_openai_compatible_endpoint_and_schema_shape src/backend/tests/test_phase025_llm_connection_diagnostics.py::test_llm_connection_test_uses_saved_cerebras_key_without_exposing_raw_key -q` failed because provider headers lacked `Accept` and `User-Agent`.
- GREEN: same command passed with 2 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase024_cerebras_provider.py src/backend/tests/test_phase025_llm_connection_diagnostics.py src/backend/tests/test_phase035_provider_selection_cerebras_first.py -q` passed with 10 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 113 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app/features/analysis/live_provider.py src/backend/tests/test_phase024_cerebras_provider.py src/backend/tests/test_phase025_llm_connection_diagnostics.py` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app/features/analysis/live_provider.py src/backend/tests/test_phase024_cerebras_provider.py src/backend/tests/test_phase025_llm_connection_diagnostics.py backups/phase_037` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 3686 total lines.
- Live check: `cerebras-test` official SDK succeeded with the saved `.env` key, and Stuck_LLM's saved `cerebras` / `llama3.1-8b` credential connection test returned `status='ok'`.

Files changed:

- `docs/task.md`
- `docs/implement.md`
- `docs/plan.md`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/tests/test_phase024_cerebras_provider.py`
- `src/backend/tests/test_phase025_llm_connection_diagnostics.py`

## phase_036 - Minimal Quote Card In Chat

Status: completed

Objective:

- Show the first market snapshot card with only the requested essentials: stock name, symbol, price, exchange, as-of timestamp, and the existing SVG line chart.
- Reuse the same quote card in chat and analysis surfaces.
- Verify whether the saved Cerebras credential can receive a real prompt response.

Scope note:

- This phase does not add Google Finance-style key statistics such as day range, year range, market cap, P/E, dividend yield, or comparison tickers.
- This phase does not change market-data provider parsing, LLM credential storage, or backend provider behavior.

Skills used:

- `frontend-design` for the compact quote card within the existing design system.
- `provider-credentials` for safe Cerebras live-check handling without printing raw keys.
- `test-driven-development` for RED compact-card coverage before UI changes.
- `lint-and-validate` for frontend validation.

Acceptance criteria:

- Latest assistant responses with a market snapshot render stock name, symbol, price, exchange, as-of timestamp, and the SVG chart.
- The analysis panel uses the same quote card instead of a separate duplicated quote grid.
- Existing screen-reader chart data remains available.
- `backups/phase_036/` records every non-backup file modified in the phase.
- Cerebras live prompt check uses the saved local credential and reports only safe provider/model/status information.

Validation:

- RED: `cd src/frontend && npm test -- ChatShell.test.tsx` failed because the compact chart did not visibly render the stock name.
- GREEN: `cd src/frontend && npm test -- ChatShell.test.tsx AnalysisPanel.test.tsx` passed with 8 tests.
- `cd src/frontend && npm test` passed with 31 tests across 7 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/frontend/src backups/phase_036` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 3592 total lines.
- Live Cerebras check reached `https://api.cerebras.ai/v1/chat/completions` using the saved `cerebras` / `llama3.1-8b` credential, but Cerebras returned HTTP 403 Forbidden.

Files changed:

- `docs/task.md`
- `docs/implement.md`
- `src/frontend/src/features/analysis/AnalysisPanel.test.tsx`
- `src/frontend/src/features/analysis/AnalysisPanel.tsx`
- `src/frontend/src/features/analysis/MarketChart.tsx`
- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/styles.css`

## phase_035 - User-Selected LLM API Key Policy

Status: completed

Objective:

- Require a saved user API key before any LLM-assisted chat intent or live analysis call.
- Remove OpenAI/Cerebras environment-variable fallback from the LLM credential path.
- Keep provider selection open for Cerebras, OpenAI, Anthropic, and custom providers, while making Cerebras the first-tested/default setup path.
- Render missing-key setup guidance in red in the chat UI.

Scope note:

- This phase does not add a native Anthropic or Gemini live adapter.
- This phase keeps OpenAI-compatible provider test behavior for existing mocked provider tests.
- Search/news/market-data provider environment variables remain separate and unchanged.

Skills used:

- `provider-credentials` for API-key source boundaries, encrypted storage, and non-exposure.
- `llm-application-dev` for provider/model/key configuration shape, informed by DeepTutor's explicit binding/model/API-key pattern.
- `test-driven-development` for RED backend no-fallback and frontend red setup-copy tests.
- `backend-development` for credential service behavior.
- `frontend-design` for setup-needed chat treatment within the existing design system.
- `lint-and-validate` for targeted and full validation.

Acceptance criteria:

- `get_llm_credential_secret` returns `None` when no credential is saved, even if `OPENAI_API_KEY` or `CEREBRAS_API_KEY` is present.
- Saved Cerebras credentials decrypt at the provider-call edge and raw keys stay out of HTTP responses and local state files.
- Saved OpenAI credentials remain selectable for later provider testing.
- Settings defaults to Cerebras but preserves OpenAI, Anthropic, Cerebras, and custom choices.
- Missing-key setup messages include clear API-key guidance.
- Chat renders the latest setup-needed assistant message with error-red styling.
- `backups/phase_035/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase035_provider_selection_cerebras_first.py::test_environment_keys_are_ignored_when_no_user_key_is_saved -q` failed because environment LLM keys still produced a credential.
- RED: `cd src/frontend && npm test -- ChatShell.test.tsx` failed because setup-needed chat messages did not receive the red API-key class.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase035_provider_selection_cerebras_first.py src/backend/tests/test_phase019_live_market_and_news.py::test_live_llm_secret_ignores_openai_environment_key_without_saved_user_key src/backend/tests/test_phase024_cerebras_provider.py::test_saved_cerebras_secret_uses_official_defaults_without_exposing_raw_key src/backend/tests/test_phase025_llm_connection_diagnostics.py::test_cerebras_environment_key_is_ignored_without_saved_user_credential -q` passed with 7 tests and one local urllib3 LibreSSL warning.
- GREEN: `cd src/frontend && npm test -- ChatShell.test.tsx SettingsModal.test.tsx App.test.tsx api.test.ts` passed with 25 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 113 tests and one local urllib3 LibreSSL warning.
- `cd src/frontend && npm test` passed with 31 tests across 7 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app/features/credentials src/backend/app/features/analysis src/backend/tests/test_phase035_provider_selection_cerebras_first.py src/backend/tests/test_phase019_live_market_and_news.py src/backend/tests/test_phase024_cerebras_provider.py src/backend/tests/test_phase025_llm_connection_diagnostics.py` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `npm audit --audit-level=high` passed with 0 vulnerabilities.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after rerun with network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m bandit -r src/backend/app src/backend/tests -ll` could not run because Bandit is not installed in the local Python environment.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_035` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 3346 total lines.

Files changed:

- `.env.example`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `scripts/setup_credentials.py`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/app/features/analysis/service.py`
- `src/backend/app/features/credentials/schemas.py`
- `src/backend/app/features/credentials/service.py`
- `src/backend/tests/test_phase006_chat_settings_market_data.py`
- `src/backend/tests/test_phase014_conversation_language.py`
- `src/backend/tests/test_phase015_runner_and_typo_confirmation.py`
- `src/backend/tests/test_phase018_live_llm_provider.py`
- `src/backend/tests/test_phase019_live_market_and_news.py`
- `src/backend/tests/test_phase024_cerebras_provider.py`
- `src/backend/tests/test_phase025_llm_connection_diagnostics.py`
- `src/backend/tests/test_phase027_settings_language_policy.py`
- `src/backend/tests/test_phase035_provider_selection_cerebras_first.py`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/features/chat/ChatShell.tsx`
- `src/frontend/src/features/settings/SettingsModal.test.tsx`
- `src/frontend/src/features/settings/SettingsModal.tsx`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/styles.css`

## phase_034 - Prompt Grounding Contract Integration

Status: completed

Objective:

- Tighten the existing live-analysis prompt and structured-output validation around explicit source-grounding rules.
- Make allowed source IDs visible in the provider prompt and require evidence items to cite only those IDs.
- Preserve future-excluded and prompt-budget-excluded source rejection through existing included-document gates.

Scope note:

- This phase does not add provider adapters, frontend UI, source-quality scoring in production, or broad prompt rewrites.
- This phase keeps live calls mocked in tests.

Skills used:

- `test-driven-development` for RED backend prompt-contract tests before implementation.
- `backend-development` for provider contract validation.
- `llm-application-dev` for structured prompt and output guardrails.
- `stock-analysis-llm` for source-grounded analysis invariants.
- `lint-and-validate` for targeted and full backend validation.

Acceptance criteria:

- Live-analysis prompt includes an explicit allowed `source_document_id` list.
- Prompt contract states that every evidence item/key claim must cite one allowed source ID.
- Prompt contract reiterates that source text is untrusted evidence and future evidence is forbidden.
- Structured output validation rejects fabricated source IDs.
- Structured output validation rejects excluded or prompt-budget-excluded source IDs because they are not supplied to the provider.
- Tests cover valid output, fabricated source ID, excluded source ID, and weak/no evidence behavior.
- `backups/phase_034/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase034_prompt_grounding_contract.py -q` failed because the prompt lacked explicit allowed source IDs and grounding contract text.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase034_prompt_grounding_contract.py -q` passed with 4 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase021_provider_policy_reliability.py src/backend/tests/test_phase023_source_audit_trail.py src/backend/tests/test_phase034_prompt_grounding_contract.py -q` passed with 25 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 109 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app/features/analysis src/backend/app/evals src/backend/tests/test_phase034_prompt_grounding_contract.py` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m bandit -r src/backend/app src/backend/tests -ll` could not run because Bandit is not installed in the local Python environment.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_033 backups/phase_034` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 3217 total lines.

Files changed:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/app/features/analysis/service.py`
- `src/backend/tests/test_phase034_prompt_grounding_contract.py`

## phase_033 - Source Quality And Evidence Weighting Evals

Status: completed

Objective:

- Add deterministic source-quality helpers on top of the eval harness.
- Classify source reliability from trusted metadata, classify freshness from `as_of_at` and `published_at`, and compute eval-only evidence quality weights.
- Emit source-quality warnings without changing live analysis, scoring probabilities, API schemas, or frontend UI.

Scope note:

- This phase keeps quality data eval-only.
- This phase does not introduce a publisher reputation database or alter final buy/hold/sell probabilities.

Skills used:

- `test-driven-development` for RED backend quality tests before implementation.
- `backend-development` for eval package structure and schema alignment.
- `security-auditor` for metadata-over-body trust boundaries.
- `lint-and-validate` for targeted and full backend validation.

Acceptance criteria:

- Future-dated sources receive zero quality and a warning.
- Low or unknown reliability sources receive quality warnings.
- Official/fresh sources outweigh social/fresh sources when relevance is equal.
- Reliability decisions use source metadata, not title/body claims.
- Evidence quality weights combine source quality and relevance score deterministically.
- Backend tests cover official, news, social, unknown, body-claim spoofing, and future-dated cases.
- `backups/phase_033/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase033_source_quality_evals.py -q` failed on missing `classify_source_quality`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase033_source_quality_evals.py -q` passed with 5 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase031_eval_harness.py src/backend/tests/test_phase032_source_safety_evals.py src/backend/tests/test_phase033_source_quality_evals.py -q` passed with 17 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase007_analysis_pipeline.py src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase023_source_audit_trail.py src/backend/tests/test_phase031_eval_harness.py src/backend/tests/test_phase032_source_safety_evals.py src/backend/tests/test_phase033_source_quality_evals.py -q` passed with 24 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app/evals src/backend/tests/test_phase033_source_quality_evals.py` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.

Files changed:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/evals/__init__.py`
- `src/backend/app/evals/rules.py`
- `src/backend/app/evals/source_quality.py`
- `src/backend/tests/test_phase033_source_quality_evals.py`

## phase_032 - Source Safety Eval Rules

Status: completed

Objective:

- Extend the deterministic eval harness with source-safety rules for untrusted external source text.
- Flag prompt-injection phrases, structured-output/schema spoofing, official-source identity spoofing, and body-text date override attempts without calling live providers.
- Keep metadata timestamps and source-type metadata authoritative over source body claims.

Scope note:

- This phase does not change live LLM prompts, ingestion adapters, frontend UI, or analysis/scoring behavior.
- This phase does not assign source-quality weights; that remains a later phase.

Skills used:

- `test-driven-development` for RED backend safety-rule tests before implementation.
- `backend-development` for integrating the rules into the existing eval runner.
- `security-auditor` for prompt-injection and source-spoofing threat checks.
- `lint-and-validate` for targeted and full backend validation.

Acceptance criteria:

- Source text containing prompt-injection or hidden-instruction phrases is flagged.
- Source text attempting JSON/schema/output-format spoofing is flagged.
- A source title/body claiming official filing or regulator identity is flagged unless trusted metadata supports that identity.
- Body text claiming a publication date before cutoff does not override `published_at` metadata.
- Safety rules are deterministic, offline, and integrated into `evaluate_case`.
- Backend tests cover each safety rule family and preserve clean-case pass behavior.
- `backups/phase_032/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase032_source_safety_evals.py -q` failed with 4 expected missing source-safety rule IDs.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase032_source_safety_evals.py -q` passed with 6 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase031_eval_harness.py src/backend/tests/test_phase032_source_safety_evals.py -q` passed with 12 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase007_analysis_pipeline.py src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase023_source_audit_trail.py src/backend/tests/test_phase031_eval_harness.py src/backend/tests/test_phase032_source_safety_evals.py -q` passed with 19 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 100 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m bandit -r src/backend/app src/backend/tests -ll` could not run because Bandit is not installed in the local Python environment.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_032` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 3043 total lines.

Files changed:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/evals/rules.py`
- `src/backend/tests/test_phase032_source_safety_evals.py`

## phase_031 - Deterministic Analysis Eval Harness

Status: completed

Objective:

- Add a backend-only deterministic evaluation harness for analysis and scoring outputs.
- Validate source cutoff, source grounding, prompt-document eligibility, probability sums, and confidence/evidence consistency without live LLM, quote, or search calls.
- Establish a stable foundation for later source-safety and source-quality eval rules from `CODEXCODING`.

Scope note:

- This phase does not change live analysis behavior, provider calls, frontend UI, ingestion adapters, or scoring formulas.
- This phase does not add prompt-injection pattern checks beyond existing cutoff and grounding invariants; that remains a later phase.

Skills used:

- `test-driven-development` for RED backend eval-harness tests before implementation.
- `backend-development` for backend package structure and schema alignment.
- `lint-and-validate` for targeted and full backend validation.

Acceptance criteria:

- Eval rules run offline against existing `AnalysisResponse` and `ScoreResponse` objects.
- A source published after `as_of_at` fails if included, used in prompt document IDs, or cited by evidence.
- Evidence and score drivers must cite existing included analysis source documents.
- Buy/hold/sell probabilities must stay in range and sum to 100 for scored outputs.
- High confidence without evidence is flagged.
- Backend tests cover passing evals and each critical failure class.
- `backups/phase_031/` records every non-backup file modified in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase031_eval_harness.py -q` failed on missing `app.evals`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase031_eval_harness.py -q` passed with 6 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase007_analysis_pipeline.py src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase023_source_audit_trail.py src/backend/tests/test_phase031_eval_harness.py -q` passed with 13 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 94 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m bandit -r src/backend/app src/backend/tests -ll` could not run because Bandit is not installed in the local Python environment.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_031` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 2951 total lines.

Files changed:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/evals/__init__.py`
- `src/backend/app/evals/runner.py`
- `src/backend/app/evals/rules.py`
- `src/backend/app/evals/types.py`
- `src/backend/tests/test_phase031_eval_harness.py`

## phase_027 - Settings-Language Response Policy

Status: completed

Objective:

- Make backend-generated assistant copy and LLM prompt language follow the selected UI language from Settings before falling back to message-language detection.
- Pass the selected UI language with chat requests without persisting raw UI preferences into analysis records.
- Preserve existing Korean/English message-language fallback when no explicit response language is supplied.

Scope note:

- This phase does not change translation copy in the frontend beyond request plumbing.
- This phase does not redesign settings UI.
- This phase does not change provider credentials, market data, chart UX, or scoring.

Skills used:

- `test-driven-development` for RED backend/frontend language-policy tests.
- `backend-development` for conversation request contract changes.
- `llm-application-dev` for prompt language precedence.
- `stock-analysis-llm` for setup/provider error copy and LLM prompt invariants.
- `frontend-design` for keeping Settings language behavior aligned without visual churn.
- `lint-and-validate` for targeted and full validation.

Acceptance criteria:

- `ConversationCommand` accepts an optional explicit response language.
- Backend assistant follow-up, setup-needed, and provider-error copy use explicit response language before message-language detection.
- Chat intent and live-analysis LLM prompts use explicit response language when supplied.
- Existing message-language fallback behavior remains unchanged when no explicit language is supplied.
- Frontend chat requests include the active Settings modal UI language.
- Backend and frontend tests cover request mapping and response-language precedence.
- `backups/phase_027/` records every non-backup file modified or created in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase027_settings_language_policy.py -q` failed with 3 expected failures before implementation.
- RED: `cd src/frontend && npm test -- api.test.ts ChatShell.test.tsx App.test.tsx` failed on missing `responseLanguage` request plumbing.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase027_settings_language_policy.py -q` passed with 3 tests and one local urllib3 LibreSSL warning.
- GREEN: `cd src/frontend && npm test -- api.test.ts ChatShell.test.tsx App.test.tsx` passed with 19 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase026_generative_chat_orchestration.py src/backend/tests/test_phase027_settings_language_policy.py -q` passed with 20 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 88 tests and one local urllib3 LibreSSL warning.
- `cd src/frontend && npm test` passed with 30 tests across 7 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `npm audit --audit-level=high` passed with 0 vulnerabilities.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m bandit -r src/backend/app src/backend/tests -ll` could not run because Bandit is not installed in the local Python environment.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_027` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 2861 total lines.

Files changed:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/conversations/schemas.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase027_settings_language_policy.py`
- `src/frontend/src/App.tsx`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/features/chat/ChatShell.tsx`
- `src/frontend/src/features/chat/ChatShell.test.tsx`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/types.ts`

## phase_026 - Generative Chat Orchestration

Status: completed

Objective:

- Let a configured LLM interpret chat intent, stock references, horizon, analysis mode, source hints, and follow-up needs through structured JSON before deterministic validation.
- Preserve deterministic stock resolution, typo confirmation, horizon validation, credential handling, and `as_of_at` evidence gates as the authority before analysis runs.
- Fall back to the existing deterministic parser when no LLM credential is configured, the provider cannot run orchestration, or structured intent output is invalid.
- Keep raw API keys, provider response bodies, and prompt/internal details out of conversation API responses.

Scope note:

- This phase uses source hints only to select known source adapter families; direct user URL/raw-text ingestion remains a later ingestion phase.
- This phase does not change scoring probabilities or chart UX.
- This phase does not implement the settings-language response policy; that remains `phase_027`.

Skills used:

- `test-driven-development` for RED backend orchestration tests before implementation.
- `backend-development` for conversation-service and provider interface changes.
- `llm-application-dev` for structured intent extraction prompt and schema design.
- `stock-analysis-llm` for credential boundaries, deterministic fallback, and source/evidence invariants.
- `security-auditor` for prompt-injection and raw-secret exposure review.
- `lint-and-validate` for targeted and full validation.

Acceptance criteria:

- Chat can use a configured OpenAI-compatible provider to parse a non-literal stock reference into a deterministic market quote before live analysis.
- Structured chat intent extraction supports stock query, market, horizon, analysis mode, source hints, and follow-up flags.
- LLM-provided stock and horizon values are validated through existing deterministic quote and enum gates before analysis is allowed.
- Existing typo-confirmation behavior cannot be bypassed by LLM intent output.
- Recognized source hints can narrow source collection to known adapters without fetching arbitrary user-provided URLs.
- Missing credentials, unsupported providers, provider errors, and malformed intent output fall back to deterministic parsing without exposing raw keys or provider internals.
- Backend tests cover successful LLM-assisted orchestration, deterministic validation blocking an unresolved LLM stock, and source-hint adapter selection.
- `backups/phase_026/` records every non-backup file modified or created in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase026_generative_chat_orchestration.py -q` failed with 3 expected orchestration failures before implementation.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase026_generative_chat_orchestration.py -q` passed with 4 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase021_provider_policy_reliability.py src/backend/tests/test_phase023_source_audit_trail.py src/backend/tests/test_phase025_llm_connection_diagnostics.py src/backend/tests/test_phase026_generative_chat_orchestration.py -q` passed with 38 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 85 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `cd src/frontend && npm test` passed with 29 tests across 7 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m bandit -r src/backend/app src/backend/tests -ll` could not run because Bandit is not installed in the local Python environment.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_026` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 2742 total lines.

Files changed:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase026_generative_chat_orchestration.py`

## phase_025 - LLM Provider Connection Diagnostics

Status: completed

Objective:

- Let users test the saved or environment-backed LLM provider connection without running a full stock analysis.
- Keep Cerebras available as a continuing comparison provider, not a one-off test path.
- Update the Cerebras local default model to the user's available production model, `llama3.1-8b`.
- Preserve raw-key non-exposure and avoid returning provider response bodies or low-level network details.
- Record the next implementation phases for generative chat, language policy, SerpApi refinement, chart UX, and E2E validation.

Scope note:

- This phase adds a connection-test endpoint and Settings modal control, but does not call a live provider during automated tests.
- This phase does not implement full generative chat orchestration; that is recorded as `phase_026`.
- This phase does not redesign charts or market data routing; those are recorded as `phase_028` and `phase_029`.

Future phases recorded:

- `phase_026`: Generative chat orchestration with structured intent extraction and deterministic validation gates.
- `phase_027`: Settings-language response policy across backend copy and LLM prompts.
- `phase_028`: SerpApi Google Finance refinement for market-qualified tickers, windows, and source/news handling.
- `phase_029`: Market chart UX refresh with period controls, axes, source/time labels, and better quote-line semantics.
- `phase_030`: End-to-end validation across provider diagnostics, chat, language, SerpApi, and chart flows.

Skills used:

- `test-driven-development` for RED backend/frontend connection-diagnostic tests.
- `backend-development` for the credential diagnostic API and provider boundary reuse.
- `provider-credentials` for encrypted-key and raw-secret response boundaries.
- `stock-analysis-llm` for provider error mapping and OpenAI-compatible call separation.
- `frontend-design` for Settings modal test-control placement and status rendering.
- `lint-and-validate` for targeted and full validation.

Acceptance criteria:

- `POST /credentials/llm/test` returns `setup_needed` when no saved or environment-backed credential exists.
- `POST /credentials/llm/test` tests the active saved credential through the existing OpenAI-compatible base URL policy and `/chat/completions` path.
- Connection-test payloads do not include analysis evidence, structured-output schemas, or raw API keys.
- Provider auth failures map to `provider_error` with `error_code="auth_error"` and user-safe copy.
- Successful connection tests return provider, model, base URL, key source, and a safe success message.
- Cerebras environment fallback defaults to `llama3.1-8b` unless `CEREBRAS_MODEL` is explicitly set.
- The Settings modal can run a saved-key connection test and display safe diagnostic messages.
- Cerebras Settings model entry references the currently available comparison models: `llama3.1-8b` and `qwen-3-235b-a22b-instruct-2507`.
- Backend and frontend tests cover the new endpoint, model default, API mapping, and UI rendering.
- `backups/phase_025/` records every non-backup file modified or created in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase025_llm_connection_diagnostics.py -q` failed on missing `/credentials/llm/test` and old Cerebras default model.
- RED: `cd src/frontend && npm test -- api.test.ts SettingsModal.test.tsx` failed on missing `testLlmCredential` API export and missing Settings modal test button.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase025_llm_connection_diagnostics.py -q` passed with 4 tests.
- GREEN: `cd src/frontend && npm test -- api.test.ts SettingsModal.test.tsx` passed with 12 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 81 tests and one local urllib3 LibreSSL warning.
- `cd src/frontend && npm test` passed with 29 tests across 7 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `npm audit --audit-level=high` passed with 0 vulnerabilities.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after rerun with network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m bandit -r src/backend/app src/backend/tests -ll` could not run because Bandit is not installed in the local Python environment.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_025` returned no matches.
- Secret sentinel grep over app code, frontend output, local state, docs, and phase_025 backups found no phase_025 raw test-key occurrences.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 2637 total lines.

Files changed:

- `.env.example`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/app/features/credentials/schemas.py`
- `src/backend/app/features/credentials/service.py`
- `src/backend/app/features/credentials/router.py`
- `src/backend/app/shared/dependencies.py`
- `src/backend/tests/test_phase025_llm_connection_diagnostics.py`
- `src/frontend/src/App.tsx`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/features/settings/SettingsModal.tsx`
- `src/frontend/src/features/settings/SettingsModal.test.tsx`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/styles.css`

## phase_024 - Cerebras OpenAI-Compatible Test Provider

Status: completed

Objective:

- Let local test runs use `CEREBRAS_API_KEY` as an OpenAI-compatible live LLM fallback.
- Use Cerebras' official OpenAI-compatible base URL by default.
- Preserve raw-key non-exposure boundaries.
- Keep UI-saved credentials higher priority than environment fallback credentials.
- Keep OpenAI environment fallback behavior unchanged.

Scope note:

- This phase does not add a Cerebras-specific SDK dependency.
- This phase does not perform a real external Cerebras API call during automated tests.
- Hosted mode still uses existing provider egress policy behavior for non-OpenAI endpoints.

Skills used:

- `test-driven-development` for RED provider/env/UI tests.
- `backend-development` for credential fallback and provider payload behavior.
- `stock-analysis-llm` for structured live-analysis output compatibility.
- `security-auditor` for raw-key boundaries and server-side env usage.
- `frontend-design` for settings provider selection.
- `lint-and-validate` for backend/frontend validation.

Acceptance criteria:

- `CEREBRAS_API_KEY` can provide a live LLM credential when no UI-saved credential or OpenAI env fallback exists.
- Default Cerebras model is `gpt-oss-120b`, overrideable with `CEREBRAS_MODEL`.
- Default Cerebras base URL is `https://api.cerebras.ai/v1`, overrideable with `CEREBRAS_BASE_URL`.
- Cerebras requests use the existing OpenAI-compatible `/chat/completions` path.
- Cerebras structured-output payload avoids array `minItems`/`maxItems` constraints so it is compatible with Cerebras structured-output requirements.
- Raw Cerebras keys are not persisted or returned.
- Settings UI can select `Cerebras` as a credential provider.
- `.env.example` documents Cerebras environment variables.
- Backend and frontend tests cover the new behavior.
- `backups/phase_024/` records every non-backup file modified or created in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase024_cerebras_provider.py -q` failed on missing env fallback and Cerebras schema shaping.
- RED: `cd src/frontend && npm test -- SettingsModal.test.tsx` failed on missing Cerebras provider option.
- GREEN: targeted backend and frontend tests passed after implementation.

Files changed:

- `.env.example`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/credentials/schemas.py`
- `src/backend/app/features/credentials/service.py`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/tests/test_phase006_chat_settings_market_data.py`
- `src/backend/tests/test_phase014_conversation_language.py`
- `src/backend/tests/test_phase015_runner_and_typo_confirmation.py`
- `src/backend/tests/test_phase018_live_llm_provider.py`
- `src/backend/tests/test_phase024_cerebras_provider.py`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/features/settings/SettingsModal.tsx`
- `src/frontend/src/features/settings/SettingsModal.test.tsx`

## phase_023 - Evidence Source Quality And Audit Trail

Status: completed

Objective:

- Make analysis source handling auditable from API response through the Analysis panel.
- Preserve source-level metadata from ingestion into analysis decisions.
- Carry safe ingestion/source warning codes into analysis results without exposing raw keys, source body text, or provider internals.
- Show users which sources were included, which were excluded, and why.
- Keep `as_of_at` future-evidence exclusion and prompt-budget exclusion visible in source audit summaries.

Scope note:

- This phase does not add new external source adapters or crawler behavior.
- This phase does not implement SQLite conversation persistence.
- This phase does not use price chart data as evidence.

Skills used:

- `test-driven-development` for RED backend/frontend tests before implementation.
- `backend-development` for API schema and service contract changes.
- `stock-analysis-llm` for source-grounded prompt and cutoff invariants.
- `frontend-design` for compact, scannable Analysis panel rendering.
- `security-auditor` for safe warning/metadata exposure.
- `lint-and-validate` for regression and static validation.

Acceptance criteria:

- `AnalysisRequestCommand` accepts safe source warning codes from source collection.
- Source documents preserve adapter, relevance score, fetched timestamp, language, and safety flags through analysis decisions.
- `AnalysisResponse` includes a `source_audit` summary with safe source warnings, included counts by source type, excluded counts by reason, and prompt document IDs.
- Future evidence remains excluded from provider prompt context and appears with `published_after_as_of_at`.
- Prompt-budget-excluded sources appear with `prompt_budget`.
- Chat live analysis passes source collection warnings into analysis results.
- Frontend API mapping exposes source audit metadata without mapping raw source body text into UI types.
- The Analysis panel renders included/excluded source counts, warning codes, source titles, prompt-used state, and exclusion reasons.
- Backend and frontend tests cover the new audit trail behavior.
- `backups/phase_023/` records every non-backup file modified or created in the phase.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase023_source_audit_trail.py -q` failed on missing `source_audit`.
- RED: `cd src/frontend && npm test -- api.test.ts AnalysisPanel.test.tsx` failed on missing source audit mapping/rendering.
- GREEN: targeted backend and frontend tests passed after implementation.

Files changed:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/analysis/schemas.py`
- `src/backend/app/features/analysis/service.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/tests/test_phase023_source_audit_trail.py`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/features/analysis/AnalysisPanel.tsx`
- `src/frontend/src/features/analysis/AnalysisPanel.test.tsx`
- `src/frontend/src/styles.css`

## phase_022 - US Market Data Provider With SerpApi Google Finance

Status: completed

Objective:

- Add a US-first market-data provider path using SerpApi Google Finance.
- Use `SERPAPI_API_KEY` from the environment; do not read, print, persist, or return the raw key.
- Prefer SerpApi for US quotes when the key is configured, then fall back to FinanceDataReader, then seeded local fixtures.
- Treat SerpApi chart data as quote/line-chart support, not authoritative OHLC/backtest data.
- Keep Korean market data behavior unchanged.

Scope note:

- The earlier SQLite conversation-store idea is intentionally out of scope for this phase.
- Conversation persistence/orchestration can be revisited later as a separate phase.

Completed summary:

- US quotes now try SerpApi Google Finance first only when `SERPAPI_API_KEY` is configured.
- SerpApi summary and graph payloads map to `MarketQuote` and line-chart `MarketBar` values without returning the raw key.
- SerpApi errors or malformed data fall through to FinanceDataReader and then seeded fixtures.
- Korean market-data behavior remains on the existing FinanceDataReader/seeded fallback path.

Skills used:

- `test-driven-development` for finishing from the existing RED backend tests.
- `backend-development` for provider parsing, fallback ordering, and API behavior.
- `security-auditor` or `provider-credentials` for raw-key non-exposure boundaries.
- `lint-and-validate` for targeted backend tests and regression validation.

Acceptance criteria:

- `GET /market-data/quotes/US/{symbol}` calls SerpApi Google Finance first when `SERPAPI_API_KEY` is present.
- SerpApi requests use `engine=google_finance` and a query shaped like `{SYMBOL}:{EXCHANGE}`, defaulting common US symbols to `NASDAQ` where needed.
- SerpApi summary fields map into `MarketQuote` without exposing the API key.
- SerpApi graph price points map into `chart_bars` for line-chart rendering. Because SerpApi graph points are not full OHLC candles, generated bars must use the point price for open/high/low/close and must not be treated as backtest-grade OHLC data.
- SerpApi failures, malformed responses, missing package errors, or quota/provider errors fall through to the existing FinanceDataReader path.
- If both SerpApi and FinanceDataReader fail, the existing seeded fallback remains available.
- Missing `SERPAPI_API_KEY` skips SerpApi entirely.
- Safe warning/error strings may use `missing_credential:serpapi_google_finance` or `provider_error:serpapi_google_finance`, but public API responses must not contain the raw key or provider internals.
- Backend tests cover SerpApi preference, fallback, and no-key skip behavior.
- `.env.example` documents `SERPAPI_API_KEY`.
- `backups/phase_022/` records every non-backup file modified or created in the phase.

Initial RED test handoff:

- `src/backend/tests/test_phase022_us_market_data_provider.py` has been added.
- Initial RED command: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py -q`.
- Initial RED result: 1 failure, 2 passing. The failing test expected `/market-data/quotes/US/GOOGL` to return a SerpApi-backed quote, but the previous implementation returned 404 because no SerpApi provider existed yet.

Suggested implementation order:

1. Back up `.env.example`, `docs/plan.md`, `docs/task.md`, `docs/implement.md`, `src/backend/app/features/market_data/service.py`, and the new phase test under `backups/phase_022/`.
2. Add `SERPAPI_API_KEY=` to `.env.example`.
3. Add a small `_search_serpapi_google_finance` wrapper so tests can monkeypatch the provider call.
4. Add SerpApi response parsing helpers for summary price, previous close, exchange, timestamp, and graph price points.
5. Update `get_quote` so US quotes use SerpApi first only when `SERPAPI_API_KEY` is configured.
6. Re-run the phase_022 targeted test, then relevant market/conversation regression tests.
7. Run compileall, Ruff, MyPy if available, `git diff --check`, and a secret grep for the test sentinel key.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `.env.example`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase022_us_market_data_provider.py`

## phase_021 - OpenAI Provider Policy, DNS Safety, And Live Call Reliability

Status: completed

Objective:

- Harden the OpenAI-compatible live provider path before adding additional live vendors.
- Make hosted provider policy explicit for official OpenAI, custom public endpoints, and local/private development endpoints.
- Detect DNS answers that resolve provider hostnames to private, loopback, link-local, metadata, or otherwise unsafe IP ranges.
- Add bounded retry, timeout, and prompt/source budget controls to live provider calls.
- Keep Anthropic credentials storable but clearly marked as not yet supported for live analysis.

Required skills for next agent:

- `test-driven-development` for adding failing provider-policy, DNS, retry, timeout, and budget tests first.
- `backend-development` for provider policy wiring, runtime config, and service-level prompt budget behavior.
- `provider-credentials` for custom provider opt-in and raw-secret non-exposure boundaries.
- `stock-analysis-llm` for live prompt budget and provider error normalization.
- `security-auditor` for DNS rebinding, SSRF, hosted egress policy, and local-provider exceptions.
- `frontend-design` and `web-design-guidelines` for any settings-modal provider status copy.
- `lint-and-validate` for backend, frontend, and docs validation before handoff.

Provider policy matrix:

| Provider mode | Local default | Hosted default | Explicit opt-in |
|---|---:|---:|---|
| OpenAI official endpoint | Allowed | Allowed | None |
| OpenAI with non-official base URL | Allowed only when public HTTPS and DNS-safe | Allowed only when allowlisted | `STUCK_LLM_PROVIDER_EGRESS_ALLOWLIST` in hosted mode |
| Custom public OpenAI-compatible endpoint | Denied | Denied | `STUCK_LLM_ALLOW_CUSTOM_PROVIDER=true`; hosted also requires allowlist |
| Custom localhost/private endpoint | Denied | Denied | Local development only with `STUCK_LLM_ALLOW_CUSTOM_PROVIDER=true` and `STUCK_LLM_ALLOW_PRIVATE_BASE_URL=true` |
| Metadata/link-local/credential-bearing URLs | Denied | Denied | No opt-in |
| Anthropic | Credential storage only | Credential storage only | Live adapter deferred to a later phase |

Acceptance criteria:

- OpenAI official base URL remains allowed without requiring a DNS lookup in local tests.
- Non-official provider hostnames are resolved before outbound calls; any unsafe DNS answer is rejected before the HTTP client is called.
- Credential-bearing URLs, query strings, fragments, metadata hosts/IPs, loopback/private/link-local IPs, `.local`, and `.internal` remain rejected by default.
- `custom` provider calls are rejected unless `STUCK_LLM_ALLOW_CUSTOM_PROVIDER=true`.
- Local/private custom endpoints are allowed only in non-hosted mode when both custom-provider and private-base-url flags are enabled.
- Hosted mode rejects custom providers unless their normalized base URL is present in `STUCK_LLM_PROVIDER_EGRESS_ALLOWLIST`.
- Hosted mode never allows private/local custom endpoints, even if the local-private flag is set.
- Provider calls retry only transient 429/503 responses with limited exponential backoff and do not retry auth/client validation failures.
- Provider call timeout is explicit and keeps retries within a bounded wall-time budget.
- Live prompt construction enforces source-count, source-excerpt, and total prompt-context budgets; budget-excluded sources are marked with `exclusion_reason="prompt_budget"`.
- Provider error responses remain user-safe and do not expose raw API keys, base URLs, response bodies, or low-level network details.
- Settings or docs make clear that Anthropic credentials can be stored but live Anthropic analysis is still unsupported.
- Backend tests cover DNS blocking, custom opt-in, hosted allowlist behavior, retry/no-retry behavior, timeout mapping, and prompt budget exclusion.
- Frontend tests cover any settings-modal provider status copy.
- `backups/phase_021/` records every non-backup file modified or created in the phase.

Suggested implementation order:

1. Add failing backend tests for DNS resolution blocking, custom-provider opt-in, hosted allowlist behavior, transient retry, timeout, and prompt budget exclusion.
2. Add a failing frontend test if the settings modal copy changes for Anthropic support status.
3. Extend runtime config with custom-provider, private-base-url, and provider-egress allowlist flags.
4. Add provider base URL policy validation with DNS resolution and safe dev-only local exceptions.
5. Add retry/backoff and explicit timeout controls around the OpenAI-compatible HTTP POST.
6. Add live prompt budget filtering before provider calls.
7. Update settings copy and environment examples.
8. Run targeted tests, full backend/frontend validation, design lint, secret checks, and diff checks.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `.env.example`
- `src/backend/app/shared/runtime_config.py`
- `src/backend/app/main.py`
- `src/backend/app/features/analysis/live_provider.py`
- `src/backend/app/features/analysis/service.py`
- `src/backend/tests/test_phase021_provider_policy_reliability.py`
- `src/frontend/src/features/settings/SettingsModal.tsx`
- `src/frontend/src/features/settings/SettingsModal.test.tsx`
- `src/frontend/src/shared/i18n.ts`

## phase_020 - Review-Filtered Security, Concurrency, A11y, And CI Hardening

Status: completed

Objective:

- Address the valid Claude-review findings without carrying forward overstated or false-positive items.
- Harden live LLM prompt context with per-source delimiters and escaping for untrusted source text.
- Reject unsafe LLM provider base URLs before constructing outbound provider endpoints.
- Preserve concurrent conversation appends against stale local-state writes.
- Improve settings-modal keyboard/backdrop behavior, market-chart data accessibility, and frontend request abort handling.
- Add CI coverage and clean up root design-lint package metadata.

Required skills for next agent:

- `test-driven-development` for adding failing security, concurrency, and accessibility tests first.
- `backend-development` for provider URL validation and local state/conversation update behavior.
- `stock-analysis-llm` and `security-auditor` for prompt delimiter and SSRF boundaries.
- `frontend-design` and `web-design-guidelines` for modal focus handling and chart alternatives.
- `lint-and-validate` for backend, frontend, CI, and design-system validation.

Acceptance criteria:

- Live LLM prompt context wraps each source in explicit untrusted-source delimiters and escapes delimiter-like source content.
- OpenAI-compatible provider calls reject non-HTTPS, loopback, private, link-local, metadata, or credential-bearing base URLs without calling the injected HTTP client.
- Provider base URL failures map to user-safe provider errors and never expose raw provider details.
- Concurrent appends to the same conversation preserve both appended message pairs instead of overwriting with a stale response.
- Local state updates use a file-lock-aware atomic write path with unique temporary files.
- Settings modal traps tab focus, closes on Escape, restores prior focus on close, and closes on backdrop click only outside the dialog.
- Market charts expose a screen-reader-accessible data table in addition to the SVG line.
- Frontend API requests include an AbortController-backed timeout and clear error mapping for aborted requests.
- GitHub Actions CI runs backend tests, frontend tests/typecheck/build, and design lint.
- Root `package.json`/`package-lock.json` are explicit design-lint workspace metadata, and `DESIGN.md` remains a first-class project file.
- Backend and frontend unit tests cover the new behavior.
- `backups/phase_020/` records every non-backup file modified or created in the phase.

Suggested implementation order:

1. Add failing backend tests for unsafe provider base URLs, prompt delimiter escaping, and concurrent conversation appends.
2. Add failing frontend tests for modal focus/backdrop behavior, chart data-table access, and API request timeout abort.
3. Harden live prompt construction and provider endpoint validation.
4. Merge concurrent conversation appends against the latest state and strengthen state-store file writes.
5. Implement modal focus handling, backdrop close, chart table, and request timeout support.
6. Add CI workflow and root package metadata cleanup.
7. Run targeted tests, full backend/frontend validation, design lint, and diff checks.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `package.json`
- `package-lock.json`
- `.github/workflows/ci.yml`
- `src/backend/app/features/analysis/**`
- `src/backend/app/features/conversations/service.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/tests/test_phase020_security_and_concurrency.py`
- `src/frontend/src/features/settings/**`
- `src/frontend/src/features/analysis/**`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/api.test.ts`
- `src/frontend/src/styles.css`

## phase_019 - Live Market Data And Search Ingestion

Status: completed

Objective:

- Replace seeded-only market snapshots with a FinanceDataReader-backed quote and daily chart path for Korean and US stocks where supported.
- Keep seeded quotes as a deterministic fallback for local tests and missing provider dependencies.
- Add Naver News, Tavily, and GNews ingestion adapters using environment-provided API keys without returning or logging secrets.
- Feed collected external news/search documents into the existing phase_018 live LLM analysis path while preserving strict `as_of_at` evidence cutoff behavior.
- Render compact price charts in chat messages and fuller market snapshot charts in the analysis panel.
- Keep price bars and chart data separate from evidence documents and LLM prompt content.

Required skills for next agent:

- `test-driven-development` for locking live-data behavior with mocked providers first.
- `backend-development` for provider adapters, API schemas, and service wiring.
- `stock-analysis-llm` for evidence cutoff, untrusted source text, and LLM handoff boundaries.
- `provider-credentials` and `security-auditor` for API-key handling and secret-leak checks.
- `frontend-design` for dense chart UX in chat and snapshot surfaces.
- `lint-and-validate` for backend/frontend validation before handoff.

Acceptance criteria:

- `GET /market-data/quotes/{market}/{symbol}` can return FinanceDataReader latest available close, previous close, change percent, and daily chart bars.
- Market data gracefully falls back to seeded local fixtures when FinanceDataReader is unavailable or returns no usable rows.
- Source collection supports `naver_news`, `tavily_news`, and `gnews_news` adapters in addition to the seeded adapters.
- Missing external API credentials return safe warning codes rather than stack traces or raw key values.
- External source documents carry `external_api` and `untrusted_source_text` safety flags.
- Chat-ready analysis uses the live search/news adapters plus deterministic seeded fallback sources.
- LLM prompts continue to receive only source documents, never price chart bars.
- Frontend API types map chart bars and change fields from backend responses.
- Chat assistant responses can show a compact price chart when a market snapshot is present.
- The analysis panel shows price, percent change, provider/source, and an expanded price chart.
- `run-all.sh` loads root `.env` values for local data-provider keys without printing them.
- Backend and frontend unit tests cover the new provider adapters, warning behavior, and chart rendering.
- `backups/phase_019/` records every non-backup file modified or created in the phase.

Suggested implementation order:

1. Add failing backend tests for FinanceDataReader quote/chart parsing and Naver/Tavily/GNews adapter parsing.
2. Add failing frontend tests for chat and analysis-panel chart rendering.
3. Extend market-data schemas and service fallback logic.
4. Extend ingestion schemas and service adapters with safe credential handling.
5. Wire chat collection defaults to live adapters plus seeded fallback evidence.
6. Extend frontend API mapping, types, chart component, and CSS.
7. Add `.env` loading to the local runner and update provider-key examples.
8. Run backend, frontend, type, build, script, and secret-leak validation.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `.env.example`
- `run-all.sh`
- `src/backend/pyproject.toml`
- `src/backend/app/features/market_data/**`
- `src/backend/app/features/ingestion/**`
- `src/backend/app/features/conversations/**`
- `src/backend/tests/test_phase019_live_market_and_news.py`
- `src/frontend/src/shared/**`
- `src/frontend/src/features/chat/**`
- `src/frontend/src/features/analysis/**`
- `src/frontend/src/styles.css`

## phase_018 - Live LLM Provider Analysis Integration

Status: completed

Objective:

- Connect the encrypted local BYOK credential flow to a real live LLM analysis path.
- Add a narrow backend provider interface with OpenAI first and Anthropic/custom-compatible boundaries preserved.
- Let chat-ready analysis requests call the live provider when credentials exist, while keeping deterministic local providers for tests and fallback.
- Return source-grounded assistant answers in the user's language with auditable evidence, `as_of_at` cutoff safety, and explicit setup-needed responses when credentials are missing.
- Keep scoring and backtest data separated from LLM evidence analysis.

Required skills for next agent:

- `stock-analysis-llm` for source-grounded provider calls and strict evidence cutoff behavior.
- `llm-application-dev` for prompt shape, structured output parsing, and provider error handling.
- `provider-credentials` for decrypting BYOK credentials only at the live-call edge.
- `api-design-principles` and `backend-development` for route/service contracts.
- `security-auditor` for prompt injection, key handling, logs, and external-provider data exposure.
- `test-driven-development`, `systematic-debugging`, and `lint-and-validate` throughout.

Acceptance criteria:

- Backend defines a small `LlmAnalysisProvider`-style interface separate from deterministic analysis logic.
- OpenAI-compatible live provider support uses the stored credential provider/model/base URL/API key and never logs or returns raw keys.
- Missing local credentials produce a Korean or English setup-needed assistant message instead of a failed stack trace or deterministic fake live result.
- Provider timeouts, malformed structured output, rate limits, and authentication failures map to explicit statuses/errors that the chat UI can show.
- Analysis prompts include only eligible source documents with `published_at <= as_of_at`; equality remains included.
- Post-`as_of_at` evidence, PnL/backtest prices, and credential metadata are excluded from the prompt.
- Source document text is treated as untrusted evidence and cannot override system instructions.
- The live result produces a structured summary/evidence handoff that scoring can consume without changing the scoring model in this phase.
- Korean user messages receive Korean live/setup/error assistant text; English messages receive English text.
- Frontend chat displays missing-credential and provider-error messages cleanly without exposing internal details.
- Unit tests cover missing credentials, provider success with a mocked client, provider failure mapping, language behavior, and cutoff filtering.
- Any opt-in integration test is skipped by default unless explicit environment variables are present.
- `backups/phase_018/` records every non-backup file modified or created in the phase.

Suggested implementation order:

1. Add failing backend tests for missing credential, mocked provider success, malformed output, provider auth/rate-limit errors, and `as_of_at` cutoff equality.
2. Add the provider interface and OpenAI-compatible adapter behind `src/backend/app/features/analysis` or a clearly shared backend provider module.
3. Reuse the phase_016 credential service to decrypt keys only inside the live provider call path.
4. Add prompt/structured-output parsing with explicit schema validation and deterministic fallback kept out of the live path.
5. Wire chat-ready requests to live analysis only when credentials are configured.
6. Add/adjust frontend tests for setup-needed and provider-error chat rendering.
7. Run backend, frontend, type, build, audit, and smoke validation.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/analysis/**`
- `src/backend/app/features/conversations/**`
- `src/backend/app/features/credentials/**` only if an API/service boundary needs a small read helper
- `src/backend/app/shared/**`
- `src/backend/tests/test_phase018_live_llm_provider.py`
- `src/frontend/src/features/chat/**`
- `src/frontend/src/shared/**`

## phase_017 - Settings Modal And Workspace Navigation

Status: completed

Objective:

- Move language/theme/model credential setup into a ChatGPT-style settings modal.
- Keep analysis defaults, snapshot, and backtest as sidebar navigation views instead of sidebar cards.
- Wire the frontend to the phase_016 credential API with masked-key responses and raw-key save/delete only.
- Preserve the chat workspace as the default first screen.

Acceptance criteria:

- The left rail exposes Chat, Analysis, Snapshot, and Backtest navigation buttons.
- Chat view shows only the conversation workspace and composer.
- Analysis view shows analysis mode, default market, and default horizon preferences.
- Snapshot view shows the current market snapshot.
- Backtest view shows the PnL simulation panel.
- Settings opens as a modal/panel with left categories for General, Model, and Security.
- General settings include language and theme.
- Model settings include provider, model, base URL, API key entry, masked key status, save, and delete.
- Security settings show credential storage/key-source status without exposing raw API keys.
- Frontend API helpers support fetching, saving, and deleting LLM credentials.
- Frontend tests cover navigation split, modal settings, credential save/delete, and existing analysis/backtest flows.
- `backups/phase_017/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/frontend/src/App.tsx`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/styles.css`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/features/settings/**`
- `src/frontend/src/features/analysis/**`
- `src/frontend/src/features/backtest/**`

## phase_016 - Local BYOK Credential Backend And CLI Setup

Status: completed

Objective:

- Add project-local skills for provider credentials and stock-analysis LLM workflows.
- Update orchestration skill routing for BYOK credentials, live LLM providers, and frontend settings work.
- Add encrypted local storage for user-provided LLM API keys without login.
- Support OpenAI, Anthropic, and OpenAI-compatible custom provider configuration.
- Add a developer CLI setup command for entering provider/model/base URL/API key.
- Keep raw API keys out of API responses and local state files.
- Fix hosted API-key guard behavior for empty configured keys.

Acceptance criteria:

- `.codex/skills/provider-credentials/SKILL.md` and `.codex/skills/stock-analysis-llm/SKILL.md` exist with concise project-specific workflows.
- `docs/agent-workflows/orchestration.md` routes BYOK credential, setup, and live LLM work to the right skills.
- `PUT /credentials/llm` saves provider, model, base URL, and encrypted API key.
- `GET /credentials/llm` returns only provider metadata, configured state, key source, and masked key text.
- `DELETE /credentials/llm` removes the stored credential.
- The raw API key is not present in API responses or the JSON state file.
- `STUCK_LLM_CREDENTIAL_KEY` is used when present; otherwise a local development credential key is generated under `.local`.
- `custom` provider credentials require an explicit base URL.
- `scripts/setup_credentials.py` can save credentials non-interactively for developer setup.
- Empty hosted API keys do not authenticate protected requests.
- Backend unit tests cover encrypted storage, masking, provider validation, CLI setup, and API-key guard behavior.
- `backups/phase_016/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/orchestration.md`
- `.env.example`
- `.codex/skills/provider-credentials/SKILL.md`
- `.codex/skills/stock-analysis-llm/SKILL.md`
- `scripts/setup_credentials.py`
- `src/backend/pyproject.toml`
- `src/backend/app/main.py`
- `src/backend/app/shared/runtime_config.py`
- `src/backend/app/shared/dependencies.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/app/features/credentials/**`
- `src/backend/tests/test_phase011_hosted_readiness.py`
- `src/backend/tests/test_phase016_credentials.py`

## phase_015 - Typo Confirmation Rule And Runner Auto-Open

Status: completed

Objective:

- Review Claude's feedback and address the user-facing issues in this slice.
- Replace hardcoded typo stock aliases with a reusable fuzzy stock-confirmation rule.
- Ask the user to confirm likely stock typos instead of silently accepting them.
- Let affirmative follow-ups reuse the confirmed candidate stock.
- Open the frontend automatically when `./run-all.sh` starts the local app.

Acceptance criteria:

- `삼성전가` and `삼성전사` no longer resolve as exact aliases.
- A likely stock typo produces a Korean or English confirmation question such as "삼성전자 말씀이신가요?"
- Confirming the candidate with `네` or `yes` continues the flow with that stock.
- The fuzzy confirmation logic is generic over known seeded aliases and is not implemented by listing typo strings.
- Exact known stock names still behave normally.
- `run-all.sh` opens the frontend URL by default after startup and supports `AUTO_OPEN_BROWSER=0` to disable it.
- Backend tests and script validation cover the new behavior.
- `backups/phase_015/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `run-all.sh`
- `src/backend/app/features/conversations/schemas.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase014_conversation_language.py`
- `src/backend/tests/test_phase015_runner_and_typo_confirmation.py`

## phase_014 - Conversation Language And Follow-Up Context

Status: completed

Objective:

- Make backend-generated conversation replies follow the user's message language for Korean and English prompts.
- Preserve a previously resolved stock when a user answers a follow-up question in the same conversation.
- Handle common Korean Samsung Electronics typo inputs in the seeded market-data MVP; this was later superseded by the phase_015 confirmation rule.
- Keep the current deterministic MVP transparent when hosted LLM analysis is not connected.

Acceptance criteria:

- Korean user messages receive Korean missing-input and ready-state assistant text.
- English user messages continue to receive English assistant text.
- After a stock is resolved and the assistant asks for horizon, a non-horizon follow-up keeps asking for horizon instead of losing the stock.
- A valid horizon follow-up records the prior stock as ready for analysis.
- Common Korean Samsung Electronics typo inputs are covered by the later phase_015 confirmation flow.
- Backend unit tests cover the new conversation and alias behavior.
- `backups/phase_014/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase014_conversation_language.py`

## phase_012 - Bilingual Theme UI Refresh

Status: completed

Objective:

- Add an explicit Korean/English UI language switch for fixed frontend copy.
- Add light and dark theme switching with persistent local preference.
- Refresh the app layout toward a ChatGPT-like left-sidebar plus main conversation workspace.
- Keep the stock-analysis workflow operational while improving visual consistency.

Acceptance criteria:

- Users can switch visible static UI copy between English and Korean.
- Users can switch between dark and light themes.
- The selected language and theme persist in local browser storage.
- The main layout uses a left control rail, central conversation area, and bottom composer.
- Existing chat, settings, analysis snapshot, and backtest tests continue to pass.
- Frontend typecheck and build pass.
- `backups/phase_012/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/frontend/src/App.tsx`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/styles.css`
- `src/frontend/src/shared/**`
- `src/frontend/src/features/chat/**`
- `src/frontend/src/features/settings/**`
- `src/frontend/src/features/analysis/**`
- `src/frontend/src/features/backtest/**`

## phase_011 - Hosted Readiness And Security Hardening

Status: completed

Objective:

- Add a minimal hosted-mode guard without changing the local-first default.
- Configure explicit CORS origins for the frontend development hosts.
- Move internal LLM prompt material out of public analysis API responses.
- Validate timestamp formats and large text payloads at the request boundary.
- Improve frontend handling for saved settings and default-market initialization.
- Reduce project-local skill description size so Codex no longer exceeds the skills context budget.

Acceptance criteria:

- CORS preflight succeeds for the local frontend origin.
- `STUCK_LLM_REQUIRE_API_KEY=true` requires a matching API key on non-health requests.
- Bad or timezone-less timestamps are rejected with validation errors rather than 500s.
- Oversized conversation and source-document payloads are rejected.
- Analysis responses omit internal `system_instructions` and `prompt_context` fields.
- Frontend initial market snapshot follows the persisted default market.
- Settings save failures render a visible inline error.
- Backend and frontend unit tests cover the new behavior.
- `backups/phase_011/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `.codex/skills/**`
- `.agents/skills/**`
- `src/backend/app/main.py`
- `src/backend/app/shared/**`
- `src/backend/app/features/analysis/**`
- `src/backend/app/features/backtest/**`
- `src/backend/app/features/conversations/**`
- `src/backend/app/features/ingestion/**`
- `src/backend/tests/**`
- `src/frontend/src/App.tsx`
- `src/frontend/src/features/settings/**`
- `src/frontend/src/shared/**`
- `src/frontend/vite.config.ts`

## phase_010 - Global Source Adapter MVP

Status: completed

Objective:

- Add backend ingestion adapters for Reddit, US news, polling/sentiment, and global macro sources.
- Keep adapters seed-backed and offline for the MVP, with a registry that can be replaced by live providers later.
- Return source documents that are compatible with the analysis pipeline.
- Preserve source metadata, timestamps, URLs, adapter names, relevance scores, and safety flags.
- Avoid server-side arbitrary URL fetching or live crawler execution in this phase.

Acceptance criteria:

- `POST /ingestion/collect` accepts stock metadata, `as_of_at`, analysis mode, and requested source adapters.
- The response includes documents from Reddit, US news, polling/sentiment, and global macro adapters.
- Quick mode returns a compact set; deep mode can return more documents from the same adapters.
- Collected documents can be submitted to `POST /analysis/requests`, where post-`as_of_at` documents are excluded by the analysis layer.
- Unsupported adapter names are rejected by request validation.
- Backend unit tests cover adapter collection, quick/deep behavior, analysis cutoff integration, and validation.
- `backups/phase_010/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/app/features/ingestion/**`
- `src/backend/tests/**`

## phase_009 - Backtest And PnL Graph Service

Status: completed

Objective:

- Add a backend backtest feature slice for seeded PnL simulations.
- Keep PnL/backtest price data separate from historical evidence analysis.
- Calculate entry price, exit price, gross return, gross PnL, max drawdown, and equity curve.
- Add a frontend PnL panel with a compact graph for local seeded simulations.

Acceptance criteria:

- `POST /backtests/simulations` accepts market, symbol, entry/exit timestamps, and quantity.
- Backtest responses include price-derived PnL metrics and an equity curve.
- Backtest errors clearly report missing seeded price data or invalid date ranges.
- Frontend exposes a local PnL simulation panel and renders the returned curve.
- Backend and frontend unit tests cover the service and graph flow.
- `backups/phase_009/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/app/features/backtest/**`
- `src/backend/tests/**`
- `src/frontend/src/App.tsx`
- `src/frontend/src/features/backtest/**`
- `src/frontend/src/shared/**`
- `src/frontend/src/styles.css`

## phase_008 - Scoring Probabilities And Confidence

Status: completed

Objective:

- Add a backend scoring feature slice for buy, hold, and sell probabilities.
- Convert analysis evidence stance and weights into auditable probability output.
- Report a confidence score that reflects eligible evidence strength and excluded-source penalty.
- Avoid producing scored probabilities when no eligible evidence is available.

Acceptance criteria:

- `POST /scoring/evaluate` accepts evidence items and excluded-source count.
- Scored responses include buy, hold, and sell probabilities summing to 100.
- Confidence decreases when evidence is weak or sources are excluded.
- Empty evidence returns `needs_evidence` and zero probabilities.
- Backend unit tests cover bullish/neutral/bearish weighting and empty-evidence behavior.
- `backups/phase_008/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/app/features/scoring/**`
- `src/backend/tests/**`

## phase_007 - Historical Analysis Pipeline

Status: completed

Objective:

- Add a backend analysis feature slice for source-grounded local analysis requests.
- Enforce `as_of_at` filtering before any prompt context or analysis summary is built.
- Store included and excluded source-document decisions in the response.
- Treat source text as untrusted evidence and keep prompt-injection instructions out of analysis instructions.
- Return stance evidence for later scoring without producing buy/hold/sell probabilities yet.

Acceptance criteria:

- `POST /analysis/requests` accepts stock, horizon, `as_of_at`, analysis mode, and source documents.
- Source documents published after `as_of_at` are excluded and do not appear in prompt context or summary.
- Included source documents produce linked evidence items with stance, weight, summary, and quote excerpt.
- Empty eligible evidence returns a `needs_evidence` status instead of fabricating analysis.
- Backend unit tests cover strict cutoff filtering, prompt-boundary safety, and empty-evidence behavior.
- `backups/phase_007/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/features/analysis/**`
- `src/backend/tests/**`

## phase_006 - Chat Settings And Market Data MVP

Status: completed

Objective:

- Add local file-backed persistence for development settings and conversations.
- Add backend settings, conversation, and seeded market-data endpoints.
- Connect the frontend shell to the backend through the existing `/api/*` proxy.
- Keep market-data snapshots separate from LLM analysis and probability scoring.
- Preserve the missing-horizon follow-up behavior before analysis requests are accepted.

Acceptance criteria:

- Settings can be read, updated, and persisted across app instances.
- A chat message creates or updates a persisted conversation.
- If a message lacks a stock or investment horizon, the assistant asks one focused follow-up.
- If required inputs are present, the assistant records a request and returns a seeded market-data snapshot without claiming LLM analysis is complete.
- Frontend chat, settings, and analysis panels render backend-backed state and include unit tests.
- Backend tests, frontend unit tests, typecheck, and build pass.
- `backups/phase_006/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/shared/**`
- `src/backend/app/features/conversations/**`
- `src/backend/app/features/settings/**`
- `src/backend/app/features/market_data/**`
- `src/backend/tests/**`
- `src/frontend/src/**`

## phase_005 - Unified Runner And Atomic Test Policy

Status: completed

Objective:

- Add a root-level unified runner for backend and frontend development servers.
- Make backend and frontend feature-folder organization explicit in docs and `AGENTS.md`.
- Make unit tests mandatory for every backend/frontend feature slice.
- Add frontend unit test infrastructure for the existing chat feature.
- Submit implemented code for `review-claude` after local validation.

Acceptance criteria:

- `./run-all.sh` starts backend and frontend together from the project root.
- Frontend dev server proxies `/api/*` requests to the backend.
- `src/README.md` explains backend/frontend feature folder conventions.
- `AGENTS.md` and workflow docs state that unit tests are mandatory.
- Backend tests and frontend unit tests pass.
- `backups/phase_005/` records every non-backup file modified or created in this phase.

Files expected to change:

- `AGENTS.md`
- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/code-authoring.md`
- `docs/agent-workflows/code-validation.md`
- `run-all.sh`
- `src/README.md`
- `src/frontend/**`

## phase_004 - Source Scaffold And Foundation Slice

Status: completed

Objective:

- Create the initial application scaffold under `src/backend` and `src/frontend`.
- Keep backend and frontend separated while preserving feature-level atomicity.
- Add the first backend health feature with a test-first workflow.
- Add a functional frontend shell for chat, settings, and analysis panels.
- Update validation and planning docs to reflect the `src/` layout.

Acceptance criteria:

- Backend code lives under `src/backend`.
- Frontend code lives under `src/frontend`.
- Backend has a passing health endpoint test.
- Frontend has an installable/buildable Vite React TypeScript scaffold.
- Feature code is grouped by atomic feature folders.
- `docs/plan.md`, `docs/agent-workflows/code-authoring.md`, and `docs/agent-workflows/code-validation.md` reflect the `src/` layout.
- `backups/phase_004/` records every non-backup file modified or created in this phase.

Files expected to change:

- `AGENTS.md`
- `.gitignore`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/code-authoring.md`
- `docs/agent-workflows/code-validation.md`
- `src/backend/**`
- `src/frontend/**`

## phase_003 - Skill Installation And Routing Policy

Status: completed

Objective:

- Install project-relevant skills from the `stock-analysis-agent` index.
- Synchronize externally installed skills into `.codex/skills/` for project-local availability.
- Document situation-based skill routing in orchestration docs.
- Record install/run permission and docs-change policies in `AGENTS.md`.

Acceptance criteria:

- Selected local, global-source, and external skills have `.codex/skills/<skill-name>/SKILL.md`.
- `docs/agent-workflows/orchestration.md` explains which skills to reference by situation.
- `AGENTS.md` remains lightweight and points to orchestration for detailed routing.
- `docs/task.md`, `docs/implement.md`, and `.find-skills/stock-analysis-agent/index.md` reflect the installation.
- `backups/phase_003/` records every non-backup file modified or created in this phase.

Files expected to change:

- `AGENTS.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/orchestration.md`
- `.find-skills/stock-analysis-agent/index.md`
- `.codex/skills/**`
- `.agents/skills/**`

## phase_002 - Skill Discovery Checklist And Index

Status: completed

Objective:

- Use the project-local `find-skills` workflow to discover skills for the stock-analysis AI agent.
- Broaden the checklist so candidates cover implementation, frontend, backend, ingestion, LLM, finance, security, testing, and deployment phases.
- Generate a project-local skill index only after checklist confirmation.

Acceptance criteria:

- `docs/checklist-001.md` records broad search vocabulary and candidate categories.
- Search was run after the user requested index generation.
- `.find-skills/stock-analysis-agent/index.md` records ranked candidates and install status.
- `backups/phase_002/` records every non-backup file modified in this phase.
- The eventual index is written to `.find-skills/stock-analysis-agent/index.md`.

Files expected to change:

- `docs/checklist-001.md`
- `docs/task.md`
- `docs/implement.md`
- `.find-skills/stock-analysis-agent/index.md`

## phase_001 - Planning And Workflow Documentation

Status: completed

Objective:

- Preserve the agreed product direction for a conversational stock-analysis AI agent.
- Define the initial architecture, service boundaries, database draft, and phase plan.
- Add lightweight agent instructions and workflow docs.
- Establish a backup convention for every modified non-backup file.

Acceptance criteria:

- `docs/plan.md` is written in English.
- `docs/task.md` and `docs/implement.md` use reverse chronological phase entries.
- `AGENTS.md` stays lightweight and points to durable docs.
- `docs/agent-workflows/code-authoring.md` exists.
- `docs/agent-workflows/code-validation.md` exists.
- `docs/agent-workflows/orchestration.md` exists.
- `backups/phase_001/` records every non-backup file modified in this phase.

Files expected to change:

- `AGENTS.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/code-authoring.md`
- `docs/agent-workflows/code-validation.md`
- `docs/agent-workflows/orchestration.md`

## Future Phase Template

```text
## phase_00x - Title

Status: pending | in_progress | completed

Objective:
- ...

Acceptance criteria:
- ...

Files expected to change:
- ...
```
