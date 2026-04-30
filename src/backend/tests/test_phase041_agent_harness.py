from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HARNESS = ROOT / "scripts" / "harness" / "run_harness.py"


def test_harness_dry_run_writes_agent_readable_reports(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--profile",
            "docs",
            "--dry-run",
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "phase041-test",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Harness report:" in result.stdout

    report_dir = tmp_path / "phase041-test"
    report_json = report_dir / "report.json"
    report_markdown = report_dir / "report.md"
    assert report_json.exists()
    assert report_markdown.exists()

    report = json.loads(report_json.read_text())
    assert report["schema_version"] == "phase_041_harness_v1"
    assert report["profile"] == "docs"
    assert report["dry_run"] is True
    assert report["status"] == "dry_run"
    assert [command["id"] for command in report["commands"]] == [
        "git.diff_check",
        "docs.placeholders",
        "docs.line_count",
        "docs.design_lint",
    ]
    assert {command["status"] for command in report["commands"]} == {"skipped"}
    assert "docs.design_lint" in report_markdown.read_text()


def test_harness_lists_profiles_for_agent_selection() -> None:
    result = subprocess.run(
        [sys.executable, str(HARNESS), "--list-profiles"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "backend",
        "docs",
        "frontend",
        "full",
        "provider",
        "quick",
    ]
