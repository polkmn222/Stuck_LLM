# Implement Phase 031-040 Summary

This file is a compact index for agents. Keep the original detailed log as the source of truth.

## phase_031 - Deterministic Analysis Eval Harness

Phase Goal
- Added backend-only `app.evals` package with `EvalCase`, `EvalFinding`, `EvalResult`, and `EvalReport` dataclasses.
- Added `evaluate_case` and `evaluate_cases` runners for deterministic offline validation.

Completed Work
- Added backend-only `app.evals` package with `EvalCase`, `EvalFinding`, `EvalResult`, and `EvalReport` dataclasses.
- Added `evaluate_case` and `evaluate_cases` runners for deterministic offline validation.
- Added analysis eval rules for future source inclusion, prompted future sources, cited future sources, unknown evidence source IDs, excluded evidence source citations, prompt source grounding, `needs_evidence` consistency, and included/excluded count consistency.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase031_eval_harness.py -q` failed on missing `app.evals`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase031_eval_harness.py -q` passed with 6 tests.

Next Steps
- The harness is not wired into CI or a CLI command yet; it is currently exercised through pytest.
- Prompt-injection pattern checks, source-quality scoring, and secret redaction are intentionally left for later phases.

## phase_032 - Source Safety Eval Rules

Phase Goal
- Extended `app.evals.rules` with deterministic source-safety checks that run inside `evaluate_case`.
- Added prompt-injection detection for source text that attempts to override prior instructions, expose system prompt content, or force recommendations regardless of evidence.

Completed Work
- Extended `app.evals.rules` with deterministic source-safety checks that run inside `evaluate_case`.
- Added prompt-injection detection for source text that attempts to override prior instructions, expose system prompt content, or force recommendations regardless of evidence.
- Added schema-spoofing detection for source text that tries to dictate JSON or response-schema output.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase032_source_safety_evals.py -q` failed with 4 expected missing source-safety rule IDs.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase032_source_safety_evals.py -q` passed with 6 tests.

Next Steps
- Pattern-based safety checks are intentionally conservative and may need tuning as real source corpora grow.
- Source-quality scoring and secret redaction remain separate follow-up phases.

## phase_033 - Source Quality And Evidence Weighting Evals

Phase Goal
- Added eval-only `app.evals.source_quality` with `SourceQuality`, `classify_source_quality`, and `evidence_quality_weight`.
- Classified reliability from trusted metadata only: official filing/regulatory source types and known official source names, news adapter/source types, social/forum source types, or unknown.

Completed Work
- Added eval-only `app.evals.source_quality` with `SourceQuality`, `classify_source_quality`, and `evidence_quality_weight`.
- Classified reliability from trusted metadata only: official filing/regulatory source types and known official source names, news adapter/source types, social/forum source types, or unknown.
- Classified freshness from `published_at` relative to `as_of_at`; future-dated sources get zero quality.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase033_source_quality_evals.py -q` failed on missing `classify_source_quality`.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase033_source_quality_evals.py -q` passed with 5 tests.

Next Steps
- Reliability classes are intentionally coarse; real publisher reputation should be a later explicit model, not inferred from body text.
- Source-quality scores are not yet exposed to the UI or used by production scoring.

## phase_034 - Prompt Grounding Contract Integration

Phase Goal
- Tightened `build_live_analysis_messages` with an explicit `allowed_source_document_ids` contract.
- `create_live_analysis` now passes only currently included/prompt-eligible source IDs into that allowed list.

Completed Work
- Tightened `build_live_analysis_messages` with an explicit `allowed_source_document_ids` contract.
- `create_live_analysis` now passes only currently included/prompt-eligible source IDs into that allowed list.
- The live prompt now states that every evidence item and key claim must cite exactly one allowed source ID.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase034_prompt_grounding_contract.py -q` failed because the prompt lacked explicit allowed source IDs and grounding contract text.
- GREEN: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase034_prompt_grounding_contract.py -q` passed with 4 tests.

