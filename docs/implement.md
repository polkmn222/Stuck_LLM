# Implementation Log

Newest phases go first. Record concrete implementation notes, commands, validation, and unresolved risks for each phase.

## phase_088 - News Source Validation, Docs, And Push Prep

Status: completed

Implementation notes:

- Recorded completed task, plan, and implementation notes for `phase_083` through `phase_088`.
- Preserved documentation backups under `backups/phase_088/` after code validation was complete, per the user's requested ordering.

Validation:

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 146 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache PYTHONPATH=src/backend python3 -m compileall src/backend/app/features/news_digest src/backend/app/features/conversations src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py` passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend/app/features/news_digest src/backend/app/features/conversations/service.py src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py` passed.
- `PYTHONPATH=src/backend python3 -m mypy src/backend/app/features/news_digest src/backend/app/features/conversations/service.py` passed with no issues.
- `cd src/frontend && npm test -- --run` passed with 51 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` first failed in the sandbox because `registry.npmjs.org` could not resolve, then passed with 0 vulnerabilities after approved network access.
- `git diff --check` passed.

Risks and follow-ups:

- Public social coverage intentionally uses search-indexed public pages only. Direct X/Facebook crawling is not implemented because authenticated scraping and private content access would add legal, operational, and security risk.

## phase_087 - Korean Prediction Intent Fallback

Status: completed

Implementation notes:

- Added `predict`, `prediction`, `forecast`, and `예측` to stock-analysis keywords.
- Added a regression test where the LLM intent provider returns `other`, proving `애플 예측` still routes to live analysis with the default five-trading-day `swing` horizon.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase077_prediction_probabilities.py::test_korean_prediction_keyword_routes_to_analysis_without_llm_intent -q` failed with `market_snapshot`.
- GREEN: the same test passed after the keyword fix.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase077_prediction_probabilities.py -q` passed.

Risks and follow-ups:

- The completed live analysis path still requires a saved LLM credential for evidence extraction.

## phase_086 - Naver And Public Social News Sources

Status: completed

Implementation notes:

- Added `naver_news` and `serpapi_social_web` to the news digest provider contract and frontend type union.
- Added Naver News API collection using `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET`.
- Added public SNS search through SerpApi Google Web with queries restricted to `x.com`, `twitter.com`, and `facebook.com`.
- Defaults now append Naver only when Naver credentials are present, and append social search only when a social/person/policy cue is present in the user's query.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_news_digest_uses_naver_and_public_social_search_when_credentials_available -q` failed before provider-specific social queries existed.
- GREEN: the same test passed after provider routing and collectors were implemented.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py -q` passed with 9 tests.

Risks and follow-ups:

- Naver coverage depends on user-supplied Naver API credentials.
- Public social search only sees indexed public posts and should be treated as supplemental sentiment/context, not complete social coverage.

## phase_085 - Diverse News Selection

Status: completed

Implementation notes:

- Added `_select_diverse_articles` so important articles are selected with category and source-domain caps before fallback fill.
- Fixed keyword matching so short tokens such as `ai` require word boundaries.
- Narrowed controversy classification by removing broad `risk` matching, which misclassified analyst valuation-risk articles.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_news_digest_selects_diverse_important_articles -q` failed before the selector existed.
- GREEN: the same test passed after selector and classifier fixes.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py -q` passed.

Risks and follow-ups:

- Category detection remains keyword-based; LLM article metadata can refine it when provider summaries are available.

## phase_084 - News Query Diversification

Status: completed

Implementation notes:

- Added `_build_news_queries` to generate multiple company-event searches for US stocks.
- Queries now cover earnings, product/service/AI strategy, CEO/leadership succession, regulation/lawsuit/antitrust controversy, analyst/valuation consensus, and S&P Global Market Intelligence research.
- Provider run transparency now records every provider/query pair.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_news_digest_builds_diversified_us_company_event_queries -q` failed before `_build_news_queries` existed.
- GREEN: the same test passed after query generation was implemented.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py -q` passed after existing tests were updated for multi-query provider runs.

Risks and follow-ups:

- The S&P Global item is discovered through provider search results; full article extraction depends on the external source being reachable and accessible.

## phase_083 - Typo And News Intent Recovery

Status: completed

Implementation notes:

- Added typo patterns for Korean news requests such as `뉴ㅛㅡ`.
- Updated local news-intent routing to recover common typo forms without relying on LLM intent classification.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_korean_news_typo_routes_to_news_digest_without_llm_intent -q` failed with `market_snapshot`.
- GREEN: the same test passed after typo recovery was added.
- Targeted regression: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase055_058_market_chat.py src/backend/tests/test_phase077_prediction_probabilities.py -q` passed with 13 tests.

Risks and follow-ups:

- Typo recovery is conservative and currently targets common news-keyword mistakes rather than a full spelling-correction engine.

## phase_082 - Prediction Docs, Backups, And Full Validation

Status: completed

Implementation notes:

- Added task and plan records for `phase_077` through `phase_082`.
- Preserved final modified-file backups under `backups/phase_082/` after all code and validation work was complete, per the user's requested ordering.

Validation:

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 141 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `python3 -m ruff check src/backend/app src/backend/tests` passed.
- `python3 -m mypy src/backend/app` passed with 53 source files.
- `cd src/frontend && npm test` passed with 51 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` first failed in the sandbox because `registry.npmjs.org` could not resolve, then passed with 0 vulnerabilities after approved network access.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.

Risks and follow-ups:

- Similar-event calibration is currently a local baseline slot derived from evidence stance, not a true historical event-matching model.

## phase_081 - Similar Event Calibration Baseline

Status: completed

Implementation notes:

- Added `similar_event_sample_count`, `similar_event_win_rate`, and `similar_event_median_return_pct` to score responses.
- Exposed the similar-event baseline in Korean/English chat copy and the analysis panel.
- Kept the implementation as a replaceable local baseline so a later historical matching engine can fill the same contract.

Validation:

- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase077_prediction_probabilities.py -q` passed after adding the new fields and chat assertions.
- RED/GREEN: `cd src/frontend && npm test -- AnalysisPanel.test.tsx api.test.ts` passed after frontend mapping and UI assertions were updated.

Risks and follow-ups:

- The baseline should be replaced by a real event similarity dataset before treating the win rate as statistically meaningful.

## phase_080 - Historical Buy-Date PnL Chat

Status: completed

Implementation notes:

- Added `pnl_simulation` conversation status and optional `backtest_result` payloads on conversation responses and assistant messages.
- Parsed Korean, ISO, and English month/day buy-date phrases into market-close timestamps.
- Routed buy-date questions to `run_backtest` with quantity `1.0`, separate from analysis requests.
- Extended seeded AAPL backtest bars back to April 1, 2026 for the example flow.

Validation:

- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase080_pnl_chat.py src/backend/tests/test_phase009_backtest.py -q` passed.
- RED/GREEN: `cd src/frontend && npm test -- api.test.ts` passed after PnL conversation mapping was added.

Risks and follow-ups:

- PnL chat currently depends on seeded/local price bars. Provider-backed historical bars should be added before broad date coverage is expected.

## phase_079 - Expected Return And Downside Risk

Status: completed

Implementation notes:

- Added rough expected return min/max percentage fields and downside probability to `ScoreResponse`.
- Derived the expected range from the buy/sell directional edge and confidence score.
- Added chat copy and analysis-panel rendering for expected return and downside risk.

Validation:

- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase077_prediction_probabilities.py -q` passed.
- RED/GREEN: `cd src/frontend && npm test -- AnalysisPanel.test.tsx api.test.ts` passed.

Risks and follow-ups:

- Expected return range is an MVP heuristic and is labeled as such in scoring rationale; it is not yet calibrated against real historical outcomes.

## phase_078 - Market Data Evidence Bundle

Status: completed

Implementation notes:

- Created a `market_data` source document from each quote's latest price, previous close, session change, and eligible chart closes.
- Filtered chart bars after the quote `as_of_at` before deriving chart context.
- Appended the market-data document to live-analysis source documents so source audit and LLM prompt grounding can show chart/market context.

Validation:

- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase077_prediction_probabilities.py -q` passed after verifying `market_data` appears in source audit and live provider documents.
- Full backend validation initially failed one existing orchestration assertion because `market_data` is now expected in `included_by_source_type`; the test was updated and the full backend suite passed.

Risks and follow-ups:

- Market-data evidence summarizes available quote/chart context; it does not yet compute richer technical indicators.

## phase_077 - Five Trading Day Prediction Probabilities

Status: completed

Implementation notes:

- Defaulted prediction-like no-horizon analysis requests to `swing`, which the response labels as the next five trading days.
- Attached `ScoreResponse` to completed `AnalysisResponse` values produced through the conversation path.
- Added score text to assistant analysis replies and rendered completed probabilities in the analysis panel.
- Preserved generic `분석해줘` horizon clarification behavior; prediction/buy/sell phrases use the new default.

Validation:

- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase077_prediction_probabilities.py src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase020_security_and_concurrency.py -q` passed.
- RED/GREEN: `cd src/frontend && npm test -- AnalysisPanel.test.tsx api.test.ts` passed.

Risks and follow-ups:

- Completed probabilities still require a saved LLM key because evidence stance extraction remains LLM-backed in the live conversation path.

## phase_076 - News Polish Docs, Backups, And Validation

Status: completed

Implementation notes:

- Added task and plan records for `phase_070` through `phase_076`.
- Preserved documentation backups under `backups/phase_076/`.
- Implementation backups were created before editing `run-all.sh`, news digest backend files, conversation service, frontend API/types, chat UI, and styles.

Validation:

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 139 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `python3 -m ruff check src/backend/app src/backend/tests` passed.
- `python3 -m mypy src/backend/app` passed with 53 source files.
- `cd src/frontend && npm test` passed with 49 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` first failed in the sandbox because `registry.npmjs.org` could not resolve, then passed with 0 vulnerabilities after approved network access.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.

