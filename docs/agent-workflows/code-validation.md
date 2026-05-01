# Code Validation Workflow

## Current Repository

Application code lives under `src/backend` and `src/frontend`.

## Documentation Checks

```bash
rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs
wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md
```

## Harness Checks

Use the project harness when an agent needs one command with an agent-readable report:

```bash
./run-harness.sh --profile quick
./run-harness.sh --profile full --keep-going
./run-harness.sh --profile docs --dry-run
```

Harness reports are written under `artifacts/harness/` and ignored by git. Use `--dry-run` to inspect selected commands before running expensive profiles.

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
- Backend conversation changes must include matrix tests for representative
  `symbol x intent x language` combinations when routing or market resolution changes.
- News/query-template changes must test provider fakes, cache hit/miss behavior,
  source transparency, and representative S&P 500 sectors without live network calls.
- Prediction/cache changes must test `as_of_at` cutoffs, evidence-hash reuse,
  prompt/model version cache misses, and absence of raw credentials or system
  prompt text in stored artifacts.
- Record validation commands and results in `docs/implement.md`.
- If a validation tool is not configured yet, state that clearly in the phase notes.
- Do not mark a phase complete when known validation failures remain.
- Provider/API-key phases must include a `/conversations` test that proves user-visible use of the saved key.
- Conversation phases must test repeated follow-up messages and reloading saved conversations by ID.
- Conversation/provider integration phases should add or update the backend E2E slice under `src/backend/tests/e2e` when the request/analysis/scoring/persistence path changes.
- Rich market-data phases must test schema mapping and UI rendering for chart, key stats, and news when available.
- AI capability or prompt-registry phases must expose provider support and prompt
  versions without returning API keys, decrypted credentials, or hidden prompt text.
