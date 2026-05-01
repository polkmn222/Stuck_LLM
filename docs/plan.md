# Conversational Stock Analysis Agent Plan

## Product Intent

Build a ChatGPT-like local web application that helps users analyze stocks through conversation. The first priority is Korean stocks, while preserving a path to US stocks and combined global analysis.

The product is an investment decision-support tool, not an automated trading or regulated advisory system. The assistant should explain buy, hold, and sell probabilities with auditable evidence, source links, dates, and confidence.

## Confirmed Requirements

- Primary use case: investment decision support.
- Market priority: Korean stocks first, then US stocks, then integrated analysis.
- Korean stock analysis must still consider global sources such as US news, Reddit, US polling/sentiment, macro signals, and sector data.
- Output should prioritize action probabilities: buy, hold, sell.
- Users choose the investment horizon. If missing, the agent asks.
- Users choose quick or deep analysis mode.
- If the user provides an analysis date/time, evidence published after that timestamp must be excluded.
- Future price data may be used only in PnL or backtest views, not in historical evidence analysis.
- Users may add URLs or raw text in addition to default automated search.
- LLM API keys must be explicitly saved by the user in Settings; environment variables are not used as LLM API-key fallback.
- The MVP starts as a local web app, but should keep a service-oriented path for team or hosted use later.

## Non-Goals For MVP

- No brokerage order placement.
- No automated live trading.
- No team login or role-based access control in the first build.
- No guarantee that probabilities are true price-outcome probabilities.
- No hidden use of future evidence in historical analysis mode.

## Architecture Direction

Use a service-oriented architecture as the target shape, but add services one at a time. Start with a single repository and a shared PostgreSQL database. Keep module and schema boundaries service-shaped so that services can be extracted later.

Recommended target services:

- `api-gateway`: frontend-facing API, authentication insertion point later.
- `chat-service`: conversations, messages, context, missing-input prompts.
- `credential-service`: user-provided provider keys, encrypted storage, masking, and rotation workflow.
- `ingestion-service`: source discovery, crawlers, API collectors, user-supplied source ingestion.
- `analysis-service`: evidence filtering, LLM calls, stance extraction, source-grounded summaries.
- `scoring-service`: buy/hold/sell probabilities, evidence weights, confidence scores.
- `market-data-service`: OHLCV data collection and normalization.
- `backtest-service`: "what if I bought then?" PnL and return simulations.

## Repository Shape

Initial target layout:

```text
src/
  backend/
    app/
      features/
        health/
        conversations/
        settings/
        analysis/
        market_data/
        backtest/
    tests/
  frontend/
    src/
      features/
        chat/
        settings/
        analysis/
docs/
  agent-workflows/
backups/
```

Feature work should be atomic. Each backend slice owns its route, schemas, tests, and service logic. Each frontend slice owns its component, local state, and UI-specific helpers.

Unit tests are mandatory for backend and frontend feature or behavior changes. Backend tests live under `src/backend/tests/`; frontend tests should be colocated with feature components under `src/frontend/src/features/<feature>/`.

## Database Schema Draft

Core identity and settings:

```text
users(id, display_name, created_at)
provider_credentials(id, user_id, provider, encrypted_api_key, is_active, created_at, updated_at)
conversations(id, user_id, title, default_market, default_as_of_mode, fixed_as_of_at, created_at, updated_at)
messages(id, conversation_id, role, content, provider, model, created_at)
```

Local BYOK credential storage starts as a single-user `llm_credentials` state area before
the schema moves to `provider_credentials` with login/user ownership.

Stock and analysis entities:

```text
stocks(id, market, symbol, name, exchange, currency, created_at)
analysis_requests(id, conversation_id, stock_id, user_query, as_of_at, horizon_type, horizon_start_at, horizon_end_at, analysis_mode, status, created_at)
source_documents(id, analysis_request_id, source_type, source_name, url, title, author, published_at, fetched_at, content_text, language, included_in_analysis, exclusion_reason)
analysis_results(id, analysis_request_id, buy_probability, hold_probability, sell_probability, confidence_score, summary, reasoning_json, model_provider, model_name, created_at)
evidence_items(id, analysis_result_id, source_document_id, stance, weight, summary, quote_excerpt)
```

