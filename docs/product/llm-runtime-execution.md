# LLM Runtime Execution

## Purpose

This document defines how the Stuck LLM runtime executes news, prediction, chart, and graph-related user requests. It complements `llm-agent-spec.md`: the spec defines the product contract, while this file defines the execution sequence and data boundaries that implementation agents should preserve.

`docs/product/llm-agent-phase-roadmap.md` is retired. Use the compact phase summaries under `docs/plan`, `docs/task`, and `docs/implement` for phase history and use this document for current runtime behavior.

## Runtime Principles

- Intent routing must choose one primary workflow before calling providers: general chat, follow-up chat, market snapshot, news digest, stock analysis, PnL/backtest, settings, or unsupported request.
- Stock analysis must not start until the market, symbol, quote, horizon, analysis mode, `as_of_at`, and candidate evidence set are resolved.
- News digest and market snapshot are valid standalone workflows. They must not silently run buy, hold, sell prediction.
- Chart and graph data are price data first. They may become analysis evidence only after conversion into a dated market-data source document and `as_of_at` filtering.
- LLM provider output is an evidence handoff, not the final probability engine. Local scoring computes buy, hold, sell probabilities and confidence from validated evidence items.
- PnL and backtest data are later evaluation artifacts. They must never be added to the historical evidence set for the original prediction.

## Intent Routing

1. Detect response language, requested market, stock query, action terms, horizon terms, source hints, and follow-up context.
2. Resolve explicit tickers or confirmed company names through the market-data universe.
3. Ask for confirmation when the symbol is ambiguous.
4. Route quote-only or stock-price requests to `market_snapshot`.
5. Route latest headlines, news, articles, or Korean news terms to `news_digest`.
6. Route recommendation, prediction, buy/hold/sell, swing, long-term, or analysis terms to `stock_analysis`.
7. Route buy-date, return, PnL, backtest, or what-if performance terms to `backtest_or_pnl`.
8. Keep `/help` and equivalent local commands before provider-backed intent routing.

## News Execution

1. Resolve target market, symbol, and company name.
2. Build query templates from company name, ticker, user terms, earnings, official announcements, business themes, regulatory themes, analyst reaction, and known mega-cap topics.
3. Choose news/search providers from the external-provider credential boundary. Resolve selected saved external credentials first; local environment credentials are compatibility fallbacks only and must not override selected keys.
4. If no paid external news/search key is selected, expand to the free RSS provider set: Seeking Alpha RSS, Yahoo Finance RSS, Google News RSS, and Bing News RSS.
5. Include EventRegistry only when an EventRegistry external credential is selected or available through the local-development compatibility boundary.
6. Include Reddit public search only when the user asks for Reddit, community, investor sentiment, or similar public social reaction. Keep it separate from article/news providers.
7. Extract user-supplied public URLs and crawl them only when they pass crawler safety checks. Seeking Alpha article URLs may be crawled through this direct URL path when publicly reachable. Convert supported Reddit search URLs into public Reddit search results when available.
8. Execute provider searches, RSS fetches, EventRegistry searches, Reddit public searches, and crawl runs with provider status tracking. Record completed, missing credential, provider error, empty result, cache hit, and cache miss states.
9. Canonicalize URLs and remove tracking parameters before dedupe.
10. Rank articles by importance, provider priority, publication time, original provider rank, source domain, and category diversity.
11. Prefer official, earnings, core business, controversy, and market-reaction articles over generic quote pages when enough alternatives exist.
12. Build a news digest with important articles, additional articles, provider runs, warnings, source dates, and links.
13. Render ChatGPT-style digest copy from the ranked article list, grouped by sections such as product or services, earnings or guidance, regulation or litigation, community or market reaction, official announcements, business or strategy, and other.
14. Include `as_of_at`, actual headline links, source domain, provider name, and publication date when known in the user-facing digest.
15. Optionally call an LLM only to rewrite the digest summary or localized article fields from supplied article metadata.
16. Treat digest output as presentation. It becomes prediction evidence only if converted into source documents and passed through the selected `as_of_at` cutoff.

## Prediction Execution