Risks and follow-ups:

- Favicon rendering uses Google's favicon endpoint in the browser. If offline or blocked, the card still shows text content, but the icon may not load.

## phase_075 - Korean News Digest Cards

Status: completed

Implementation notes:

- Reworked `NewsDigestView` to render a Korean headline/summary list before article cards.
- Replaced the plain ordered article list with compact cards showing favicon-style icon, source domain, provider, category, original title link, and clipped summary.
- Added CSS line clamps and `overflow-wrap` so long provider snippets do not push outside the chat message box.
- Extended frontend API/types to carry `category`, `headlineKo`, `summaryKo`, `importanceScore`, and `sourceDomain`.

Validation:

- RED: `cd src/frontend && npm test -- ChatShell.test.tsx api.test.ts` failed because the new API fields and UI elements were absent.
- GREEN: the same command passed with 22 tests.

Risks and follow-ups:

- The UI still exposes provider adapter IDs for transparency. A later presentation pass can add friendly labels while keeping adapter IDs available.

## phase_074 - LLM Korean News Metadata

Status: completed

Implementation notes:

- Updated the news summary prompt to ask for compact JSON with digest `summary` and per-article Korean metadata.
- Added JSON extraction and safe per-article updates keyed by article ID.
- Kept plain text summary fallback for providers that do not return JSON.

Validation:

- Covered by `test_llm_news_json_updates_korean_article_headlines`.

Risks and follow-ups:

- LLM article translation quality depends on the saved provider. Deterministic fallback uses the original provider title/snippet when JSON output is unavailable.

## phase_073 - News Importance Categories

Status: completed

Implementation notes:

- Added `NewsCategory` and article fields for category, Korean headline/summary, importance score, and source domain.
- Added category detection for earnings, official, core business, controversy, market reaction, product/service, quote pages, and other.
- Ranked deduped articles by importance score before timestamp and provider rank.

Validation:

- Covered by `test_news_digest_prioritizes_official_earnings_and_business_news_over_quote_pages`.

Risks and follow-ups:

- Category detection is keyword-based until LLM metadata is available. It is intentionally conservative and can be refined with real search samples.

## phase_072 - News Query And Quote Page Demotion

Status: completed

Implementation notes:

- Changed US news search query generation from `stock news` to `latest company news earnings official business controversy`.
- Added quote-page detection for Google Finance/Yahoo Finance-style price/history pages and negative scoring for those results.
- Normalized and truncated provider snippets to prevent long navigation text from reaching the UI.

Validation:

- Covered by `test_news_digest_query_targets_news_instead_of_stock_price_pages`.

Risks and follow-ups:

- Providers can still return quote pages when the result set is sparse; they should now fall below actual news when news results are present.

## phase_071 - Joint Dev Server Shutdown

Status: completed

Implementation notes:

- Split `run-all.sh` traps into `trap cleanup EXIT` and `trap shutdown INT TERM`.
- Added `shutdown()` so Ctrl+C clears traps, terminates both tracked child processes, waits for them, and exits with code 130.
- Started backend and frontend commands with `exec` so the recorded PIDs correspond to the server processes rather than wrapper shells.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase015_runner_and_typo_confirmation.py::test_run_all_ctrl_c_uses_shutdown_trap_and_execs_server_processes -q` failed because `shutdown()` and `exec` were absent.
- GREEN: targeted backend command passed after the script update.

Risks and follow-ups:

- `npm run dev` still owns the Vite child lifecycle internally. In normal npm behavior, terminating npm should terminate Vite; if a future environment leaves Vite orphaned, add process-tree cleanup.

## phase_070 - Ruff And MyPy Install

Status: completed

Implementation notes:

- Installed `ruff 0.15.12` and `mypy 1.19.1` into the user Python environment with `python3 -m pip install --user`.
- The backend `pyproject.toml` already listed both tools under `[project.optional-dependencies].dev`, so no project dependency file change was needed.

Validation:

- `python3 -m ruff --version` reported `ruff 0.15.12`.
- `python3 -m mypy --version` reported `mypy 1.19.1 (compiled: yes)`.
- Full phase validation under `phase_076` used both tools successfully.

Risks and follow-ups:

- The installed console scripts are in the user Python bin directory, which is not on PATH. Use `python3 -m ruff` and `python3 -m mypy`, or add that bin directory to PATH later.

## phase_069 - News Digest Docs, Backups, And Validation

Status: completed

Implementation notes:

- Added reverse-chronological task and plan records for `phase_064` through `phase_069`.
- Preserved pre-documentation copies under `backups/phase_069/`.
- Preserved implementation-file copies under `backups/phase_064/` before modifying the news, conversation, API, chat, and style surfaces.

Validation:

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 135 tests and one local urllib3 LibreSSL warning.
- `cd src/frontend && npm test` passed with 49 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` first failed in the sandbox because `registry.npmjs.org` could not resolve, then passed with 0 vulnerabilities after approved network access.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `python3 -m ruff ...` and `python3 -m mypy ...` could not run because this interpreter does not have runnable Ruff or MyPy modules installed.

Risks and follow-ups:

- Live news quality depends on provider quotas and provider result metadata. Missing provider credentials are surfaced in the digest warnings instead of blocking all results.

## phase_068 - Chat News Digest UI

Status: completed

Implementation notes:

- Added `NewsDigest`, `NewsArticle`, and provider-run UI types plus API snake_case to camelCase mapping.
- Rendered news digests inside assistant messages with a concise overview, linked important stories, provider transparency chips, and warning copy.
- Added a `나머지 기사 보기` / `Show more articles` button that reveals additional articles only on demand.

Validation:

- RED: `cd src/frontend && npm test -- ChatShell.test.tsx api.test.ts` failed because API mapping and news digest UI rendering were absent.
- GREEN: the same command passed with 22 tests.

Risks and follow-ups:

- The UI currently renders provider names as internal adapter IDs. A later polish pass can add user-facing provider labels without changing the transparent audit data.

## phase_067 - Chat News Request Routing

Status: completed

Implementation notes:

- Added `news_digest` to chat intent and conversation status types.
- Routed news-keyword requests before the market snapshot path so news-only requests do not ask for horizon.
- Added top-level and message-level `news_digest` response payloads.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py -q` failed before the news digest module existed.
- GREEN: the same command passed with 2 tests after routing and digest integration.

Risks and follow-ups:

- Ambiguous news requests without a resolvable stock still use the existing missing-stock path. Broader company-name resolution remains tied to the market-data resolver and S&P 500 directory.

## phase_066 - LLM News Summary Fallback

Status: completed

Implementation notes:

- Added an LLM summary prompt that sends only article metadata, provider IDs, dates, snippets, and links.
- Kept deterministic summary output when the saved LLM credential is absent or the provider call fails.
- Verified that news digest requests do not invoke live stock analysis.

Validation:

- Covered by `test_korean_news_request_returns_digest_without_horizon_and_uses_llm_summary`.

Risks and follow-ups:

- The LLM summary is a concise overview string, not a structured citation parser. The linked article list remains the auditable source of record.

## phase_065 - News Query Ranking And Dedupe

Status: completed

Implementation notes:

- Normalized US quote requests to `{company} {symbol} stock news`, matching the `finance_news_app.py` prototype behavior.
- Canonicalized URLs by removing fragments and `utm_*` query parameters before duplicate detection.
- Ranked articles by parsed published time, then provider priority and provider rank.
- Split ranked articles into up to 5 important articles and up to 10 additional articles.

Validation:

- Covered by `test_news_digest_collects_providers_dedupes_and_tracks_transparency`.

Risks and follow-ups:

- Some providers return relative dates such as `2 hours ago`; those are preserved for display but sort after parseable timestamps.

## phase_064 - News Digest Provider Contract

Status: completed

Implementation notes:

- Added `src/backend/app/features/news_digest/` with schemas and provider service logic.
- Implemented Tavily Search, GNews, SerpApi Google News, and SerpApi Google Web adapters through the existing environment-key pattern.
- Flattened grouped SerpApi Google News `stories` records from the Streamlit prototype into first-class article records.
- Provider runs now expose provider name, query, result count, status, and warning for UI transparency.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py -q` failed with `ModuleNotFoundError: No module named 'app.features.news_digest'`.
- GREEN: the same command passed with 2 tests after the provider contract and chat integration.

Risks and follow-ups:

- No separate persistent news cache was added. Repeated identical news requests may call providers again unless a later cache phase is introduced.

## phase_063 - Provider USD/KRW Conversion Rate

Status: completed

Implementation notes:

- Added `get_usd_krw_rate()` to the market-data service. It uses the existing SerpApi Google Finance transport and tries `USD-KRW`, `USD/KRW`, then `USDKRW`.
- Updated Korean US-stock snapshot copy to use `STUCK_LLM_USD_KRW_RATE` first, then provider FX, then the local fallback.
- Added flexible rate formatting so fractional rates display as values such as `USD/KRW 1,392.50 기준` while integer env rates still display cleanly.
- Adjusted older Korean US-stock tests to set a deterministic env rate when they mock only the equity quote request.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed because Korean US-stock copy still used `USD/KRW 1,400`.
- GREEN: same command passed with 6 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py src/backend/tests/test_phase026_generative_chat_orchestration.py src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py -q` passed with 14 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed with 50 source files.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 133 tests and one local urllib3 LibreSSL warning.
- `cd src/frontend && npm test -- MarketChart.test.tsx ChatShell.test.tsx App.test.tsx AnalysisPanel.test.tsx` passed with 28 tests.
- `cd src/frontend && npm test` passed with 47 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app src/backend/tests src/frontend/src backups/phase_060 backups/phase_061 backups/phase_062 backups/phase_063` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 5228 total lines.

Risks and follow-ups:

- FX remains a spot display conversion. Historical analysis still needs timestamped FX evidence if future phases use converted prices as analytical evidence.

