"""Reusable subprocess assertions for Ladon's installed console scripts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Sequence


PROCESS_TIMEOUT_SECONDS = 20
FORBIDDEN_CALLER_OPTIONS = (
    "--agent-only",
    "--llm",
    "--model-only",
    "--prompt-only",
)


def assert_analyzer_process_contract(
    command: Sequence[str],
    *,
    fixture_root: Path,
    fixture_target: str,
) -> None:
    """Assert stable help, streams, and 0/1/2/3 exits for installed Ladon."""

    assert_analyzer_help(command)
    assert_default_text(command, fixture_root, fixture_target)
    assert_json_stdout(command, fixture_root, fixture_target)
    assert_exit_classes(command, fixture_root, fixture_target)


def assert_analyzer_help(command: Sequence[str]) -> None:
    """Assert ordinary public help has no caller-specific options."""

    help_run = invoke(command, "--help")
    assert help_run.returncode == 0
    assert "usage:" in help_run.stdout
    assert all(option not in help_run.stdout for option in FORBIDDEN_CALLER_OPTIONS)
    assert "--skip-build" not in help_run.stdout
    runset_help = invoke(command, "runset", "--help")
    assert runset_help.returncode == 0
    assert "--manifest" in runset_help.stdout
    assert "--bundle-dir" in runset_help.stdout
    assert runset_help.stderr == ""
    assert all(
        option not in runset_help.stdout for option in FORBIDDEN_CALLER_OPTIONS
    )


def assert_default_text(
    command: Sequence[str],
    fixture_root: Path,
    fixture_target: str,
) -> None:
    """Assert default output is exactly one text representation."""

    text_run = analyze(command, fixture_root, fixture_target)
    assert text_run.returncode == 0
    assert text_run.stdout.startswith("Ladon ")
    assert text_run.stderr == ""


def assert_json_stdout(
    command: Sequence[str],
    fixture_root: Path,
    fixture_target: str,
) -> None:
    """Assert canonical JSON stdout contains no text or diagnostics."""

    json_run = analyze(
        command,
        fixture_root,
        fixture_target,
        "--format",
        "json",
        "--output",
        "-",
    )
    assert json_run.returncode == 0
    payload = json.loads(json_run.stdout)
    assert payload["metadata"]["report_version"] == "ladon-report-v3"
    assert payload["projection"]["name"] == "review"
    assert json_run.stderr == ""


def assert_exit_classes(
    command: Sequence[str],
    fixture_root: Path,
    fixture_target: str,
) -> None:
    """Assert invocation, operational, and policy failures are distinct."""

    invalid = invoke(command, "--format", "yaml")
    assert invalid.returncode == 2
    assert invalid.stdout == ""

    removed = invoke(command, "--skip-build")
    assert removed.returncode == 2
    assert "omit it" in removed.stderr

    missing = analyze(
        command,
        fixture_root / "missing",
        fixture_target,
    )
    assert missing.returncode == 1
    assert missing.stdout == ""
    assert "does not exist" in missing.stderr

    rejected = analyze(
        command,
        fixture_root,
        fixture_target,
        "--fail-on",
        "kind:architecture_policy.skipped_no_policy",
    )
    assert rejected.returncode == 3
    assert "failure policy matched" in rejected.stderr


def assert_bridge_process_contract(command: Sequence[str]) -> None:
    """Assert the supported auxiliary bridge's applicable process contract."""

    help_run = invoke(command, "--help")
    assert help_run.returncode == 0
    assert "usage:" in help_run.stdout
    assert help_run.stderr == ""

    invalid = invoke(command)
    assert invalid.returncode == 2
    assert invalid.stdout == ""


def analyze(
    command: Sequence[str],
    fixture_root: Path,
    fixture_target: str,
    *extra: str,
) -> subprocess.CompletedProcess[str]:
    """Invoke the analyzer on one portable Lean text fixture."""

    return invoke(
        command,
        "--repo-root",
        str(fixture_root),
        "--root",
        fixture_target,
        *extra,
    )


def invoke(
    command: Sequence[str],
    *args: str,
) -> subprocess.CompletedProcess[str]:
    """Run one installed console command with bounded captured streams."""

    return subprocess.run(
        [*command, *args],
        text=True,
        capture_output=True,
        check=False,
        timeout=PROCESS_TIMEOUT_SECONDS,
    )
