#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


SCHEMA_VERSION = "phase_041_harness_v1"
DEFAULT_OUTPUT_DIR = Path("artifacts/harness")
DEFAULT_TAIL_CHARS = 6000


@dataclass(frozen=True)
class HarnessCommand:
    command_id: str
    description: str
    argv: tuple[str, ...]
    cwd: str = "."
    env: tuple[tuple[str, str], ...] = ()
    allowed_exit_codes: tuple[int, ...] = (0,)


COMMANDS: dict[str, HarnessCommand] = {
    "git.diff_check": HarnessCommand(
        command_id="git.diff_check",
        description="Check changed files for whitespace errors.",
        argv=("git", "diff", "--check"),
    ),
    "docs.placeholders": HarnessCommand(
        command_id="docs.placeholders",
        description="Search docs and source for unresolved placeholders.",
        argv=(
            "rg",
            "-n",
            "TO[D]O|TB[D]|FIX[M]E",
            "AGENTS.md",
            "docs",
            "src/backend",
            "src/frontend/src",
        ),
        allowed_exit_codes=(0, 1),
    ),
    "docs.line_count": HarnessCommand(
        command_id="docs.line_count",
        description="Report current agent documentation line counts.",
        argv=("/bin/zsh", "-lc", "wc -l AGENTS.md docs/*.md docs/agent-workflows/*.md"),
    ),
    "docs.design_lint": HarnessCommand(
        command_id="docs.design_lint",
        description="Validate DESIGN.md with the project design linter.",
        argv=("npx", "@google/design.md", "lint", "DESIGN.md"),
    ),
    "backend.tests": HarnessCommand(
        command_id="backend.tests",
        description="Run all backend tests.",
        argv=("python3", "-m", "pytest", "src/backend/tests", "-q"),
        env=(("PYTHONPATH", "src/backend"),),
    ),
    "backend.compileall": HarnessCommand(
        command_id="backend.compileall",
        description="Compile backend app and tests.",
        argv=("python3", "-m", "compileall", "-q", "src/backend/app", "src/backend/tests"),
        env=(("PYTHONPYCACHEPREFIX", "/tmp/stuck_llm_pycache"),),
    ),
    "backend.ruff": HarnessCommand(
        command_id="backend.ruff",
        description="Run Ruff over backend code.",
        argv=("python3", "-m", "ruff", "check", "src/backend"),
        env=(("PYTHONPATH", "/tmp/stuck_llm_backend_dev"),),
    ),
    "backend.mypy": HarnessCommand(
        command_id="backend.mypy",
        description="Typecheck backend app code.",
        argv=("python3", "-m", "mypy", "src/backend/app"),
        env=(("PYTHONPATH", "/tmp/stuck_llm_backend_dev:src/backend"),),
    ),
    "frontend.tests": HarnessCommand(
        command_id="frontend.tests",
        description="Run frontend unit tests.",
        argv=("npm", "test"),
        cwd="src/frontend",
    ),
    "frontend.typecheck": HarnessCommand(
        command_id="frontend.typecheck",
        description="Typecheck frontend code.",
        argv=("npm", "run", "typecheck"),
        cwd="src/frontend",
    ),
    "frontend.build": HarnessCommand(
        command_id="frontend.build",
        description="Build frontend assets.",
        argv=("npm", "run", "build"),
        cwd="src/frontend",
    ),
    "provider.conversation": HarnessCommand(
        command_id="provider.conversation",
        description="Run provider and conversation regression tests.",
        argv=(
            "python3",
            "-m",
            "pytest",
            "src/backend/tests/test_phase038_persistent_chat_and_ticker_snapshots.py",
            "src/backend/tests/test_phase026_generative_chat_orchestration.py",
            "src/backend/tests/test_phase025_llm_connection_diagnostics.py",
            "src/backend/tests/test_phase024_cerebras_provider.py",
            "src/backend/tests/test_phase035_provider_selection_cerebras_first.py",
            "-q",
        ),
        env=(("PYTHONPATH", "src/backend"),),
    ),
}