1. Resolve quote, horizon, analysis mode, `as_of_at`, language, and source hints.
2. Collect source documents from selected adapters, convert important news digest or crawl-derived articles into source documents when available, and add a market-data source document derived from the quote and eligible chart window context.
3. Normalize every source document with stable IDs, source metadata, `published_at`, `fetched_at`, URL, language, adapter, relevance, and safety flags.
4. Exclude sources with `published_at > as_of_at` and preserve the exclusion reason.
5. Apply prompt-budget limits after eligibility filtering. Prompt-budget exclusions remain visible in source audit output.
6. Build prompt context from eligible source documents only. Source content must be escaped and framed as untrusted evidence.
7. Resolve the per-message LLM credential first, then the active saved credential. If no selected or active LLM credential exists, return a setup-needed assistant response and store source audit state without making a live provider call.
8. If eligible evidence is empty, return needs-evidence state instead of fabricating claims.
9. If a compatible prediction artifact exists for the exact cache boundary, reuse it without recalling the provider.
10. Otherwise call the selected LLM provider with allowed source document IDs and structured-output requirements.
11. Validate provider output. Evidence items must cite only allowed document IDs and include stance, weight, summary, and excerpt.
12. If provider output is malformed, return a provider-error state with `provider_error_code` preserved; do not synthesize a local prediction fallback.
13. Run local scoring only after valid provider evidence extraction. Normalize buy, hold, and sell probabilities to 100 percent and compute confidence, expected range, downside probability, and similar-event baseline locally.
14. Persist response artifacts with provider, model, prompt version, response schema version, evidence hash, source audit, and cache metadata, but never raw API keys, decrypted credentials, hidden prompts, or user secrets.

## Chart And Graph Execution

- Market snapshot requests show quote, chart bars, key stats, provider state, and related news when available.
- Chart window controls may refetch market data for supported providers, such as a Google Finance-style US quote provider.
- Chart bars are rendered as UI price data and kept visually separate from LLM evidence and PnL/backtest output.
- Chart bars used in prediction must be summarized through a market-data source document with `published_at` and `fetched_at` equal to the quote `as_of_at`.
- Chart-derived evidence must ignore bars after the quote `as_of_at`.
- SerpApi Google Finance graph points are quote-line data, not full OHLC candles. If converted into bars, open, high, low, and close may share the same price.
- Loading, hover, empty, refetch-error, and responsive states must keep stable chart dimensions.
- PnL graphs are evaluation views. They must not be included in prediction prompts or prediction artifact evidence hashes.

## Cache And Artifact Boundaries

- News provider caches store reusable provider payloads and status by provider operation, query, symbol, and cache version.
- News processing records store digest lineage, provider runs, query templates, cache hits, and cache misses.
- Prediction artifacts are reusable only when market, symbol, horizon, analysis mode, `as_of_at`, selected credential-derived provider, model, base URL, prompt version, response schema version, and evidence hash match.
- Prompt, model, evidence, response schema, provider, horizon, or `as_of_at` changes must force prediction cache misses.
- Future PnL, future chart bars, later news, and backtest outcomes must not invalidate a frozen historical prediction by entering its evidence hash.

## User-Facing Output

- Show the selected workflow state near the response: market snapshot, news digest, analysis completed, setup needed, provider error, needs input, needs evidence, or PnL simulation.
- Show source dates, provider status, warning states, included/excluded source counts, prompt-used source IDs, and provider/model metadata near analysis output.
- Label stale, incomplete, provider-error, provider-limited, thin-evidence, and missing-credential responses explicitly.
- News digest replies should expose the evidence trail with headline links, source/provider badges, and `as_of_at` instead of presenting unsupported generic summaries.
- Prediction replies may use base, bull, and bear scenario sections for readability, but they must remain information-based scenario analysis tied to eligible evidence and local scoring output.
- Answer in the user's language when feasible while keeping provider names, tickers, source titles, and URLs accurate.

## Validation Expectations

- Intent routing tests should cover quote-only, news, prediction, PnL, settings, help, ambiguous stock, and follow-up paths.
- News tests should cover query planning, provider fakes, cache hit/miss records, URL canonicalization, ranking, diversity, missing credentials, provider errors, and LLM summary field limits without live network calls.
- Prediction tests should cover `published_at == as_of_at`, future-source exclusion, prompt document IDs, prompt-budget exclusion, missing credentials, malformed provider output, cache boundaries, local scoring, and absence of raw secrets.
- Chart tests should cover stable rendering, window refetch, error state, accessible chart data, and separation between market chart data and PnL graph data.
- E2E-style conversation tests should prove simple chat, news digest, prediction, repeated prediction cache reuse, and PnL separation with deterministic providers.
