# Implement Phase 061-070 Summary

This file is a compact index for agents. Keep the original detailed log as the source of truth.

## phase_061 - Chat Auto Scroll To Latest

Phase Goal
- Added a bottom scroll anchor to `ChatShell`.
- Added an effect keyed by message count and pending activity state to call `scrollIntoView`.

Completed Work
- Added a bottom scroll anchor to `ChatShell`.
- Added an effect keyed by message count and pending activity state to call `scrollIntoView`.
- Guarded `scrollIntoView` with optional chaining so non-browser test environments remain compatible.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `cd src/frontend && npm test -- ChatShell.test.tsx` failed because no scroll call occurred.
- GREEN: same command passed with 10 tests.

Next Steps
- The chat still updates after complete responses. A streaming phase should reuse the same anchor for incremental token updates.

## phase_062 - S&P 500 Symbol Directory Routing

Phase Goal
- Added `sp500_constituents.csv` under `market_data` as a local S&P 500 constituent directory.
- Added a cached CSV loader that builds symbol and normalized company-name aliases from the directory.

Completed Work
- Added `sp500_constituents.csv` under `market_data` as a local S&P 500 constituent directory.
- Added a cached CSV loader that builds symbol and normalized company-name aliases from the directory.
- Updated resolver ordering so explicit aliases remain first, then S&P 500 directory matches, then direct S&P ticker tokens typed under a KR default route to US lookup.

Changed Files
- See the original detailed log for the file list.

Important Notes
- GREEN: same command passed after the S&P 500 directory resolver.
- Full validation is recorded above under `phase_063`.

Next Steps
- The CSV is a local seed, not an automatic membership refresh. Add a managed refresh/import workflow before relying on the file as an always-current index universe.

## phase_063 - Provider USD/KRW Conversion Rate

Phase Goal
- Added `get_usd_krw_rate()` to the market-data service. It uses the existing SerpApi Google Finance transport and tries `USD-KRW`, `USD/KRW`, then `USDKRW`.
- Updated Korean US-stock snapshot copy to use `STUCK_LLM_USD_KRW_RATE` first, then provider FX, then the local fallback.

Completed Work
- Added `get_usd_krw_rate()` to the market-data service. It uses the existing SerpApi Google Finance transport and tries `USD-KRW`, `USD/KRW`, then `USDKRW`.
- Updated Korean US-stock snapshot copy to use `STUCK_LLM_USD_KRW_RATE` first, then provider FX, then the local fallback.
- Adjusted older Korean US-stock tests to set a deterministic env rate when they mock only the equity quote request.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase055_058_market_chat.py -q` failed because Korean US-stock copy still used `USD/KRW 1,400`.
- GREEN: same command passed with 6 tests and one local urllib3 LibreSSL warning.

Next Steps
- FX remains a spot display conversion. Historical analysis still needs timestamped FX evidence if future phases use converted prices as analytical evidence.

## phase_064 - News Digest Provider Contract

Phase Goal
- Added `src/backend/app/features/news_digest/` with schemas and provider service logic.
- Implemented Tavily Search, GNews, SerpApi Google News, and SerpApi Google Web adapters through the existing environment-key pattern.

Completed Work
- Added `src/backend/app/features/news_digest/` with schemas and provider service logic.
- Implemented Tavily Search, GNews, SerpApi Google News, and SerpApi Google Web adapters through the existing environment-key pattern.
- Flattened grouped SerpApi Google News `stories` records from the Streamlit prototype into first-class article records.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py -q` failed with `ModuleNotFoundError: No module named 'app.features.news_digest'`.
- GREEN: the same command passed with 2 tests after the provider contract and chat integration.

Next Steps
- No separate persistent news cache was added. Repeated identical news requests may call providers again unless a later cache phase is introduced.

## phase_065 - News Query Ranking And Dedupe

Phase Goal
- Normalized US quote requests to `{company} {symbol} stock news`, matching the `finance_news_app.py` prototype behavior.
- Canonicalized URLs by removing fragments and `utm_*` query parameters before duplicate detection.

Completed Work
- Normalized US quote requests to `{company} {symbol} stock news`, matching the `finance_news_app.py` prototype behavior.
- Canonicalized URLs by removing fragments and `utm_*` query parameters before duplicate detection.
- Ranked articles by parsed published time, then provider priority and provider rank.