Processing, cache, and replay entities:

```text
kv_cache(id, namespace, cache_key, payload_json, created_at, expires_at)
news_processing_runs(id, digest_id, stock_id, generated_at, cache_hits, cache_misses, provider_runs_json, query_templates_json)
prediction_artifacts(id, artifact_key, stock_id, as_of_at, horizon_type, evidence_set_hash, prompt_version, model_provider, model_name, summary, evidence_items_json, created_at)
ai_prompt_inventory(id, prompt_key, version, owner_feature, purpose, created_at)
```

KV cache entries are disposable acceleration data. Processing runs and prediction
artifacts are audit and replay data and must never store raw provider secrets,
decrypted credentials, hidden system prompts, or post-cutoff evidence.

Market data and PnL:

```text
price_bars(id, stock_id, timestamp, interval, open, high, low, close, volume, source)
pnl_simulations(id, analysis_request_id, stock_id, entry_at, exit_at, entry_price, exit_price, quantity, gross_return_pct, gross_pnl, created_at)
```

Critical rule: `analysis_requests.as_of_at` is the evidence cutoff. Any source with `published_at > as_of_at` must be stored as excluded and must not affect LLM analysis or scoring.

## Analysis Flow

1. User sends a chat message.
2. Chat service extracts stock, market, horizon, analysis mode, source hints, and `as_of_at`.
3. If required information is missing, the assistant asks one focused follow-up question.
4. Ingestion service collects default and user-provided sources.
5. Analysis service filters out evidence after `as_of_at`.
6. Analysis service calls the selected LLM provider with only eligible evidence.
7. Scoring service calculates buy, hold, sell probabilities and confidence.
8. Evidence items link each probability driver back to source documents.
9. Chat service stores and returns the answer.

## PnL Flow

1. User asks "what if I bought then?" or opens a result graph.
2. Backtest service asks for entry/exit policy if missing.
3. Market-data service retrieves price bars for the requested period.
4. Backtest service calculates return, PnL, drawdown, and comparison views.
5. UI renders the chart separately from the evidence-analysis view.

## Data Source Strategy

Use a hybrid strategy:

- Prefer official APIs, search APIs, and stable feeds for core sources.
- Add site-specific crawlers only where allowed and operationally stable.
- Keep experimental crawlers behind settings flags.
- If a source fails, quick analysis may continue with a warning; deep analysis should warn or stop when core sources are missing.

Initial source priority:

1. Korean market data and company metadata.
2. Naver news search or equivalent news provider.
3. Naver discussion-board adapter or fallback through search/user URLs.
4. Global news and macro search.
5. Reddit and US sentiment/polling adapters.

## Skill And Tool Discovery

Installed project-local skills that should be used during implementation:

- `architecture`: architecture decisions and ADRs.
- `api-design-principles`: API shape and route design.
- `backend-development`: backend API, service boundaries, and implementation structure.
- `database-design`: schema design, migrations, and indexing.
- `frontend-design`: ChatGPT-style UI and analysis screens.
- `llm-application-dev`: prompt, RAG, provider abstraction, and LLM application patterns.
- `openai-docs`: current OpenAI API and model implementation guidance.
- `test-driven-development`: feature and bugfix implementation.
- `systematic-debugging`: failures and unexpected behavior.
- `security-auditor`: API key storage, source ingestion, and prompt/data safety review.
- `lint-and-validate`: validation after every code change.
- `agent-workflow-docs` and `agents-md`: workflow documentation maintenance.
- `quant-backtest`, `vectorbt-expert`, `backtesting-trading-strategies`, `backtest`, `quick-stats`, `optimize`, and `strategy-compare`: backtesting and PnL work.
- `firecrawl`, `agent-browser`, and `apify-ultimate-scraper`: source ingestion and browser automation, with security/legal review before sensitive use.
- `webapp-testing`, `vercel-react-best-practices`, `web-design-guidelines`, and `shadcn`: frontend implementation and validation.

Skill discovery index:

- `.find-skills/stock-analysis-agent/index.md`

