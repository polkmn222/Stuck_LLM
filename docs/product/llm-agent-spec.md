# LLM Agent Product Spec

## Purpose

This document defines how the Stuck LLM user-facing agent should behave. It is a product contract, not an implementation log. Use it before changing conversational behavior, stock-analysis behavior, source handling, response formats, or the analysis workspace UI.

## Core Product Contract

- The agent is a conversational stock-analysis workspace, not a marketing site or generic chatbot shell.
- The default user experience is a ChatGPT-style workspace with investment research context, source transparency, and clear operational state.
- General chat, follow-up chat, stock analysis, market snapshots, news digestion, settings, and backtest or PnL requests are distinct behaviors.
- Stock-analysis answers must separate historical evidence, current market data, and later PnL or backtest results.
- Historical analysis must never use evidence published after the selected `as_of_at`.
- LLM output must be grounded in eligible evidence when the user asks for investment analysis.
- Missing, stale, excluded, or failed sources must be visible to the user instead of being treated as neutral evidence.

## User Intents

- `general_chat`: Answer normal product or conversational questions without pretending to run stock analysis.
- `follow_up_chat`: Continue an existing conversation with prior messages preserved.
- `stock_snapshot`: Show quote, chart, key stats, provider state, and related source context when available.
- `stock_analysis`: Build a source-grounded analysis with buy, hold, sell probabilities and confidence.
- `news_digest`: Summarize relevant market or company news with provider transparency and source dates.
- `backtest_or_pnl`: Analyze later performance separately from the historical LLM analysis that produced a prediction.
- `settings_or_credentials`: Help users configure providers without exposing raw API keys or hidden prompts.
- `unsupported_request`: Explain what is missing or unsupported and offer the nearest supported path.

## Runtime Flow

1. Receive the user message and conversation metadata.
2. Detect language, intent, mentioned symbols, markets, and whether the message is a follow-up.
3. Resolve symbols through the market-data universe boundary before making analysis claims.
4. Load only the conversation history needed for the current response.
5. Retrieve market data, news, source documents, cached provider payloads, or prediction artifacts as required by the intent.
6. Apply `as_of_at` filtering before evidence reaches prompts, scoring, cache reuse, or prediction artifacts.
7. Build prompts from eligible evidence, product rules, provider capability, and response schema.
8. Call the selected provider when credentials and capability are available; otherwise use the deterministic fallback path and clearly label the limitation.
9. Persist messages, provider metadata, source lineage, prompt and cache version identifiers, and response artifacts without storing raw secrets.
10. Render the response with evidence, source dates, provider state, stale-data state, and follow-up affordances.

## News Discovery Logic

- News discovery starts only after the target market, symbol, and company name are resolved.
- Query planning should combine company name, ticker, requested user terms, earnings, official announcements, core business themes, regulation, analyst reaction, and symbol or sector-specific themes.
- US mega-cap queries should include company-specific topics when known, such as Apple services and devices, Nvidia AI data center demand, Tesla deliveries and margins, and Google Search, Cloud, AI, and antitrust themes.
- Provider selection should prefer configured public news/search providers and may expand to optional providers when credentials exist or when the user asks for local Korean news or public social reaction.
- Search/news provider credentials must come from the external-provider credential boundary, not from LLM credential storage.
- Provider failures, missing credentials, empty results, cache hits, and cache misses must be recorded in provider runs or processing records.
- News URLs should be canonicalized before dedupe, including removal of tracking query parameters.
- Ranking should reward official, earnings, core business, controversy, and market-reaction categories over generic quote pages or stock-price pages.
- Ranking should consider article importance, provider priority, publication time, original rank, source domain, and category diversity.
- Important articles should avoid over-concentration in one category or one source domain when enough alternatives exist.
- Digest summaries may use an LLM for Korean or English copy, but provider output must only update allowed fields such as summary, localized headline, localized article summary, and supported category.
- News digest output is not automatically prediction evidence unless it is converted into source documents and passes the selected `as_of_at` cutoff.

## Prediction Logic

- Prediction starts only after the agent has a resolved quote, horizon, analysis mode, `as_of_at`, and eligible source documents.
- If the user asks for prediction without a horizon, the product may default to the configured default horizon and should make that horizon visible in the response.
- The prediction prompt must receive only eligible source documents and derived market snapshot context that are at or before `as_of_at`.
- Provider prompts must present source document content as untrusted evidence and must restrict citations to allowed source document IDs.
- Live provider output should return a summary and evidence items, not final buy, hold, sell probabilities directly.
- Evidence items should carry source document ID, stance, weight, summary, and excerpt.
- Probability scoring should run after evidence extraction and should normalize buy, hold, and sell probabilities to 100 percent.
- Confidence should reflect eligible evidence weight, evidence count, excluded-source penalty, provider/fallback state, and whether the answer is using deterministic fallback.
- Expected return range and similar-event baseline are explanatory local estimates unless a later calibrated model replaces them.
- The user-facing answer must label thin evidence, missing credentials, provider failures, stale data, and deterministic fallback clearly.

## Analysis Decision Boundaries