Next Steps
- Summary-level key-claim citation is still enforced by prompt contract, while machine validation remains evidence-item source ID validation.
- Later structured-output schema work could add claim-level citation fields if the UI needs per-claim audit display.

## phase_035 - User-Selected LLM API Key Policy

Phase Goal
- Removed LLM credential fallback from `OPENAI_API_KEY`, `OpenAI_API_Key`, and `CEREBRAS_API_KEY`; `get_llm_credential_secret` now returns a credential only from encrypted local state.
- Preserved user-selectable providers in the credential API: `openai`, `anthropic`, `cerebras`, and `custom`.

Completed Work
- Removed LLM credential fallback from `OPENAI_API_KEY`, `OpenAI_API_Key`, and `CEREBRAS_API_KEY`; `get_llm_credential_secret` now returns a credential only from encrypted local state.
- Preserved user-selectable providers in the credential API: `openai`, `anthropic`, `cerebras`, and `custom`.
- Defaulted the Settings model credential form and setup CLI prompts to Cerebras/`llama3.1-8b`, while keeping OpenAI, Anthropic, Cerebras, and custom options selectable.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase035_provider_selection_cerebras_first.py::test_environment_keys_are_ignored_when_no_user_key_is_saved -q` failed because environment LLM keys still produced a credential.
- RED: `cd src/frontend && npm test -- ChatShell.test.tsx` failed because setup-needed chat messages did not receive the red API-key class.

Next Steps
- Anthropic remains storable but live calls still return unsupported-provider until a native adapter is added.
- Gemini is not yet in the credential provider union; adding it should be a dedicated provider-adapter phase.

## phase_036 - Minimal Quote Card In Chat

Phase Goal
- Updated `MarketChart` so the reusable chart card visibly includes stock name, symbol, formatted price, percentage change, exchange, and as-of timestamp.
- Reused that card in both the latest chat assistant response and the analysis panel snapshot.

Completed Work
- Updated `MarketChart` so the reusable chart card visibly includes stock name, symbol, formatted price, percentage change, exchange, and as-of timestamp.
- Reused that card in both the latest chat assistant response and the analysis panel snapshot.
- Removed the analysis panel's separate quote grid to avoid rendering two competing market snapshot summaries.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `cd src/frontend && npm test -- ChatShell.test.tsx` failed because the compact chart did not visibly render the stock name.
- GREEN: `cd src/frontend && npm test -- ChatShell.test.tsx AnalysisPanel.test.tsx` passed with 8 tests.

Next Steps
- The saved Cerebras credential currently does not produce a successful live response; provider-side access, key validity, or model permission should be checked before treating Cerebras as operational.
- The quote card intentionally omits Google Finance-style stats until the market-data schema is expanded.

## phase_037 - Cerebras Provider Header Compatibility

Phase Goal
- Compared `cerebras-test/index.js`, which succeeds through the official `@cerebras/cerebras_cloud_sdk`, with Stuck_LLM's direct `urllib` OpenAI-compatible provider path.
- Confirmed the saved Stuck_LLM Cerebras key and `cerebras-test/.env` key have the same mask, so the failure was not caused by a stale saved credential.

Completed Work
- Compared `cerebras-test/index.js`, which succeeds through the official `@cerebras/cerebras_cloud_sdk`, with Stuck_LLM's direct `urllib` OpenAI-compatible provider path.
- Confirmed the saved Stuck_LLM Cerebras key and `cerebras-test/.env` key have the same mask, so the failure was not caused by a stale saved credential.
- Confirmed direct Python requests with the default `urllib` User-Agent received Cerebras HTTP 403 with provider body `error code: 1010`.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase024_cerebras_provider.py::test_cerebras_provider_uses_openai_compatible_endpoint_and_schema_shape src/backend/tests/test_phase025_llm_connection_diagnostics.py::test_llm_connection_test_uses_saved_cerebras_key_without_exposing_raw_key -q` failed because provider headers lacked `Accept` and `User-Agent`.
- GREEN: same command passed with 2 tests.

