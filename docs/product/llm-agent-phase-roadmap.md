# LLM Agent Phase Roadmap

Purpose
- Define the next implementation sequence for the user-facing LLM stock-analysis agent.
- Keep future phases small enough for agents to implement, validate, and document independently.
- Make news discovery, prediction, UI, cache, and PnL boundaries visible before code changes.

Current Status
- `phase_111` through `phase_118` have implementation coverage in the compact phase summaries under `docs/plan`, `docs/task`, and `docs/implement`.
- The runtime validation matrix now covers simple chat, news digest, prediction, prediction cache reuse, and PnL separation with deterministic providers.

## phase_109 - Product Spec Detail And Roadmap

Goal
- Expand the product contract with explicit news discovery, prediction, analysis-boundary, cache, and PnL separation rules.

Scope
- Update `docs/product/llm-agent-spec.md`.
- Add this roadmap and link it from product documentation entry points.

Acceptance Criteria
- News discovery and prediction logic are explicitly documented.
- The next implementation phases are listed with scope and validation expectations.
- Product docs state when later implementation must ask before updating specs.

Validation
- Run documentation placeholder checks and whitespace checks.

## phase_110 - News Retrieval Pipeline

Goal
- Make the news retrieval pipeline an explicit backend boundary instead of scattered private helper behavior.

Scope
- Define a testable news query plan for symbol, company, requested user text, sector themes, provider capabilities, and optional social/local sources.
- Preserve canonical URL dedupe, category scoring, provider status, query templates, and source-domain diversity.
- Keep provider calls mocked in tests.

Acceptance Criteria
- Query planning produces deterministic templates for Apple, Google/Alphabet, Nvidia, Tesla, and representative S&P 500 sectors.
- Provider runs report completed, missing credential, provider error, empty, cache hit, and cache miss states.
- Important articles prefer official, earnings, core business, controversy, and market-reaction sources over quote pages.
- Raw provider credentials are absent from responses, caches, logs, and snapshots.

Validation
- Backend unit tests for query plans, provider fakes, dedupe, ranking, diversity, and missing credentials.

## phase_111 - Evidence Normalization

Goal
- Convert market data, news, and source documents into one auditable evidence contract before LLM prompts.

Scope
- Normalize `published_at`, `fetched_at`, source URL, provider, source type, language, relevance, and safety flags.
- Preserve excluded sources with reasons instead of deleting them.
- Treat source text as untrusted content.

Acceptance Criteria
- `published_at == as_of_at` is included.
- `published_at > as_of_at` is excluded with `published_after_as_of_at`.
- Missing source data is surfaced as uncertainty, not neutral evidence.
- Prompt context contains only eligible source documents and no raw secrets or hidden system prompts in stored artifacts.

Validation
- Backend unit tests for cutoff equality, future-source exclusion, prompt document IDs, source warnings, and prompt-injection-like text.

## phase_112 - Prediction Orchestration

Goal
- Keep stock prediction orchestration explicit from intent routing through quote resolution, evidence collection, provider call, and scoring.

Scope
- Separate simple chat, follow-up chat, market snapshot, news digest, stock analysis, PnL/backtest, and settings behavior.
- Require resolved quote and horizon before prediction.
- Use configured defaults only when the response clearly labels them.

Acceptance Criteria
- Ambiguous stock requests ask for confirmation before analysis.
- News digest does not require horizon and does not run stock analysis.
- Prediction requests collect eligible evidence and call the provider only when credentials are available.
- Missing credentials return setup guidance in Korean and English.

Validation
- Backend conversation tests across intent, symbol, language, follow-up, missing credential, and confirmed-stock paths.

## phase_113 - Probability And Confidence Rules

Goal
- Make probability and confidence scoring behavior explicit, stable, and testable.

Scope
- Normalize buy, hold, and sell probabilities to 100 percent.
- Compute confidence from evidence weight, evidence count, excluded-source penalty, and fallback/provider state.
- Keep expected return range and similar-event baseline clearly labeled as local estimates.

Acceptance Criteria
- Empty evidence returns `needs_evidence` with zero probabilities.
- Thin evidence produces lower confidence than diverse eligible evidence.
- Bearish, bullish, and neutral evidence produce directionally coherent probabilities.
- Probability output remains internally consistent after rounding.

