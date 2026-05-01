# Implement Phase 021-030 Summary

This file is a compact index for agents. Keep the original detailed log as the source of truth.

## phase_021 - OpenAI Provider Policy, DNS Safety, And Live Call Reliability

Phase Goal
- Scoped the phase to the OpenAI-compatible live provider path; Anthropic remains credential-storable but live analysis is explicitly deferred.
- Added `ProviderNetworkPolicy` and runtime config flags for custom provider opt-in, dev-only private base URLs, and hosted egress allowlists.

Completed Work
- Scoped the phase to the OpenAI-compatible live provider path; Anthropic remains credential-storable but live analysis is explicitly deferred.
- Added `ProviderNetworkPolicy` and runtime config flags for custom provider opt-in, dev-only private base URLs, and hosted egress allowlists.
- Kept official OpenAI (`https://api.openai.com/v1`) allowed by default and treated non-official OpenAI-compatible endpoints as policy-controlled.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase021_provider_policy_reliability.py -q` failed on missing `ProviderNetworkPolicy`.
- RED: `cd src/frontend && npm test -- SettingsModal.test.tsx` failed on missing Anthropic unsupported-status copy.

Next Steps
- DNS validation is a defense-in-depth application control, not a substitute for hosted network egress policy. Production deployment should still enforce outbound allowlists at the network layer.
- Anthropic live analysis remains unsupported until a dedicated Anthropic adapter phase maps Messages API/tool-use output into `LiveAnalysisOutput`.

## phase_022 - US Market Data Provider With SerpApi Google Finance

Phase Goal
- Added a SerpApi Google Finance provider path for US market snapshots behind `SERPAPI_API_KEY`.
- Kept provider order as SerpApi first for configured US quotes, then FinanceDataReader, then seeded fixtures.

Completed Work
- Added a SerpApi Google Finance provider path for US market snapshots behind `SERPAPI_API_KEY`.
- Kept provider order as SerpApi first for configured US quotes, then FinanceDataReader, then seeded fixtures.
- Added `_search_serpapi_google_finance` as a narrow wrapper that uses `engine=google_finance`, `window=1D`, and `{SYMBOL}:{EXCHANGE}` queries.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py -q` reported 1 failed and 2 passed before implementation.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase022_us_market_data_provider.py -q` passed with 3 tests.

Next Steps
- SerpApi Google Finance is suitable for US quote snapshots, line charts, and Google Finance-adjacent market context, not precision OHLC/backtest execution data.
- If a future phase uses SerpApi graph data in `MarketBar`, keep the source label explicit and avoid presenting those generated bars as real OHLC candles.

## phase_023 - Evidence Source Quality And Audit Trail

Phase Goal
- Added `SourceAuditSummary` to analysis responses with safe source warnings, included counts by source type, excluded counts by reason, and prompt document IDs.
- Extended source document inputs/decisions to preserve `adapter`, `relevance_score`, `safety_flags`, `fetched_at`, and `language` metadata from ingestion.

Completed Work
- Added `SourceAuditSummary` to analysis responses with safe source warnings, included counts by source type, excluded counts by reason, and prompt document IDs.
- Extended source document inputs/decisions to preserve `adapter`, `relevance_score`, `safety_flags`, `fetched_at`, and `language` metadata from ingestion.
- Passed source collection warnings from chat live analysis into `AnalysisRequestCommand`.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase023_source_audit_trail.py -q` failed on missing `source_audit`.
- RED: `cd src/frontend && npm test -- api.test.ts AnalysisPanel.test.tsx` failed on missing source audit mapping and rendering.

Next Steps
- Source audit summaries now show warning and exclusion codes, but deeper source quality scoring, article extraction, and cross-provider deduplication remain future work.
- Warning-code sanitization is intentionally narrow; future external adapters should continue returning stable machine codes rather than provider response text.

## phase_024 - Cerebras OpenAI-Compatible Test Provider

Phase Goal
- Added `cerebras` as a first-class credential provider alongside OpenAI, Anthropic, and custom providers.
- Added `CEREBRAS_API_KEY` environment fallback for local live-analysis testing when no UI-saved credential or OpenAI environment fallback exists.

