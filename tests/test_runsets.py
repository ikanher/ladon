from __future__ import annotations

import json
import os
import shutil
import sys
import threading
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ladon.pipeline import RunContext, run_pipeline
from ladon.process_supervisor import (
    ProcessCancelled,
    run_streaming_target_process,
)
from ladon.report_v3 import build_report_v3, load_report_v3_schema
from ladon.runset_contract import (
    EntryValidity,
    RunsetPolicy,
    content_sha256,
    load_bundle_schema,
    load_runset_manifest,
    load_runset_state_schema,
)
from ladon.runsets import (
    AnalysisOutcome,
    ReusableArtifact,
    RunsetAnalysisRequest,
    SharedArtifactPool,
    execute_runset,
    validate_bundle_reports,
)
from ladon.runset_support import (
    default_validity,
    resolve_validities,
    reuse_record,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "runsets"
MANIFEST_PATH = FIXTURE_ROOT / "manifest-v1.json"
TINY_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


@pytest.fixture(scope="module")
def report_bytes() -> bytes:
    """Build one real schema-valid ordinary report for orchestration tests."""

    model = run_pipeline(
        RunContext(repo_root=TINY_ROOT, requested_root="Tiny.lean")
    ).to_report_model()
    payload = build_report_v3(model, projection="review").to_dict()
    return (
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def fixed_validity(
    entry,
    _repository: Path,
    *,
    changed: str | None = None,
) -> EntryValidity:
    """Return compatible inventory and entry-selective semantic identities."""

    selected = (
        f"{entry.identifier}:changed"
        if entry.identifier == changed
        else entry.identifier
    )
    return EntryValidity(
        input_fingerprint=digest(f"input:{selected}"),
        source_index_fingerprint=digest("inventory"),
        lean_cache_fingerprint=(
            digest(f"lean:{selected}") if entry.backend == "lean" else None
        ),
    )


def digest(value: str) -> str:
    return content_sha256(value.encode("utf-8"))


def successful_runner(
    content: bytes,
    calls: list[str],
    shared_seen: list[set[str]] | None = None,
):
    artifact = object()

    def run(request: RunsetAnalysisRequest) -> AnalysisOutcome:
        calls.append(request.entry.identifier)
        if shared_seen is not None:
            shared_seen.append(set(request.shared_artifacts))
        return AnalysisOutcome(
            status="complete",
            report_bytes=content,
            resource_counters={"helperLaunches": 0, "peakRssMiB": 12},
            reusable_artifacts={
                "source-index": ReusableArtifact(
                    fingerprint=digest("inventory"),
                    value=artifact,
                )
            },
        )

    return run


def test_serial_success_publishes_independent_schema_valid_reports_and_bundle(
    tmp_path: Path,
    report_bytes: bytes,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    calls: list[str] = []
    shared: list[set[str]] = []

    result = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=tmp_path / "bundle",
        runner=successful_runner(report_bytes, calls, shared),
        validity_resolver=fixed_validity,
        resume=False,
    )

    assert calls == ["core", "helper", "facade"]
    assert shared == [set(), {"source-index"}, {"source-index"}]
    assert result.analyzer_launches == 3
    assert result.exit_code == 0
    assert [row.status for row in result.bundle.entries] == [
        "complete",
        "complete",
        "complete",
    ]
    assert len({row.report.path for row in result.bundle.entries if row.report}) == 3
    Draft202012Validator(load_bundle_schema()).validate(
        result.bundle.to_payload()
    )
    state = json.loads(result.state_path.read_text(encoding="utf-8"))
    Draft202012Validator(load_runset_state_schema()).validate(state)
    report_validator = Draft202012Validator(load_report_v3_schema())
    for entry in result.bundle.entries:
        assert entry.report is not None
        report_validator.validate(
            json.loads((result.bundle_path.parent / entry.report.path).read_bytes())
        )
    assert validate_bundle_reports(
        result.bundle,
        bundle_dir=result.bundle_path.parent,
    ) == ()


def test_fresh_equivalent_runs_make_byte_identical_movable_bundles(
    tmp_path: Path,
    report_bytes: bytes,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    paths = [tmp_path / "first", tmp_path / "second"]
    results = [
        execute_runset(
            manifest,
            workspace_root=FIXTURE_ROOT,
            bundle_dir=path,
            runner=successful_runner(report_bytes, []),
            validity_resolver=fixed_validity,
            resume=False,
        )
        for path in paths
    ]

    assert results[0].bundle_path.read_bytes() == results[1].bundle_path.read_bytes()
    moved = tmp_path / "moved"
    shutil.copytree(paths[0], moved)
    moved_payload = json.loads((moved / "bundle.json").read_text(encoding="utf-8"))
    assert validate_bundle_reports(moved_payload, bundle_dir=moved) == ()


def test_unchanged_resume_is_zero_launch_and_corruption_is_selective(
    tmp_path: Path,
    report_bytes: bytes,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    bundle_dir = tmp_path / "bundle"
    first_calls: list[str] = []
    execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, first_calls),
        validity_resolver=fixed_validity,
    )

    forbidden_calls: list[str] = []
    resumed = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, forbidden_calls),
        validity_resolver=fixed_validity,
    )

    assert forbidden_calls == []
    assert resumed.analyzer_launches == 0
    assert resumed.resume_hits == 3
    assert {entry.status for entry in resumed.bundle.entries} == {"resume-hit"}

    (bundle_dir / "reports/helper.json").write_text(
        '{"truncated":',
        encoding="utf-8",
    )
    repair_calls: list[str] = []
    repaired = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, repair_calls),
        validity_resolver=fixed_validity,
    )

    assert repair_calls == ["helper"]
    assert repaired.analyzer_launches == 1
    assert [entry.status for entry in repaired.bundle.entries] == [
        "resume-hit",
        "complete",
        "resume-hit",
    ]


