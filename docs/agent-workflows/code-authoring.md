# Code Authoring Workflow

## Scope

Use this workflow for all application code and phase-level documentation changes.

## Expected Stack

- Backend: Python, likely FastAPI.
- Frontend: TypeScript, React, and Vite.
- Database: PostgreSQL first; keep service-shaped schema boundaries.
- Charts: browser-rendered charts for PnL and analysis evidence views.

## Authoring Rules

- Start each implementation with a `phase_00x` entry in the compact task summary for the active 10-phase bucket.
- Keep detailed task and implementation logs at `docs/task/task.md` and `docs/implement/implement.md`; open them only when the compact summaries are insufficient.
- Update the matching range README title index when adding a new summary file.
- Back up every modified non-backup file under `backups/<phase_id>/`.
- Do not back up files already under `backups/`.
- Write new Markdown content in English only.
- Read `docs/product/README.md` and `docs/product/llm-agent-spec.md` before changing user-facing LLM agent behavior, evidence rules, response shape, provider behavior, cache semantics, runtime flow, or workspace UI rules.
- Ask the user before updating `docs/product/` when a new feature or behavior change affects those product specs, unless the current request already includes the documentation update.
- Place backend code under `src/backend`.
- Place frontend code under `src/frontend`.
- Keep feature slices atomic:
  - Backend: `src/backend/app/features/<feature>/`.
  - Frontend: `src/frontend/src/features/<feature>/`.
- Every feature or behavior change must include unit tests in the same phase.
- Conversation, market-data, news, and prediction changes must include matrix-style
  unit tests across representative symbols, intents, and Korean/English routing
  where behavior depends on text classification.
- Do not add cross-feature helpers until at least two feature slices need the same behavior.
- Shared code must live in an explicit `shared/` folder and must have its own tests.
- Keep historical evidence analysis separate from future PnL/backtest data.
- Enforce `analysis_requests.as_of_at` before LLM prompts or scoring.
- Cache and processing records must be keyed by `symbol`, `intent` or provider
  operation, `as_of_at` where relevant, provider/model, and prompt/cache version.
- Prefer adapters for external sources instead of embedding source-specific logic in analysis code.
- Keep provider logic behind explicit OpenAI, Anthropic, and Gemini interfaces.

## Backend Slice Shape

- `router.py`: HTTP routes for one feature.
- `schemas.py`: request and response models for one feature.
- `service.py`: business logic when needed.
- `tests/test_<feature>.py`: behavior tests that fail before production code is added.
- Unit tests are mandatory for every backend route, service, source adapter, scoring rule, and data transformation.

## Frontend Slice Shape

- Components live in `src/frontend/src/features/<feature>/`.
- Shared layout belongs in `src/frontend/src/App.tsx` or a future `src/frontend/src/shared/`.
- Keep API client code separate from presentation once backend integration starts.
- Unit tests are mandatory for every feature component, interaction, view-state helper, and data-mapping function.
- Prefer colocated tests such as `src/frontend/src/features/chat/ChatShell.test.tsx`.

## Source Adapter Rules

- Store raw source metadata, URL, `published_at`, and `fetched_at`.
- Mark excluded sources instead of deleting them.
- Do not treat missing source data as neutral evidence.
- Report failed sources in user-facing analysis results.
- For market snapshots, model chart bars, key stats, and news explicitly when the provider returns them.
- Do not use LLM credential storage for search/news/market-data keys.
- Provider-response caches may store normalized payloads and provider status, but
  must never store API keys, decrypted credentials, hidden system prompts, or
  user secrets.

## Stock Universe Rules

- S&P 500 company metadata must resolve through a single market-data universe boundary.
- News requests may use metadata-only S&P 500 records when live quote data is
  unavailable, but chart and prediction paths still require real or fixture market data.
- Query-template changes for US stocks must include Apple, Google/Alphabet,
  Nvidia, Tesla, and representative sector tests such as financials, energy,
  health care, consumer, and retail.

## LLM Rules

- Follow `docs/product/llm-agent-spec.md` as the product contract for user-facing LLM behavior.
- LLM prompts must receive only eligible evidence for the selected `as_of_at`.
- Responses must include buy, hold, sell probabilities plus confidence.
- Evidence summaries must link back to stored source documents.
- Model/provider selection belongs in settings and per-message metadata.
- Generic chat, follow-up chat, and stock-analysis prompts are separate behaviors with separate tests.
- A saved LLM API key is not complete until `/conversations` can use it for repeated user-visible replies.
- Prediction artifacts may be reused only when evidence hash, prompt version,
  provider, model, horizon, and `as_of_at` match. Prompt/model version changes
  must force a cache miss.
