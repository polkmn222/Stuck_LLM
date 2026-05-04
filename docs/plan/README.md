# Planning Documentation Rules

Purpose
- Route agents to compact planning summaries before they open the full planning log.
- Preserve the original detailed plan at `docs/plan/plan.md`.

Current Status
- Detailed source plan: `docs/plan/plan.md`.
- Compact range folders: `plan_001_100/` and `plan_101_200/`.
- Latest compact range: `plan_101_200/plan_111_120.md`.

Required Reading Order
- Start with this file for documentation rules.
- Open the matching range README, such as `plan_101_200/README.md`.
- Open the matching 10-phase summary file.
- Open `plan.md` only when architecture details, data model notes, or decision-log wording is required.

Core Rules
- Keep range folders in 100-phase buckets: `plan_001_100/`, `plan_101_200/`, `plan_201_300/`.
- Keep summary files in 10-phase buckets: `plan_101_110.md`, `plan_111_120.md`, and so on.
- The summary filename must use the full 10-phase range even when only part of the range exists.
- Add phase title indexes to each range README so agents can find the right summary quickly.
- Write new Markdown content in English only.
- Do not delete, move, or rewrite `plan.md`.
- Before changing any existing non-backup Markdown file, preserve it under `backups/<phase_id>/`.
- Do not back up files already under `backups/`.
