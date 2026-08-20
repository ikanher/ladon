from __future__ import annotations

import json
import shutil
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from ladon.cli import main
from ladon.report_v3 import load_report_v3_schema
from ladon.runset_cli import OrdinaryCliRunsetAdapter
from ladon.runset_contract import load_bundle_schema, load_runset_manifest
from ladon.runset_support import reuse_record

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "runsets"
MANIFEST_PATH = FIXTURE_ROOT / "manifest-v1.json"
FORBIDDEN_CALLER_OPTIONS = (
    "--agent-only",
    "--llm",
    "--model-only",
    "--prompt-only",
)


def run_fixture(
    tmp_path: Path,
    bundle_dir: Path,
    *extra: str,
) -> int:
    """Run the tracked portable manifest through the public CLI."""

    return main(
        [
            "runset",
            "--manifest",
            str(MANIFEST_PATH),
            "--bundle-dir",
            str(bundle_dir),
            "--cache-dir",
            str(tmp_path / "cache"),
            *extra,
        ]
    )


def assert_schema_valid_bundle(payload: dict, bundle_dir: Path) -> None:
    """Check the portable index and each independently canonical report."""

    Draft202012Validator(load_bundle_schema()).validate(payload)
    report_validator = Draft202012Validator(load_report_v3_schema())
    for entry in payload["entries"]:
        report_validator.validate(
            json.loads(
                (bundle_dir / entry["report"]["path"]).read_text(
                    encoding="utf-8"
                )
            )
        )


def test_runset_cli_publishes_clean_independent_reports(
    tmp_path: Path,
    capsys,
) -> None:
    bundle_dir = tmp_path / "bundle"

    status = run_fixture(
        tmp_path,
        bundle_dir,
        "--no-resume",
        "--progress",
        "off",
    )

    captured = capsys.readouterr()
    assert status == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert_schema_valid_bundle(payload, bundle_dir)
    assert payload == json.loads(
        (bundle_dir / "bundle.json").read_text(encoding="utf-8")
    )
    assert [entry["status"] for entry in payload["entries"]] == [
        "complete",
        "complete",
        "complete",
    ]


def test_runset_cli_unchanged_resume_is_zero_launch(
    tmp_path: Path,
    capsys,
) -> None:
    bundle_dir = tmp_path / "bundle"
    assert run_fixture(
        tmp_path,
        bundle_dir,
        "--no-resume",
        "--progress",
        "off",
    ) == 0
    capsys.readouterr()
    resumed = run_fixture(
        tmp_path,
        bundle_dir,
        "--progress",
        "off",
        "--format",
        "text",
    )

    captured = capsys.readouterr()
    assert resumed == 0
    assert captured.err == ""
    assert "Analyzer launches: 0" in captured.out
    assert "Resume hits: 3" in captured.out
    canonical = json.loads(
        (bundle_dir / "bundle.json").read_text(encoding="utf-8")
    )
    assert {entry["status"] for entry in canonical["entries"]} == {
        "resume-hit"
    }


def write_architecture_policy(path: Path, identifier: str) -> None:
    """Write one valid policy whose bytes participate in resume validity."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "id": identifier,
                "groups": {
                    "fixture": {
                        "patterns": ["Fixture.*"],
                    }
                },
                "rules": [],
            }
        ),
        encoding="utf-8",
    )


def test_runset_cli_policy_edit_at_same_path_invalidates_resume(
    tmp_path: Path,
    capsys,
) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(FIXTURE_ROOT, workspace)
    policy = workspace / "repository" / ".ladon" / "architecture-policy.json"
    bundle_dir = tmp_path / "bundle"
    cache_dir = tmp_path / "cache"
    manifest = workspace / "manifest-v1.json"
    write_architecture_policy(policy, "first")

    initial = main(
        [
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
        ]
    )
    assert initial == 0
    capsys.readouterr()
    write_architecture_policy(policy, "second")

    resumed = main(
        [
            "runset",
            "--manifest",
            str(manifest),
            "--bundle-dir",
            str(bundle_dir),
            "--cache-dir",
            str(cache_dir),
            "--progress",
            "off",
            "--format",
            "text",
        ]
    )

    captured = capsys.readouterr()
    assert resumed == 0
    assert captured.err == ""
    assert "Analyzer launches: 3" in captured.out
    assert "Resume hits: 0" in captured.out


@pytest.mark.parametrize(
    ("use_cache", "lean_cache", "status", "reason"),
    [
        (False, None, "bypassed", "cache_disabled"),
        (True, None, "unavailable", "cache_not_configured"),
        (
            True,
            "configured",
            "unavailable",
            (
                "aggregate_fingerprint_unavailable; "
                "per-module fingerprints remain in the canonical report"
            ),
        ),
    ],
)
def test_runset_cli_records_sound_lean_cache_availability(
    tmp_path: Path,
    use_cache: bool,
    lean_cache: str | None,
    status: str,
    reason: str,
) -> None:
    manifest = load_runset_manifest(MANIFEST_PATH)
    entry = replace(manifest.entries[0], backend="lean")
    adapter = OrdinaryCliRunsetAdapter(
        manifest=replace(manifest, entries=(entry,)),
        workspace_root=FIXTURE_ROOT,
        progress_mode="off",
        cache_dir=tmp_path / "source-index",
        lean_cache_dir=(
            tmp_path / "lean-cache" if lean_cache is not None else None
        ),
        use_cache=use_cache,
    )

    validity = adapter.resolve_validity(entry, adapter.repository_root)
    evidence = reuse_record(validity, {})["lean-cache"]

    assert validity.lean_cache_fingerprint is None
    assert evidence == {
        "fingerprint": None,
        "status": status,
        "reason": reason,
    }


def test_runset_json_progress_keeps_stdout_machine_clean(
    tmp_path: Path,
    capsys,
) -> None:
    status = run_fixture(
        tmp_path,
        tmp_path / "bundle",
        "--no-resume",
        "--progress",
        "json",
    )

    captured = capsys.readouterr()
    assert status == 0
    assert json.loads(captured.out)["schema"] == "ladon-analysis-bundle-v1"
    events = [
        json.loads(line)
        for line in captured.err.splitlines()
        if line.strip()
    ]
    assert events
    assert all(event["schemaVersion"] == 1 for event in events)
    assert any(
        str(event["phase"]).startswith("runset.") for event in events
    )


def test_runset_rejects_unknown_major_before_creating_bundle(
    tmp_path: Path,
    capsys,
) -> None:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    invalid = deepcopy(payload)
    invalid["schemaVersion"] = 2
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(invalid), encoding="utf-8")
    bundle_dir = tmp_path / "bundle"

    status = main(
        [
            "runset",
            "--manifest",
            str(manifest),
            "--bundle-dir",
            str(bundle_dir),
            "--progress",
            "off",
        ]
    )

    captured = capsys.readouterr()
    assert status == 2
    assert captured.out == ""
    assert "supported major is 1" in captured.err
    assert not bundle_dir.exists()


def test_runset_help_is_an_ordinary_cli_surface(capsys) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["runset", "--help"])

    captured = capsys.readouterr()
    assert raised.value.code == 0
    assert "--manifest" in captured.out
    assert "--bundle-dir" in captured.out
    assert captured.err == ""
    assert all(option not in captured.out for option in FORBIDDEN_CALLER_OPTIONS)
