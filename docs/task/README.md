# Task Documentation Rules

Purpose
- Route agents to compact task summaries before they open the full task log.
- Preserve the original detailed log at `docs/task/task.md`.

Current Status
- Detailed source log: `docs/task/task.md`.
- Compact range folders: `task_001_100/` and `task_101_200/`.
- Latest compact range: `task_101_200/task_111_120.md`.

Required Reading Order
- Start with this file for documentation rules.
- Open the matching range README, such as `task_101_200/README.md`.
- Open the matching 10-phase summary file.
- Open `task.md` only when exact acceptance criteria or historical scope wording is required.

Core Rules
- Keep range folders in 100-phase buckets: `task_001_100/`, `task_101_200/`, `task_201_300/`.
- Keep summary files in 10-phase buckets: `task_101_110.md`, `task_111_120.md`, and so on.
- The summary filename must use the full 10-phase range even when only part of the range exists.
- Add phase title indexes to each range README so agents can find the right summary quickly.
- Write new Markdown content in English only.
- Do not delete, move, or rewrite `task.md`.
- Before changing any existing non-backup Markdown file, preserve it under `backups/<phase_id>/`.
- Do not back up files already under `backups/`.