## phase_062 - S&P 500 Symbol Directory Routing

Status: completed

Implementation notes:

- Added `sp500_constituents.csv` under `market_data` as a local S&P 500 constituent directory.
- Added a cached CSV loader that builds symbol and normalized company-name aliases from the directory.
- Added localized aliases for high-frequency US names, including `월마트` to `WMT`.
- Updated resolver ordering so explicit aliases remain first, then S&P 500 directory matches, then direct S&P ticker tokens typed under a KR default route to US lookup.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed because `월마트 주가` returned `needs_input`.
- GREEN: same command passed after the S&P 500 directory resolver.
- Full validation is recorded above under `phase_063`.

Risks and follow-ups:

- The CSV is a local seed, not an automatic membership refresh. Add a managed refresh/import workflow before relying on the file as an always-current index universe.

## phase_061 - Chat Auto Scroll To Latest

Status: completed

Implementation notes:

- Added a bottom scroll anchor to `ChatShell`.
- Added an effect keyed by message count and pending activity state to call `scrollIntoView`.
- Guarded `scrollIntoView` with optional chaining so non-browser test environments remain compatible.

Validation:

- RED: `cd src/frontend && npm test -- ChatShell.test.tsx` failed because no scroll call occurred.
- GREEN: same command passed with 10 tests.
- Full validation is recorded above under `phase_063`.

Risks and follow-ups:

- The chat still updates after complete responses. A streaming phase should reuse the same anchor for incremental token updates.

## phase_060 - Chart Hover Tooltip And Thinner Directional Line

Status: completed

Implementation notes:

- Added pointer tracking to `MarketChart` and selects the nearest chart point by SVG x-coordinate.
- Rendered a dark tooltip with date/time and `Price: ...` text, plus a vertical hover guide.
- Kept red/green directional classes based on the selected chart window's first and last bars rather than quote-level daily change.
- Reduced chart stroke widths to make dense graph windows more legible.

Validation:

- RED: `cd src/frontend && npm test -- MarketChart.test.tsx` failed because tooltip and selected-window behavior were absent.
- GREEN: same command passed with 3 tests.
- Full validation is recorded above under `phase_063`.

Risks and follow-ups:

- Tooltip positioning is intentionally simple and bounded to the SVG chart. If touch support becomes a requirement, add tap/focus affordances separately.

## phase_059 - Readable Finance Chart And Fresh New Chat

Status: completed

Implementation notes:

- Reviewed `gpt-coding/finance_app.py` and translated its Google Finance chart behavior into the existing React chart surface: larger plot area, visible price axis, date/time axis, start-price reference, direction-aware line color, and latest marker.
- Expanded `MarketChart` from the prior small sparkline into a stable `760 x 360` SVG coordinate system with margins for labels.
- Kept currency labels tied to the quote currency, so AAPL/GOOG chart labels stay in USD while Korean quote charts stay in KRW.
- Added a `chatSessionKey` reset in `App` so clicking `New chat` clears the active snapshot and remounts `ChatShell`, removing stale messages from the conversation area.
- Updated chart-related frontend tests to expect the additional visible axis labels and added coverage that `New chat` returns to the empty conversation state.

Validation:

- `cd src/frontend && npm test -- MarketChart.test.tsx App.test.tsx ChatShell.test.tsx AnalysisPanel.test.tsx` passed with 25 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm test` passed with 44 tests.
- `cd src/frontend && npm run build` passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 131 tests and one local urllib3 LibreSSL warning.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app src/backend/tests src/frontend/src backups/phase_059` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 4959 total lines.

Risks and follow-ups:

- The chart still uses the repo's lightweight SVG implementation. If later interactions require hover crosshairs, zoom, or tooltips, add them intentionally rather than pulling in Plotly only for parity with the Streamlit prototype.

## phase_058 - Google Finance Style Chart Context

Status: completed

Implementation notes:

- Added `MarketChart.test.tsx` covering the Google Finance-style context missing from the current SVG chart.
- Refactored `MarketChart` to compute plotted points once and render a start-price dotted reference, latest-price marker, active window label, and first/last axis labels.
- Preserved exchange-local dates by formatting from the provider timestamp string before falling back to browser `Date`.
- Added chart CSS for start lines, latest markers, chart reference labels, and responsive metadata layout without adding a charting dependency.

Validation:

- RED: `cd src/frontend && npm test -- MarketChart.test.tsx` failed because `Start 267.56 USD`, latest marker label, `Apr 23`, `Apr 28`, and `5D` were missing.
- GREEN: `cd src/frontend && npm test -- MarketChart.test.tsx` passed.
- `cd src/frontend && npm test -- ChatShell.test.tsx AnalysisPanel.test.tsx MarketChart.test.tsx api.test.ts` passed with 23 tests.
- `cd src/frontend && npm test` passed with 43 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- Full-project validation listed under `phase_055` also passed.

Risks and follow-ups:

- The chart remains a compact SVG line chart. A future charting-library migration should still preserve the start/latest/date labels added here.

## phase_057 - US Snapshot Currency Display Policy

Status: completed

Implementation notes:

- Added Korean snapshot copy that keeps the original US price in USD and appends an approximate KRW conversion.
- Added `STUCK_LLM_USD_KRW_RATE` support for deterministic local conversion, with a local fallback rate for offline operation.
- Added Google/Alphabet US alias routing so `구글 주가` does not fall through to KR quote lookup and produce KRW-labeled US data.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed because `구글 주가` returned `needs_input` and did not include converted KRW text.
- GREEN: same command passed with 4 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py src/backend/tests/test_phase026_generative_chat_orchestration.py src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase055_058_market_chat.py -q` passed with 23 tests and one local urllib3 LibreSSL warning.
- Full-project validation listed under `phase_055` also passed.

Risks and follow-ups:

- KRW conversion is display-only and uses a configured or fallback reference rate. A later FX provider phase should replace the fallback with timestamped exchange-rate data.

## phase_056 - Search-Style US Ticker Normalization

Status: completed

Implementation notes:

- Added Apple and Google/Alphabet aliases, including Korean localized names, into the market-data resolver.
- Added quote-search filler stripping for words such as `stock`, `price`, `quote`, `주가`, and `시세`.
- Changed alias matching to use word-aware English matching instead of broad substring matching.
- Updated SerpApi Google Finance lookup to prefer the first candidate with graph data while keeping graphless quote summaries as fallback.
- Updated the chat-intent prompt so search-style phrases are classified as market snapshots unless the user asks for analysis/scoring.
- Updated the old phase_053 test expectation because `애플` is now an explicit deterministic alias by product requirement.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed because Google did not resolve and the first graphless SerpApi candidate was accepted.
- GREEN: same command passed with 4 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py src/backend/tests/test_phase026_generative_chat_orchestration.py src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase055_058_market_chat.py -q` passed with 23 tests and one local urllib3 LibreSSL warning.
- Full-project validation listed under `phase_055` also passed.

Risks and follow-ups:

- The deterministic alias set is intentionally small. Broader support should come from a symbol directory or LLM-confirmed lookup flow rather than adding many aliases by hand.

## phase_055 - Ambiguous Chat Follow-Up And Snapshot Guard

Status: completed

Implementation notes:

- Added `test_phase055_058_market_chat.py` to cover the reported `apple` 500, LLM follow-up question surfacing, Korean Google routing, and graph-first SerpApi behavior.
- Changed stock-only quote requests with a resolved quote and no analysis intent to return market snapshots instead of falling through to `_assistant_reply` and raising `ValueError`.
- Surfaced LLM `needs_follow_up` / `follow_up_question` as a user-visible assistant clarification.
- Preserved stock-confirmation follow-ups with explicit horizons by treating quote plus parsed horizon as analysis intent.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed with the reported 500, generic follow-up question, missing Google routing, and graphless candidate behavior.
- GREEN: same command passed with 4 tests and one local urllib3 LibreSSL warning.
- Regression: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase015_runner_and_typo_confirmation.py src/backend/tests/test_phase055_058_market_chat.py -q` passed with 9 tests and one local urllib3 LibreSSL warning after narrowing snapshot handling for confirmed-stock horizon follow-ups.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 131 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed with 50 source files.
- `cd src/frontend && npm test` passed with 43 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after approved network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.
- `./run-harness.sh --profile quick` passed and wrote `artifacts/harness/20260429T070555Z-quick/report.json` plus `report.md`.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app src/backend/tests src/frontend/src backups/phase_055 backups/phase_056 backups/phase_057 backups/phase_058` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 4878 total lines.

Risks and follow-ups:

- The app still relies on SerpApi and a focused alias set for rich US quote snapshots. Unknown localized names should continue through LLM intent/follow-up rather than unsupported deterministic guesses.

## phase_052 - Conversation Deletion And Fixed Settings Rail

Status: completed

Implementation notes:

- Added `ConversationDeleteResponse` with `deleted_count`.
- Added conversation service functions to delete one conversation or clear all conversations through the local state store.
- Added `DELETE /conversations/{conversation_id}` and `DELETE /conversations` routes.
- Added frontend API helpers `deleteConversation` and `clearConversations`.
- Added a per-conversation delete button in the left rail with accessible labels such as `Delete AAPL`.
- Added a confirm-gated Settings Security action for clearing all saved chat history.
- Updated the side-rail CSS so brand/nav/history/footer are grid rows, the conversation list owns its scroll, and Settings stays in the bottom footer.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase052_conversation_delete.py -q` failed because conversation DELETE endpoints returned 405.
- GREEN: same command passed with 3 tests and one local urllib3 LibreSSL warning.
- RED: `cd src/frontend && npm test -- api.test.ts App.test.tsx SettingsModal.test.tsx` failed because the delete API helpers, left-rail delete button, and Settings clear-history action did not exist.
- GREEN: same command passed with 27 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 127 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed with 50 source files.
- `cd src/frontend && npm test` passed with 42 tests.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after approved network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend/app src/backend/tests src/frontend/src backups/phase_049 backups/phase_050 backups/phase_051 backups/phase_052` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 4600 total lines.

