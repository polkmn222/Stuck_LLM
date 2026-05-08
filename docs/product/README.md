# Product Documentation

Purpose
- Define the user-facing behavior contract for the Stuck LLM product.
- Keep product behavior separate from agent workflow rules and phase logs.
- Route implementation agents to the right product spec before changing chat, analysis, evidence, or UI behavior.

Read First
- `llm-agent-spec.md`: conversational LLM agent behavior, stock-analysis runtime, evidence rules, response rules, UI expectations, and maintenance policy.
- `llm-runtime-execution.md`: execution order and data boundaries for news, prediction, charts, graph data, caches, and artifacts.

Retired Docs
- `llm-agent-phase-roadmap.md` is no longer used. Use compact phase summaries under `docs/plan`, `docs/task`, and `docs/implement` for phase history.

Maintenance
- Ask the user before changing these product specs when a new feature or behavior change affects documented agent behavior, UI rules, evidence rules, response shape, provider behavior, cache semantics, or runtime flow.
- Update the relevant product spec in the same phase when the user request already includes the documentation change.
- Keep product docs in English only.