Completed Work
- Added `cerebras` as a first-class credential provider alongside OpenAI, Anthropic, and custom providers.
- Added `CEREBRAS_API_KEY` environment fallback for local live-analysis testing when no UI-saved credential or OpenAI environment fallback exists.
- Added `CEREBRAS_MODEL`, defaulting to `gpt-oss-120b`.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase024_cerebras_provider.py -q` failed on missing Cerebras env fallback and Cerebras response schema shaping.
- RED: `cd src/frontend && npm test -- SettingsModal.test.tsx` failed on missing Cerebras provider option.

Next Steps
- Automated tests mock Cerebras provider calls; a real integration smoke test still requires a valid `CEREBRAS_API_KEY` and explicit user approval to make an outbound request.
- Hosted deployments still need explicit egress policy for non-OpenAI provider endpoints.

## phase_025 - LLM Provider Connection Diagnostics

Phase Goal
- Added `POST /credentials/llm/test` to validate the active saved or environment-backed LLM credential without running a stock-analysis prompt.
- Reused the existing OpenAI-compatible provider URL validation, retry, timeout, and HTTP error mapping for connection tests.

Completed Work
- Added `POST /credentials/llm/test` to validate the active saved or environment-backed LLM credential without running a stock-analysis prompt.
- Reused the existing OpenAI-compatible provider URL validation, retry, timeout, and HTTP error mapping for connection tests.
- Added `OpenAiCompatibleAnalysisProvider.test_connection`, which sends a minimal `/chat/completions` payload with no source evidence and no structured-output schema.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase025_llm_connection_diagnostics.py -q` failed with three missing-route failures and one old default-model failure.
- RED: `cd src/frontend && npm test -- api.test.ts SettingsModal.test.tsx` failed on missing `testLlmCredential` API export and missing Settings modal `Test connection` button.

Next Steps
- Automated validation uses mocked HTTP calls; a real Cerebras smoke test still requires the user's valid key and an explicit live call through the new Settings control or endpoint.
- `auth_error` confirms the provider rejected the credential request, but it does not distinguish expired key, wrong key, account/model authorization, or provider-side policy without a deliberately exposed provider-specific diagnostic layer.

## phase_026 - Generative Chat Orchestration

Phase Goal
- Added a structured chat-intent request path to the existing OpenAI-compatible provider.
- Added `ChatIntentOutput` with intent, stock query, market, horizon, analysis mode, source hints, follow-up flag, and follow-up question fields.

Completed Work
- Added a structured chat-intent request path to the existing OpenAI-compatible provider.
- Added `ChatIntentOutput` with intent, stock query, market, horizon, analysis mode, source hints, follow-up flag, and follow-up question fields.
- Added `build_chat_intent_messages` with escaped JSON user/conversation context and instructions to treat chat text as untrusted data.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase026_generative_chat_orchestration.py -q` failed with 3 tests because the provider was not yet called and non-literal stock references stayed at `needs_input`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase026_generative_chat_orchestration.py -q` passed with 4 tests and one local urllib3 LibreSSL warning.

Next Steps
- The orchestration call adds one LLM round trip before live analysis when credentials are configured; future work may cache or combine this with analysis where latency matters.
- Source hints currently select only known adapters and do not ingest arbitrary URLs or raw text.

## phase_027 - Settings-Language Response Policy

Phase Goal
- Added optional `response_language` to `ConversationCommand`.
- Backend conversation handling now uses explicit response language before falling back to Hangul/message-language detection.

Completed Work
- Added optional `response_language` to `ConversationCommand`.
- Backend conversation handling now uses explicit response language before falling back to Hangul/message-language detection.
- Backend-generated missing-input, setup-needed, provider-error, and live-analysis assistant copy now follow that explicit language.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase027_settings_language_policy.py -q` failed with 3 expected failures because `response_language` was ignored and prompts followed message-language detection.
- RED: `cd src/frontend && npm test -- api.test.ts ChatShell.test.tsx App.test.tsx` failed on missing `responseLanguage` request plumbing.

Next Steps
- Existing conversations do not store a language preference; the active frontend UI language is sent per new message.
- Other backend endpoints outside chat still use their existing language behavior unless they later receive an explicit language parameter.
