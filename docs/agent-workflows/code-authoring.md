# Code Authoring Workflow

## Scope

Use this workflow for all application code in future phases. The repository is currently in planning stage.

## Expected Stack

- Backend: Python, likely FastAPI.
- Frontend: TypeScript, React, and Vite.
- Database: PostgreSQL first; keep service-shaped schema boundaries.
- Charts: browser-rendered charts for PnL and analysis evidence views.

## Authoring Rules

- Start each implementation with a `phase_00x` entry in `docs/task.md`.
- Update `docs/implement.md` with concrete notes and validation results.
- Back up every modified non-backup file under `backups/<phase_id>/`.
- Place backend code under `src/backend`.
- Place frontend code under `src/frontend`.
- Keep feature slices atomic:
  - Backend: `src/backend/app/features/<feature>/`.
  - Frontend: `src/frontend/src/features/<feature>/`.
- Every feature or behavior change must include unit tests in the same phase.
- Do not add cross-feature helpers until at least two feature slices need the same behavior.
- Shared code must live in an explicit `shared/` folder and must have its own tests.
- Keep historical evidence analysis separate from future PnL/backtest data.
- Enforce `analysis_requests.as_of_at` before LLM prompts or scoring.
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

## LLM Rules

- LLM prompts must receive only eligible evidence for the selected `as_of_at`.
- Responses must include buy, hold, sell probabilities plus confidence.
- Evidence summaries must link back to stored source documents.
- Model/provider selection belongs in settings and per-message metadata.
- Generic chat, follow-up chat, and stock-analysis prompts are separate behaviors with separate tests.
- A saved LLM API key is not complete until `/conversations` can use it for repeated user-visible replies.
