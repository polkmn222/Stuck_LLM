# Implement Phase 131-140 Summary

This file is a compact implementation index for agents. Keep the detailed source log separate when it exists.

## phase_131 - Free RSS News Providers

Completed Work
- Added `seekingalpha_rss`, `yahoo_finance_rss`, `google_news_rss`, and `bing_news_rss` news provider schema values.
- Added free RSS provider expansion for no-key news paths.
- Added XML RSS parsing and provider collectors connected to existing dedupe, ranking, provider-run, and cache behavior.
- Added `test_phase131_free_rss_news_providers.py`.

Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase131_free_rss_news_providers.py -q`: passed.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase130_crawl_and_scenario_prediction.py src/backend/tests/test_phase131_free_rss_news_providers.py -q`: passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend/app/features/news_digest src/backend/tests/test_phase131_free_rss_news_providers.py`: passed.

## phase_132 - EventRegistry News Provider

Completed Work
- Added `eventregistry` external provider credential metadata.
- Added `eventregistry_news` news provider schema value.
- Added direct REST EventRegistry collector without adding an SDK dependency.
- Added selected-key handling for EventRegistry provider calls.
- Added `test_phase132_eventregistry_news_provider.py`.

Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase132_eventregistry_news_provider.py -q`: passed.
- Credential/news regression tests passed for the new provider boundary.
- Ruff passed for touched backend news/credential files.

## phase_133 - Reddit Public Search Provider

Completed Work
- Added `reddit_public_search` news provider schema value.
- Added subreddit public search fanout for Reddit/community/sentiment-style requests.
- Kept user-supplied Reddit search URL crawl behavior separate from automatic Reddit public search.
- Added `test_phase133_reddit_public_search_provider.py`.

Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase133_reddit_public_search_provider.py -q`: passed.
- News provider regression tests for phases 130-133 passed.
- Ruff passed for touched backend news files.

## phase_134 - ChatGPT-Style News And Scenario Replies

Completed Work
- Added sectioned news digest reply formatting with `as_of_at`, headline markdown links, source domains, providers, and publication dates.
- Added Korean and English category labels for product/services, earnings/guidance, regulation/litigation, community/market reaction, official announcements, business/strategy, and other.
- Added scenario-style prediction text that keeps scoring output and labels the result as information-based scenario analysis.
- Added `test_phase134_chatgpt_style_response_format.py`.

Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase134_chatgpt_style_response_format.py -q`: passed.
- News/conversation/prediction focused regression tests passed.
- Ruff passed for touched backend conversation files.

## phase_135 - External News Provider Credential Selection

Completed Work
- Added encrypted external credential profile state for Tavily, GNews, SerpAPI, and EventRegistry.
- Added backend external credential schemas, service functions, and profile endpoints.
- Passed selected external credentials into conversation news digest and prediction news context.
- Updated news digest provider collectors to prefer explicit selected keys over local environment compatibility keys.
- Added `test_phase135_external_provider_credential_selection.py`.