def test_changed_validity_reruns_entry_and_its_declared_dependent_only(
    tmp_path: Path,
    report_bytes: bytes,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    bundle_dir = tmp_path / "bundle"
    execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, []),
        validity_resolver=fixed_validity,
    )
    calls: list[str] = []

    result = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, calls),
        validity_resolver=lambda entry, root: fixed_validity(
            entry,
            root,
            changed="helper",
        ),
    )

    assert calls == ["facade", "helper"] or calls == ["helper", "facade"]
    assert result.resume_hits == 1
    by_id = {entry.identifier: entry.status for entry in result.bundle.entries}
    assert by_id == {
        "core": "resume-hit",
        "helper": "complete",
        "facade": "complete",
    }


@pytest.mark.parametrize(
    ("resource_name", "resource_value"),
    [
        ("overall_timeout_seconds", 37.0),
        ("max_rss_mib", 768),
        ("max_report_bytes", 10_000_000),
    ],
)
def test_changed_global_resource_invalidates_every_resume_entry(
    tmp_path: Path,
    report_bytes: bytes,
    resource_name: str,
    resource_value: int | float,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    bundle_dir = tmp_path / resource_name
    initial = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, []),
        validity_resolver=fixed_validity,
    )
    changed = replace(
        manifest,
        resources=replace(
            manifest.resources,
            **{resource_name: resource_value},
        ),
    )
    _, initial_fingerprints = resolve_validities(
        manifest,
        (FIXTURE_ROOT / manifest.repository).resolve(),
        fixed_validity,
    )
    _, changed_fingerprints = resolve_validities(
        changed,
        (FIXTURE_ROOT / manifest.repository).resolve(),
        fixed_validity,
    )
    calls: list[str] = []

    resumed = execute_runset(
        changed,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, calls),
        validity_resolver=fixed_validity,
    )

    assert initial.resume_hits == 0
    assert calls == ["core", "helper", "facade"]
    assert resumed.resume_hits == 0
    assert initial_fingerprints.keys() == changed_fingerprints.keys()
    assert all(
        initial_fingerprints[identifier]
        != changed_fingerprints[identifier]
        for identifier in initial_fingerprints
    )


