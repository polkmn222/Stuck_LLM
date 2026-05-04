# Implement Phase 111-120 Summary

This file is a compact implementation index for agents. Keep the original detailed log as the source of truth.

## phase_111 - Evidence Normalization Boundary

Completed Work
- Added `src/backend/app/features/analysis/evidence_normalization.py`.
- Analysis service now uses the boundary for source decisions, source audit, prompt context, prompt budget, and fallback evidence items.

Validation
- Covered by `test_phase110_118_llm_agent_contract.py`.

## phase_112 - Prediction Orchestration Routing Guard

Completed Work
- Fixed exact-ticker news requests so news/PnL requests cannot be intercepted by the market snapshot early return.

Validation
- RED: phase 118 E2E initially failed because `AAPL latest news` returned `market_snapshot`.
- GREEN: phase 118 E2E passed after routing guard update.

## phase_113 - Confidence Factor Scoring Metadata

Completed Work
- Added `confidence_factors` to score responses.
- Scoring now reports eligible evidence, thin evidence, stance diversity, and excluded-source penalty factors.

Validation
- Contract tests assert probability normalization and confidence penalty factors.

## phase_114 - Analysis UI Operational State

Completed Work
- Frontend analysis panel renders provider/model state and confidence factors.
- API mapper preserves score confidence factors.

Validation
- `AnalysisPanel.test.tsx` and `api.test.ts` cover the new fields.

## phase_115 - News Digest Transparency UX

Completed Work
- News digest article cards render publication dates.
- Provider run chips render provider status and result count.

Validation
- `NewsDigestView.test.tsx` and `ChatShell.test.tsx` cover article dates and provider run status.

## phase_116 - Prediction Cache Schema Boundary

Completed Work
- Added `PREDICTION_RESPONSE_SCHEMA_VERSION`.
- Prediction artifact keys and stored artifacts include response schema version.

Validation
- Contract tests assert stored artifact schema version and horizon cache misses.

## phase_117 - PnL Evaluation Artifact Separation

Completed Work
- Backtest responses include `evaluation_kind: pnl_simulation`.
- Frontend API mapper preserves `evaluationKind`.

Validation
- Contract tests assert PnL records do not rewrite analysis requests or prediction artifacts.

## phase_118 - Conversation E2E Validation Matrix

Completed Work
- Added deterministic backend E2E matrix covering simple chat, news digest, prediction, repeated prediction cache reuse, and PnL simulation.

Validation
- `PYTHONPATH=src/backend:src/backend/tests python3 -m pytest src/backend/tests/test_phase110_118_llm_agent_contract.py src/backend/tests/e2e/test_phase118_validation_matrix.py src/backend/tests/test_phase064_069_news_digest.py src/backend/tests/test_phase077_prediction_probabilities.py src/backend/tests/test_phase095_prediction_artifact_store.py src/backend/tests/test_phase009_backtest.py src/backend/tests/test_phase104_news_digest_formatting.py src/backend/tests/e2e/test_chat_to_analysis.py -q`: passed with 27 tests and one existing urllib3 LibreSSL warning.
- `cd src/frontend && npm test -- AnalysisPanel.test.tsx NewsDigestView.test.tsx api.test.ts ChatShell.test.tsx`: passed with 28 tests.
- `PYTHONPYCACHEPREFIX=/tmp/stuck_llm_pycache python3 -m compileall -q src/backend/app src/backend/tests`: passed.
- `cd src/frontend && npm run typecheck`: passed.
- `cd src/frontend && npm run build`: passed.
- `rg -n "TO[D]O|TB[D]|FIX[M]E" AGENTS.md docs`: passed with no matches.
- `wc -l AGENTS.md README.md docs/product/README.md docs/product/llm-agent-spec.md docs/product/llm-agent-phase-roadmap.md docs/plan/README.md docs/task/README.md docs/implement/README.md docs/plan/plan_101_200/README.md docs/task/task_101_200/README.md docs/implement/implement_101_200/README.md docs/plan/plan_101_200/plan_111_120.md docs/task/task_101_200/task_111_120.md docs/implement/implement_101_200/implement_111_120.md`: completed; `AGENTS.md` remains 60 lines.
- `git diff --check`: passed.

Important Notes
- Modified non-backup files were preserved under `backups/phase_111/`.
- The urllib3 LibreSSL warning is pre-existing environment noise and not caused by this phase.

Next Steps
- Use `phase_119` for the next implementation slice.