Risks and follow-ups:

- Conversation deletion is permanent in the local state store. A future multi-user or hosted mode should add archival, ownership checks, or undo if product requirements call for it.

## phase_051 - Frontend Chart Period Controls

Status: completed

Implementation notes:

- Added a frontend `MarketChartWindow` type matching the backend-supported Google Finance windows.
- Mapped backend `chart_window` into frontend `MarketQuote.chartWindow`.
- Updated `fetchMarketQuote` to accept an optional chart window and send it as a query parameter.
- Added compact period buttons to `MarketChart` with stable sizing and active `aria-pressed` state.
- Updated `ChatShell` to accept an `onFetchMarketQuote` callback, refetch only the selected message's chart, and store message-local chart overrides.
- Limited period controls to US `serpapi_google_finance` snapshots so Korean/fixture charts keep the prior static rendering.
- Added localized chart-refresh error copy for English and Korean.

Validation:

- RED: `cd src/frontend && npm test -- api.test.ts ChatShell.test.tsx` failed because `chartWindow` was not mapped and the chat chart had no period buttons.
- GREEN: same command passed with 18 tests.

Risks and follow-ups:

- Period changes are request/response updates, not streamed provider progress. The existing phase_054 pending activity covers chat requests, while chart refetches only disable the chart period controls.
- The controls intentionally avoid prefetching large windows such as `MAX` to reduce SerpApi quota pressure.

## phase_050 - US Google Finance Chart Window Contract

Status: completed

Implementation notes:

- Added `MarketChartWindow` with supported Google Finance periods: `1D`, `5D`, `1M`, `6M`, `YTD`, `1Y`, `5Y`, and `MAX`.
- Added `chart_window` to `MarketQuote`, defaulting to `1D` for existing fixture and FinanceDataReader paths.
- Updated `GET /market-data/quotes/{market}/{symbol}` to accept a validated `window` query parameter.
- Threaded `window` through `get_quote`, `_quote_from_serpapi_google_finance`, `_search_serpapi_google_finance`, and `_quote_from_serpapi_payload`.
- Updated SerpApi Google Finance query candidates so exchange-qualified inputs such as `AAPL:NASDAQ` also try `NASDAQ:AAPL`.
- Added reversed exchange candidates for known mapped US symbols while preserving the existing unknown-symbol fallback order.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py::test_us_quote_endpoint_passes_requested_chart_window_to_serpapi src/backend/tests/test_phase022_us_market_data_provider.py::test_colon_us_quote_tries_reversed_google_finance_exchange_candidate -q` failed because the backend always passed `window=1D` and did not try `NASDAQ:AAPL`.
- GREEN: same command passed with 2 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py -q` passed with 6 tests.

Risks and follow-ups:

- `MAX` can produce larger payloads from SerpApi; phase_051 should avoid eager prefetching every period and only fetch when the user selects a period.

## phase_049 - Google Finance Runtime Comparison

Status: completed

Implementation notes:

- Reviewed `gpt-coding/finance_app.py` and confirmed the standalone graph flow is graph-first: build Google Finance query candidates, call SerpApi with `engine=google_finance`, include `window`, and accept the first candidate with graph data.
- Reviewed `gpt-coding/finance_news_app.py` and confirmed the news app is separate from graph retrieval; news remains out of scope for phases 050 through 052.
- Confirmed the current app already owns the right backend boundary under `market_data`, but the API does not yet expose `window`.
- Confirmed the current frontend chart is static per assistant message and needs an explicit quote refetch path for `1D`, `5D`, `1M`, `6M`, `YTD`, `1Y`, `5Y`, and `MAX`.
- Confirmed the left rail settings button is inside the same scroll container as conversation history, which explains the observed overlap/scroll behavior.
- Confirmed conversation list APIs are read/create/update only; deletion needs explicit backend and frontend contracts.

Validation:

- `python3 -m streamlit --version` passed and reported Streamlit 1.50.0.
- `python3 -m py_compile gpt-coding/finance_app.py gpt-coding/finance_news_app.py` initially failed because Python tried to write bytecode under the macOS user cache outside the sandbox.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m py_compile gpt-coding/finance_app.py gpt-coding/finance_news_app.py` passed.
- `python3 -c "import os; print('SERPAPI_API_KEY=set' if os.environ.get('SERPAPI_API_KEY') else 'SERPAPI_API_KEY=missing')"` reported `SERPAPI_API_KEY=missing`.

Risks and follow-ups:

- True live Google Finance comparison still requires a `SERPAPI_API_KEY` in the launched backend environment.
- The standalone app tries `AAPL:NASDAQ`, but the current issue screenshot shows that Google Finance may require `NASDAQ:AAPL`; phase_050 should include both directions for colon inputs.

## phase_054 - Chat Request Activity Indicator

Status: completed

Implementation notes:

- Added localized chat copy for pending request activity in English and Korean.
- Rendered an `aria-live` assistant activity message while `ChatShell` is waiting for `onSendMessage`.
- Included short activity lines for LLM intent/provider checks and ticker/market-data API checks.
- Kept the send button disabled while the activity indicator is visible and removed the indicator when the response arrives.
- Styled the pending activity message as a dashed assistant message so it reads as operational status rather than final assistant content.

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

Risks and follow-ups:

- This is client-side in-flight copy, not streamed backend step telemetry; true per-API progress events would require a backend streaming or job-status contract.

## phase_053 - LLM Confirmed Korean US Ticker Snapshot

Status: completed

Implementation notes:

- Updated the chat-intent prompt so the LLM can infer localized or translated company names into canonical stock queries and markets when confident.
- Added `StockConfirmationSnapshot` to assistant messages so LLM-inferred stock candidates can be persisted across a follow-up confirmation.
- Changed conversation orchestration so LLM-inferred `market_snapshot` candidates ask for stock confirmation before fetching market data.
- Kept stock-analysis intent behavior unchanged so existing non-literal analysis requests can still proceed through the LLM interpretation path.
- Preserved existing typo-confirmation behavior; fuzzy typo confirmations with an explicit horizon still proceed to analysis rather than a snapshot.
- Added a backend test proving `애플` can become an LLM-confirmed `AAPL` US graph snapshot without adding a hard-coded `애플` market-data alias.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase026_generative_chat_orchestration.py::test_llm_inferred_korean_us_stock_requires_confirmation_before_snapshot -q` failed because LLM-inferred `애플` was immediately returned as a market snapshot instead of requiring confirmation.
- GREEN: same command passed with one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase026_generative_chat_orchestration.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py -q` passed with 13 tests and one local urllib3 LibreSSL warning.

Risks and follow-ups:

- This phase depends on a saved LLM credential for localized-name inference; without one, the deterministic alias table still intentionally does not recognize `애플`.
- The first confirmed snapshot uses the existing default chart window; richer window controls remain a later phase.

## phase_048 - SerpApi Google News Ingestion Adapter

Status: completed

Implementation notes:

- Added `serpapi_google_news` as a selectable source adapter.
- Added SerpApi Google News collection behind environment-only `SERPAPI_API_KEY`.
- Built the adapter on the existing ingestion source document shape so analysis cutoff and prompt grounding continue to happen downstream.
- Flattened both flat `news_results` entries and grouped `stories` entries into article-level source documents.
- Normalized SerpApi-style published timestamps such as `Apr 28 2026, 01:15 PM UTC-04:00`.
- Marked returned documents with `external_api` and `untrusted_source_text` safety flags and avoided returning the raw key in responses.
- Added the adapter to the default source adapter list so analysis requests can use it when the key is configured.

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

Risks and follow-ups:

- Default analysis source collection can now attempt one more external adapter when `SERPAPI_API_KEY` is missing, producing a safe missing-credential warning.

## phase_047 - Nested Google Finance News Snapshot Parsing

Status: completed

Implementation notes:

- Added market-data parsing for nested SerpApi Google Finance news sections using `news_results[].items`.
- Skipped section wrapper records when nested items are present so labels such as `In the news` are not rendered as articles.
- Allowed nested news entries without a dedicated title to use their snippet as the `MarketNewsItem.title`, preserving links, source, timestamps, and snippet text.
- Kept existing flat `news_results` parsing unchanged for current rich ticker snapshots.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py::test_ticker_snapshot_flattens_nested_google_finance_news_items -q` failed because the parser returned the wrapper title `In the news` instead of the nested article.
- GREEN: same command passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py src/backend/tests/test_phase022_us_market_data_provider.py -q` passed with 7 tests and one local urllib3 LibreSSL warning.

Risks and follow-ups:

- Nested Google Finance news remains display metadata for market snapshots; source-grounded analysis evidence still flows through ingestion adapters and cutoff filtering.

## phase_046 - SerpApi Google Finance Query Candidate Fallback

Status: completed

Implementation notes:

- Added a SerpApi Google Finance query candidate builder for US symbols.
- Kept the existing mapped exchange as the first candidate, then tried `NASDAQ`, `NYSE`, and the bare ticker without duplicates.
- Updated SerpApi quote lookup so a candidate with no usable quote falls through to the next candidate before falling back to FinanceDataReader or seeded fixtures.
- Kept `SERPAPI_API_KEY` environment-only and out of API responses.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py::test_serpapi_google_finance_tries_exchange_candidates_until_quote_found -q` failed because only `ACME:NASDAQ` was tried and the route returned 404.
- GREEN: same command passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py -q` passed with 4 tests.

Risks and follow-ups:

- The fallback increases SerpApi calls for unmapped US tickers when early candidates are quote-less; later work can add short-lived caching if quota pressure appears.

## phase_041 - Agent Harness Foundation

Status: completed

Implementation notes:

- Added `scripts/harness/run_harness.py` as the project-local harness entrypoint.
- Added `run-harness.sh` as a root wrapper so agents can run harness profiles without remembering the Python script path.
- Implemented profile registry support for `docs`, `backend`, `frontend`, `provider`, `quick`, and `full`.
- Added `--dry-run` so agents can inspect selected commands and generate reports without running expensive checks.
- Added `--list-profiles` so agents can discover available validation profiles from the repository.
- Added `--keep-going` and stdout/stderr tail capture so failing runs still produce useful agent-readable diagnostics.
- Wrote each harness run to `report.json` and `report.md` under `artifacts/harness/<run_id>/`.
- Ignored generated harness reports through `.gitignore`.
- Added root `AGENTS.md` and `docs/agent-workflows/code-validation.md` guidance for the new harness command.
- Documented future harness phases only: `phase_042` browser/user-journey harness, `phase_043` eval corpus CLI, `phase_044` agent-readable observability, and `phase_045` structural/documentation garbage-collection lint.

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

Risks and follow-ups:

- `phase_041` does not add browser automation, eval corpus execution, observability traces, or structural lint; those remain planned as `phase_042` through `phase_045`.
- The harness currently runs local command profiles sequentially and does not yet aggregate CI artifacts from remote systems.

## phase_040 - Agent Workflow Provider Validation Policy

Status: completed

Implementation notes:

- Added root-agent guidance that agents should proactively patch `docs/agent-workflows` in the same phase when the workflow docs no longer drive the requested behavior.
- Updated orchestration guidance so LLM provider/API-key tasks must validate the real `/conversations` path, not only settings diagnostics or provider connection tests.
- Required provider acceptance criteria to split simple chat, follow-up chat, stock-analysis requests, and market snapshot requests.
- Clarified that LLM provider credentials are separate from search, news, and market-data provider keys such as `SERPAPI_API_KEY`, `NAVER_CLIENT_ID`, `TAVILY_API_KEY`, and `GNEWS_API_KEY`.
- Required provider work to prove repeated same-conversation calls and follow-up questions, because first-call success is not enough for user-visible behavior.
- Expanded Google Finance-style expectations so agents scope rich snapshot schema and UI when users expect chart bars, key stats, and related news beyond a minimal quote.
- Recorded the phase in `docs/plan.md` and `docs/task.md` with newest-first ordering.

Validation:

- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_038 backups/phase_039 backups/phase_040` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 3952 total lines.

