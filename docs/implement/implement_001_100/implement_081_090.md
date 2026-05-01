# Implement Phase 081-090 Summary

This file is a compact index for agents. Keep the original detailed log as the source of truth.

## phase_081 - Similar Event Calibration Baseline

Phase Goal
- Added `similar_event_sample_count`, `similar_event_win_rate`, and `similar_event_median_return_pct` to score responses.
- Exposed the similar-event baseline in Korean/English chat copy and the analysis panel.

Completed Work
- Added `similar_event_sample_count`, `similar_event_win_rate`, and `similar_event_median_return_pct` to score responses.
- Exposed the similar-event baseline in Korean/English chat copy and the analysis panel.
- Kept the implementation as a replaceable local baseline so a later historical matching engine can fill the same contract.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED/GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase008_scoring.py src/backend/tests/test_phase077_prediction_probabilities.py -q` passed after adding the new fields and chat assertions.
- RED/GREEN: `cd src/frontend && npm test -- AnalysisPanel.test.tsx api.test.ts` passed after frontend mapping and UI assertions were updated.

Next Steps
- The baseline should be replaced by a real event similarity dataset before treating the win rate as statistically meaningful.

## phase_082 - Prediction Docs, Backups, And Full Validation

Phase Goal
- Added task and plan records for `phase_077` through `phase_082`.
- Preserved final modified-file backups under `backups/phase_082/` after all code and validation work was complete, per the user's requested ordering.

Completed Work
- Added task and plan records for `phase_077` through `phase_082`.
- Preserved final modified-file backups under `backups/phase_082/` after all code and validation work was complete, per the user's requested ordering.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 141 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests` passed.

Next Steps
- Similar-event calibration is currently a local baseline slot derived from evidence stance, not a true historical event-matching model.

## phase_083 - Typo And News Intent Recovery

Phase Goal
- Updated local news-intent routing to recover common typo forms without relying on LLM intent classification.

Completed Work
- Updated local news-intent routing to recover common typo forms without relying on LLM intent classification.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_korean_news_typo_routes_to_news_digest_without_llm_intent -q` failed with `market_snapshot`.
- GREEN: the same test passed after typo recovery was added.

Next Steps
- Typo recovery is conservative and currently targets common news-keyword mistakes rather than a full spelling-correction engine.

## phase_084 - News Query Diversification

Phase Goal
- Added `_build_news_queries` to generate multiple company-event searches for US stocks.
- Queries now cover earnings, product/service/AI strategy, CEO/leadership succession, regulation/lawsuit/antitrust controversy, analyst/valuation consensus, and S&P Global Market Intelligence research.

Completed Work
- Added `_build_news_queries` to generate multiple company-event searches for US stocks.
- Queries now cover earnings, product/service/AI strategy, CEO/leadership succession, regulation/lawsuit/antitrust controversy, analyst/valuation consensus, and S&P Global Market Intelligence research.
- Provider run transparency now records every provider/query pair.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_news_digest_builds_diversified_us_company_event_queries -q` failed before `_build_news_queries` existed.
- GREEN: the same test passed after query generation was implemented.

Next Steps
- The S&P Global item is discovered through provider search results; full article extraction depends on the external source being reachable and accessible.

## phase_085 - Diverse News Selection

Phase Goal
- Added `_select_diverse_articles` so important articles are selected with category and source-domain caps before fallback fill.
- Fixed keyword matching so short tokens such as `ai` require word boundaries.

Completed Work
- Added `_select_diverse_articles` so important articles are selected with category and source-domain caps before fallback fill.
- Fixed keyword matching so short tokens such as `ai` require word boundaries.
- Narrowed controversy classification by removing broad `risk` matching, which misclassified analyst valuation-risk articles.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_news_digest_selects_diverse_important_articles -q` failed before the selector existed.
- GREEN: the same test passed after selector and classifier fixes.

Next Steps
- Category detection remains keyword-based; LLM article metadata can refine it when provider summaries are available.

## phase_086 - Naver And Public Social News Sources

Phase Goal
- Added `naver_news` and `serpapi_social_web` to the news digest provider contract and frontend type union.
- Added Naver News API collection using `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET`.

Completed Work
- Added `naver_news` and `serpapi_social_web` to the news digest provider contract and frontend type union.
- Added Naver News API collection using `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET`.
- Added public SNS search through SerpApi Google Web with queries restricted to `x.com`, `twitter.com`, and `facebook.com`.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_news_digest_uses_naver_and_public_social_search_when_credentials_available -q` failed before provider-specific social queries existed.
- GREEN: the same test passed after provider routing and collectors were implemented.