Changed Files
- See the original detailed log for the file list.

Important Notes
- Covered by `test_news_digest_collects_providers_dedupes_and_tracks_transparency`.

Next Steps
- Some providers return relative dates such as `2 hours ago`; those are preserved for display but sort after parseable timestamps.

## phase_066 - LLM News Summary Fallback

Phase Goal
- Added an LLM summary prompt that sends only article metadata, provider IDs, dates, snippets, and links.
- Kept deterministic summary output when the saved LLM credential is absent or the provider call fails.

Completed Work
- Added an LLM summary prompt that sends only article metadata, provider IDs, dates, snippets, and links.
- Kept deterministic summary output when the saved LLM credential is absent or the provider call fails.
- Verified that news digest requests do not invoke live stock analysis.

Changed Files
- See the original detailed log for the file list.

Important Notes
- Covered by `test_korean_news_request_returns_digest_without_horizon_and_uses_llm_summary`.

Next Steps
- The LLM summary is a concise overview string, not a structured citation parser. The linked article list remains the auditable source of record.

## phase_067 - Chat News Request Routing

Phase Goal
- Added `news_digest` to chat intent and conversation status types.
- Routed news-keyword requests before the market snapshot path so news-only requests do not ask for horizon.

Completed Work
- Added `news_digest` to chat intent and conversation status types.
- Routed news-keyword requests before the market snapshot path so news-only requests do not ask for horizon.
- Added top-level and message-level `news_digest` response payloads.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py -q` failed before the news digest module existed.
- GREEN: the same command passed with 2 tests after routing and digest integration.

Next Steps
- Ambiguous news requests without a resolvable stock still use the existing missing-stock path. Broader company-name resolution remains tied to the market-data resolver and S&P 500 directory.

## phase_068 - Chat News Digest UI

Phase Goal
- Added `NewsDigest`, `NewsArticle`, and provider-run UI types plus API snake_case to camelCase mapping.
- Rendered news digests inside assistant messages with a concise overview, linked important stories, provider transparency chips, and warning copy.

Completed Work
- Added `NewsDigest`, `NewsArticle`, and provider-run UI types plus API snake_case to camelCase mapping.
- Rendered news digests inside assistant messages with a concise overview, linked important stories, provider transparency chips, and warning copy.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `cd src/frontend && npm test -- ChatShell.test.tsx api.test.ts` failed because API mapping and news digest UI rendering were absent.
- GREEN: the same command passed with 22 tests.

Next Steps
- The UI currently renders provider names as internal adapter IDs. A later polish pass can add user-facing provider labels without changing the transparent audit data.

## phase_069 - News Digest Docs, Backups, And Validation

Phase Goal
- Added reverse-chronological task and plan records for `phase_064` through `phase_069`.
- Preserved pre-documentation copies under `backups/phase_069/`.

Completed Work
- Added reverse-chronological task and plan records for `phase_064` through `phase_069`.
- Preserved pre-documentation copies under `backups/phase_069/`.
- Preserved implementation-file copies under `backups/phase_064/` before modifying the news, conversation, API, chat, and style surfaces.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 135 tests and one local urllib3 LibreSSL warning.
- `cd src/frontend && npm test` passed with 49 tests.

Next Steps
- Live news quality depends on provider quotas and provider result metadata. Missing provider credentials are surfaced in the digest warnings instead of blocking all results.

## phase_070 - Ruff And MyPy Install

Phase Goal
- Installed `ruff 0.15.12` and `mypy 1.19.1` into the user Python environment with `python3 -m pip install --user`.
- The backend `pyproject.toml` already listed both tools under `[project.optional-dependencies].dev`, so no project dependency file change was needed.

Completed Work
- Installed `ruff 0.15.12` and `mypy 1.19.1` into the user Python environment with `python3 -m pip install --user`.
- The backend `pyproject.toml` already listed both tools under `[project.optional-dependencies].dev`, so no project dependency file change was needed.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `python3 -m ruff --version` reported `ruff 0.15.12`.
- `python3 -m mypy --version` reported `mypy 1.19.1 (compiled: yes)`.

Next Steps
- The installed console scripts are in the user Python bin directory, which is not on PATH. Use `python3 -m ruff` and `python3 -m mypy`, or add that bin directory to PATH later.