Risks and follow-ups:

- The workflow docs now require richer provider validation, but future phases still need to choose the smallest relevant test subset for each provider change so validation remains fast.

## phase_039 - ChatGPT-Style Conversation Workspace

Status: completed

Implementation notes:

- Added frontend conversation summary loading through `GET /conversations` and selected conversation loading through `GET /conversations/{id}`.
- Reworked the app shell so the left rail lists previous conversations, supports a new-chat action, and loads saved conversation snapshots on selection.
- Made `ChatShell` controlled by the active conversation snapshot while preserving a local fallback for isolated component use.
- Updated message sending so follow-up messages continue the active conversation ID and update both the active snapshot and left-rail summary.
- Changed the chat area to a stable workspace with an independently scrolling message list and a persistent composer.
- Rendered message-level market snapshots inside assistant messages so earlier charts, key stats, and related news remain visible after later follow-ups.
- Extended frontend market data types and API mapping for `keyStats`, `newsItems`, and per-message `marketSnapshot`.
- Extended `MarketChart` to display compact key stats and related news alongside the existing quote and chart.
- Added Korean and English copy for previous-chat, new-chat, and empty-history states.

Validation:

- RED: `cd src/frontend && npm test -- ChatShell.test.tsx App.test.tsx api.test.ts` failed on missing conversation API mapping, missing previous-chat rail behavior, and missing message-level snapshot rendering.
- GREEN: same command passed with 23 tests.
- `cd src/frontend && npm test` passed with 34 tests across 7 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after approved network access; the sandboxed run could not resolve `registry.npmjs.org`.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.

Risks and follow-ups:

- The workspace now supports saved conversation selection and preserved message content, but it still uses request/response updates rather than streaming or live push.
- Conversation persistence remains backed by the current local state store rather than authenticated multi-user storage.

## phase_038 - Persistent LLM Chat And Rich Ticker Snapshots

Status: completed

Implementation notes:

- Added a generic chat-completion request path to the OpenAI-compatible provider so saved Cerebras or custom OpenAI-compatible credentials can answer normal conversation prompts.
- Kept generic chat separate from structured stock-analysis prompts and response parsing.
- Added prompt construction for generic chat that includes recent same-conversation user and assistant messages for follow-up context.
- Updated conversation flow so simple chat uses the saved user LLM credential through `/conversations`, stores the assistant response, and returns `chat_completed`.
- Added ticker-only snapshot handling so a request like `AAPL` fetches market data instead of asking for swing, intraday, or long-term analysis horizon.
- Preserved explicit analysis behavior for analysis, buy/sell, comparison, and strategy-style requests.
- Added message-level `market_snapshot` attachments and response statuses so assistant messages can carry their own chart/news/stat data.
- Added newest-first conversation summaries and a `GET /conversations` endpoint for previous-chat selection.
- Expanded Google Finance/SerpApi parsing to populate chart bars, key stats, and related news on `MarketQuote`.
- Added backend tests for repeated saved-key chat through `/conversations` and rich ticker snapshots.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py -q` failed because generic chat returned `needs_input` and ticker-only `AAPL` asked for a horizon.
- GREEN: same command passed with 2 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase022_us_market_data_provider.py src/backend/tests/test_phase026_generative_chat_orchestration.py -q` passed with 14 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 115 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `git diff --check` passed.

Risks and follow-ups:

- Live provider success still depends on the user's saved credential and provider account permissions; tests cover the repeated user path without exposing raw keys.
- Rich snapshot quality depends on the upstream SerpApi Google Finance payload shape, so later provider work may need fixture coverage for additional exchange-specific variants.

## phase_037 - Cerebras Provider Header Compatibility

Status: completed

Implementation notes:

- Compared `cerebras-test/index.js`, which succeeds through the official `@cerebras/cerebras_cloud_sdk`, with Stuck_LLM's direct `urllib` OpenAI-compatible provider path.
- Confirmed the saved Stuck_LLM Cerebras key and `cerebras-test/.env` key have the same mask, so the failure was not caused by a stale saved credential.
- Confirmed direct Python requests with the default `urllib` User-Agent received Cerebras HTTP 403 with provider body `error code: 1010`.
- Confirmed the same direct Python request succeeds when it sends an explicit non-urllib `User-Agent`.
- Added DeepTutor-inspired explicit provider header construction in `live_provider.py` via `_provider_headers`, including `Accept: application/json`, `Content-Type: application/json`, `Authorization`, and `User-Agent: Stuck_LLM/0.1`.
- Reused `_provider_headers` for analysis calls, chat-intent calls, and connection tests.
- Extended Cerebras provider and connection diagnostic tests to assert the safe header contract without exposing raw keys in responses.
- Preserved the current phase_035 policy that LLM runtime calls require saved credentials rather than environment fallback.

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
- Live provider checks with approved network access:
  - `cd cerebras-test && npm start` succeeded through the official Cerebras SDK.
  - Direct Stuck_LLM-style Python request with default urllib headers failed with HTTP 403 / `error code: 1010`.
  - Direct Stuck_LLM-style Python request with explicit `User-Agent` succeeded with HTTP 200.
  - `test_llm_credential_connection` returned configured `cerebras`, model `llama3.1-8b`, and `status='ok'`.

Risks and follow-ups:

- DeepTutor's broader provider-neutral env model, model catalog, streaming abstraction, and telemetry are intentionally not imported yet because they would change Stuck_LLM's credential policy and architecture.
- Later provider work can extract `_provider_headers` and endpoint helpers into a dedicated `features/llm` module if multiple provider families need richer routing.

## phase_036 - Minimal Quote Card In Chat

Status: completed

Implementation notes:

- Updated `MarketChart` so the reusable chart card visibly includes stock name, symbol, formatted price, percentage change, exchange, and as-of timestamp.
- Reused that card in both the latest chat assistant response and the analysis panel snapshot.
- Removed the analysis panel's separate quote grid to avoid rendering two competing market snapshot summaries.
- Kept the existing SVG line chart and screen-reader chart data table.
- Added compact-card assertions for stock name, symbol, exchange, as-of timestamp, and price in `ChatShell.test.tsx`.
- Updated `AnalysisPanel.test.tsx` to match the single-card market snapshot layout.
- Used the saved local Cerebras credential for a real `/chat/completions` prompt check without printing raw secrets.

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
- Saved credential status check reported configured `cerebras`, model `llama3.1-8b`, base URL `https://api.cerebras.ai/v1`, and a masked key.
- Sandboxed live Cerebras request failed DNS resolution as expected under restricted network access; rerun with approved network access reached Cerebras and returned HTTP 403 Forbidden.

Risks and follow-ups:

- The saved Cerebras credential currently does not produce a successful live response; provider-side access, key validity, or model permission should be checked before treating Cerebras as operational.
- The quote card intentionally omits Google Finance-style stats until the market-data schema is expanded.

## phase_035 - User-Selected LLM API Key Policy

Status: completed

Implementation notes:

- Removed LLM credential fallback from `OPENAI_API_KEY`, `OpenAI_API_Key`, and `CEREBRAS_API_KEY`; `get_llm_credential_secret` now returns a credential only from encrypted local state.
- Preserved user-selectable providers in the credential API: `openai`, `anthropic`, `cerebras`, and `custom`.
- Defaulted the Settings model credential form and setup CLI prompts to Cerebras/`llama3.1-8b`, while keeping OpenAI, Anthropic, Cerebras, and custom options selectable.
- Kept saved Cerebras credentials on the existing OpenAI-compatible provider path with the official `https://api.cerebras.ai/v1` default base URL.
- Updated setup-needed backend copy to explicitly ask for an API key.
- Added `message-needs-api-key` styling so the latest setup-needed assistant message appears in the app's error-red color.
- Updated `.env.example` to state that LLM provider keys must be saved through Settings and are not read as environment fallback.
- Used DeepTutor's explicit LLM configuration shape as the product pattern: provider binding, model, API key, and host/base URL are explicit configuration, not implicit fallback.

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

