# Orchestration Workflow

## Phase Discipline

- Use one active phase at a time.
- Name phases as `phase_001`, `phase_002`, and so on.
- Keep `docs/task.md` and `docs/implement.md` newest-first.
- Create backups under `backups/<phase_id>/` for modified non-backup files.

## Recommended Execution Order

1. Update `docs/task.md` with the phase goal and acceptance criteria.
2. Inspect the relevant files and existing docs.
3. Implement the smallest coherent slice.
4. Update `docs/implement.md` with decisions and validation.
5. Copy modified non-backup files to `backups/<phase_id>/`.
6. Run validation and fix failures.
7. Summarize changed files, validation, and residual risks.

## Service Addition Order

1. `chat-service` and settings.
2. `market-data-service`.
3. `ingestion-service`.
4. `analysis-service`.
5. `scoring-service`.
6. `backtest-service`.
7. Hosted/team mode.

## Decision Logging

Record architecture decisions in `docs/plan.md` until a dedicated ADR folder exists. Use ADR files once the implementation introduces irreversible choices such as database migration tooling, auth provider, or deployment platform.

## Permission Policy

- Run non-destructive installation, setup, validation, discovery, and local execution commands without asking for extra user confirmation.
- Still follow system sandbox rules when a tool explicitly requires approval.
- Ask before destructive cleanup, credential exposure, paid external actions, production deployment, or broad changes outside the current request.

## Docs Change Policy

- Keep docs aligned with code and policy changes.
- If the current user request already includes the needed docs change, update docs directly.
- If a code or policy change implies additional docs updates outside the current request, ask before editing those docs.
- Update `docs/task.md` and `docs/implement.md` for every phase-level implementation, installation, workflow, or policy change.
- Back up every modified non-backup file under `backups/<phase_id>/`.

## Skill Routing By Situation

### Product Or Requirements Discovery

- Use `brainstorming` when product behavior, target users, workflows, or scoring semantics are still unclear.
- Use `ask-questions-if-underspecified` when a missing decision could change architecture, cost, safety, data access, or acceptance criteria.
- Use `create-plan` for repository-grounded implementation plans.
- Use `concise-planning` for short execution checklists after the design is already accepted.

### Architecture And Backend Design

- Use `architecture` for service boundaries, ADRs, trade-off analysis, and modular-to-service extraction decisions.
- Use `backend-development` for backend API shape, service decomposition, microservice patterns, and implementation structure.
- Use `api-design-principles` for REST/GraphQL routes, request/response contracts, error formats, pagination, idempotency, and developer-facing API consistency.
- Use `database-design` for schema design, migrations, indexing, normalization, and data lifecycle modeling.
- Use `supabase-postgres-best-practices` for PostgreSQL query performance, schema review, indexes, RLS-adjacent thinking, and operational Postgres guidance.

### Frontend And UI

- Use `frontend-design` whenever building or changing user-facing UI, including chat, settings, dashboards, analysis details, and PnL views.
- Use `vercel-react-best-practices` when writing, reviewing, or refactoring React/Next.js components, pages, data fetching, performance, or bundle-sensitive code.
- Use `web-design-guidelines` for UI audits, accessibility checks, forms, focus states, navigation state, responsive behavior, and UX review.
- Use `shadcn` only when the project adopts shadcn/ui or has a `components.json` file.

### LLM Providers And AI Behavior

- Use `llm-application-dev` for prompt engineering, RAG patterns, provider abstraction, tool-calling design, hallucination reduction, and LLM app architecture.
- Use `openai-docs` for current OpenAI API/model usage, model selection, structured outputs, tool calls, and migration guidance.
- Use `provider-credentials` for BYOK provider setup, encrypted API-key storage, secret masking, credential deletion, and login-ready credential boundaries.
- Use `stock-analysis-llm` for live stock-analysis LLM calls, strict `as_of_at` prompt construction, missing-credential responses, and provider/deterministic fallback separation.
- Use `security-auditor` when LLM prompts include user content, URLs, source documents, credentials, or external provider calls.
- Provider/API-key work must validate the real `/conversations` user path, not only Settings connection diagnostics.
- Separate acceptance criteria for simple chat, follow-up chat in the same conversation, and stock-analysis requests.
- A successful provider phase must prove repeated use across one conversation, with prior messages preserved and raw keys absent from responses, prompts, logs, and local state.

### Setup And Credentials