PROFILES: dict[str, tuple[str, ...]] = {
    "backend": (
        "backend.tests",
        "backend.compileall",
        "backend.ruff",
        "backend.mypy",
    ),
    "docs": (
        "git.diff_check",
        "docs.placeholders",
        "docs.line_count",
        "docs.design_lint",
    ),
    "frontend": (
        "frontend.tests",
        "frontend.typecheck",
        "frontend.build",
    ),
    "full": (
        "git.diff_check",
        "docs.placeholders",
        "docs.line_count",
        "docs.design_lint",
        "backend.tests",
        "backend.compileall",
        "backend.ruff",
        "backend.mypy",
        "frontend.tests",
        "frontend.typecheck",
        "frontend.build",
    ),
    "provider": ("provider.conversation",),
    "quick": (
        "git.diff_check",
        "docs.placeholders",
        "backend.tests",
        "frontend.tests",
    ),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _tail(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def _command_env(command: HarnessCommand) -> dict[str, str]:
    env = os.environ.copy()
    for key, value in command.env:
        env[key] = value
    return env


def _relative_cwd(project_root: Path, cwd: str) -> Path:
    if cwd == ".":
        return project_root
    return project_root / cwd


def _command_report(
    command: HarnessCommand,
    *,
    status: str,
    duration_seconds: float,
    return_code: Optional[int] = None,
    stdout: str = "",
    stderr: str = "",
    tail_chars: int = DEFAULT_TAIL_CHARS,
) -> dict[str, object]:
    return {
        "id": command.command_id,
        "description": command.description,
        "command": list(command.argv),
        "cwd": command.cwd,
        "env": dict(command.env),
        "allowed_exit_codes": list(command.allowed_exit_codes),
        "status": status,
        "return_code": return_code,
        "duration_seconds": round(duration_seconds, 3),
        "stdout_tail": _tail(stdout, tail_chars),
        "stderr_tail": _tail(stderr, tail_chars),
    }


def _run_command(
    command: HarnessCommand,
    *,
    project_root: Path,
    tail_chars: int,
) -> dict[str, object]:
    started = time.monotonic()
    process = subprocess.run(
        list(command.argv),
        cwd=_relative_cwd(project_root, command.cwd),
        env=_command_env(command),
        text=True,
        capture_output=True,
        check=False,
    )
    duration = time.monotonic() - started
    status = "passed" if process.returncode in command.allowed_exit_codes else "failed"
    return _command_report(
        command,
        status=status,
        duration_seconds=duration,
        return_code=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
        tail_chars=tail_chars,
    )


def _markdown_report(report: dict[str, object]) -> str:
    lines = [
        f"# Harness Report - {report['profile']}",
        "",
        f"- Status: {report['status']}",
        f"- Dry run: {report['dry_run']}",
        f"- Started: {report['started_at']}",
        f"- Finished: {report['finished_at']}",
        f"- Duration seconds: {report['duration_seconds']}",
        "",
        "| Command | Status | Return Code | Duration |",
        "|---|---:|---:|---:|",
    ]
    for command in report["commands"]:  # type: ignore[index]
        lines.append(
            "| {id} | {status} | {return_code} | {duration_seconds} |".format(
                id=command["id"],
                status=command["status"],
                return_code="" if command["return_code"] is None else command["return_code"],
                duration_seconds=command["duration_seconds"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def _write_reports(report: dict[str, object], output_dir: Path, run_id: str) -> Path:
    report_dir = output_dir / run_id
    report_dir.mkdir(parents=True, exist_ok=True)
    report_json = report_dir / "report.json"
    report_markdown = report_dir / "report.md"
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_markdown.write_text(_markdown_report(report), encoding="utf-8")
    return report_dir


def _run_profile(
    profile: str,
    *,
    project_root: Path,
    dry_run: bool,
    keep_going: bool,
    tail_chars: int,
) -> dict[str, object]:
    started_at = _utc_now()
    started = time.monotonic()
    reports: list[dict[str, object]] = []

    for command_id in PROFILES[profile]:
        command = COMMANDS[command_id]
        if dry_run:
            reports.append(
                _command_report(
                    command,
                    status="skipped",
                    duration_seconds=0.0,
                    tail_chars=tail_chars,
                )
            )
            continue
        report = _run_command(command, project_root=project_root, tail_chars=tail_chars)
        reports.append(report)
        if report["status"] == "failed" and not keep_going:
            break

    if dry_run:
        status = "dry_run"
    elif any(report["status"] == "failed" for report in reports):
        status = "failed"
    else:
        status = "passed"

    finished_at = _utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "profile": profile,
        "status": status,
        "dry_run": dry_run,
        "project_root": str(project_root),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": round(time.monotonic() - started, 3),
        "commands": reports,
    }


def _default_run_id(profile: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{profile}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Stuck_LLM validation harness profiles.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="quick")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id")
    parser.add_argument("--tail-chars", type=int, default=DEFAULT_TAIL_CHARS)
    parser.add_argument("--list-profiles", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.list_profiles:
        for profile in sorted(PROFILES):
            print(profile)
        return 0

    project_root = Path(__file__).resolve().parents[2]
    run_id = args.run_id or _default_run_id(args.profile)
    report = _run_profile(
        args.profile,
        project_root=project_root,
        dry_run=args.dry_run,
        keep_going=args.keep_going,
        tail_chars=args.tail_chars,
    )
    report_dir = _write_reports(report, args.output_dir, run_id)
    print(f"Harness report: {report_dir / 'report.json'}")
    print(f"Harness markdown: {report_dir / 'report.md'}")
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
