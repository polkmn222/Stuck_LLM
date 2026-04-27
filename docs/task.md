# Task Log

Newest phases go first. Every implementation phase must use a `phase_00x` identifier and update this file before final handoff.

## phase_018 - Live LLM Provider Analysis Integration

Status: planned

Objective:

- Connect the encrypted local BYOK credential flow to a real live LLM analysis path.
- Add a narrow backend provider interface with OpenAI first and Anthropic/custom-compatible boundaries preserved.
- Let chat-ready analysis requests call the live provider when credentials exist, while keeping deterministic local providers for tests and fallback.
- Return source-grounded assistant answers in the user's language with auditable evidence, `as_of_at` cutoff safety, and explicit setup-needed responses when credentials are missing.
- Keep scoring and backtest data separated from LLM evidence analysis.

Required skills for next agent:

- `stock-analysis-llm` for source-grounded provider calls and strict evidence cutoff behavior.
- `llm-application-dev` for prompt shape, structured output parsing, and provider error handling.
- `provider-credentials` for decrypting BYOK credentials only at the live-call edge.
- `api-design-principles` and `backend-development` for route/service contracts.
- `security-auditor` for prompt injection, key handling, logs, and external-provider data exposure.
- `test-driven-development`, `systematic-debugging`, and `lint-and-validate` throughout.

Acceptance criteria:

- Backend defines a small `LlmAnalysisProvider`-style interface separate from deterministic analysis logic.
- OpenAI-compatible live provider support uses the stored credential provider/model/base URL/API key and never logs or returns raw keys.
- Missing local credentials produce a Korean or English setup-needed assistant message instead of a failed stack trace or deterministic fake live result.
- Provider timeouts, malformed structured output, rate limits, and authentication failures map to explicit statuses/errors that the chat UI can show.
- Analysis prompts include only eligible source documents with `published_at <= as_of_at`; equality remains included.
- Post-`as_of_at` evidence, PnL/backtest prices, and credential metadata are excluded from the prompt.
- Source document text is treated as untrusted evidence and cannot override system instructions.
- The live result produces a structured summary/evidence handoff that scoring can consume without changing the scoring model in this phase.
- Korean user messages receive Korean live/setup/error assistant text; English messages receive English text.
- Frontend chat displays missing-credential and provider-error messages cleanly without exposing internal details.
- Unit tests cover missing credentials, provider success with a mocked client, provider failure mapping, language behavior, and cutoff filtering.
- Any opt-in integration test is skipped by default unless explicit environment variables are present.
- `backups/phase_018/` records every non-backup file modified or created in the phase.

Suggested implementation order:

