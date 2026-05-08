# Agent Instructions

## Project Status
- Planning-stage repository for a conversational stock-analysis AI agent.
- Read compact docs first: `docs/plan/README.md`, `docs/task/README.md`, and `docs/implement/README.md`; open full logs only when compact summaries are insufficient.
- Product behavior specs live in `docs/product/README.md`; read them before changing LLM agent, evidence, response, UI, provider, or cache behavior.
- Current docs use 100-phase folders with 10-phase summary files, for example `docs/implement/implement_101_200/implement_101_110.md`.

## Package Manager
- Backend: Python/FastAPI under `src/backend`.
- Frontend: npm/Vite/React under `src/frontend`.
- Install frontend deps with `cd src/frontend && npm install`.
- Run both dev servers with `./run-all.sh` from the repository root.
- Only run `./run-all.sh` when the user explicitly runs it or when an agent needs it for validation/testing; stop test servers after validation unless the user asks to keep them running.

## File-Scoped Commands
| Task | Command |
|------|---------|
| Find placeholders | `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs` |
| Markdown size check | `wc -l AGENTS.md docs/**/*.md` |
| Harness quick validation | `./run-harness.sh --profile quick` |
| Backend test | `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` |
| Frontend unit test | `cd src/frontend && npm test` |
| Frontend typecheck | `cd src/frontend && npm run typecheck` |
| Frontend build | `cd src/frontend && npm run build` |
| Design system lint | `npx @google/design.md lint DESIGN.md` |

## Key Conventions
- Use phase IDs as `phase_001`, `phase_002`, and so on.
- Keep detailed logs at `docs/plan/plan.md`, `docs/task/task.md`, and `docs/implement/implement.md`.
- Keep compact summaries in 100-phase folders and 10-phase files such as `task_101_110.md`.
- Same-phase requirement: a new summary file is incomplete until the matching range README phase-title index is updated.
- Back up every non-backup file modified in a phase under `backups/<phase_id>/`.
- Do not back up files already under `backups/`.
- Write new Markdown content in English only.
- Keep analysis data and later PnL/backtest data separated.
- Do not mix post-`as_of_at` evidence into historical LLM analysis.
- Non-destructive installs, setup, and validation commands may run without extra user confirmation.
- If code or policy changes require docs updates, ask first unless the current user request already includes those doc updates.
- If new features or behavior changes affect `docs/product/`, ask the user before updating those specs unless the current request already includes the update.
- If `docs/agent-workflows` no longer drives the requested behavior, proactively patch those workflow docs in the same phase.
- Keep new implementation slices atomic under `src/backend/app/features/<feature>` and `src/frontend/src/features/<feature>`.
- Every backend or frontend feature/behavior change must include unit tests in the same phase.
- New feature folders must be obvious to humans and agents; avoid cross-feature files unless the code is genuinely shared.
- For frontend or UI work, read `DESIGN.md` first and keep visual changes aligned with its tokens and rationale.

## Skill Routing
- See `docs/agent-workflows/orchestration.md` for which skills to use by situation.
- Use `.codex/skills/<skill-name>/SKILL.md` as the project-local install source of truth.

## Workflow Docs
- Code authoring: `docs/agent-workflows/code-authoring.md`
- Validation: `docs/agent-workflows/code-validation.md`
- Orchestration: `docs/agent-workflows/orchestration.md`

## Commit Attribution
AI commits MUST include:
```
Co-Authored-By: (the agent model's name and attribution byline)
```