Next Steps
- DeepTutor's broader provider-neutral env model, model catalog, streaming abstraction, and telemetry are intentionally not imported yet because they would change Stuck_LLM's credential policy and architecture.
- Later provider work can extract `_provider_headers` and endpoint helpers into a dedicated `features/llm` module if multiple provider families need richer routing.

## phase_038 - Persistent LLM Chat And Rich Ticker Snapshots

Phase Goal
- Added a generic chat-completion request path to the OpenAI-compatible provider so saved Cerebras or custom OpenAI-compatible credentials can answer normal conversation prompts.
- Kept generic chat separate from structured stock-analysis prompts and response parsing.

Completed Work
- Added a generic chat-completion request path to the OpenAI-compatible provider so saved Cerebras or custom OpenAI-compatible credentials can answer normal conversation prompts.
- Kept generic chat separate from structured stock-analysis prompts and response parsing.
- Added prompt construction for generic chat that includes recent same-conversation user and assistant messages for follow-up context.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `PYTHONPATH=src/backend python3 -m pytest src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py -q` failed because generic chat returned `needs_input` and ticker-only `AAPL` asked for a horizon.
- GREEN: same command passed with 2 tests and one local urllib3 LibreSSL warning.

Next Steps
- Live provider success still depends on the user's saved credential and provider account permissions; tests cover the repeated user path without exposing raw keys.
- Rich snapshot quality depends on the upstream SerpApi Google Finance payload shape, so later provider work may need fixture coverage for additional exchange-specific variants.

## phase_039 - ChatGPT-Style Conversation Workspace

Phase Goal
- Added frontend conversation summary loading through `GET /conversations` and selected conversation loading through `GET /conversations/{id}`.
- Reworked the app shell so the left rail lists previous conversations, supports a new-chat action, and loads saved conversation snapshots on selection.

Completed Work
- Added frontend conversation summary loading through `GET /conversations` and selected conversation loading through `GET /conversations/{id}`.
- Reworked the app shell so the left rail lists previous conversations, supports a new-chat action, and loads saved conversation snapshots on selection.
- Made `ChatShell` controlled by the active conversation snapshot while preserving a local fallback for isolated component use.

Changed Files
- See the original detailed log for the file list.

Important Notes
- RED: `cd src/frontend && npm test -- ChatShell.test.tsx App.test.tsx api.test.ts` failed on missing conversation API mapping, missing previous-chat rail behavior, and missing message-level snapshot rendering.
- GREEN: same command passed with 23 tests.

Next Steps
- The workspace now supports saved conversation selection and preserved message content, but it still uses request/response updates rather than streaming or live push.
- Conversation persistence remains backed by the current local state store rather than authenticated multi-user storage.

## phase_040 - Agent Workflow Provider Validation Policy

Phase Goal
- Added root-agent guidance that agents should proactively patch `docs/agent-workflows` in the same phase when the workflow docs no longer drive the requested behavior.
- Updated orchestration guidance so LLM provider/API-key tasks must validate the real `/conversations` path, not only settings diagnostics or provider connection tests.

Completed Work
- Added root-agent guidance that agents should proactively patch `docs/agent-workflows` in the same phase when the workflow docs no longer drive the requested behavior.
- Updated orchestration guidance so LLM provider/API-key tasks must validate the real `/conversations` path, not only settings diagnostics or provider connection tests.
- Required provider acceptance criteria to split simple chat, follow-up chat, stock-analysis requests, and market snapshot requests.

Changed Files
- See the original detailed log for the file list.

Important Notes
- `npx @google/design.md lint DESIGN.md` passed with 0 errors and 0 warnings.
- `git diff --check` passed.

Next Steps
- The workflow docs now require richer provider validation, but future phases still need to choose the smallest relevant test subset for each provider change so validation remains fast.