1. Add failing backend tests for missing credential, mocked provider success, malformed output, provider auth/rate-limit errors, and `as_of_at` cutoff equality.
2. Add the provider interface and OpenAI-compatible adapter behind `src/backend/app/features/analysis` or a clearly shared backend provider module.
3. Reuse the phase_016 credential service to decrypt keys only inside the live provider call path.
4. Add prompt/structured-output parsing with explicit schema validation and deterministic fallback kept out of the live path.
5. Wire chat-ready requests to live analysis only when credentials are configured.
6. Add/adjust frontend tests for setup-needed and provider-error chat rendering.
7. Run backend, frontend, type, build, audit, and smoke validation.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/analysis/**`
- `src/backend/app/features/conversations/**`
- `src/backend/app/features/credentials/**` only if an API/service boundary needs a small read helper
- `src/backend/app/shared/**`
- `src/backend/tests/test_phase018_live_llm_provider.py`
- `src/frontend/src/features/chat/**`
- `src/frontend/src/shared/**`

## phase_017 - Settings Modal And Workspace Navigation

Status: completed

Objective:

- Move language/theme/model credential setup into a ChatGPT-style settings modal.
- Keep analysis defaults, snapshot, and backtest as sidebar navigation views instead of sidebar cards.
- Wire the frontend to the phase_016 credential API with masked-key responses and raw-key save/delete only.
- Preserve the chat workspace as the default first screen.

Acceptance criteria:

- The left rail exposes Chat, Analysis, Snapshot, and Backtest navigation buttons.
- Chat view shows only the conversation workspace and composer.
- Analysis view shows analysis mode, default market, and default horizon preferences.
- Snapshot view shows the current market snapshot.
- Backtest view shows the PnL simulation panel.
- Settings opens as a modal/panel with left categories for General, Model, and Security.
- General settings include language and theme.
- Model settings include provider, model, base URL, API key entry, masked key status, save, and delete.
- Security settings show credential storage/key-source status without exposing raw API keys.
- Frontend API helpers support fetching, saving, and deleting LLM credentials.
- Frontend tests cover navigation split, modal settings, credential save/delete, and existing analysis/backtest flows.
- `backups/phase_017/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/frontend/src/App.tsx`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/styles.css`
- `src/frontend/src/shared/api.ts`
- `src/frontend/src/shared/types.ts`
- `src/frontend/src/shared/i18n.ts`
- `src/frontend/src/features/settings/**`
- `src/frontend/src/features/analysis/**`
- `src/frontend/src/features/backtest/**`

## phase_016 - Local BYOK Credential Backend And CLI Setup

Status: completed

Objective:

- Add project-local skills for provider credentials and stock-analysis LLM workflows.
- Update orchestration skill routing for BYOK credentials, live LLM providers, and frontend settings work.
- Add encrypted local storage for user-provided LLM API keys without login.
- Support OpenAI, Anthropic, and OpenAI-compatible custom provider configuration.
- Add a developer CLI setup command for entering provider/model/base URL/API key.
- Keep raw API keys out of API responses and local state files.
- Fix hosted API-key guard behavior for empty configured keys.

Acceptance criteria:

- `.codex/skills/provider-credentials/SKILL.md` and `.codex/skills/stock-analysis-llm/SKILL.md` exist with concise project-specific workflows.
- `docs/agent-workflows/orchestration.md` routes BYOK credential, setup, and live LLM work to the right skills.
- `PUT /credentials/llm` saves provider, model, base URL, and encrypted API key.
- `GET /credentials/llm` returns only provider metadata, configured state, key source, and masked key text.
- `DELETE /credentials/llm` removes the stored credential.
- The raw API key is not present in API responses or the JSON state file.
- `STUCK_LLM_CREDENTIAL_KEY` is used when present; otherwise a local development credential key is generated under `.local`.
- `custom` provider credentials require an explicit base URL.
- `scripts/setup_credentials.py` can save credentials non-interactively for developer setup.
- Empty hosted API keys do not authenticate protected requests.
- Backend unit tests cover encrypted storage, masking, provider validation, CLI setup, and API-key guard behavior.
- `backups/phase_016/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/orchestration.md`
- `.env.example`
- `.codex/skills/provider-credentials/SKILL.md`
- `.codex/skills/stock-analysis-llm/SKILL.md`
- `scripts/setup_credentials.py`
- `src/backend/pyproject.toml`
- `src/backend/app/main.py`
- `src/backend/app/shared/runtime_config.py`
- `src/backend/app/shared/dependencies.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/app/features/credentials/**`
- `src/backend/tests/test_phase011_hosted_readiness.py`
- `src/backend/tests/test_phase016_credentials.py`

## phase_015 - Typo Confirmation Rule And Runner Auto-Open

Status: completed

Objective:

- Review Claude's feedback and address the user-facing issues in this slice.
- Replace hardcoded typo stock aliases with a reusable fuzzy stock-confirmation rule.
- Ask the user to confirm likely stock typos instead of silently accepting them.
- Let affirmative follow-ups reuse the confirmed candidate stock.
- Open the frontend automatically when `./run-all.sh` starts the local app.

Acceptance criteria:

- `삼성전가` and `삼성전사` no longer resolve as exact aliases.
- A likely stock typo produces a Korean or English confirmation question such as "삼성전자 말씀이신가요?"
- Confirming the candidate with `네` or `yes` continues the flow with that stock.
- The fuzzy confirmation logic is generic over known seeded aliases and is not implemented by listing typo strings.
- Exact known stock names still behave normally.
- `run-all.sh` opens the frontend URL by default after startup and supports `AUTO_OPEN_BROWSER=0` to disable it.
- Backend tests and script validation cover the new behavior.
- `backups/phase_015/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `run-all.sh`
- `src/backend/app/features/conversations/schemas.py`
- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase014_conversation_language.py`
- `src/backend/tests/test_phase015_runner_and_typo_confirmation.py`

## phase_014 - Conversation Language And Follow-Up Context

Status: completed

Objective:

- Make backend-generated conversation replies follow the user's message language for Korean and English prompts.
- Preserve a previously resolved stock when a user answers a follow-up question in the same conversation.
- Handle common Korean Samsung Electronics typo inputs in the seeded market-data MVP; this was later superseded by the phase_015 confirmation rule.
- Keep the current deterministic MVP transparent when hosted LLM analysis is not connected.

Acceptance criteria:

- Korean user messages receive Korean missing-input and ready-state assistant text.
- English user messages continue to receive English assistant text.
- After a stock is resolved and the assistant asks for horizon, a non-horizon follow-up keeps asking for horizon instead of losing the stock.
- A valid horizon follow-up records the prior stock as ready for analysis.
- Common Korean Samsung Electronics typo inputs are covered by the later phase_015 confirmation flow.
- Backend unit tests cover the new conversation and alias behavior.
- `backups/phase_014/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/features/conversations/service.py`
- `src/backend/app/features/market_data/service.py`
- `src/backend/tests/test_phase014_conversation_language.py`

## phase_012 - Bilingual Theme UI Refresh

Status: completed

Objective:

- Add an explicit Korean/English UI language switch for fixed frontend copy.
- Add light and dark theme switching with persistent local preference.
- Refresh the app layout toward a ChatGPT-like left-sidebar plus main conversation workspace.
- Keep the stock-analysis workflow operational while improving visual consistency.

Acceptance criteria:

- Users can switch visible static UI copy between English and Korean.
- Users can switch between dark and light themes.
- The selected language and theme persist in local browser storage.
- The main layout uses a left control rail, central conversation area, and bottom composer.
- Existing chat, settings, analysis snapshot, and backtest tests continue to pass.
- Frontend typecheck and build pass.
- `backups/phase_012/` records every non-backup file modified or created in this phase.

Files expected to change:

- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/frontend/src/App.tsx`
- `src/frontend/src/App.test.tsx`
- `src/frontend/src/styles.css`
- `src/frontend/src/shared/**`
- `src/frontend/src/features/chat/**`
- `src/frontend/src/features/settings/**`
- `src/frontend/src/features/analysis/**`
- `src/frontend/src/features/backtest/**`

## phase_011 - Hosted Readiness And Security Hardening

Status: completed

Objective:

- Add a minimal hosted-mode guard without changing the local-first default.
- Configure explicit CORS origins for the frontend development hosts.
- Move internal LLM prompt material out of public analysis API responses.
- Validate timestamp formats and large text payloads at the request boundary.
- Improve frontend handling for saved settings and default-market initialization.
- Reduce project-local skill description size so Codex no longer exceeds the skills context budget.

Acceptance criteria:

- CORS preflight succeeds for the local frontend origin.
- `STUCK_LLM_REQUIRE_API_KEY=true` requires a matching API key on non-health requests.
- Bad or timezone-less timestamps are rejected with validation errors rather than 500s.
- Oversized conversation and source-document payloads are rejected.
- Analysis responses omit internal `system_instructions` and `prompt_context` fields.
- Frontend initial market snapshot follows the persisted default market.
- Settings save failures render a visible inline error.
- Backend and frontend unit tests cover the new behavior.
- `backups/phase_011/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `.codex/skills/**`
- `.agents/skills/**`
- `src/backend/app/main.py`
- `src/backend/app/shared/**`
- `src/backend/app/features/analysis/**`
- `src/backend/app/features/backtest/**`
- `src/backend/app/features/conversations/**`
- `src/backend/app/features/ingestion/**`
- `src/backend/tests/**`
- `src/frontend/src/App.tsx`
- `src/frontend/src/features/settings/**`
- `src/frontend/src/shared/**`
- `src/frontend/vite.config.ts`

## phase_010 - Global Source Adapter MVP

Status: completed

Objective:

- Add backend ingestion adapters for Reddit, US news, polling/sentiment, and global macro sources.
- Keep adapters seed-backed and offline for the MVP, with a registry that can be replaced by live providers later.
- Return source documents that are compatible with the analysis pipeline.
- Preserve source metadata, timestamps, URLs, adapter names, relevance scores, and safety flags.
- Avoid server-side arbitrary URL fetching or live crawler execution in this phase.

Acceptance criteria:

- `POST /ingestion/collect` accepts stock metadata, `as_of_at`, analysis mode, and requested source adapters.
- The response includes documents from Reddit, US news, polling/sentiment, and global macro adapters.
- Quick mode returns a compact set; deep mode can return more documents from the same adapters.
- Collected documents can be submitted to `POST /analysis/requests`, where post-`as_of_at` documents are excluded by the analysis layer.
- Unsupported adapter names are rejected by request validation.
- Backend unit tests cover adapter collection, quick/deep behavior, analysis cutoff integration, and validation.
- `backups/phase_010/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/app/features/ingestion/**`
- `src/backend/tests/**`

## phase_009 - Backtest And PnL Graph Service

Status: completed

Objective:

- Add a backend backtest feature slice for seeded PnL simulations.
- Keep PnL/backtest price data separate from historical evidence analysis.
- Calculate entry price, exit price, gross return, gross PnL, max drawdown, and equity curve.
- Add a frontend PnL panel with a compact graph for local seeded simulations.

Acceptance criteria:

- `POST /backtests/simulations` accepts market, symbol, entry/exit timestamps, and quantity.
- Backtest responses include price-derived PnL metrics and an equity curve.
- Backtest errors clearly report missing seeded price data or invalid date ranges.
- Frontend exposes a local PnL simulation panel and renders the returned curve.
- Backend and frontend unit tests cover the service and graph flow.
- `backups/phase_009/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/app/features/backtest/**`
- `src/backend/tests/**`
- `src/frontend/src/App.tsx`
- `src/frontend/src/features/backtest/**`
- `src/frontend/src/shared/**`
- `src/frontend/src/styles.css`

## phase_008 - Scoring Probabilities And Confidence

Status: completed

Objective:

- Add a backend scoring feature slice for buy, hold, and sell probabilities.
- Convert analysis evidence stance and weights into auditable probability output.
- Report a confidence score that reflects eligible evidence strength and excluded-source penalty.
- Avoid producing scored probabilities when no eligible evidence is available.

Acceptance criteria:

- `POST /scoring/evaluate` accepts evidence items and excluded-source count.
- Scored responses include buy, hold, and sell probabilities summing to 100.
- Confidence decreases when evidence is weak or sources are excluded.
- Empty evidence returns `needs_evidence` and zero probabilities.
- Backend unit tests cover bullish/neutral/bearish weighting and empty-evidence behavior.
- `backups/phase_008/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/shared/state_store.py`
- `src/backend/app/features/scoring/**`
- `src/backend/tests/**`

## phase_007 - Historical Analysis Pipeline

Status: completed

Objective:

- Add a backend analysis feature slice for source-grounded local analysis requests.
- Enforce `as_of_at` filtering before any prompt context or analysis summary is built.
- Store included and excluded source-document decisions in the response.
- Treat source text as untrusted evidence and keep prompt-injection instructions out of analysis instructions.
- Return stance evidence for later scoring without producing buy/hold/sell probabilities yet.

Acceptance criteria:

- `POST /analysis/requests` accepts stock, horizon, `as_of_at`, analysis mode, and source documents.
- Source documents published after `as_of_at` are excluded and do not appear in prompt context or summary.
- Included source documents produce linked evidence items with stance, weight, summary, and quote excerpt.
- Empty eligible evidence returns a `needs_evidence` status instead of fabricating analysis.
- Backend unit tests cover strict cutoff filtering, prompt-boundary safety, and empty-evidence behavior.
- `backups/phase_007/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/features/analysis/**`
- `src/backend/tests/**`

## phase_006 - Chat Settings And Market Data MVP

Status: completed

Objective:

- Add local file-backed persistence for development settings and conversations.
- Add backend settings, conversation, and seeded market-data endpoints.
- Connect the frontend shell to the backend through the existing `/api/*` proxy.
- Keep market-data snapshots separate from LLM analysis and probability scoring.
- Preserve the missing-horizon follow-up behavior before analysis requests are accepted.

Acceptance criteria:

- Settings can be read, updated, and persisted across app instances.
- A chat message creates or updates a persisted conversation.
- If a message lacks a stock or investment horizon, the assistant asks one focused follow-up.
- If required inputs are present, the assistant records a request and returns a seeded market-data snapshot without claiming LLM analysis is complete.
- Frontend chat, settings, and analysis panels render backend-backed state and include unit tests.
- Backend tests, frontend unit tests, typecheck, and build pass.
- `backups/phase_006/` records every non-backup file modified or created in this phase.

Files expected to change:

- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `src/backend/app/main.py`
- `src/backend/app/shared/**`
- `src/backend/app/features/conversations/**`
- `src/backend/app/features/settings/**`
- `src/backend/app/features/market_data/**`
- `src/backend/tests/**`
- `src/frontend/src/**`

## phase_005 - Unified Runner And Atomic Test Policy

Status: completed

Objective:

- Add a root-level unified runner for backend and frontend development servers.
- Make backend and frontend feature-folder organization explicit in docs and `AGENTS.md`.
- Make unit tests mandatory for every backend/frontend feature slice.
- Add frontend unit test infrastructure for the existing chat feature.
- Submit implemented code for `review-claude` after local validation.

Acceptance criteria:

- `./run-all.sh` starts backend and frontend together from the project root.
- Frontend dev server proxies `/api/*` requests to the backend.
- `src/README.md` explains backend/frontend feature folder conventions.
- `AGENTS.md` and workflow docs state that unit tests are mandatory.
- Backend tests and frontend unit tests pass.
- `backups/phase_005/` records every non-backup file modified or created in this phase.

Files expected to change:

- `AGENTS.md`
- `README.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/code-authoring.md`
- `docs/agent-workflows/code-validation.md`
- `run-all.sh`
- `src/README.md`
- `src/frontend/**`

## phase_004 - Source Scaffold And Foundation Slice

Status: completed

Objective:

- Create the initial application scaffold under `src/backend` and `src/frontend`.
- Keep backend and frontend separated while preserving feature-level atomicity.
- Add the first backend health feature with a test-first workflow.
- Add a functional frontend shell for chat, settings, and analysis panels.
- Update validation and planning docs to reflect the `src/` layout.

Acceptance criteria:

- Backend code lives under `src/backend`.
- Frontend code lives under `src/frontend`.
- Backend has a passing health endpoint test.
- Frontend has an installable/buildable Vite React TypeScript scaffold.
- Feature code is grouped by atomic feature folders.
- `docs/plan.md`, `docs/agent-workflows/code-authoring.md`, and `docs/agent-workflows/code-validation.md` reflect the `src/` layout.
- `backups/phase_004/` records every non-backup file modified or created in this phase.

Files expected to change:

- `AGENTS.md`
- `.gitignore`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/code-authoring.md`
- `docs/agent-workflows/code-validation.md`
- `src/backend/**`
- `src/frontend/**`

## phase_003 - Skill Installation And Routing Policy

Status: completed

Objective:

- Install project-relevant skills from the `stock-analysis-agent` index.
- Synchronize externally installed skills into `.codex/skills/` for project-local availability.
- Document situation-based skill routing in orchestration docs.
- Record install/run permission and docs-change policies in `AGENTS.md`.

Acceptance criteria:

- Selected local, global-source, and external skills have `.codex/skills/<skill-name>/SKILL.md`.
- `docs/agent-workflows/orchestration.md` explains which skills to reference by situation.
- `AGENTS.md` remains lightweight and points to orchestration for detailed routing.
- `docs/task.md`, `docs/implement.md`, and `.find-skills/stock-analysis-agent/index.md` reflect the installation.
- `backups/phase_003/` records every non-backup file modified or created in this phase.

Files expected to change:

- `AGENTS.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/orchestration.md`
- `.find-skills/stock-analysis-agent/index.md`
- `.codex/skills/**`
- `.agents/skills/**`

## phase_002 - Skill Discovery Checklist And Index

Status: completed

Objective:

- Use the project-local `find-skills` workflow to discover skills for the stock-analysis AI agent.
- Broaden the checklist so candidates cover implementation, frontend, backend, ingestion, LLM, finance, security, testing, and deployment phases.
- Generate a project-local skill index only after checklist confirmation.

Acceptance criteria:

- `docs/checklist-001.md` records broad search vocabulary and candidate categories.
- Search was run after the user requested index generation.
- `.find-skills/stock-analysis-agent/index.md` records ranked candidates and install status.
- `backups/phase_002/` records every non-backup file modified in this phase.
- The eventual index is written to `.find-skills/stock-analysis-agent/index.md`.

Files expected to change:

- `docs/checklist-001.md`
- `docs/task.md`
- `docs/implement.md`
- `.find-skills/stock-analysis-agent/index.md`

## phase_001 - Planning And Workflow Documentation

Status: completed

Objective:

- Preserve the agreed product direction for a conversational stock-analysis AI agent.
- Define the initial architecture, service boundaries, database draft, and phase plan.
- Add lightweight agent instructions and workflow docs.
- Establish a backup convention for every modified non-backup file.

Acceptance criteria:

- `docs/plan.md` is written in English.
- `docs/task.md` and `docs/implement.md` use reverse chronological phase entries.
- `AGENTS.md` stays lightweight and points to durable docs.
- `docs/agent-workflows/code-authoring.md` exists.
- `docs/agent-workflows/code-validation.md` exists.
- `docs/agent-workflows/orchestration.md` exists.
- `backups/phase_001/` records every non-backup file modified in this phase.

Files expected to change:

- `AGENTS.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/implement.md`
- `docs/agent-workflows/code-authoring.md`
- `docs/agent-workflows/code-validation.md`
- `docs/agent-workflows/orchestration.md`

## Future Phase Template

```text
## phase_00x - Title

Status: pending | in_progress | completed

Objective:
- ...

Acceptance criteria:
- ...

Files expected to change:
- ...
```
