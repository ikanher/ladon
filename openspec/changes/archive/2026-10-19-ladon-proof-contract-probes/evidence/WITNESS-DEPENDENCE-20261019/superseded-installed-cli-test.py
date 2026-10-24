from __future__ import annotations

import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest
from installed_query_contract import (
    assert_installed_exhaustive_query_contract,
    assert_installed_query_help_contract,
)
from installed_signal_contract import (
    assert_installed_lean_signal_contract,
    assert_installed_text_signal_contract,
    fake_batch_lake_script,
)
from jsonschema import Draft202012Validator

from ladon.installed_contract import (
    assert_analyzer_process_contract,
    invoke,
)
from ladon.report_v2 import load_report_schema
from ladon.report_v3 import load_report_v3_schema

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"
RUNSET_MANIFEST = (
    Path(__file__).parent
    / "fixtures"
    / "runsets"
    / "manifest-v1.json"
)


# Installed entry points and compatibility projections.
# These subprocess assertions intentionally use the wheel-selected consoles.
# Local imports only validate the schema or reusable contract assertions.
def test_installed_analyzer_process_contract() -> None:
    assert_analyzer_process_contract(
        analyzer_command(),
        fixture_root=FIXTURE_ROOT,
        fixture_target="Tiny.lean",
    )


