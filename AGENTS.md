# Agent Instructions

## Project Status
- Planning-stage repository for a conversational stock-analysis AI agent.
- See `docs/plan.md` for product scope, architecture, phases, and data model.
- See `docs/task.md` and `docs/implement.md` before changing implementation scope.

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
| Markdown size check | `wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md` |
| Harness quick validation | `./run-harness.sh --profile quick` |
| Backend test | `PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q` |
| Frontend unit test | `cd src/frontend && npm test` |
| Frontend typecheck | `cd src/frontend && npm run typecheck` |
| Frontend build | `cd src/frontend && npm run build` |
| Design system lint | `npx @google/design.md lint DESIGN.md` |

## Key Conventions
- Use phase IDs as `phase_001`, `phase_002`, and so on.
- Keep `docs/task.md` and `docs/implement.md` in reverse chronological order, newest phase first.
- Back up every non-backup file modified in a phase under `backups/<phase_id>/`.
- Keep analysis data and later PnL/backtest data separated.
- Do not mix post-`as_of_at` evidence into historical LLM analysis.
- Non-destructive installs, setup, and validation commands may run without extra user confirmation.
- If code or policy changes require docs updates, ask first unless the current user request already includes those doc updates.
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