Validation
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase135_external_provider_credential_selection.py -q`: passed.
- Credential/news focused regression tests passed.
- Ruff passed for touched backend credential/news/conversation files.

## phase_136 - Frontend Credential And Source Badges

Completed Work
- Added frontend API/type mapping for external credential profile list, save, select, and delete endpoints.
- Added Settings Model-tab controls for news/search provider keys.
- Added Chat selected credential badge and clickable markdown source links.
- Split news source/provider badges in `NewsDigestView`.
- Added CSS for selected-key pills, markdown message links, news provider badges, and settings subsections.
- Updated App state wiring and focused frontend tests.

Validation
- RED: `cd src/frontend && npm test -- api.test.ts SettingsModal.test.tsx ChatShell.test.tsx` failed before frontend external credential API/UI implementation.
- GREEN: `cd src/frontend && npm test -- api.test.ts SettingsModal.test.tsx ChatShell.test.tsx` passed.
- Focused regression: `cd src/frontend && npm test -- App.test.tsx NewsDigestView.test.tsx api.test.ts SettingsModal.test.tsx ChatShell.test.tsx` passed with 50 tests.
- Typecheck: `cd src/frontend && npm run typecheck` passed.

## phase_137 - Product And Runtime Documentation Update

Completed Work
- Updated `docs/product/llm-agent-spec.md` with free RSS, EventRegistry, Reddit public search, selected external credential, source-linked news, scenario-analysis, and UI badge rules.
- Updated `docs/product/llm-runtime-execution.md` with provider selection order, RSS/EventRegistry/Reddit execution, direct URL crawl behavior, source-linked output, and scenario response boundaries.
- Added compact phase 131-140 plan, task, and implementation summaries.
- Updated compact documentation READMEs to point at the new latest range.

Validation
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `git diff --check`: passed.
- `wc -l docs/product/llm-agent-spec.md docs/product/llm-runtime-execution.md docs/plan/README.md docs/task/README.md docs/implement/README.md docs/plan/plan_101_200/README.md docs/task/task_101_200/README.md docs/implement/implement_101_200/README.md docs/plan/plan_101_200/plan_131_140.md docs/task/task_101_200/task_131_140.md docs/implement/implement_101_200/implement_131_140.md`: completed.

## phase_138 - Reddit Sentiment Query Boundary

Completed Work
- Added Reddit public-search activation terms for investor sentiment, retail sentiment, social reaction, market reaction, and Korean sentiment/reaction wording.
- Changed Reddit public-search provider queries to include the resolved company name, ticker, and cleaned user request.
- Preserved `SOCIAL_QUERY_SUFFIX`, including the Trump/tariffs terms used for X/social search.
- Added focused coverage to `test_phase133_reddit_public_search_provider.py`.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase133_reddit_public_search_provider.py -q` failed because sentiment/social-reaction wording did not activate `reddit_public_search`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase133_reddit_public_search_provider.py -q`: passed with 3 tests.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend/app/features/news_digest/service.py src/backend/tests/test_phase133_reddit_public_search_provider.py`: passed.

## phase_139 - Reddit Partial Failure Visibility

Completed Work
- Changed Reddit public-search collection to return a partial-failure count alongside successful articles.
- Propagated a soft `provider_error:reddit_public_search` warning into provider runs and digest warnings when at least one subreddit succeeds and another fails.
- Kept successful Reddit articles in the digest and preserved all-failed behavior as a provider error.
- Added focused coverage to `test_phase133_reddit_public_search_provider.py`.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase133_reddit_public_search_provider.py -q` failed because partial Reddit fan-out failures were recorded as fully `completed`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase133_reddit_public_search_provider.py -q`: passed with 4 tests.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend/app/features/news_digest/service.py src/backend/tests/test_phase133_reddit_public_search_provider.py`: passed.

## phase_140 - EventRegistry Payload Guard

Completed Work
- Added strict EventRegistry `articles.results` payload validation so malformed payloads are normalized into provider errors.
- Preserved well-formed empty EventRegistry result lists as normal empty results.
- Tightened `ExternalCredentialMap` to use `ExternalCredentialProvider` keys and updated selected external credential typing in conversation service.
- Added focused coverage to `test_phase132_eventregistry_news_provider.py`.

Validation
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase132_eventregistry_news_provider.py -q` failed with a leaked `TypeError` for `articles.results=None`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase132_eventregistry_news_provider.py -q`: passed with 3 tests.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase135_external_provider_credential_selection.py -q`: passed with 2 tests.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend/app/features/news_digest/service.py src/backend/app/features/conversations/service.py src/backend/tests/test_phase132_eventregistry_news_provider.py`: passed.

## Final Validation

- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q`: passed with 199 tests and one existing urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests`: passed.
- `PYTHONPATH=src/backend python3 -m ruff check src/backend`: passed.
- `cd src/frontend && npm test`: passed with 62 tests.
- `cd src/frontend && npm run typecheck`: passed.
- `cd src/frontend && npm run build`: passed.
- `cd src/frontend && npm audit --audit-level=high`: passed with 0 vulnerabilities.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `git diff --check`: passed.