## External AI Assistant Pattern Audit

The WealthOS local repository was reviewed for portable AI assistant patterns.
Adopted ideas are capability matrices, prompt inventory, boolean-only provider
status, data-grounded prompt rules, and provider-response cache/inflight thinking.
Not adopted are framework-specific Next.js routes, committed `.env.local` secret
policy, and blanket no-forecast prompts that conflict with this project's
prediction mode.

## Planned Build Phases

- `phase_106`: News digest UI labels moved into the shared i18n copy boundary.
- `phase_105`: Local state sidecar write optimization for unchanged cache/artifact domains.
- `phase_104`: News digest prompt and LLM-output formatting extraction from `conversations/service.py`.
- `phase_103`: Chat news digest component extraction from `ChatShell` with standalone frontend coverage.
- `phase_102`: Backend E2E chat-to-prediction-analysis test slice for `/conversations` persistence and scoring.
- `phase_101`: Centralized environment-backed external provider credential boundary for search/news/market-data keys.
- `phase_100`: Local state sidecar split for KV cache, news processing runs, and prediction artifacts.
- `phase_099`: Shared provider status warning helper for ingestion and news digest flows.
- `phase_098`: Conversation formatting helper extraction as the first `conversations/service.py` decomposition slice.
- `phase_097`: Land in-flight AI capability and processing-cache work with minimal cache status/invalidation API and review-folder gitignore cleanup.
- `phase_096`: AI capability matrix and prompt inventory diagnostics route inspired by the WealthOS assistant audit.
- `phase_095`: Prediction artifact store keyed by evidence hash, prompt version, provider, model, horizon, and `as_of_at`.
- `phase_094`: S&P 500 symbol and sector-aware query templates for company news.
- `phase_093`: DB-backed KV cache and news processing run records using the local state-store DB boundary.
- `phase_092`: S&P 500 stock-universe repository boundary and metadata-only news fallback.
- `phase_091`: Agent workflow docs hardening for external repo audits, matrix unit tests, cache policy, and processing DB rules.
- `phase_090`: Backend regression matrix for Apple, Google, Nvidia, and Tesla news, chart, and prediction requests.
- `phase_089`: Review fixes for social-only news routing and environment-isolated news provider tests.
- `phase_088`: News source validation, documentation, backups, and push preparation.
- `phase_087`: Korean prediction intent fallback so `애플 예측` routes to live analysis without relying on LLM intent classification.
- `phase_086`: Optional Naver News and public social-search providers for news digest coverage.
- `phase_085`: Diverse important-article selection across categories and source domains.
- `phase_084`: Diversified company-event news queries including product/AI, leadership, regulation, analyst, and S&P Global research searches.
- `phase_083`: Korean news typo recovery for requests such as `애플 뉴ㅛㅡ`.
- `phase_082`: Prediction documentation, backups, and full validation.
- `phase_081`: Similar-event calibration baseline fields for sample count, win rate, and median return.
- `phase_080`: Historical buy-date PnL simulation in chat with separate `backtest_result` payloads.
- `phase_079`: Expected return range and downside risk metadata on scored predictions.
- `phase_078`: Market-data evidence bundle from current quote and chart context.
- `phase_077`: Five-trading-day default prediction probabilities in chat and analysis UI.
- `phase_076`: News polish documentation, backups, and full validation.
- `phase_075`: ChatGPT-style Korean news digest UI with key headlines, favicon cards, and overflow-safe snippets.
- `phase_074`: LLM JSON news summary parsing for Korean article headlines and summaries.
- `phase_073`: News importance categories and priority ordering across official, earnings, business, controversy, and market stories.
- `phase_072`: News query and ranking refinement to demote quote/history pages and target real company news.
- `phase_071`: `run-all.sh` Ctrl+C shutdown handling so backend and frontend terminate together.
- `phase_070`: Local backend validation tooling install for Ruff and MyPy.
- `phase_069`: News digest documentation, backups, and full backend/frontend validation.
- `phase_068`: ChatGPT-style news digest UI with linked top stories, expandable extra articles, and provider transparency.
- `phase_067`: Conversation routing for news requests without quote-horizon analysis requirements.
- `phase_066`: LLM-backed news overview generation with deterministic fallback and source-grounding constraints.
- `phase_065`: News query normalization, provider result dedupe, ranking, and important/additional article split.
- `phase_064`: News digest provider contract using Tavily, GNews, SerpApi Google News, and SerpApi Google Web.
- `phase_063`: Provider-backed USD/KRW display conversion for Korean US-stock snapshot text.
- `phase_062`: Local S&P 500 symbol directory routing for US quote lookup under a KR default market.
- `phase_061`: GPT-style chat auto-scroll to the newest conversation content.
- `phase_060`: Chart hover tooltip plus thinner selected-window directional line styling.
- `phase_059`: Readable finance chart port from `gpt-coding/finance_app.py` behavior plus fresh `New chat` reset.
- `phase_058`: Google Finance-style chart context with active window, start reference, latest marker, and exchange-local axis labels.
- `phase_057`: US snapshot currency policy that keeps graph data in USD and adds KRW conversion in Korean chat copy.
- `phase_056`: Search-style and localized US ticker normalization for Apple and Google plus graph-first SerpApi candidate selection.
- `phase_055`: Ambiguous chat follow-up handling and stock-only snapshot guard to prevent `/conversations` 500s.
- `phase_054`: ChatGPT-style in-flight activity copy while LLM and data requests are pending.
- `phase_053`: LLM-confirmed localized Korean input to US ticker market snapshots.
- `phase_052`: Conversation deletion and left-rail settings isolation.
- `phase_051`: Frontend US graph period controls backed by market-data refetches.
- `phase_050`: US Google Finance market-data API `window` contract and bidirectional exchange-query fallback.
- `phase_049`: Runtime comparison between `gpt-coding` Google Finance Streamlit apps and the current FastAPI/React implementation.
- `phase_048`: SerpApi Google News ingestion adapter for source documents.
- `phase_047`: Nested SerpApi Google Finance news parsing for market snapshots.
- `phase_046`: SerpApi Google Finance query candidate fallback for unmapped US tickers.
- `phase_045`: Structural and documentation garbage-collection lint for feature boundaries, backup policy, phase freshness, and agent-workflow drift detection.
- `phase_044`: Agent-readable observability reports for request IDs, provider calls, conversation status transitions, market snapshots, and validation failures.
- `phase_043`: Eval corpus harness CLI that runs deterministic analysis/scoring/source-safety cases outside pytest and emits stable reports.
- `phase_042`: Browser and user-journey harness with Playwright checks for saved-key chat, follow-up conversations, ticker snapshots, and previous-chat reload.
- `phase_041`: Agent harness foundation with `./run-harness.sh`, validation profiles, dry-run inspection, and JSON/Markdown reports.
- `phase_040`: Agent workflow provider-validation policy requiring real `/conversations` API-key checks, repeated follow-up validation, credential boundary clarity, and rich snapshot expectations.
- `phase_039`: ChatGPT-style conversation workspace with left-rail saved conversation loading, internal chat scrolling, and message-level chart/news/stat preservation.
- `phase_038`: Persistent LLM simple chat, conversation summaries, message-level market snapshots, ticker-only snapshot flow, and SerpApi key stats/news parsing.
- `phase_037`: Cerebras provider header compatibility with explicit JSON accept and non-urllib User-Agent, verified through the saved credential connection test.
- `phase_036`: Minimal reusable market quote card in chat and analysis with stock name, symbol, price, exchange, as-of timestamp, and SVG line chart.
- `phase_035`: User-selected LLM credential policy with Cerebras-first setup, no environment fallback, and red missing-key UI copy.
- `phase_034`: Prompt grounding contract integration for explicit allowed source IDs and structured-output citation validation.
- `phase_033`: Eval-only source quality and evidence weighting helpers based on metadata reliability, freshness, and relevance.
- `phase_032`: Source safety eval rules for prompt-injection, schema-spoofing, official-source spoofing, and metadata/body-date mismatch checks.
- `phase_031`: Deterministic analysis eval harness for cutoff safety, source grounding, probability consistency, and confidence/evidence invariants.
- `phase_030`: End-to-end validation across provider diagnostics, generative chat orchestration, settings-language responses, SerpApi market data, and improved chart rendering.
- `phase_029`: Market chart UX refresh with period controls, clearer axes, source/time labels, hover or focus details, and separate quote-line versus OHLC semantics.
- `phase_028`: SerpApi Google Finance refinement with market-qualified ticker parsing, US ticker auto-routing, configurable graph windows, source/news handling, and safe provider diagnostics.
- `phase_027`: Settings-language response policy so backend-generated assistant copy and LLM prompts follow the selected UI language before falling back to message-language detection.
- `phase_026`: Generative chat orchestration that lets the LLM interpret intent, stock, horizon, source hints, and follow-up needs through structured JSON while keeping deterministic validation gates.
- `phase_025`: LLM provider connection diagnostics for saved credentials, Cerebras comparison-model defaults, safe auth/rate-limit/base-URL error surfacing, and Settings modal test controls.
- `phase_024`: Cerebras OpenAI-compatible live LLM test provider using `CEREBRAS_API_KEY`, official base URL defaults, structured-output payload compatibility, and settings/provider typing.
- `phase_023`: Evidence source audit trail with source warnings, safety flags, inclusion/exclusion reason summaries, prompt document IDs, and analysis-panel rendering.
- `phase_022`: SerpApi Google Finance provider for US market snapshots, quote line charts, and safe fallback to FinanceDataReader/seeded fixtures.
- `phase_021`: OpenAI-compatible provider policy, DNS safety, custom/local opt-in, retry/timeout, and live prompt budget controls.
- `phase_020`: Review-filtered security hardening, prompt delimiters, provider base URL validation, local-state concurrency, frontend accessibility, API aborts, and CI.
- `phase_019`: FinanceDataReader price snapshots/charts, Naver/Tavily/GNews search ingestion, `.env` provider loading, and chart UX in chat/analysis panels.
- `phase_018`: Live LLM provider analysis integration with BYOK credential gating, source-grounded prompts, structured output parsing, and Korean/English setup/error responses.
- `phase_011`: Hosted readiness guard, public-response hardening, and validation cleanup.
- `phase_017`: ChatGPT-style settings modal and workspace navigation split.
- `phase_016`: Local BYOK credential backend, encrypted storage, project skills, and CLI setup.
- `phase_015`: Fuzzy stock typo confirmation rules and runner browser auto-open.
- `phase_014`: Conversation language matching, follow-up context carryover, and Korean stock alias tolerance.
- `phase_013`: Team login, user boundaries, and deployment exploration.
- `phase_012`: Bilingual UI, light/dark theming, and ChatGPT-like layout refresh.
- `phase_010`: Reddit, US news, polling/sentiment, and global macro adapters.
- `phase_009`: Backtest and PnL graph service.
- `phase_008`: Scoring model, evidence weighting, and confidence reporting.
- `phase_007`: LLM analysis pipeline with strict `as_of_at` filtering.
- `phase_006`: Chat, settings, local persistence, and market-data MVP.
- `phase_005`: Unified dev runner and mandatory unit-test policy.
- `phase_004`: `src/backend` and `src/frontend` scaffold, health endpoint, and initial UI shell.
- `phase_003`: Skill installation and routing policy.
- `phase_002`: Skill discovery checklist and index.
- `phase_001`: Planning, workflow docs, backup rules, and architecture baseline.