def test_changed_shared_execution_policy_changes_entry_validity() -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    changed = replace(
        manifest,
        policy=RunsetPolicy(
            stop_on_required_failure=False,
            continue_on_advisory_failure=True,
        ),
    )
    repository = (FIXTURE_ROOT / manifest.repository).resolve()

    _, initial = resolve_validities(manifest, repository, fixed_validity)
    _, updated = resolve_validities(changed, repository, fixed_validity)

    assert initial.keys() == updated.keys()
    assert all(initial[key] != updated[key] for key in initial)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("runsetFingerprint", digest("different-runset")),
        ("schema", "ladon-analysis-runset-state-v999"),
    ],
)
def test_incompatible_state_header_is_rejected_without_resume_hits(
    tmp_path: Path,
    report_bytes: bytes,
    field: str,
    value: str,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    bundle_dir = tmp_path / field
    initial = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, []),
        validity_resolver=fixed_validity,
    )
    state = json.loads(initial.state_path.read_text(encoding="utf-8"))
    state[field] = value
    initial.state_path.write_text(json.dumps(state), encoding="utf-8")
    calls: list[str] = []

    resumed = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, calls),
        validity_resolver=fixed_validity,
    )

    assert calls == ["core", "helper", "facade"]
    assert resumed.resume_hits == 0


def test_lean_cache_reuse_requires_returned_exact_fingerprint() -> None:
    fingerprint = digest("lean-cache")
    validity = EntryValidity(
        input_fingerprint=digest("input"),
        lean_cache_fingerprint=fingerprint,
    )
    pool = SharedArtifactPool()
    artifact = object()

    pool.publish(
        validity,
        {
            "lean-cache": ReusableArtifact(
                fingerprint=fingerprint,
                value=artifact,
            )
        },
    )

    assert pool.compatible(validity) == {"lean-cache": artifact}
    row = reuse_record(validity, pool.compatible(validity))
    assert row["lean-cache"] == {
        "fingerprint": fingerprint,
        "status": "hit",
    }
    with pytest.raises(ValueError, match="mismatched fingerprint"):
        pool.publish(
            validity,
            {
                "lean-cache": ReusableArtifact(
                    fingerprint=digest("different"),
                    value=object(),
                )
            },
        )


def test_default_lean_validity_records_explicit_unavailable_evidence() -> None:
    entry = replace(load_runset_manifest(MANIFEST_PATH).entries[0], backend="lean")

    validity = default_validity(
        entry,
        (FIXTURE_ROOT / "repository").resolve(),
    )
    row = reuse_record(validity, {})

    assert validity.lean_cache_fingerprint is None
    assert row["lean-cache"] == {
        "fingerprint": None,
        "status": "unavailable",
        "reason": "aggregate_lean_cache_fingerprint_unavailable",
    }


def test_advisory_failure_continues_and_required_failure_stops(
    tmp_path: Path,
    report_bytes: bytes,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)

    def advisory_failure(request: RunsetAnalysisRequest) -> AnalysisOutcome:
        if request.entry.identifier == "helper":
            return AnalysisOutcome(
                status="failed",
                diagnostics=(
                    {"id": "fixture.failure", "severity": "error", "message": "x"},
                ),
            )
        return AnalysisOutcome(status="complete", report_bytes=report_bytes)

    continued = execute_runset(
        replace(
            manifest,
            entries=tuple(
                replace(entry, depends_on=())
                for entry in manifest.entries
            ),
        ),
        workspace_root=FIXTURE_ROOT,
        bundle_dir=tmp_path / "advisory",
        runner=advisory_failure,
        validity_resolver=fixed_validity,
        resume=False,
    )

    assert [entry.status for entry in continued.bundle.entries] == [
        "complete",
        "failed",
        "complete",
    ]
    assert continued.exit_code == 0
    assert (continued.bundle_path.parent / "reports/core.json").is_file()

    def required_failure(request: RunsetAnalysisRequest) -> AnalysisOutcome:
        if request.entry.identifier == "core":
            return AnalysisOutcome(status="failed")
        return AnalysisOutcome(status="complete", report_bytes=report_bytes)

    stopped = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=tmp_path / "required",
        runner=required_failure,
        validity_resolver=fixed_validity,
        resume=False,
    )

    assert [entry.status for entry in stopped.bundle.entries] == [
        "failed",
        "skipped",
        "skipped",
    ]
    assert stopped.exit_code == 1