Next Steps
- Naver coverage depends on user-supplied Naver API credentials.
- Public social search only sees indexed public posts and should be treated as supplemental sentiment/context, not complete social coverage.

## phase_087 - Korean Prediction Intent Fallback

Phase Goal
- See the original detailed log for the exact phase goal.

Completed Work
- Recorded as completed in the original phase log.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase077_prediction_probabilities.py::test_korean_prediction_keyword_routes_to_analysis_without_llm_intent -q` failed with `market_snapshot`.
- GREEN: the same test passed after the keyword fix.

Next Steps
- The completed live analysis path still requires a saved LLM credential for evidence extraction.

## phase_088 - News Source Validation, Docs, And Push Prep

Phase Goal
- Recorded completed task, plan, and implementation notes for `phase_083` through `phase_088`.
- Preserved documentation backups under `backups/phase_088/` after code validation was complete, per the user's requested ordering.

Completed Work
- Recorded completed task, plan, and implementation notes for `phase_083` through `phase_088`.
- Preserved documentation backups under `backups/phase_088/` after code validation was complete, per the user's requested ordering.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` passed with 146 tests and one local urllib3 LibreSSL warning.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache PYTHONPATH=src/backend python3 -m compileall src/backend/app/features/news_digest src/backend/app/features/conversations src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py` passed.

Next Steps
- Public social coverage intentionally uses search-indexed public pages only. Direct X/Facebook crawling is not implemented because authenticated scraping and private content access would add legal, operational, and security risk.

## phase_089 - News Review Routing And Test Isolation

Phase Goal
- Reviewed the `phase_086` through `phase_088` continuation work around optional Naver, public social news search, and Korean prediction fallback.
- Added a regression test proving the conversation path includes `serpapi_social_web` provider runs and public X results for social-reaction requests.

Completed Work
- Reviewed the `phase_086` through `phase_088` continuation work around optional Naver, public social news search, and Korean prediction fallback.
- Added a regression test proving the conversation path includes `serpapi_social_web` provider runs and public X results for social-reaction requests.
- Isolated existing news digest tests from developer-local `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET` environment variables.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase064_069_news_digest.py::test_korean_social_reaction_request_routes_to_news_digest_without_llm_intent -q` failed with no `news_digest` payload before the routing fix.
- GREEN: the same test passed after adding social-news routing keywords.

Next Steps
- Continue with the next phase summary or the original detailed log as needed.

## phase_090 - US Mega-Cap Intent Matrix Regression

Phase Goal
- Covered three user intents per symbol: Korean news digest, Korean stock chart/snapshot, and Korean prediction.
- The fake LLM intent provider intentionally returns `other`, so the test locks in deterministic local routing and alias/S&P 500 resolution rather than relying on the classifier.

Completed Work
- Covered three user intents per symbol: Korean news digest, Korean stock chart/snapshot, and Korean prediction.
- The fake LLM intent provider intentionally returns `other`, so the test locks in deterministic local routing and alias/S&P 500 resolution rather than relying on the classifier.
- The fake SerpApi Google Finance fixture includes chart bars and USD/KRW lookup handling, matching the Korean market snapshot response path.

Changed Files
- See the original detailed log for the file list.

Important Notes
- Ad hoc matrix check passed for 12 paths: four symbols times news, chart, and prediction.
- `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase090_us_mega_cap_intent_matrix.py -q` passed.

Next Steps
- This phase validates backend routing with deterministic provider fakes. It does not perform live SerpApi, Tavily, GNews, or LLM network validation.
