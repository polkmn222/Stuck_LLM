# Implement Phase 071-080 Summary

This file is a compact index for agents. Keep the original detailed log as the source of truth.

## phase_071 - Joint Dev Server Shutdown

Phase Goal
- Split `run-all.sh` traps into `trap cleanup EXIT` and `trap shutdown INT TERM`.
- Added `shutdown()` so Ctrl+C clears traps, terminates both tracked child processes, waits for them, and exits with code 130.

Completed Work
- Split `run-all.sh` traps into `trap cleanup EXIT` and `trap shutdown INT TERM`.
- Added `shutdown()` so Ctrl+C clears traps, terminates both tracked child processes, waits for them, and exits with code 130.
- Started backend and frontend commands with `exec` so the recorded PIDs correspond to the server processes rather than wrapper shells.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase015_runner_and_typo_confirmation.py::test_run_all_ctrl_c_uses_shutdown_trap_and_execs_server_processes -q` failed because `shutdown()` and `exec` were absent.
- GREEN: targeted backend command passed after the script update.

Next Steps
- `npm run dev` still owns the Vite child lifecycle internally. In normal npm behavior, terminating npm should terminate Vite; if a future environment leaves Vite orphaned, add process-tree cleanup.

## phase_072 - News Query And Quote Page Demotion

Phase Goal
- Changed US news search query generation from `stock news` to `latest company news earnings official business controversy`.
- Added quote-page detection for Google Finance/Yahoo Finance-style price/history pages and negative scoring for those results.

Completed Work
- Changed US news search query generation from `stock news` to `latest company news earnings official business controversy`.
- Added quote-page detection for Google Finance/Yahoo Finance-style price/history pages and negative scoring for those results.
- Normalized and truncated provider snippets to prevent long navigation text from reaching the UI.

Changed Files
- See the original detailed log for the file list.

Important Notes
- Covered by `test_news_digest_query_targets_news_instead_of_stock_price_pages`.

Next Steps
- Providers can still return quote pages when the result set is sparse; they should now fall below actual news when news results are present.

## phase_073 - News Importance Categories

Phase Goal
- Added `NewsCategory` and article fields for category, Korean headline/summary, importance score, and source domain.
- Added category detection for earnings, official, core business, controversy, market reaction, product/service, quote pages, and other.

Completed Work
- Added `NewsCategory` and article fields for category, Korean headline/summary, importance score, and source domain.
- Added category detection for earnings, official, core business, controversy, market reaction, product/service, quote pages, and other.
- Ranked deduped articles by importance score before timestamp and provider rank.

Changed Files
- See the original detailed log for the file list.

Important Notes
- Covered by `test_news_digest_prioritizes_official_earnings_and_business_news_over_quote_pages`.

Next Steps
- Category detection is keyword-based until LLM metadata is available. It is intentionally conservative and can be refined with real search samples.

## phase_074 - LLM Korean News Metadata

Phase Goal
- Updated the news summary prompt to ask for compact JSON with digest `summary` and per-article Korean metadata.
- Added JSON extraction and safe per-article updates keyed by article ID.

Completed Work
- Updated the news summary prompt to ask for compact JSON with digest `summary` and per-article Korean metadata.
- Added JSON extraction and safe per-article updates keyed by article ID.
- Kept plain text summary fallback for providers that do not return JSON.

Changed Files
- See the original detailed log for the file list.

Important Notes
- Covered by `test_llm_news_json_updates_korean_article_headlines`.

Next Steps
- LLM article translation quality depends on the saved provider. Deterministic fallback uses the original provider title/snippet when JSON output is unavailable.

## phase_075 - Korean News Digest Cards

Phase Goal
- Reworked `NewsDigestView` to render a Korean headline/summary list before article cards.
- Replaced the plain ordered article list with compact cards showing favicon-style icon, source domain, provider, category, original title link, and clipped summary.

Completed Work
- Reworked `NewsDigestView` to render a Korean headline/summary list before article cards.
- Replaced the plain ordered article list with compact cards showing favicon-style icon, source domain, provider, category, original title link, and clipped summary.
- Added CSS line clamps and `overflow-wrap` so long provider snippets do not push outside the chat message box.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `cd src/frontend && npm test -- ChatShell.test.tsx api.test.ts` failed because the new API fields and UI elements were absent.
- GREEN: the same command passed with 22 tests.

Next Steps
- The UI still exposes provider adapter IDs for transparency. A later presentation pass can add friendly labels while keeping adapter IDs available.

## phase_076 - News Polish Docs, Backups, And Validation

Phase Goal
- Added task and plan records for `phase_070` through `phase_076`.
- Preserved documentation backups under `backups/phase_076/`.

Completed Work
- Added task and plan records for `phase_070` through `phase_076`.
- Preserved documentation backups under `backups/phase_076/`.
- Implementation backups were created before editing `run-all.sh`, news digest backend files, conversation service, frontend API/types, chat UI, and styles.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 139 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.

Next Steps
- Favicon rendering uses Google's favicon endpoint in the browser. If offline or blocked, the card still shows text content, but the icon may not load.

## phase_077 - Five Trading Day Prediction Probabilities

Phase Goal
- Defaulted prediction-like no-horizon analysis requests to `swing`, which the response labels as the next five trading days.
- Attached `ScoreResponse` to completed `AnalysisResponse` values produced through the conversation path.

Completed Work
- Defaulted prediction-like no-horizon analysis requests to `swing`, which the response labels as the next five trading days.
- Attached `ScoreResponse` to completed `AnalysisResponse` values produced through the conversation path.
- Added score text to assistant analysis replies and rendered completed probabilities in the analysis panel.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase077_prediction_probabilities.py src/backend/tests/test_phase006_chat_settings_market_data.py src/backend/tests/test_phase014_conversation_language.py src/backend/tests/test_phase020_security_and_concurrency.py -q` passed.
- RED/GREEN: `cd src/frontend && npm test -- AnalysisPanel.test.tsx api.test.ts` passed.