def test_cancellation_preserves_completed_report_and_starts_no_later_entry(
    tmp_path: Path,
    report_bytes: bytes,
) -> None:
    manifest = replace(
        load_runset_manifest(MANIFEST_PATH),
        entries=tuple(
            replace(entry, depends_on=())
            for entry in load_runset_manifest(MANIFEST_PATH).entries
        ),
    )
    calls: list[str] = []
    received_tokens: list[threading.Event] = []

    def cancelling_runner(request: RunsetAnalysisRequest) -> AnalysisOutcome:
        calls.append(request.entry.identifier)
        received_tokens.append(request.cancel_event)
        if request.entry.identifier == "helper":
            raise ProcessCancelled("fixture cancellation")
        return AnalysisOutcome(status="complete", report_bytes=report_bytes)

    result = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=tmp_path / "bundle",
        runner=cancelling_runner,
        validity_resolver=fixed_validity,
        resume=False,
    )

    assert calls == ["core", "helper"]
    assert received_tokens[0] is received_tokens[1]
    assert received_tokens[0].is_set()
    assert [entry.status for entry in result.bundle.entries] == [
        "complete",
        "interrupted",
        "skipped",
    ]
    assert result.exit_code == 1
    assert (result.bundle_path.parent / "reports/core.json").is_file()


def test_report_limit_failure_leaves_existing_destination_intact(
    tmp_path: Path,
    report_bytes: bytes,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    manifest = replace(
        manifest,
        entries=(manifest.entries[0],),
        resources=replace(manifest.resources, max_report_bytes=10),
    )
    destination = tmp_path / "bundle" / manifest.entries[0].output
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"existing\n")

    result = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=tmp_path / "bundle",
        runner=successful_runner(report_bytes, []),
        validity_resolver=fixed_validity,
        resume=False,
    )

    assert result.bundle.entries[0].status == "failed"
    assert destination.read_bytes() == b"existing\n"


def test_partial_required_report_is_preserved_but_never_a_resume_hit(
    tmp_path: Path,
    report_bytes: bytes,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    manifest = replace(manifest, entries=(manifest.entries[0],))
    bundle_dir = tmp_path / "bundle"
    partial = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=lambda _request: AnalysisOutcome(
            status="partial",
            report_bytes=report_bytes,
        ),
        validity_resolver=fixed_validity,
    )

    assert partial.bundle.entries[0].status == "partial"
    assert partial.bundle.entries[0].report is not None
    assert (bundle_dir / "reports/core.json").is_file()
    calls: list[str] = []
    resumed = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=bundle_dir,
        runner=successful_runner(report_bytes, calls),
        validity_resolver=fixed_validity,
    )
    assert calls == ["core"]
    assert resumed.resume_hits == 0
    assert resumed.bundle.entries[0].status == "complete"


def test_cancel_token_drives_existing_supervisor_descendant_cleanup(
    tmp_path: Path,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    manifest = replace(manifest, entries=(manifest.entries[0],))
    child_pid_path = tmp_path / "child.pid"
    program = (
        "import pathlib, subprocess, sys, time; "
        "child = subprocess.Popen("
        "[sys.executable, '-c', 'import time; time.sleep(60)']); "
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
        "time.sleep(60)"
    )

    def supervised_runner(request: RunsetAnalysisRequest) -> AnalysisOutcome:
        timer = threading.Timer(0.2, request.cancel_event.set)
        timer.start()
        try:
            run_streaming_target_process(
                [sys.executable, "-c", program],
                cwd=tmp_path,
                timeout_seconds=3,
                input_text="{}\n",
                stdout_line_validator=lambda _line: None,
                cancel_event=request.cancel_event,
                terminate_grace_seconds=0.1,
            )
        finally:
            timer.cancel()
        raise AssertionError("cancelled process unexpectedly completed")

    result = execute_runset(
        manifest,
        workspace_root=FIXTURE_ROOT,
        bundle_dir=tmp_path / "bundle",
        runner=supervised_runner,
        validity_resolver=fixed_validity,
        resume=False,
    )

    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    assert result.bundle.entries[0].status == "interrupted"
    assert process_is_live(child_pid) is False


def process_is_live(pid: int) -> bool:
    """Return false for absent or already terminated zombie descendants."""

    status = Path(f"/proc/{pid}/status")
    if not status.exists():
        return False
    try:
        state = next(
            row for row in status.read_text(encoding="utf-8").splitlines()
            if row.startswith("State:")
        )
    except (FileNotFoundError, ProcessLookupError):
        return False
    if "\tZ" in state:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True