Validation
- Backend scoring tests for empty, bullish, bearish, neutral, mixed, excluded-source, and rounding cases.

## phase_114 - Analysis UI Surface

Goal
- Show prediction, confidence, evidence, provider, and stale-data state in the workspace without mixing price data and LLM evidence.

Scope
- Keep the chat as the central workspace.
- Surface buy, hold, sell probabilities, confidence, expected range, downside risk, and similar-event baseline.
- Show included, excluded, prompt-used, stale, and failed-provider states near source audit output.

Acceptance Criteria
- Loaded, loading, empty, setup-needed, provider-error, stale-data, and needs-evidence states are readable on desktop and mobile.
- Source dates and provider state are visible near analysis output.
- Charts keep stable dimensions when changing windows or loading.

Validation
- Frontend unit tests for analysis states, source audit states, probability rendering, and responsive-safe text.

## phase_115 - News Digest UX

Goal
- Make news digest useful as a separate user workflow and as a transparent input candidate for later analysis.

Scope
- Render important articles, additional articles, provider runs, warnings, source dates, source domains, and localized summaries.
- Keep news digest visually separate from prediction evidence and PnL/backtest output.

Acceptance Criteria
- News digest cards show article title, source, date, category, provider, query context, and link when available.
- Additional articles are expandable without resizing the overall workspace unpredictably.
- Missing provider credentials and provider errors are visible but do not expose secrets.

Validation
- Frontend tests for Korean and English copy, provider transparency, article expansion, warnings, and empty states.

## phase_116 - Prediction Cache Boundary

Goal
- Enforce prediction artifact reuse only when the historical analysis boundary is identical.

Scope
- Key artifacts by market, symbol, horizon, `as_of_at`, evidence hash, prompt version, provider, model, base URL, and response schema version.
- Store audit metadata without raw API keys, hidden prompts, or user secrets.

Acceptance Criteria
- Same boundary reuses the artifact without recalling the provider.
- Different `as_of_at`, evidence hash, prompt version, provider, model, horizon, or schema version causes a cache miss.
- Future PnL/backtest results never invalidate or rewrite historical prediction evidence.

Validation
- Backend cache tests for reuse, cache miss dimensions, secret absence, and future-evaluation separation.

## phase_117 - Backtest And PnL Separation

Goal
- Add or refine later-outcome evaluation without contaminating historical LLM analysis.

Scope
- Treat PnL and backtest as evaluation artifacts tied to entry, exit, assumptions, and market data.
- Link evaluations to frozen prediction artifacts when available.
- Keep the original prediction evidence set immutable.

Acceptance Criteria
- PnL responses show entry time, exit time, return, PnL, max drawdown, and assumptions.
- Historical prediction prompts and stored prediction artifacts contain no future prices.
- Evaluation records can compare later outcomes with frozen prediction output.

Validation
- Backend tests for PnL calculation, missing price data, future-price exclusion from prompts, and artifact immutability.

## phase_118 - End-To-End Validation Matrix

Goal
- Prove the full user-visible path across chat, news, prediction, cache, provider errors, and PnL separation.

Scope
- Use deterministic provider fakes and fixture market/news data.
- Cover Korean and English, Apple, Google/Alphabet, Nvidia, Tesla, representative S&P 500 sectors, missing credentials, stale data, provider failures, follow-up conversations, and conversation reloads.

Acceptance Criteria
- `/conversations` proves simple chat, follow-up chat, stock analysis, news digest, setup-needed, provider-error, and PnL paths.
- Raw keys, hidden prompts, and future evidence are absent from responses, logs, caches, local state, and snapshots.
- Frontend critical views render the resulting states clearly.

Validation
- Backend E2E-style tests with deterministic providers.
- Focused frontend unit tests for rendered state handoff.
- Project docs validation after implementation.

## Operating Rule

- Each phase should update implementation docs and backups at handoff time, while still preserving existing files before editing when repository rules require pre-edit backups.
- If a phase changes documented product behavior, ask the user before changing product specs unless the user request already includes that documentation update.
