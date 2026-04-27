---
name: provider-credentials
description: Manage Stuck_LLM BYOK provider credentials, encrypted API-key storage, masking, setup flows, and future login-ready credential boundaries.
---

# Provider Credentials

Use this skill when adding or changing user-provided LLM/search provider credentials.

## Rules

- Treat API keys as secrets from input through storage, logs, tests, and responses.
- Never return raw keys from an API. Return `configured`, provider metadata, key source, and masked text only.
- Encrypt keys at rest with authenticated encryption; do not invent crypto primitives.
- Prefer `STUCK_LLM_CREDENTIAL_KEY`; allow generated local development keys only for non-hosted local mode.
- Keep credential records shaped for later `user_id` ownership even before login exists.
- Provider config should include provider/binding, model, optional base URL, and secret material.
- `custom` or OpenAI-compatible providers must require explicit base URL.

## Workflow

1. Define or update the credential API contract before implementation.
2. Add failing tests for raw-key non-exposure, encrypted state, provider validation, delete, and setup flows.
3. Implement backend service code behind `src/backend/app/features/credentials`.
4. Ensure CLI/web setup uses the same service contract.
5. Run backend tests, compileall, Ruff, MyPy, and secret-grep checks.

## Validation Focus

- Raw key absent from JSON state files and HTTP responses.
- Masking is stable and useful enough for users to identify a key.
- Local generated key files are outside git-tracked paths and permissioned narrowly where possible.
- Hosted mode must not silently use generated local credential keys.