- Use `provider-credentials` before changing CLI setup, web settings, local credential storage, provider config schemas, or API key masking.
- Use `security-auditor` for credential threat modeling, encryption key handling, hosted-mode restrictions, and raw-secret exposure checks.
- Use `api-design-principles` for credential API contracts, redacted responses, delete semantics, and validation errors.
- Use `backend-development` for credential routes, services, local repositories, and setup command integration.
- Use `frontend-design`, `vercel-react-best-practices`, and `web-design-guidelines` when moving credential entry into the ChatGPT-style settings modal.
- Use `lint-and-validate` after every credential or setup change.

### Data Ingestion, Search, And Crawling

- Use `firecrawl` for search, scrape, map, crawl, browser extraction, or LLM-ready markdown from public web sources.
- Use `agent-browser` when data extraction or verification requires page interaction, login/session handling, screenshots, form actions, or browser QA.
- Use `apify-ultimate-scraper` when a supported platform actor is a better fit for social, trend, Reddit, brand-monitoring, or structured extraction tasks.
- Use `security-auditor` before implementing URL ingestion, arbitrary fetches, crawler execution, SSRF-sensitive endpoints, or handling third-party page content.
- Use `systematic-debugging` for blocked crawlers, inconsistent extraction, source timestamp errors, flaky browser automation, or API failures.
- Keep LLM provider keys separate from search/news/market-data keys such as `SERPAPI_API_KEY`, `NAVER_CLIENT_ID`, `TAVILY_API_KEY`, and `GNEWS_API_KEY`.
- When users expect a Google Finance-style result, expand the snapshot schema and UI for chart, key stats, news, and related data instead of stopping at the minimal `MarketQuote`.

### Historical Evidence And Scoring

- Use `architecture` when changing the boundary between ingestion, analysis, scoring, and backtest services.
- Use `test-driven-development` before implementing `as_of_at` filtering, source inclusion/exclusion, evidence weighting, or scoring.
- Use `stock-analysis-llm` before connecting eligible evidence to live provider calls or changing source-grounded analysis prompts.
- Use `systematic-debugging` for probability mismatches, cutoff leaks, missing evidence, duplicated sources, or confidence-score regressions.
- Use `security-auditor` when source text could include prompt injection or when evidence is sent to external LLM providers.

### Backtesting, PnL, And Quant Analytics

- Use `quant-backtest` for systematic trading infrastructure, portfolio backtests, walk-forward validation, transaction costs, look-ahead bias, risk metrics, and mark-to-market logic.
- Use `vectorbt-expert` for VectorBT implementation, signals, entries/exits, position sizing, equity curves, drawdowns, and trade analysis.
- Use `backtesting-trading-strategies` for broader strategy validation and performance comparison.
- Use `backtest` for quick script-based backtest generation.
- Use `quick-stats` for fast stats checks without creating files.
- Use `optimize` for parameter sweeps and heatmaps after baseline correctness is established.
- Use `strategy-compare` to compare multiple strategies or long/short directions.
- Use `setup` only when intentionally bootstrapping the Python backtesting environment.

### Testing, Validation, And Review

- Use `test-driven-development` before feature and bugfix implementation.
- Use `lint-and-validate` after every code change and before final handoff.
- Use `webapp-testing` for local webapp Playwright checks, screenshots, console logs, and server lifecycle testing.
- Use `code-review-checklist` when reviewing changes for functionality, security, performance, maintainability, and missing tests.
- Use `review-claude` only when the user explicitly asks for a Claude second-pass review.
- Use `systematic-debugging` whenever tests fail or behavior is unexpected.

### Skills, Plugins, And Agent Workflow

- Use `find-skills` when asked to discover, rank, install, or maintain project-relevant skills.
- Use `skill-installer` for installing skills from curated lists or GitHub sources.
- Use `skill-creator` when creating or improving project-specific skills, such as Naver source ingestion, Korean market data, or scoring-evaluation skills.
- Use `plugin-creator` only when packaging a local Codex plugin or marketplace entry.
- Use `agents-md` when editing `AGENTS.md`; keep it short and link to detailed docs.
- Use `agent-workflow-docs` when changing code-authoring, validation, orchestration, or phase artifact workflows.

### Deployment And Later Operations

- Use `architecture` before choosing deployment, queues, auth, or service extraction.
- Use `security-auditor` for auth, API keys, secrets, logs, crawler credentials, and hosted multi-user risks.
- Use `lint-and-validate` and `webapp-testing` before exposing a running app to team users.
- Re-run `find-skills` before adopting new deployment, observability, hosted database, or CI/CD tooling.