Risks and follow-ups:

- Anthropic remains storable but live calls still return unsupported-provider until a native adapter is added.
- Gemini is not yet in the credential provider union; adding it should be a dedicated provider-adapter phase.
- Existing historical phase logs still describe the former environment fallback behavior; `phase_035` supersedes that policy for current runtime behavior.

## phase_034 - Prompt Grounding Contract Integration

Status: completed

Implementation notes:

- Tightened `build_live_analysis_messages` with an explicit `allowed_source_document_ids` contract.
- `create_live_analysis` now passes only currently included/prompt-eligible source IDs into that allowed list.
- The live prompt now states that every evidence item and key claim must cite exactly one allowed source ID.
- The live prompt now explicitly forbids citing excluded, prompt-budget-excluded, future, or fabricated source IDs.
- The live prompt reiterates that source text is untrusted evidence, not instructions, and that weak evidence should be acknowledged instead of fabricated.
- Existing structured-output validation continues to reject fabricated IDs in `OpenAiCompatibleAnalysisProvider`.
- Existing service-level evidence conversion continues to map provider output citing unsupplied/excluded IDs to `provider_error` with `malformed_output`.
- No provider adapters, frontend UI, ingestion behavior, or scoring formula changed.

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

Risks and follow-ups:

- Summary-level key-claim citation is still enforced by prompt contract, while machine validation remains evidence-item source ID validation.
- Later structured-output schema work could add claim-level citation fields if the UI needs per-claim audit display.

## phase_033 - Source Quality And Evidence Weighting Evals

Status: completed

Implementation notes:

- Added eval-only `app.evals.source_quality` with `SourceQuality`, `classify_source_quality`, and `evidence_quality_weight`.
- Classified reliability from trusted metadata only: official filing/regulatory source types and known official source names, news adapter/source types, social/forum source types, or unknown.
- Classified freshness from `published_at` relative to `as_of_at`; future-dated sources get zero quality.
- Combined source quality with bounded relevance score for deterministic eval-only evidence quality weights.
- Integrated source-quality warnings into `evaluate_case` as warning severity findings, so low/unknown reliability and future-dated quality concerns are visible without failing otherwise valid eval cases.
- Kept quality data out of analysis API schemas, scoring formulas, live provider calls, and frontend UI.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase033_source_quality_evals.py -q` failed on missing `classify_source_quality`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase033_source_quality_evals.py -q` passed with 5 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase031_eval_harness.py src/backend/tests/test_phase032_source_safety_evals.py src/backend/tests/test_phase033_source_quality_evals.py -q` passed with 17 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase007_analysis_pipeline.py src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase023_source_audit_trail.py src/backend/tests/test_phase031_eval_harness.py src/backend/tests/test_phase032_source_safety_evals.py src/backend/tests/test_phase033_source_quality_evals.py -q` passed with 24 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend/app/evals src/backend/tests/test_phase033_source_quality_evals.py` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.

Risks and follow-ups:

- Reliability classes are intentionally coarse; real publisher reputation should be a later explicit model, not inferred from body text.
- Source-quality scores are not yet exposed to the UI or used by production scoring.

## phase_032 - Source Safety Eval Rules

Status: completed

Implementation notes:

- Extended `app.evals.rules` with deterministic source-safety checks that run inside `evaluate_case`.
- Added prompt-injection detection for source text that attempts to override prior instructions, expose system prompt content, or force recommendations regardless of evidence.
- Added schema-spoofing detection for source text that tries to dictate JSON or response-schema output.
- Added official identity spoofing detection when untrusted metadata claims SEC/EDGAR/DART/regulator/filing authority.
- Kept trusted official metadata narrow through source types such as `official_filing`, `regulatory_filing`, `sec_filing`, `dart_filing`, and known official source names.
- Added body-date metadata mismatch detection when source body text claims an older publication date while authoritative `published_at` is after `as_of_at`.
- Added phase_032 tests for clean source pass behavior, prompt injection, schema spoofing, official-source spoofing, trusted official metadata, and body-date mismatch.
- Kept all checks offline and deterministic; live prompt construction and ingestion behavior are unchanged.

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

Risks and follow-ups:

- Pattern-based safety checks are intentionally conservative and may need tuning as real source corpora grow.
- Source-quality scoring and secret redaction remain separate follow-up phases.

## phase_031 - Deterministic Analysis Eval Harness

Status: completed

Implementation notes:

- Added backend-only `app.evals` package with `EvalCase`, `EvalFinding`, `EvalResult`, and `EvalReport` dataclasses.
- Added `evaluate_case` and `evaluate_cases` runners for deterministic offline validation.
- Added analysis eval rules for future source inclusion, prompted future sources, cited future sources, unknown evidence source IDs, excluded evidence source citations, prompt source grounding, `needs_evidence` consistency, and included/excluded count consistency.
- Added scoring eval rules for analysis-request mismatch, probability range, scored probability sums, non-zero probabilities in `needs_evidence`, high confidence without evidence/drivers, and score-driver source grounding.
- Kept the harness out of live provider, ingestion, scoring, and frontend paths; it is a test/eval utility over existing response schemas.
- Added phase_031 tests covering passing evals, cutoff failures, grounding failures, probability failures, high unsupported confidence, and multi-case report summaries.

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

Risks and follow-ups:

- The harness is not wired into CI or a CLI command yet; it is currently exercised through pytest.
- Prompt-injection pattern checks, source-quality scoring, and secret redaction are intentionally left for later phases.

## phase_027 - Settings-Language Response Policy

Status: completed

Implementation notes:

- Added optional `response_language` to `ConversationCommand`.
- Backend conversation handling now uses explicit response language before falling back to Hangul/message-language detection.
- Backend-generated missing-input, setup-needed, provider-error, and live-analysis assistant copy now follow that explicit language.
- Chat intent extraction and live analysis prompts receive the same explicit language, so provider prompts ask for the Settings-selected output language.
- Frontend `SendMessageRequest` now includes `responseLanguage`.
- `sendConversationMessage` maps `responseLanguage` to backend `response_language`.
- `ChatShell` accepts `responseLanguage` and includes it with every submitted chat message.
- `App` passes the current Settings modal UI language from local `uiPreferences`.
- UI language remains a local frontend preference and is not persisted into backend analysis settings or analysis records.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase027_settings_language_policy.py -q` failed with 3 expected failures because `response_language` was ignored and prompts followed message-language detection.
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

Risks and follow-ups:

- Existing conversations do not store a language preference; the active frontend UI language is sent per new message.
- Other backend endpoints outside chat still use their existing language behavior unless they later receive an explicit language parameter.
- SerpApi refinement remains `phase_028`.

## phase_026 - Generative Chat Orchestration

Status: completed

Implementation notes:

- Added a structured chat-intent request path to the existing OpenAI-compatible provider.
- Added `ChatIntentOutput` with intent, stock query, market, horizon, analysis mode, source hints, follow-up flag, and follow-up question fields.
- Added `build_chat_intent_messages` with escaped JSON user/conversation context and instructions to treat chat text as untrusted data.
- Conversation handling now attempts LLM intent extraction only when an LLM credential exists and the injected provider supports `interpret_chat`.
- Missing credentials, unsupported providers, provider errors, and malformed intent output fall back to the existing deterministic parser.
- LLM-provided stock references still resolve through `resolve_quote_from_text`; unresolved output cannot create an analysis request.
- Existing fuzzy stock typo confirmation remains authoritative and cannot be bypassed by LLM output.
- LLM-provided horizon and analysis mode values are accepted only through typed enum validation.
- Recognized source hints can narrow source collection to known adapter families such as `reddit` and `global_macro`; arbitrary URL/raw-text ingestion is still excluded.
- Kept conversation API response shape unchanged so frontend mapping did not need a contract update.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase026_generative_chat_orchestration.py -q` failed with 3 tests because the provider was not yet called and non-literal stock references stayed at `needs_input`.
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

Risks and follow-ups:

- The orchestration call adds one LLM round trip before live analysis when credentials are configured; future work may cache or combine this with analysis where latency matters.
- Source hints currently select only known adapters and do not ingest arbitrary URLs or raw text.
- Settings-language precedence for generated backend and LLM copy remains `phase_027`.

## phase_025 - LLM Provider Connection Diagnostics

Status: completed

Implementation notes:

- Added `POST /credentials/llm/test` to validate the active saved or environment-backed LLM credential without running a stock-analysis prompt.
- Reused the existing OpenAI-compatible provider URL validation, retry, timeout, and HTTP error mapping for connection tests.
- Added `OpenAiCompatibleAnalysisProvider.test_connection`, which sends a minimal `/chat/completions` payload with no source evidence and no structured-output schema.
- Added `LlmConnectionTestResult` with safe status, provider, model, base URL, key source, error code, and message fields.
- Kept raw API keys, provider response bodies, and low-level transport details out of connection-test API responses.
- Mapped `401` and `403` provider failures to `auth_error` with user-safe copy.
- Updated the Cerebras environment fallback default model to `llama3.1-8b` based on the user's currently available key.
- Kept `qwen-3-235b-a22b-instruct-2507` visible as a Cerebras comparison model option for later testing.
- Added frontend API mapping for connection-test results.
- Added a Settings modal `Test connection` control that runs against the saved credential and renders safe diagnostic status.
- Updated the Settings modal provider switch so choosing Cerebras defaults to `llama3.1-8b` and the official Cerebras base URL when the current values are provider defaults.
- Recorded `phase_026` through `phase_030` as separate future phases in `docs/plan.md` and `docs/task.md`.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase025_llm_connection_diagnostics.py -q` failed with three missing-route failures and one old default-model failure.
- RED: `cd src/frontend && npm test -- api.test.ts SettingsModal.test.tsx` failed on missing `testLlmCredential` API export and missing Settings modal `Test connection` button.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase025_llm_connection_diagnostics.py -q` passed with 4 tests.
- GREEN: `cd src/frontend && npm test -- api.test.ts SettingsModal.test.tsx` passed with 12 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase016_credentials.py src/backend/tests/test_phase024_cerebras_provider.py src/backend/tests/test_phase025_llm_connection_diagnostics.py -q` passed with 11 tests.
- `cd src/frontend && npm test -- App.test.tsx api.test.ts SettingsModal.test.tsx` passed with 19 tests.
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

