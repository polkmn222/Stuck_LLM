# Implementation Documentation Rules

Purpose
- Route agents to compact implementation summaries before they open the full implementation log.
- Preserve the original detailed log at `docs/implement/implement.md`.

Current Status
- Detailed source log: `docs/implement/implement.md`.
- Compact range folders: `implement_001_100/` and `implement_101_200/`.
- Latest compact range: `implement_101_200/implement_101_110.md`.

Required Reading Order
- Start with this file for documentation rules.
- Open the matching range README, such as `implement_101_200/README.md`.
- Open the matching 10-phase summary file.
- Open `implement.md` only when exact validation output, full implementation notes, or historical wording is required.

Core Rules
- Keep range folders in 100-phase buckets: `implement_001_100/`, `implement_101_200/`, `implement_201_300/`.
- Keep summary files in 10-phase buckets: `implement_101_110.md`, `implement_111_120.md`, and so on.
- The summary filename must use the full 10-phase range even when only part of the range exists.
- Add phase title indexes to each range README so agents can find the right summary quickly.
- Write new Markdown content in English only.
- Do not delete, move, or rewrite `implement.md`.
- Before changing any existing non-backup Markdown file, preserve it under `backups/<phase_id>/`.
- Do not back up files already under `backups/`.