Next Steps
- Completed probabilities still require a saved LLM key because evidence stance extraction remains LLM-backed in the live conversation path.

## phase_078 - Market Data Evidence Bundle

Phase Goal
- Created a `market_data` source document from each quote's latest price, previous close, session change, and eligible chart closes.
- Filtered chart bars after the quote `as_of_at` before deriving chart context.

Completed Work
- Created a `market_data` source document from each quote's latest price, previous close, session change, and eligible chart closes.
- Filtered chart bars after the quote `as_of_at` before deriving chart context.
- Appended the market-data document to live-analysis source documents so source audit and LLM prompt grounding can show chart/market context.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase077_prediction_probabilities.py -q` passed after verifying `market_data` appears in source audit and live provider documents.
- Full backend validation initially failed one existing orchestration assertion because `market_data` is now expected in `included_by_source_type`; the test was updated and the full backend suite passed.

Next Steps
- Market-data evidence summarizes available quote/chart context; it does not yet compute richer technical indicators.

## phase_079 - Expected Return And Downside Risk

Phase Goal
- Added rough expected return min/max percentage fields and downside probability to `ScoreResponse`.
- Derived the expected range from the buy/sell directional edge and confidence score.

Completed Work
- Added rough expected return min/max percentage fields and downside probability to `ScoreResponse`.
- Derived the expected range from the buy/sell directional edge and confidence score.
- Added chat copy and analysis-panel rendering for expected return and downside risk.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase077_prediction_probabilities.py -q` passed.
- RED/GREEN: `cd src/frontend && npm test -- AnalysisPanel.test.tsx api.test.ts` passed.

Next Steps
- Expected return range is an MVP heuristic and is labeled as such in scoring rationale; it is not yet calibrated against real historical outcomes.

## phase_080 - Historical Buy-Date PnL Chat

Phase Goal
- Added `pnl_simulation` conversation status and optional `backtest_result` payloads on conversation responses and assistant messages.
- Parsed Korean, ISO, and English month/day buy-date phrases into market-close timestamps.

Completed Work
- Added `pnl_simulation` conversation status and optional `backtest_result` payloads on conversation responses and assistant messages.
- Parsed Korean, ISO, and English month/day buy-date phrases into market-close timestamps.
- Routed buy-date questions to `run_backtest` with quantity `1.0`, separate from analysis requests.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase080_pnl_chat.py src/backend/tests/test_phase009_backtest.py -q` passed.
- RED/GREEN: `cd src/frontend && npm test -- api.test.ts` passed after PnL conversation mapping was added.

Next Steps
- PnL chat currently depends on seeded/local price bars. Provider-backed historical bars should be added before broad date coverage is expected.