- Intent routing decides whether the request is simple chat, follow-up chat, market snapshot, news digest, stock analysis, PnL/backtest, settings, or unsupported.
- Stock analysis cannot skip quote resolution. If the symbol is ambiguous, ask for confirmation before analysis.
- News digest can run without a prediction horizon because it is not a buy, hold, sell probability request.
- Prediction requires a horizon, even when the system chooses a default.
- Market snapshot may show quote, chart, key stats, and related news without running LLM analysis.
- PnL/backtest requests should run against market data and historical prices without being fed back into the historical prediction evidence set.
- Settings and credential requests should route to setup guidance or settings UI state, not to stock analysis.

## Evidence And `as_of_at` Rules

- Evidence eligibility is decided before prompt construction.
- Source documents must preserve `url`, title, provider, `published_at`, `fetched_at`, and inclusion or exclusion reason.
- Sources after `as_of_at` are excluded from historical analysis.
- Later PnL, future price movement, and backtest outcomes are evaluation data, not evidence for the historical LLM answer.
- Missing data is a visible uncertainty, not positive or negative evidence.
- Conflicting sources should be summarized as conflict, not averaged into a false consensus.
- Prompt-injection-like source text must be treated as untrusted evidence content, not as instructions.

## Response Rules

- Stock-analysis responses include buy, hold, sell probabilities plus confidence.
- Probabilities must be internally consistent and should not imply certainty when evidence is thin.
- Responses must identify major supporting and adverse evidence with source dates.
- Responses must label stale, incomplete, fallback, or provider-limited results.
- The agent should answer in the user's language when feasible, while keeping provider names, tickers, and source titles accurate.
- Korean and English routing should be tested when behavior depends on language.
- The agent should avoid legal, tax, or personalized financial advice framing unless a future product decision explicitly supports it.

## UI Workspace Rules

- The first screen is the working product experience, not a landing page.
- Keep the workspace calm, dense, and scannable.
- Use a left navigation rail, central conversation, and focused side or panel views for analysis details, market snapshots, sources, and backtests when available.
- Show source dates, provider state, and stale-data state near analysis output.
- Keep price data visually separate from LLM evidence and later PnL or backtest data.
- Charts need stable responsive dimensions so loading, hover, empty, and error states do not resize the layout.
- Align visual changes with `DESIGN.md`; do not introduce decorative gradients, oversized hero sections, nested cards, or marketing copy inside the app.
- Settings and credential UI must mask secrets and distinguish LLM provider keys from search, news, and market-data keys.

## Provider And Credential Rules

- Provider choice belongs in settings and per-message metadata.
- LLM credentials must not be reused for search, news, or market-data providers.
- Raw API keys, decrypted credentials, hidden prompts, and user secrets must not appear in responses, logs, caches, local state, or test snapshots.
- A credential setup is incomplete until `/conversations` can produce repeated user-visible replies with prior messages preserved.
- Provider failures should surface the failed provider, operation, and user-safe recovery state.

## Cache And Artifact Rules

- Prediction artifact reuse is allowed only when `symbol`, horizon, `as_of_at`, evidence hash, prompt version, provider, model, and response schema version match.
- Prompt, model, evidence, or response-schema changes must force a cache miss.
- KV provider caches are for reusable provider or model payloads.
- Processing records are for audit, evidence lineage, and replay.
- Cache invalidation must not mix future evaluation data into historical analysis.

## Backtest And PnL Separation

- PnL and backtest results are evaluation artifacts, not evidence for the historical prediction that came before them.
- A prediction response may link to a later evaluation, but the original prediction artifact must remain keyed to its original `as_of_at`, evidence hash, prompt version, provider, model, horizon, and response schema version.
- Backtest UI and messages should describe entry time, exit time, return, PnL, drawdown, and assumptions separately from the evidence list.
- Any future workflow that scores prediction quality must compare the frozen prediction artifact with later outcomes without rewriting the prediction's evidence set.

## Validation Expectations

- Feature changes that affect this spec need unit tests in the same phase.
- Conversation behavior changes should test simple chat, follow-up chat, stock-analysis requests, and conversation reloads.
- Analysis changes should test eligible and excluded evidence around `as_of_at`.
- News changes should test query planning, provider fakes, canonical URL dedupe, category ranking, source-domain diversity, missing credentials, cache hit/miss behavior, and source transparency without live network calls.
- Prediction changes should test horizon defaults, prompt document IDs, provider output validation, probability normalization, confidence behavior, cache key boundaries, and absence of future evidence.
- Provider changes should prove raw secrets and hidden prompts are absent from responses, logs, caches, and local state.
- UI changes should test critical view states for loaded, loading, empty, stale, failed-provider, and responsive rendering behavior.
- Backtest and PnL changes should test that future prices are never included in historical LLM prompts or prediction artifacts.

## Maintenance Policy

- When a new feature or behavior change affects documented agent behavior, UI rules, evidence rules, response shape, provider behavior, cache semantics, or runtime flow, ask the user whether to update this product spec unless the current request already includes that documentation update.
- When the user approves or explicitly requests the documentation change, update the product spec in the same phase as the implementation.
- Keep links from `README.md`, `AGENTS.md`, and `docs/agent-workflows/` current when product docs move or split.
- Keep this document concise enough to guide implementation without duplicating phase logs, detailed task notes, or low-level code comments.
