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
- API keys should support both UI entry and environment-variable fallback.
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

## Planned Build Phases

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