## Decision Log

- `phase_081`: Similar-event calibration is exposed as a replaceable baseline slot, not a statistically validated historical matching model.
- `phase_080`: Buy-date questions return separate PnL simulations and must not create analysis requests or feed future prices into historical LLM evidence.
- `phase_079`: Expected return range is a rough five-trading-day heuristic derived from directional score edge and confidence until calibrated backtests exist.
- `phase_078`: Current market snapshot and eligible chart context may become `market_data` evidence at `as_of_at`; future PnL/backtest data remains excluded from analysis prompts.
- `phase_077`: Prediction-like no-horizon requests default to `swing`, presented as the next five trading days; generic analysis requests may still ask for horizon.
- `phase_058`: Keep the current dependency-free SVG chart, but add the chart context users expected from the standalone Google Finance app.
- `phase_057`: Keep US quote payloads and graphs in USD; Korean assistant copy may add approximate KRW conversion using `STUCK_LLM_USD_KRW_RATE` or an offline fallback until a real FX provider exists.
- `phase_056`: Treat `애플`/Apple/AAPL and `구글`/Google/GOOG as deterministic quote aliases, superseding the earlier phase_053 requirement that `애플` require LLM confirmation.
- `phase_055`: A resolved stock plus no analysis intent should return a market snapshot; LLM `needs_follow_up` should become the assistant's one focused clarification question.
- `phase_054`: Use a client-side pending activity message for immediate ChatGPT-style feedback before adding backend streaming or per-provider progress events.
- `phase_053`: Localized names such as `애플` are not added as deterministic aliases; a saved LLM intent can infer `AAPL` and the app persists a confirmation candidate before fetching market data.
- `phase_052`: Delete local conversation history through explicit DELETE APIs and keep Settings outside the conversation scroll area so it remains a stable bottom action.
- `phase_051`: Fetch chart windows on demand from the active message card instead of preloading all periods, preserving older snapshots and SerpApi quota.
- `phase_050`: Treat chart period as a market-data API query parameter, not frontend-only state, so selected windows are reflected in the provider request and returned quote metadata.
- `phase_049`: Bring over the standalone graph app's SerpApi `window` and candidate behavior first; keep the separate Google News app out of scope until graph interaction is stable.
- `phase_048`: Add SerpApi Google News as an ingestion adapter, not a parallel analysis path, so source documents still use the existing safety flags, cutoff filtering, and prompt-grounding contracts.
- `phase_047`: Treat nested Google Finance news section wrappers as containers and expose only article-level items in market snapshots.
- `phase_046`: Keep SerpApi Google Finance fallback inside the market-data provider and try exchange-qualified candidates before falling back to FinanceDataReader or fixtures.
- `phase_041`: Harness engineering starts with a small local command runner and agent-readable reports before adding browser automation, eval corpora, observability, or structural garbage collection.
- `phase_041`: `phase_042` through `phase_045` remain documented future work so the first harness slice stays limited to command orchestration and reporting.
- `phase_040`: Provider/API-key work is incomplete unless the saved key is exercised through `/conversations` and repeated same-conversation follow-up, not only Settings diagnostics.
- `phase_039`: Market snapshots belong to the message that produced them so later follow-up messages cannot erase earlier charts, news, or stats from the chat history.
- `phase_038`: Ticker-only inputs such as `AAPL` should return a market snapshot with available chart/news/stats before asking for analysis horizon; buy/sell/compare analysis intents still require horizon validation.
- `phase_038`: LLM provider credentials remain saved-user-key only, while `SERPAPI_API_KEY` and other search/news/market-data keys stay environment-configured and separate.
- `phase_034`: Tighten the existing live-analysis prompt contract instead of adding a parallel analysis package or broad prompt rewrite.
- `phase_033`: Keep source quality eval-only until the product UI and scoring semantics are ready to expose quality fields.
- `phase_032`: Treat source safety as deterministic eval coverage first, before changing live prompts or source-quality weighting.
- `phase_031`: Add deterministic offline evals before expanding source safety and source quality so cutoff, grounding, probability, and confidence invariants can be regression-tested without live providers.
- `phase_001`: Prioritize investment decision support before trading automation.
- `phase_001`: Korean stocks first; US and global sources remain in the design.
- `phase_001`: Use buy/hold/sell probabilities with source-level auditability.
- `phase_001`: Respect strict historical evidence cutoff when `as_of_at` is set.
- `phase_001`: Separate historical analysis from future PnL/backtest views.
- `phase_001`: Target service-oriented architecture, implemented incrementally.
- `phase_001`: Use Python backend and TypeScript frontend.
- `phase_004`: Application code lives under `src/backend` and `src/frontend`.
- `phase_004`: Feature work should remain atomic under backend and frontend feature folders.
- `phase_005`: `./run-all.sh` is the root command for local backend/frontend development.
- `phase_005`: Unit tests are mandatory for backend and frontend feature/behavior changes.
- `phase_006`: Local MVP state uses a JSON file at `.local/stuck_llm_state.json` by default, overrideable with `STUCK_LLM_STATE_PATH`.
- `phase_006`: Seeded market-data fixtures can support UI and API flow, but they are not analysis evidence or completed probabilities.
- `phase_006`: Chat requests must collect stock and horizon before recording a request as ready for later analysis.
- `phase_007`: Analysis prompt context is built only from source documents with `published_at <= as_of_at`.
- `phase_007`: Source text is treated as untrusted evidence and must not alter system instructions.
- `phase_007`: The local analysis provider creates evidence stance items, but probability scoring remains separate.
- `phase_008`: Buy, hold, and sell probabilities are normalized from evidence stance weights with an explicit hold baseline.
- `phase_008`: Empty evidence returns `needs_evidence` and zero probabilities rather than treating missing evidence as neutral.
- `phase_008`: Confidence is an MVP heuristic based on eligible evidence count, evidence weight, and excluded-source penalty.
- `phase_009`: PnL/backtest results are stored separately from evidence analysis and must not be used as historical evidence.
- `phase_009`: The MVP backtest uses seeded local price bars and gross PnL only.
- `phase_009`: The frontend PnL graph is an operational panel, not an analysis probability view.
- `phase_010`: Global source adapters are seed-backed and offline until live provider credentials, source policy, rate limits, and security controls are reviewed.
- `phase_010`: Ingestion collects source documents and metadata, while analysis remains responsible for `as_of_at` inclusion/exclusion decisions.
- `phase_010`: Server-side arbitrary URL fetching and crawler execution are intentionally excluded from the adapter MVP.
- `phase_011`: Local mode remains unauthenticated by default; hosted mode can require a static API key through environment variables until real user login is selected.
- `phase_019`: Market snapshots use FinanceDataReader opportunistically and fall back to seeded fixtures when live data is unavailable.
- `phase_019`: Price/chart bars are response data for UX and must not be inserted into LLM source evidence or historical prompt context.
- `phase_019`: Naver, Tavily, and GNews search/news adapters normalize external content into untrusted source documents with safe missing-credential warnings.
- `phase_019`: Local `.env` keys may configure search/news/market-data providers, but LLM analysis no longer uses environment API-key fallback after `phase_035`.
- `phase_020`: Claude-review findings are accepted only after local verification; false positives should not become phase scope.
- `phase_020`: LLM provider base URLs must be public HTTPS API origins by default; local/private/metadata endpoints are rejected before outbound calls.
- `phase_020`: Prompt context uses source-level untrusted delimiters plus escaped JSON payloads so source text cannot spoof prompt structure.
- `phase_020`: Concurrent conversation appends merge against the latest stored messages before writing local JSON state.
- `phase_021`: OpenAI-compatible live calls should use official OpenAI endpoints by default; hosted non-official endpoints require an explicit allowlist.
- `phase_021`: Custom OpenAI-compatible providers are opt-in, and localhost/private endpoints are local-development only.
- `phase_021`: DNS resolution is part of provider URL validation for non-official hosts, but hosted egress policy remains the primary production control.
- `phase_021`: Live LLM calls use bounded retry, timeout, and prompt/source budget controls before adding additional vendor adapters.
- `phase_021`: Anthropic credentials remain storable for setup continuity, but live Anthropic calls stay deferred until a dedicated adapter phase.
- `phase_022`: US market snapshots should prefer SerpApi Google Finance when `SERPAPI_API_KEY` is configured, then fall back to FinanceDataReader and seeded fixtures.
- `phase_022`: SerpApi graph data supports quote line charts, but it is not full OHLC candle data and must not be used as authoritative backtest input.
- `phase_022`: The SQLite conversation-store idea is deferred; conversation storage/orchestration should be handled in a separate phase.
- `phase_023`: Analysis responses should carry a compact source audit trail so users can see source warnings, included/excluded source counts, exclusion reasons, and exactly which source IDs entered the prompt.
- `phase_023`: Source audit metadata may expose safe provider/status codes and source-level flags, but not raw source body text, API keys, provider internals, or future-evidence content.
- `phase_024`: Cerebras uses the OpenAI-compatible live provider path with `https://api.cerebras.ai/v1`, saved user API keys, and `gpt-oss-120b` as the local-test default model.
- `phase_035`: Follow DeepTutor's explicit provider-binding pattern at the product level: provider, model, base URL, and API key are selected/configured deliberately, and LLM calls require a saved user key.
- `phase_035`: Environment variables are not used as LLM credential fallback; missing saved keys return setup-needed copy and the chat UI renders the API-key prompt in error red.
- `phase_025`: Provider health should be testable directly from Settings without running a full stock-analysis prompt or exposing raw provider responses.
- `phase_025`: Cerebras remains a long-running comparison provider; the local default model is updated to `llama3.1-8b` based on the user's currently available key, while `qwen-3-235b-a22b-instruct-2507` stays available for later performance comparison.
- `phase_025`: Connection diagnostics return user-safe status codes and messages; raw keys, provider response bodies, and low-level network details remain server-side.
- `phase_025`: Generative chat orchestration, language-policy changes, SerpApi refinement, and chart redesign are recorded as separate future phases rather than bundled into provider diagnostics.
- `phase_026`: Configured OpenAI-compatible providers may extract structured chat intent before analysis, but deterministic quote resolution, typo confirmation, horizon validation, and credential gates remain authoritative.
- `phase_026`: LLM source hints can narrow collection to known adapter families; arbitrary user URLs and raw-text ingestion remain excluded until a dedicated ingestion phase.
- `phase_027`: Chat requests may carry an explicit UI-selected response language; backend copy and LLM prompts use it before falling back to message-language detection.
- `phase_027`: UI language remains a local frontend preference, passed per chat request rather than persisted into backend analysis settings.
- `phase_011`: Public analysis API responses must not expose internal LLM prompt material.
- `phase_011`: Request-boundary validation should reject malformed timestamps and oversized text before service logic runs.
- `phase_011`: Project-local skill descriptions should stay concise so the skills index loads without context-budget warnings.
- `phase_012`: Frontend static UI copy supports English and Korean independently from backend-generated conversation text.
- `phase_012`: UI theme preference is a local browser concern and does not change persisted backend analysis settings.
- `phase_012`: The product layout follows a ChatGPT-like left control rail with a central conversation workspace.
- `phase_014`: Backend-generated conversation text follows the current user message language for Korean and English.
- `phase_014`: Conversation follow-up handling can reuse the last resolved stock while still requiring an explicit investment horizon.
- `phase_015`: Likely stock typos must ask for explicit user confirmation before the assistant records an analysis request.
- `phase_015`: Local runner startup may open the frontend browser automatically, but the behavior must remain disableable for validation and automation.
- `phase_016`: Local BYOK credentials are encrypted at rest, returned only as masked metadata, and scoped for later login/user ownership.
- `phase_016`: `STUCK_LLM_CREDENTIAL_KEY` takes precedence for credential encryption; local development may auto-generate a key under `.local`.
- `phase_016`: Developer setup can write provider credentials through the same backend service contract used by future UI settings.
- `phase_017`: General/model/security settings belong in a ChatGPT-style modal, while Analysis, Snapshot, and Backtest are workspace navigation views.
- `phase_017`: Frontend credential UI must use masked credential status and send raw keys only on explicit save.
- `phase_018`: Live LLM calls must be credential-gated, source-grounded, structured, and separate from deterministic test/fallback providers.
- `phase_018`: Missing credentials should produce setup-needed assistant responses in the user's language instead of pretending that live analysis ran.
- `phase_018`: Chat-ready requests use the live analysis path only after stock and horizon are resolved; deterministic analysis remains available through the analysis endpoint.
- `phase_018`: The first live adapter is OpenAI-compatible with structured JSON output; unsupported providers must fail with explicit user-safe statuses.
- `phase_018`: Raw BYOK credentials are decrypted only at the live provider-call edge and must not appear in prompts, responses, logs, or stored analysis records.