Risks and follow-ups:

- Automated validation uses mocked HTTP calls; a real Cerebras smoke test still requires the user's valid key and an explicit live call through the new Settings control or endpoint.
- `auth_error` confirms the provider rejected the credential request, but it does not distinguish expired key, wrong key, account/model authorization, or provider-side policy without a deliberately exposed provider-specific diagnostic layer.
- Generative chat behavior, settings-language response policy, SerpApi refinement, and chart redesign remain separate future phases to avoid mixing behavior changes into provider diagnostics.

## phase_024 - Cerebras OpenAI-Compatible Test Provider

Status: completed

Implementation notes:

- Added `cerebras` as a first-class credential provider alongside OpenAI, Anthropic, and custom providers.
- Added `CEREBRAS_API_KEY` environment fallback for local live-analysis testing when no UI-saved credential or OpenAI environment fallback exists.
- Added `CEREBRAS_MODEL`, defaulting to `gpt-oss-120b`.
- Added `CEREBRAS_BASE_URL`, defaulting to `https://api.cerebras.ai/v1`.
- Kept UI-saved encrypted credentials as the highest-priority credential source.
- Kept OpenAI environment fallback priority above Cerebras environment fallback for backward compatibility.
- Reused the existing OpenAI-compatible provider and `/chat/completions` path for Cerebras.
- Added Cerebras-specific structured-output payload shaping that removes array `minItems`/`maxItems` constraints before provider calls.
- Added Cerebras to the Settings modal provider picker and frontend credential provider type.
- Documented Cerebras env vars in `.env.example`.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase024_cerebras_provider.py -q` failed on missing Cerebras env fallback and Cerebras response schema shaping.
- RED: `cd src/frontend && npm test -- SettingsModal.test.tsx` failed on missing Cerebras provider option.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase024_cerebras_provider.py -q` passed with 2 tests.
- GREEN: `cd src/frontend && npm test -- SettingsModal.test.tsx` passed with 4 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase019_live_market_and_news.py src/backend/tests/test_phase021_provider_policy_reliability.py src/backend/tests/test_phase024_cerebras_provider.py -q` passed with 40 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 77 tests and one local urllib3 LibreSSL warning.
- `cd src/frontend && npm test -- SettingsModal.test.tsx api.test.ts` passed with 10 tests.
- `cd src/frontend && npm test` passed with 27 tests across 7 files.
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
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_024` returned no matches.
- Secret sentinel grep over app code, frontend output, local state, docs, and phase_024 backups found no phase_024 raw test-key occurrences.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 2486 total lines.

Risks and follow-ups:

- Automated tests mock Cerebras provider calls; a real integration smoke test still requires a valid `CEREBRAS_API_KEY` and explicit user approval to make an outbound request.
- Hosted deployments still need explicit egress policy for non-OpenAI provider endpoints.
- The default Cerebras model is documented for local testing and may need revision as available model names change.

## phase_023 - Evidence Source Quality And Audit Trail

Status: completed

Implementation notes:

- Added `SourceAuditSummary` to analysis responses with safe source warnings, included counts by source type, excluded counts by reason, and prompt document IDs.
- Extended source document inputs/decisions to preserve `adapter`, `relevance_score`, `safety_flags`, `fetched_at`, and `language` metadata from ingestion.
- Passed source collection warnings from chat live analysis into `AnalysisRequestCommand`.
- Sanitized source warning codes before returning them in public analysis responses.
- Kept prompt document IDs tied only to documents that remain included after `as_of_at` filtering and prompt-budget filtering.
- Extended frontend API mapping and UI types for source audit metadata without mapping raw source body text into UI models.
- Added a compact source audit section to the Analysis panel with included/excluded counts, warnings, source titles, prompt-used state, and exclusion reasons.
- Kept price/market snapshot rendering visually separate from evidence/source audit rendering.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase023_source_audit_trail.py -q` failed on missing `source_audit`.
- RED: `cd src/frontend && npm test -- api.test.ts AnalysisPanel.test.tsx` failed on missing source audit mapping and rendering.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase023_source_audit_trail.py -q` passed with 1 test.
- GREEN: `cd src/frontend && npm test -- api.test.ts AnalysisPanel.test.tsx` passed with 9 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase019_live_market_and_news.py src/backend/tests/test_phase021_provider_policy_reliability.py src/backend/tests/test_phase023_source_audit_trail.py -q` passed with 25 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 75 tests and one local urllib3 LibreSSL warning.
- `cd src/frontend && npm test` passed with 26 tests across 7 files.
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
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_023` returned no matches.
- Secret sentinel grep over app code, frontend output, local state, docs, and phase_023 backups found no phase_023 raw test-key occurrences.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 2371 total lines.

Risks and follow-ups:

- Source audit summaries now show warning and exclusion codes, but deeper source quality scoring, article extraction, and cross-provider deduplication remain future work.
- Warning-code sanitization is intentionally narrow; future external adapters should continue returning stable machine codes rather than provider response text.
- The Analysis panel shows the audit trail, but source drilldown remains title/date/status only to avoid exposing raw prompt/source body text in the UI.

## phase_022 - US Market Data Provider With SerpApi Google Finance

Status: completed

Implementation notes:

- Added a SerpApi Google Finance provider path for US market snapshots behind `SERPAPI_API_KEY`.
- Kept provider order as SerpApi first for configured US quotes, then FinanceDataReader, then seeded fixtures.
- Added `_search_serpapi_google_finance` as a narrow wrapper that uses `engine=google_finance`, `window=1D`, and `{SYMBOL}:{EXCHANGE}` queries.
- Defaulted common US tickers such as `GOOGL` to the expected Google Finance exchange, with NASDAQ as the fallback exchange.
- Parsed SerpApi summary fields into `MarketQuote` price, currency, exchange, previous close, change percent, and timestamp.
- Parsed SerpApi graph points into quote-line `MarketBar` values by setting open/high/low/close to the point price. These generated bars remain provider-labeled quote data, not backtest-grade OHLC candles.
- Preserved Korean market-data behavior on the existing FinanceDataReader/seed fallback path.
- Documented `SERPAPI_API_KEY` in `.env.example` without reading, printing, persisting, or returning raw keys.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py -q` reported 1 failed and 2 passed before implementation.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py -q` passed with 3 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py src/backend/tests/test_phase019_live_market_and_news.py src/backend/tests/test_phase022_us_market_data_provider.py -q` passed with 21 tests and one local urllib3 LibreSSL warning.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 74 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` initially caught an optional `previous_close` narrowing issue, then passed after the guard was clarified.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m bandit -r src/backend/app/features/market_data -ll` could not run because Bandit is not installed in the local Python environment.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_022` returned no matches.
- Secret sentinel grep over app code, frontend output, local state, docs, and `.env.example` found no phase_022 test-key occurrences.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 2261 total lines.

Risks and follow-ups:

- SerpApi Google Finance is suitable for US quote snapshots, line charts, and Google Finance-adjacent market context, not precision OHLC/backtest execution data.
- If a future phase uses SerpApi graph data in `MarketBar`, keep the source label explicit and avoid presenting those generated bars as real OHLC candles.
- News results from Google Finance can include relative timestamps, so any future evidence ingestion from SerpApi needs strict timestamp normalization before `as_of_at` filtering.

## phase_021 - OpenAI Provider Policy, DNS Safety, And Live Call Reliability

Implementation notes:

- Scoped the phase to the OpenAI-compatible live provider path; Anthropic remains credential-storable but live analysis is explicitly deferred.
- Added `ProviderNetworkPolicy` and runtime config flags for custom provider opt-in, dev-only private base URLs, and hosted egress allowlists.
- Kept official OpenAI (`https://api.openai.com/v1`) allowed by default and treated non-official OpenAI-compatible endpoints as policy-controlled.
- Added DNS resolution validation for non-official provider hostnames before outbound calls. Private, loopback, link-local, reserved, unspecified, multicast, metadata, `.local`, and `.internal` destinations are rejected unless a local-development custom-provider exception applies.
- Allowed localhost/private custom providers only when `STUCK_LLM_ALLOW_CUSTOM_PROVIDER=true` and `STUCK_LLM_ALLOW_PRIVATE_BASE_URL=true` are enabled outside hosted mode. Hosted mode still requires `STUCK_LLM_PROVIDER_EGRESS_ALLOWLIST` and never allows private/local endpoints.
- Added bounded 429/503 retry with backoff around OpenAI-compatible HTTP POST calls; 401/403 and other non-transient errors are not retried.
- Made provider timeout explicit at 20 seconds per attempt, with at most two retries.
- Added live prompt budget filtering before provider calls: source count, per-source excerpt, and total prompt context limits. Excluded eligible sources now use `exclusion_reason="prompt_budget"`.
- Added settings-modal copy that Anthropic credentials can be saved but live Anthropic analysis is not connected yet.
- Documented provider policy flags in `.env.example`.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase021_provider_policy_reliability.py -q` failed on missing `ProviderNetworkPolicy`.
- RED: `cd src/frontend && npm test -- SettingsModal.test.tsx` failed on missing Anthropic unsupported-status copy.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase021_provider_policy_reliability.py -q` passed with 11 tests.
- GREEN: `cd src/frontend && npm test -- SettingsModal.test.tsx` passed with 3 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase020_security_and_concurrency.py src/backend/tests/test_phase021_provider_policy_reliability.py -q` passed with 27 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 71 tests and one urllib3 LibreSSL warning from the local Python runtime.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `cd src/frontend && npm test` passed with 24 tests across 7 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `npm run design:lint` passed with 0 errors and 0 warnings.
- `npm audit --audit-level=high` passed with 0 vulnerabilities.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after rerun with network access; the initial sandboxed run could not resolve `registry.npmjs.org`.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_021` returned no matches.
- Secret sentinel grep over `src/frontend/dist`, `backups/phase_021`, and `.local` found no phase_021 fake keys or raw timeout detail strings.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 2147 total lines.