def test_installed_legacy_dual_files_and_conflict(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    text_path = tmp_path / "report.txt"

    dual = run_analyzer(
        "--json",
        str(json_path),
        "--text",
        str(text_path),
    )

    assert dual.returncode == 0
    assert dual.stdout == ""
    assert "deprecated" in dual.stderr
    assert json.loads(json_path.read_text(encoding="utf-8"))
    assert text_path.read_text(encoding="utf-8").startswith("Ladon ")

    conflict = run_analyzer(
        "--json",
        str(json_path),
        "--format",
        "json",
    )
    assert conflict.returncode == 2
    assert conflict.stdout == ""


def test_installed_v1_json_adapter_warns_about_information_loss() -> None:
    v1 = run_analyzer(
        "--format",
        "json",
        "--output",
        "-",
        "--report-version",
        "v1",
    )
    assert v1.returncode == 0
    assert json.loads(v1.stdout)["metadata"]["report_version"] == "clean-core-1"
    assert "information" in v1.stderr or "loses" in v1.stderr


def test_installed_v2_adapter_preserves_compatibility_wire_shape() -> None:
    v2 = run_analyzer(
        "--format",
        "json",
        "--output",
        "-",
        "--report-version",
        "v2",
    )

    assert v2.returncode == 0
    payload = json.loads(v2.stdout)
    Draft202012Validator(load_report_schema()).validate(payload)
    assert all(
        "disposition" not in phase
        for phase in payload["phases"].values()
    )
    assert "phase dispositions" in v2.stderr
    assert "duplicates large phase payloads" in v2.stderr


def test_installed_v1_rejects_text_and_legacy_dual_output(tmp_path: Path) -> None:
    text = run_analyzer("--report-version", "v1")
    dual = run_analyzer(
        "--json",
        str(tmp_path / "report.json"),
        "--text",
        str(tmp_path / "report.txt"),
        "--report-version",
        "v1",
    )

    assert text.returncode == 2
    assert text.stdout == ""
    assert "sole JSON" in text.stderr
    assert dual.returncode == 2
    assert dual.stdout == ""
    assert "sole JSON" in dual.stderr


def test_installed_output_write_failure_is_operational(tmp_path: Path) -> None:
    destination = tmp_path / "directory"
    destination.mkdir()

    result = run_analyzer("--format", "json", "--output", str(destination))

    assert result.returncode == 1
    assert result.stdout == ""
    assert "not a regular file" in result.stderr


def test_installed_invalid_policy_is_invocation_error(tmp_path: Path) -> None:
    policy = tmp_path / "invalid-policy.json"
    policy.write_text('{"groups": [], "rules": []}', encoding="utf-8")

    result = run_analyzer("--architecture-policy", str(policy))

    assert result.returncode == 2
    assert result.stdout == ""
    assert "invalid invocation" in result.stderr


# Build ordering, helper behavior, and descendant cleanup.
# The PATH-local Lake programs expose operational behavior without a toolchain.
# Real Lean execution remains owned by the separate pinned integration gate.
def test_installed_build_failure_emits_partial_report(tmp_path: Path) -> None:
    repo_root, fake_bin = build_fixture(tmp_path, "printf 'broken\\n' >&2; exit 7")
    output = tmp_path / "partial.json"

    result = subprocess.run(
        [
            *analyzer_command(),
            "--repo-root",
            str(repo_root),
            "--root",
            "Tiny.lean",
            "--build",
            "--format",
            "json",
            "--output",
            str(output),
            "--fail-on",
            "phase:proof_xray:skipped",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=environment_with_fake_bin(fake_bin),
    )

    assert result.returncode == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["phases"]["discover"]["status"] == "complete"
    assert payload["phases"]["build"]["status"] == "failed"
    assert payload["phases"]["build"]["required"] is True
    assert payload["metadata"]["failure_policy"]["matches"]
    assert payload["sections"]["build"]["command"][0] == str(
        fake_bin / "lake"
    )


def test_installed_text_backend_build_check_can_complete(tmp_path: Path) -> None:
    repo_root, fake_bin = build_fixture(tmp_path, "printf 'built\\n'")

    result = run_build(
        repo_root,
        fake_bin,
        "--format",
        "json",
        "--output",
        "-",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["metadata"]["extraction_backend"] == "text"
    assert payload["phases"]["build"]["status"] == "complete"
    assert payload["phases"]["build"]["required"] is True


def test_installed_lean_backend_builds_then_uses_fake_helper(
    tmp_path: Path,
) -> None:
    payload = {
        "version": "fixture-v2",
        "header": {"imports": []},
        "commands": [],
    }
    repo_root, fake_bin = build_fixture(tmp_path, "exit 0")
    install_fake_lean_helper(
        repo_root,
        fake_bin,
        fake_batch_lake_script(payload),
    )

    result = run_build(
        repo_root,
        fake_bin,
        "--extraction-backend",
        "lean",
        "--format",
        "json",
        "--output",
        "-",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["phases"]["build"]["status"] == "complete"
    assert payload["phases"]["lean_extraction"]["status"] == "complete"
    assert payload["phases"]["lean_extraction"]["required"] is True


def test_installed_no_build_lean_names_missing_compiled_state(
    tmp_path: Path,
) -> None:
    repo_root, fake_bin = build_fixture(tmp_path, "exit 0")

    result = subprocess.run(
        [
            *analyzer_command(),
            "--repo-root",
            str(repo_root),
            "--root",
            "Tiny.lean",
            "--extraction-backend",
            "lean",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=environment_with_fake_bin(fake_bin),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "compiled project state" in result.stderr
    assert "--build" in result.stderr


def test_installed_build_termination_cleans_descendant(tmp_path: Path) -> None:
    child_pid_path = tmp_path / "child.pid"
    body = (
        f"{sys.executable} -c \"import pathlib, subprocess, sys, time; "
        "child = subprocess.Popen([sys.executable, '-c', "
        "'import time; time.sleep(60)']); "
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
        "time.sleep(60)\""
    )
    repo_root, fake_bin = build_fixture(tmp_path, body)
    process = subprocess.Popen(
        [
            *analyzer_command(),
            "--repo-root",
            str(repo_root),
            "--root",
            "Tiny.lean",
            "--build",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment_with_fake_bin(fake_bin),
    )
    wait_for_path(child_pid_path)

    process.send_signal(signal.SIGTERM)

    stdout, _stderr = process.communicate(timeout=4)
    assert process.returncode == 128 + signal.SIGTERM
    assert stdout == ""
    assert process_is_live(int(child_pid_path.read_text(encoding="utf-8"))) is False


def publish_installed_runset(tmp_path: Path) -> tuple[Path, dict]:
    """Publish the portable fixture through the selected console."""

    bundle_dir = tmp_path / "bundle"
    published = invoke(
        analyzer_command(),
        "runset",
        "--manifest",
        str(RUNSET_MANIFEST),
        "--bundle-dir",
        str(bundle_dir),
        "--cache-dir",
        str(tmp_path / "cache"),
        "--no-resume",
        "--progress",
        "off",
    )
    assert published.returncode == 0
    bundle_path = bundle_dir / "bundle.json"
    return bundle_path, json.loads(bundle_path.read_text(encoding="utf-8"))


# Runset publication, resume, and cancellation.
# Every path uses ordinary installed commands and caller-owned temporary state.
# Matrix-Factorization and other maintainer repositories are never fixtures.
def replace_first_report_with_state(
    bundle_path: Path,
    bundle: dict,
    *,
    state: str,
    reason: str,
) -> dict:
    """Turn one complete entry into a valid reportless terminal row."""

    terminal = bundle["entries"][0]
    report = terminal["report"]
    (bundle_path.parent / report["path"]).unlink()
    terminal["diagnostics"] = [
        {
            "id": f"runset.{state}",
            "message": reason,
            "severity": "error",
        }
    ]
    terminal["phaseSummary"] = {}
    terminal["report"] = None
    terminal["resourceCounters"] = {}
    terminal["status"] = state
    bundle["completeness"] = "partial"
    bundle_path.write_text(
        json.dumps(bundle, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return terminal


def assert_installed_failure_diagnostic(
    atlas: dict,
    terminal: dict,
    reason: str,
) -> dict:
    """Check installed atlas output quotes state and its support boundary."""

    diagnostic = atlas["workflowDiagnostics"][0]
    assert diagnostic["entryId"] == terminal["id"]
    assert diagnostic["state"] == terminal["status"]
    assert diagnostic["reason"] == reason
    assert "no canonical analysis report" in diagnostic["nonclaim"]
    assert atlas["summary"]["reports"] == 2
    return diagnostic


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        ("failed", "runner failed before report publication"),
        ("interrupted", "caller interrupted entry before report publication"),
    ],
)
def test_installed_bundle_atlas_preserves_unreported_failure_state(
    tmp_path: Path,
    state: str,
    reason: str,
) -> None:
    bundle_path, bundle = publish_installed_runset(tmp_path)
    terminal = replace_first_report_with_state(
        bundle_path,
        bundle,
        state=state,
        reason=reason,
    )

    atlas_run = invoke(
        analyzer_command(),
        "atlas",
        "--bundle",
        str(bundle_path),
    )

    assert atlas_run.returncode == 0
    assert atlas_run.stderr == ""
    atlas = json.loads(atlas_run.stdout)
    diagnostic = assert_installed_failure_diagnostic(
        atlas,
        terminal,
        reason,
    )

    atlas_path = tmp_path / "atlas.json"
    atlas_path.write_text(atlas_run.stdout, encoding="utf-8")
    workflow_run = invoke(
        analyzer_command(),
        "workflow",
        "--atlas",
        str(atlas_path),
    )

    assert workflow_run.returncode == 0
    assert workflow_run.stderr == ""
    workflow = json.loads(workflow_run.stdout)
    assert workflow["sections"]["workflowDiagnostics"] == [diagnostic]


def test_installed_runset_resume_and_selective_source_invalidation(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(RUNSET_MANIFEST.parent, workspace)
    manifest = workspace / RUNSET_MANIFEST.name
    bundle_dir = tmp_path / "bundle"
    cache_dir = tmp_path / "cache"

    initial = invoke(
        analyzer_command(),
        "runset",
        "--manifest",
        str(manifest),
        "--bundle-dir",
        str(bundle_dir),
        "--cache-dir",
        str(cache_dir),
        "--no-resume",
        "--progress",
        "off",
    )
    resumed = invoke(
        analyzer_command(),
        "runset",
        "--manifest",
        str(manifest),
        "--bundle-dir",
        str(bundle_dir),
        "--cache-dir",
        str(cache_dir),
        "--progress",
        "off",
    )

    assert initial.returncode == resumed.returncode == 0
    assert initial.stderr == resumed.stderr == ""
    assert {
        entry["status"] for entry in json.loads(resumed.stdout)["entries"]
    } == {"resume-hit"}

    core = workspace / "repository" / "Fixture" / "Core.lean"
    core.write_text(
        core.read_text(encoding="utf-8")
        + "\ntheorem changed : True := by trivial\n",
        encoding="utf-8",
    )
    invalidated = invoke(
        analyzer_command(),
        "runset",
        "--manifest",
        str(manifest),
        "--bundle-dir",
        str(bundle_dir),
        "--cache-dir",
        str(cache_dir),
        "--progress",
        "off",
    )

    assert invalidated.returncode == 0
    assert invalidated.stderr == ""
    assert {
        entry["id"]: entry["status"]
        for entry in json.loads(invalidated.stdout)["entries"]
    } == {
        "core": "complete",
        "helper": "resume-hit",
        "facade": "complete",
    }


def test_installed_runset_cancellation_reaps_active_descendant(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(RUNSET_MANIFEST.parent, workspace)
    manifest = workspace / RUNSET_MANIFEST.name
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["entries"] = [payload["entries"][0]]
    payload["entries"][0]["options"] = {"build": True}
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    repository = workspace / "repository"
    (repository / "lakefile.lean").write_text(
        "package Fixture\n",
        encoding="utf-8",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    child_pid_path = tmp_path / "runset-child.pid"
    lake = fake_bin / "lake"
    lake.write_text(
        "#!/bin/sh\n"
        f"sleep 60 & echo $! > {child_pid_path}\n"
        "wait\n",
        encoding="utf-8",
    )
    lake.chmod(lake.stat().st_mode | stat.S_IXUSR)
    bundle_dir = tmp_path / "bundle"

    process = subprocess.Popen(
        [
            *analyzer_command(),
            "runset",
            "--manifest",
            str(manifest),
            "--bundle-dir",
            str(bundle_dir),
            "--no-resume",
            "--progress",
            "off",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment_with_fake_bin(fake_bin),
    )
    wait_for_path(child_pid_path)
    process.send_signal(signal.SIGTERM)
    stdout, stderr = process.communicate(timeout=6)

    assert process.returncode == 1
    assert json.loads(stdout)["entries"][0]["status"] == "interrupted"
    assert "runset interrupted" in stderr
    assert process_is_live(
        int(child_pid_path.read_text(encoding="utf-8"))
    ) is False


def run_installed_reportset(*arguments: str) -> None:
    """Require one installed report-set operation to use clean channels."""

    result = invoke(analyzer_command(), *arguments)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


# Report-set operations form one installed end-to-end review loop.
# File outputs keep stdout and stderr empty so automation can compose commands.
# Library-specific semantic assertions remain in their owning unit suites.
def test_installed_runset_to_complete_reportset_workflow(
    tmp_path: Path,
) -> None:
    bundle_path, _bundle = publish_installed_runset(tmp_path)
    atlas_path = tmp_path / "atlas.json"
    sqlite_path = tmp_path / "atlas.sqlite"
    generated_cards = tmp_path / "generated-cards.md"
    query_path = tmp_path / "query.json"
    diff_path = tmp_path / "diff.json"
    cards_path = tmp_path / "cards.json"
    workflow_path = tmp_path / "workflow.json"

    run_installed_reportset(
        "atlas",
        "--bundle",
        str(bundle_path),
        "--output-sqlite",
        str(sqlite_path),
        "--output-cards",
        str(generated_cards),
        "--output",
        str(atlas_path),
    )
    run_installed_reportset(
        "query",
        "--db",
        str(sqlite_path),
        "--query",
        "hotspots",
        "--output",
        str(query_path),
    )
    run_installed_reportset(
        "diff",
        "--before",
        str(atlas_path),
        "--after",
        str(atlas_path),
        "--output",
        str(diff_path),
    )
    run_installed_reportset(
        "cards",
        "--atlas",
        str(atlas_path),
        "--output",
        str(cards_path),
    )
    run_installed_reportset(
        "workflow",
        "--atlas",
        str(atlas_path),
        "--before",
        str(atlas_path),
        "--output",
        str(workflow_path),
    )

    assert json.loads(atlas_path.read_text(encoding="utf-8"))["schema"] == (
        "ladon-report-atlas-v1"
    )
    query = json.loads(query_path.read_text(encoding="utf-8"))
    assert query["schema"] == "ladon-atlas-query-result-v1"
    assert query["status"] in {"complete", "non_exhaustive"}
    assert isinstance(query["rows"], list)
    assert json.loads(diff_path.read_text(encoding="utf-8"))["schema"] == (
        "ladon-atlas-diff-v1"
    )
    assert isinstance(json.loads(cards_path.read_text(encoding="utf-8")), list)
    assert json.loads(workflow_path.read_text(encoding="utf-8"))["schema"] == (
        "ladon-atlas-workflow-v1"
    )
    assert generated_cards.read_text(encoding="utf-8").startswith(
        "# Ladon Atlas Reviewer Cards"
    )


def test_installed_query_exhaustive_accepts_exact_complete_coverage(
    tmp_path: Path,
) -> None:
    assert_installed_exhaustive_query_contract(
        analyzer_command(),
        tmp_path,
    )


def test_installed_query_help_documents_exhaustive_authority() -> None:
    assert_installed_query_help_contract(analyzer_command())


# Preview and findings exercise the ordinary inspection surface.
# Repeated invocations check stable machine output while text stays human-facing.
# Evidence assertions stop at Ladon's routing authority and do not claim truth.
def test_installed_preview_text_and_json_are_semantically_aligned() -> None:
    base = (
        "preview",
        "--repo-root",
        str(FIXTURE_ROOT),
        "--root",
        "Tiny",
        "--scope",
        "owner",
        "--no-cache",
    )
    machine = invoke(analyzer_command(), *base, "--format", "json")
    human = invoke(analyzer_command(), *base, "--format", "text")

    assert machine.returncode == human.returncode == 0
    assert machine.stderr == human.stderr == ""
    payload = json.loads(machine.stdout)
    assert payload["scope"]["resolvedRoots"] == ["Tiny"]
    assert payload["execution"] == {
        "cacheDirectory": None,
        "extractionBackend": "text",
        "leanCompiledStateExpectation": "not_required",
        "willRunLake": False,
        "willRunLean": False,
        "willRunVersionControl": False,
    }
    assert "Resolved roots: Tiny" in human.stdout
    assert (
        f"Primary modules: "
        f"{payload['scope']['primaryPopulation']['selectedCount']} selected"
    ) in human.stdout
    assert f"Scope fingerprint: {payload['scope']['fingerprint']}" in human.stdout


def test_installed_findings_repeat_lookup_filter_and_text_parity(
    tmp_path: Path,
) -> None:
    report = tmp_path / "report.json"
    analyzed = run_analyzer(
        "--format",
        "json",
        "--output",
        str(report),
        "--progress",
        "off",
    )
    assert analyzed.returncode == 0
    assert analyzed.stdout == analyzed.stderr == ""

    arguments = (
        "findings",
        "--report",
        str(report),
        "--format",
        "json",
    )
    first = invoke(analyzer_command(), *arguments)
    repeated = invoke(analyzer_command(), *arguments)
    text = invoke(
        analyzer_command(),
        "findings",
        "--report",
        str(report),
        "--format",
        "text",
    )

    assert first.returncode == repeated.returncode == text.returncode == 0
    assert first.stderr == repeated.stderr == text.stderr == ""
    assert first.stdout == repeated.stdout
    payload = json.loads(first.stdout)
    assert_installed_finding_projection(payload, text.stdout)

    selected = payload["findings"][0]
    lookup = installed_finding_selection(
        report,
        "--id",
        selected["id"],
    )
    filtered = installed_finding_selection(
        report,
        "--filter",
        f"kind={selected['kind']}",
    )
    assert lookup["findings"] == [selected]
    assert all(
        row["kind"] == selected["kind"]
        for row in filtered["findings"]
    )


# Resource ceilings and retained partial evidence.
# Each failure must preserve clean channels, a stable reason, and atomic output.
# Platform-specific RSS enforcement is asserted only on its supported host.
@pytest.mark.parametrize(
    ("option", "value", "diagnostic"),
    [
        ("--overall-timeout", "0.000001", "overall_wall_time limit exceeded"),
        ("--max-rss-mib", "1", "process_tree_rss limit exceeded"),
        ("--max-report-bytes", "1", "report_bytes limit exceeded"),
    ],
)
def test_installed_resource_limits_fail_without_partial_publication(
    tmp_path: Path,
    option: str,
    value: str,
    diagnostic: str,
) -> None:
    if option == "--max-rss-mib" and sys.platform != "linux":
        pytest.skip("process-tree RSS enforcement is Linux-specific")
    output = tmp_path / f"{option.removeprefix('--')}.json"

    result = run_analyzer(
        "--format",
        "json",
        "--output",
        str(output),
        option,
        value,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert diagnostic in result.stderr
    assert not output.exists()


def test_installed_partial_discovery_retains_schema_valid_report(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "partial-source"
    package = repo_root / "Pkg"
    package.mkdir(parents=True)
    (repo_root / "Pkg.lean").write_text(
        "import Pkg.Good\nimport Pkg.Broken\n",
        encoding="utf-8",
    )
    (package / "Good.lean").write_text(
        "theorem good : True := by trivial\n",
        encoding="utf-8",
    )
    (package / "Broken.lean").write_bytes(b"\xffinvalid")
    output = tmp_path / "partial.json"

    result = invoke(
        analyzer_command(),
        "--repo-root",
        str(repo_root),
        "--root",
        "Pkg",
        "--scope",
        "inventory",
        "--format",
        "json",
        "--output",
        str(output),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "source_index.source_failed" in result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    Draft202012Validator(load_report_v3_schema()).validate(payload)
    phase = payload["phases"]["discover"]
    assert phase["status"] == "partial"
    assert phase["disposition"] == "required-rejection"
    assert phase["counters"]["indexed_modules"] == 2
    assert phase["counters"]["source_cache_failed"] == 1


@pytest.mark.parametrize(
    ("mode", "diagnostic"),
    [
        ("malformed", "malformed helper JSON frame"),
        ("timeout", "exceeded its configured deadline"),
    ],
)
def test_installed_partial_lean_failures_preserve_schema_valid_report(
    tmp_path: Path,
    mode: str,
    diagnostic: str,
) -> None:
    repo_root, fake_bin = build_fixture(tmp_path, "exit 0")
    install_fake_lean_helper(
        repo_root,
        fake_bin,
        failing_batch_lake_script(mode),
    )
    output = tmp_path / f"lean-{mode}.json"

    result = run_build(
        repo_root,
        fake_bin,
        "--extraction-backend",
        "lean",
        "--lean-timeout",
        "0.1",
        "--format",
        "json",
        "--output",
        str(output),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    payload = json.loads(output.read_text(encoding="utf-8"))
    Draft202012Validator(load_report_v3_schema()).validate(payload)
    phase = payload["phases"]["lean_extraction"]
    assert phase["status"] == "partial"
    assert phase["disposition"] == "required-rejection"
    assert diagnostic in json.dumps(payload)


def test_installed_text_signal_contract_preserves_raw_populations_and_authority(
    tmp_path: Path,
) -> None:
    assert_installed_text_signal_contract(
        analyzer_command(),
        tmp_path,
    )


def test_installed_lean_signal_contract_caps_coarse_similarity_and_namespace_drift(
    tmp_path: Path,
) -> None:
    assert_installed_lean_signal_contract(
        analyzer_command(),
        tmp_path,
    )


# Shared installed-process construction and liveness checks.
# Helpers create only caller-owned temporary repositories and fake executables.
# Signal cleanup treats a zombie as terminated pending host-process reaping.
def analyzer_command() -> list[str]:
    """Return the installed analyzer selected by the distribution smoke."""

    return [os.environ.get("LADON_CONSOLE", str(Path(sys.executable).with_name("ladon")))]


def run_analyzer(*extra: str) -> subprocess.CompletedProcess[str]:
    """Run the portable fixture through the selected installed console."""

    return invoke(
        analyzer_command(),
        "--repo-root",
        str(FIXTURE_ROOT),
        "--root",
        "Tiny.lean",
        *extra,
    )


def run_build(
    repo_root: Path,
    fake_bin: Path,
    *extra: str,
) -> subprocess.CompletedProcess[str]:
    """Run one explicit build through a PATH-local fake Lake."""

    return subprocess.run(
        [
            *analyzer_command(),
            "--repo-root",
            str(repo_root),
            "--root",
            "Tiny.lean",
            "--build",
            *extra,
        ],
        text=True,
        capture_output=True,
        check=False,
        env=environment_with_fake_bin(fake_bin),
    )


def assert_installed_finding_projection(
    payload: dict,
    text: str,
) -> None:
    """Require complete finding rows and text identifiers."""

    assert payload["selected"] == len(payload["findings"])
    assert payload["selected"] > 0
    assert payload["omitted"] == 0
    for finding in payload["findings"]:
        assert finding["id"] in text
        assert finding["authority"]
        assert finding["evidenceRefs"]


def installed_finding_selection(
    report: Path,
    option: str,
    value: str,
) -> dict:
    """Run and decode one exact or filtered installed finding selection."""

    result = invoke(
        analyzer_command(),
        "findings",
        "--report",
        str(report),
        option,
        value,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    return json.loads(result.stdout)


def build_fixture(tmp_path: Path, lake_body: str) -> tuple[Path, Path]:
    """Create one tiny Lake repository and PATH-local Lake stand-in."""

    repo_root = tmp_path / "target"
    repo_root.mkdir()
    (repo_root / "Tiny.lean").write_text("def tiny : Nat := 1\n", encoding="utf-8")
    (repo_root / "lakefile.lean").write_text("package Tiny\n", encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    lake = fake_bin / "lake"
    lake.write_text(f"#!/bin/sh\n{lake_body}\n", encoding="utf-8")
    lake.chmod(lake.stat().st_mode | stat.S_IXUSR)
    return repo_root, fake_bin


def failing_batch_lake_script(mode: str) -> str:
    """Return a fake Lake with one controlled malformed or timeout batch."""

    return f"""#!/usr/bin/env python3
import json
import sys
import time

if len(sys.argv) > 1 and sys.argv[1] == "build":
    raise SystemExit(0)
if "--batch" in sys.argv:
    if {mode!r} == "malformed":
        print("not-json")
    else:
        time.sleep(60)
    raise SystemExit(0)
print(json.dumps({{
    "version": "2",
    "helperVersion": "installed-partial-helper-v1",
    "leanVersion": "Lean 4.fixture",
    "declarations": [],
}}))
"""


def install_fake_lean_helper(
    repo_root: Path,
    fake_bin: Path,
    script: str,
    *,
    module: str = "Tiny",
) -> None:
    """Install a direct-Lean stand-in and its required compiled module."""

    lean = fake_bin / "lean"
    lean.write_text(script, encoding="utf-8")
    lean.chmod(lean.stat().st_mode | stat.S_IXUSR)
    compiled = (
        repo_root
        / ".lake"
        / "build"
        / "lib"
        / "lean"
        / Path(*module.split("."))
    ).with_suffix(".olean")
    compiled.parent.mkdir(parents=True, exist_ok=True)
    compiled.write_bytes(b"installed fixture compiled module")


def environment_with_fake_bin(fake_bin: Path) -> dict[str, str]:
    """Prepend a fake toolchain directory for one installed-process test."""

    environment = dict(os.environ)
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
    return environment


def wait_for_path(path: Path) -> None:
    """Wait briefly for the fake build to publish its descendant PID."""

    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise AssertionError(f"timed out waiting for {path}")


def process_is_live(pid: int) -> bool:
    """Treat a zombie descendant as cleaned pending host reaping."""

    status = Path(f"/proc/{pid}/status")
    if not status.exists():
        return False
    state = next(
        line
        for line in status.read_text(encoding="utf-8").splitlines()
        if line.startswith("State:")
    )
    return "\tZ" not in state
