# Code Validation Workflow

## Current Repository

Application code lives under `src/backend` and `src/frontend`.

## Documentation Checks

```bash
rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs
wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md
```

## Future Backend Checks

Use these backend commands:

```bash
PYTHONPATH=src/backend python3 -m pytest src/backend/tests -q
PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests
PYTHONPATH=/tmp/stuck_llm_backend_dev python3 -m ruff check src/backend
PYTHONPATH=/tmp/stuck_llm_backend_dev:src/backend python3 -m mypy src/backend/app
```

Install backend validation tools into `/tmp/stuck_llm_backend_dev` when unavailable locally:

```bash
python3 -m pip install --target /tmp/stuck_llm_backend_dev ruff mypy
```

## Frontend Checks

Use these frontend commands:

```bash
cd src/frontend && npm install
cd src/frontend && npm test
cd src/frontend && npm run typecheck
cd src/frontend && npm run build
cd src/frontend && npm audit --audit-level=high
```

## Validation Rules

- Run validation after every code change.
- Unit tests are required for backend and frontend feature/behavior changes.
- Record validation commands and results in `docs/implement.md`.
- If a validation tool is not configured yet, state that clearly in the phase notes.
- Do not mark a phase complete when known validation failures remain.