Risks and follow-ups:

- DNS validation is a defense-in-depth application control, not a substitute for hosted network egress policy. Production deployment should still enforce outbound allowlists at the network layer.
- Anthropic live analysis remains unsupported until a dedicated Anthropic adapter phase maps Messages API/tool-use output into `LiveAnalysisOutput`.
- Concurrent conversation requests still preserve stored messages but do not reason over sibling requests that arrive while analysis is already running.

## phase_020 - Review-Filtered Security, Concurrency, A11y, And CI Hardening

Implementation notes:

- Accepted only the verified Claude-review findings for this phase and left overstated findings out of scope.
- Hardened live LLM prompt context so each eligible source is emitted as escaped JSON inside explicit untrusted-source delimiters.
- Added provider base URL validation before OpenAI-compatible endpoint assembly. Non-HTTPS, loopback, private, link-local, metadata, `.local`, `.internal`, and credential-bearing URLs are rejected without calling the HTTP client.
- Added `invalid_base_url` as a safe provider-error code and mapped it to Korean/English user-safe summaries.
- Changed concurrent conversation append persistence to merge each append's new message pair against the latest stored conversation messages.
- Updated `LocalStateStore` writes and updates to use a file-lock-aware critical section and process/thread-specific temporary files before atomic replace.
- Added settings modal backdrop close, Escape close, tab focus trapping, and prior-focus restoration.
- Split market chart SVG accessibility from a screen-reader-accessible data table so chart values are not color/SVG only.
- Added `AbortController` timeout handling to frontend API requests.
- Added GitHub Actions CI for backend tests/mypy/ruff, frontend tests/typecheck/build, and design lint.
- Converted the root `package.json`/`package-lock.json` to explicit design-lint workspace metadata.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase020_security_and_concurrency.py -q` failed on unsafe provider URLs calling the HTTP client, unescaped source delimiters, and stale concurrent append overwrites.
- RED: `cd src/frontend && npm test -- SettingsModal.test.tsx AnalysisPanel.test.tsx api.test.ts` failed on missing modal backdrop/focus behavior, missing chart data table, and missing request abort timeout.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase020_security_and_concurrency.py -q` passed with 7 tests.
- GREEN: `cd src/frontend && npm test -- SettingsModal.test.tsx AnalysisPanel.test.tsx api.test.ts` passed with 9 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase020_security_and_concurrency.py -q` passed with 16 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 60 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `cd src/frontend && npm test` passed with 23 tests across 7 files.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `npm run design:lint` passed with 0 errors and 0 warnings.
- `npm audit --audit-level=high` passed with 0 vulnerabilities.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after rerun with network access; the initial sandboxed run could not resolve `registry.npmjs.org`.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_020` returned no matches.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 2025 total lines.

Risks and follow-ups:

- Provider base URL validation is intentionally conservative. Local/private custom LLM endpoints are rejected by default; an explicit opt-in policy should be designed if local custom providers need to return.
- Provider URL validation does not resolve public hostnames to detect private DNS answers; hosted deployment should add egress allowlists or network policy.
- Conversation append merging preserves concurrent messages, but concurrent requests still do not reason over messages that arrive while their analysis is already running.

## phase_019 - Live Market Data And Search Ingestion

Implementation notes:

- Added `MarketBar` data and extended market quotes with previous close, change percent, and daily chart bars.
- Added a FinanceDataReader-backed market-data path for latest available daily OHLCV data with seeded fixture fallback.
- Preserved seeded quote behavior for offline/local deterministic tests when FinanceDataReader is absent or unavailable.
- Added Naver News, Tavily, and GNews ingestion adapters that normalize results into existing source-document records.
- External source documents are marked with `external_api` and `untrusted_source_text` safety flags.
- Missing external provider credentials return safe `missing_credential:<adapter>` warnings without exposing key names or values beyond the adapter code.
- Chat source collection now tries Naver, Tavily, GNews, Reddit seed, US news seed, and global macro seed for complete analysis requests.
- Kept price/chart bars separate from source documents so live LLM prompts receive evidence only, not market chart data.
- Added OpenAI environment-key fallback for live LLM calls when no UI-saved credential exists; UI-saved credentials still take priority.
- Updated `run-all.sh` to source root `.env` values without printing secrets.
- Added frontend market chart rendering for compact chat assistant responses and expanded analysis snapshots.
- Added `finance-datareader>=0.9.96` to backend dependencies and provider key examples to `.env.example`.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase019_live_market_and_news.py -q` failed before implementation on seeded-only market data and unsupported live adapters.
- RED: `cd src/frontend && npm test -- AnalysisPanel.test.tsx ChatShell.test.tsx` failed before implementation because chart rendering did not exist.
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase019_live_market_and_news.py::test_live_llm_secret_can_fall_back_to_openai_environment_key -q` failed before env fallback was added.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase019_live_market_and_news.py -q` passed with 4 tests.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py src/backend/tests/test_phase016_credentials.py src/backend/tests/test_phase018_live_llm_provider.py src/backend/tests/test_phase019_live_market_and_news.py -q` passed with 32 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 53 tests.
- `cd src/frontend && npm test` passed with 20 tests across 6 files.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `bash -n run-all.sh` passed.
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after rerun with network access; the initial sandboxed run could not resolve `registry.npmjs.org`.
- `python3 -m pip install --user 'finance-datareader>=0.9.96'` installed `finance-datareader==0.9.110` for local validation.
- `PYTHONPATH=src/backend python3 -c "from app.features.market_data.service import get_quote; q=get_quote('KR','005930'); print(q.source if q else None, q.last_price if q else None, q.as_of_at if q else None, len(q.chart_bars) if q else None)"` returned `finance_data_reader 225000.0 2026-04-27T15:30:00+09:00 30`.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_019/manifest.md` returned no matches.
- Secret sentinel grep over `src/frontend/dist`, `backups/phase_019`, and `.local` found no phase_019 fake provider keys.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 1913 total lines.

Risks and follow-ups:

- FinanceDataReader is best-effort and may fail under network/provider changes; the app falls back to seeded fixtures rather than blocking chat.
- External news/search adapters are API-backed only. Reddit/X/SNS scraping remains intentionally deferred pending official API and policy review.
- Naver/Tavily/GNews results are snippets/search documents, not guaranteed full articles; deeper evidence extraction and deduplication should be a later phase.
- Anthropic credentials remain stored/supported in settings, but live Anthropic calls are still unsupported by the phase_018 provider implementation.

## phase_018 - Live LLM Provider Analysis Integration

Implementation notes:

- Added a narrow live LLM provider boundary under `src/backend/app/features/analysis/live_provider.py`.
- Added an OpenAI-compatible HTTP adapter that posts to `/chat/completions` with JSON-schema structured output.
- Kept the existing deterministic `/analysis/requests` path intact for local tests and fallback behavior.
- Added `create_live_analysis` as the credential-gated live path; it decrypts BYOK credentials only immediately before provider calls.
- Wired complete chat requests through seeded source collection, strict `as_of_at` filtering, live analysis, and persisted analysis records.
- Missing credentials now return `setup_needed` assistant messages in Korean or English instead of the old fake-live "LLM not connected" response.
- Provider auth, rate-limit, timeout, unsupported-provider, and malformed-output failures map to user-safe provider-error messages and status fields.
- Live prompts include only eligible source documents with `published_at <= as_of_at`; equality remains included and future documents are stored as excluded.
- Source documents are labeled as untrusted evidence in prompt context and provider output is validated before converting to scoring-compatible evidence items.
- Extended conversation responses and frontend types to carry `analysis_result` while keeping scoring and backtest data separate.
- Updated the snapshot UI to show setup-needed and provider-error statuses without internal provider details.

Validation:

- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py -q` failed before implementation because the live provider module did not exist.
- RED: `cd src/frontend && npm test -- AnalysisPanel.test.tsx` failed before implementation because setup/provider statuses rendered as the generic recorded state.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase018_live_llm_provider.py -q` passed with 9 tests.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase015_runner_and_typo_confirmation.py src/backend/tests/test_phase018_live_llm_provider.py -q` passed with 23 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 49 tests.
- `cd src/frontend && npm test` passed with 19 tests across 6 files.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend` passed.
- `PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app` passed.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npm run build` passed.
- `cd src/frontend && npm audit --audit-level=high` passed with 0 vulnerabilities after rerun with network access; the initial sandboxed run could not resolve `registry.npmjs.org`.
- `git diff --check` passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs src/backend src/frontend/src backups/phase_018/manifest.md` returned no matches.
- Secret grep over `.local`, `src/frontend/dist`, and non-original phase_018 backups found no phase_018 raw test keys or provider-internal detail strings.
- `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` reported 1792 total lines.

Risks and follow-ups:

- Anthropic credentials are preserved in the credential schema but live Anthropic calls intentionally return an unsupported-provider status in this phase.
- The first live provider path uses seeded offline source collection from the existing ingestion MVP; real source collection policy and rate limits remain future work.
- Live responses are validated into evidence handoff items, but probability scoring remains a separate explicit step.

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
