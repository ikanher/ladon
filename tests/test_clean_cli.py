from __future__ import annotations

import json
import sys
from pathlib import Path

from ladon.analysis.generated_family_candidate_profile import (
    CANDIDATE_PROFILE_SCHEMA,
    COMMAND_SKELETON_VERSION,
    DECLARATION_STEM_VERSION,
    GROUPING_VERSION,
)
from ladon.cli import build_parser, main
from ladon.progress import ResourceLimitExceeded


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def json_progress_events(stderr: str) -> list[dict]:
    """Decode a stderr stream that must contain only progress records."""

    return [json.loads(line) for line in stderr.splitlines()]


def embedded_json_progress_events(stderr: str) -> list[dict]:
    """Decode progress records embedded alongside human diagnostics."""

    return [
        json.loads(line)
        for line in stderr.splitlines()
        if line.startswith("{")
    ]


def assert_progress_event_contract(events: list[dict]) -> None:
    """Check fields shared by every emitted progress event."""

    assert events
    assert all(event["schemaVersion"] == 1 for event in events)
    assert all(event["phase"] for event in events)


def assert_serialization_progress_completed(events: list[dict]) -> None:
    """Check that JSON serialization reports one complete terminal event."""

    serialization = [
        event
        for event in events
        if event["phase"] == "serialization.json"
        and event["event"] == "finish"
    ]
    assert len(serialization) == 1
    assert serialization[0]["completed"] == serialization[0]["total"]
    assert serialization[0]["completed"] > 0


def assert_retained_partial_discovery(payload: dict) -> None:
    """Check the retained inventory and required partial disposition."""

    assert payload["phases"]["discover"]["status"] == "partial"
    assert payload["phases"]["discover"]["required"] is True
    assert payload["phases"]["discover"]["disposition"] == "required-rejection"
    assert payload["sections"]["module_dag"]["module_count"] == 2


def assert_partial_discovery_diagnostics(stderr: str, output: Path) -> None:
    """Check controlling diagnostics name the failed module and report."""

    assert "source_index.source_failed" in stderr
    assert "Broken" in stderr
    assert str(output) in stderr


def assert_partial_progress_terminal_states(stderr: str) -> None:
    """Check retained downstream work is explicitly labeled partial."""

    terminal = {
        event["phase"]: event["status"]
        for event in embedded_json_progress_events(stderr)
        if event["event"] == "finish"
    }
    assert terminal["discover"] == "partial"
    assert terminal["module_dag"] == "partial"


def test_import_ladon_uses_clean_entrypoint() -> None:
    sys.modules.pop("ladon.ladon", None)

    import ladon

    assert callable(ladon.main)
    assert "ladon.ladon" not in sys.modules


def test_top_level_help_discovers_every_ordinary_command() -> None:
    help_text = build_parser().format_help()

    for command in (
        "runset",
        "preview",
        "findings",
        "atlas",
        "query",
        "diff",
        "cards",
        "workflow",
    ):
        assert f"  {command}" in help_text
    assert "LLM" not in help_text


def test_clean_cli_writes_json_and_text_module_dag(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    text_path = tmp_path / "report.txt"

    status = run_tiny_cli(json_path, text_path)

    assert status == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["analysis_root_module"] == "Tiny"
    assert payload["module_dag"]["module_count"] == 3
    assert payload["module_dag"]["edge_count"] == 3
    assert payload["module_dag"]["acyclic"] is True
    assert payload["architecture_policy"]["status"] == "skipped_no_policy"


def test_clean_cli_writes_text_report_sections(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    text_path = tmp_path / "report.txt"

    status = run_tiny_cli(json_path, text_path)

    assert status == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert "pipeline" in payload
    text = text_path.read_text(encoding="utf-8")
    assert "Module DAG" in text
    assert "Pipeline Phases" in text
    assert "Declaration Graph" not in text


def test_repeatable_emit_uses_one_analysis_and_shared_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    json_path = tmp_path / "report.json"
    text_path = tmp_path / "report.txt"
    calls = 0
    from ladon import cli

    original = cli.run_pipeline

    def counted_pipeline(context):
        nonlocal calls
        calls += 1
        return original(context)

    monkeypatch.setattr(cli, "run_pipeline", counted_pipeline)
    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--emit",
            f"json={json_path}",
            "--emit",
            f"text={text_path}",
        ]
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    text = text_path.read_text(encoding="utf-8")
    assert status == 0
    assert calls == 1
    assert f"Snapshot: {payload['snapshot']['identity']}" in text
    assert payload["snapshot"]["decision"]["status"] == "stable"


def test_emit_preflight_rejects_duplicates_before_analysis(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        "ladon.cli.run_pipeline",
        lambda _context: (_ for _ in ()).throw(
            AssertionError("analysis must not start")
        ),
    )

    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--emit",
            f"json={tmp_path / 'first.json'}",
            "--emit",
            f"json={tmp_path / 'second.json'}",
        ]
    )

    assert status == 2
    assert "--emit formats must be unique" in capsys.readouterr().err


def test_emit_failure_does_not_reanalyze_or_remove_successful_output(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    json_path = tmp_path / "report.json"
    text_path = tmp_path / "report.txt"
    from ladon import cli

    analysis_calls = 0
    original_pipeline = cli.run_pipeline
    original_target = cli.emit_report_target

    def counted_pipeline(context):
        nonlocal analysis_calls
        analysis_calls += 1
        return original_pipeline(context)

    def fail_text_target(payload, plan, target, **kwargs):
        if target.format == "text":
            raise OSError("injected text destination failure")
        return original_target(payload, plan, target, **kwargs)

    monkeypatch.setattr(cli, "run_pipeline", counted_pipeline)
    monkeypatch.setattr(cli, "emit_report_target", fail_text_target)
    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--emit",
            f"json={json_path}",
            "--emit",
            f"text={text_path}",
        ]
    )

    assert status == 1
    assert analysis_calls == 1
    assert json_path.is_file()
    assert not text_path.exists()
    assert "injected text destination failure" in capsys.readouterr().err


def test_cli_loads_strict_generated_candidate_profile_before_analysis(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    profile_path = tmp_path / "candidate-profile.json"
    output = tmp_path / "report.json"
    profile = explicit_candidate_profile()
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--generated-family-candidate-profile",
            str(profile_path),
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert status == 0
    assert payload["sections"]["module_dag"][
        "generated_family_candidates"
    ]["profile"]["profileVersion"] == "portable-numbered-family-v2"

    invalid = dict(profile)
    invalid["profileVersion"] = "generic-numbered-family-v1"
    profile_path.write_text(json.dumps(invalid), encoding="utf-8")
    monkeypatch.setattr(
        "ladon.cli.run_pipeline",
        lambda _context: (_ for _ in ()).throw(
            AssertionError("invalid profile must fail before analysis")
        ),
    )
    invalid_status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--generated-family-candidate-profile",
            str(profile_path),
        ]
    )
    assert invalid_status == 2
    assert "built-in profile identity is reserved" in capsys.readouterr().err


def explicit_candidate_profile() -> dict:
    """Return one strict non-default candidate profile for CLI tests."""

    return {
        "schema": CANDIDATE_PROFILE_SCHEMA,
        "profileVersion": "portable-numbered-family-v2",
        "grouping": {"version": GROUPING_VERSION},
        "clauses": {
            "minimumMembers": 3,
            "minimumDensity": {"numerator": 3, "denominator": 4},
            "directInternalImportMemberCoverage": {
                "numerator": 3,
                "denominator": 5,
            },
            "lexicalMemberCoverage": {
                "numerator": 2,
                "denominator": 3,
            },
            "lexicalFeatures": [
                COMMAND_SKELETON_VERSION,
                DECLARATION_STEM_VERSION,
            ],
        },
        "normalizers": {
            "declarationStem": DECLARATION_STEM_VERSION,
            "commandSkeleton": COMMAND_SKELETON_VERSION,
        },
        "representatives": {"limit": 5},
    }


def run_tiny_cli(json_path: Path, text_path: Path) -> int:
    """Run the CLI on the tiny fixture."""

    return main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--output-json",
            str(json_path),
            "--output-text",
            str(text_path),
            "--generated-at-utc",
            "2026-05-10T00:00:00+00:00",
        ]
    )


def test_clean_cli_rejects_unsupported_legacy_option(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--verify-export-surface",
        ]
    )

    assert status == 2
    assert "unsupported clean-core option" in capsys.readouterr().err


def test_clean_cli_accepts_lean_cache_dir_option(tmp_path: Path) -> None:
    args = build_parser().parse_args(["--lean-cache-dir", str(tmp_path / "cache")])

    assert args.lean_cache_dir == str(tmp_path / "cache")


def test_explicit_json_progress_stays_on_stderr(capsys) -> None:
    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--format",
            "json",
            "--output",
            "-",
            "--progress",
            "json",
        ]
    )

    captured = capsys.readouterr()
    assert status == 0
    assert json.loads(captured.out)["metadata"]["analysis_root_module"] == "Tiny"
    events = json_progress_events(captured.err)
    assert_progress_event_contract(events)
    assert_serialization_progress_completed(events)


def test_report_size_limit_fails_before_file_publication(
    tmp_path: Path,
    capsys,
) -> None:
    output = tmp_path / "oversized.json"

    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--format",
            "json",
            "--output",
            str(output),
            "--max-report-bytes",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert not output.exists()
    assert "report_bytes limit exceeded" in captured.err


def test_overall_limit_writes_schema_valid_retained_partial_report(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    output = tmp_path / "partial.json"

    def injected_limit(_budget, phase: str) -> None:
        if phase == "module_dag":
            raise ResourceLimitExceeded(
                kind="overall_wall_time",
                phase=phase,
                observed=2.0,
                limit=1.0,
            )

    monkeypatch.setattr("ladon.progress.RunBudget.check", injected_limit)
    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert status == 1
    assert payload["phases"]["module_dag"]["status"] == "failed"
    assert payload["phases"]["module_dag"]["required"] is True
    assert payload["sections"]["module_dag"]["completeness"][
        "metricsSuppressed"
    ] is True
    assert "resource.overall_wall_time" in captured.err
    assert str(output) in captured.err


def test_partial_discovery_writes_retained_report_and_controlling_diagnostic(
    tmp_path: Path,
    capsys,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "A.lean").write_text("def a : Nat := 1\n", encoding="utf-8")
    (repo / "B.lean").write_text("def b : Nat := 2\n", encoding="utf-8")
    (repo / "Broken.lean").write_bytes(b"\xff")
    output = tmp_path / "partial.json"

    status = main(
        [
            "--repo-root",
            str(repo),
            "--scope",
            "inventory",
            "--no-cache",
            "--format",
            "json",
            "--output",
            str(output),
            "--progress",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert status == 1
    assert_retained_partial_discovery(payload)
    assert_partial_discovery_diagnostics(captured.err, output)
    assert_partial_progress_terminal_states(captured.err)


def test_clean_cli_accepts_architecture_policy_json(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    json_path = tmp_path / "report.json"
    policy_path.write_text(
        json.dumps(
            {
                "id": "tiny-boundaries",
                "groups": {
                    "root": ["Tiny"],
                    "core": ["Tiny.Core"],
                },
                "rules": [
                    {
                        "id": "root-core-boundary",
                        "kind": "forbid_direct_imports",
                        "from": ["root"],
                        "to": ["core"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--architecture-policy",
            str(policy_path),
            "--output-json",
            str(json_path),
        ]
    )

    assert status == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["architecture_policy"]["policyId"] == "tiny-boundaries"
    assert any(
        finding["kind"] == "architecture_policy.direct_forbidden_import"
        for finding in payload["findings"]
    )


def test_clean_cli_discovers_repo_local_architecture_policy(tmp_path: Path) -> None:
    (tmp_path / ".ladon").mkdir()
    (tmp_path / "Pkg").mkdir()
    (tmp_path / "Pkg.lean").write_text("import Pkg.Alpha\n", encoding="utf-8")
    (tmp_path / "Pkg" / "Alpha.lean").write_text("import Pkg.Beta\n", encoding="utf-8")
    (tmp_path / "Pkg" / "Beta.lean").write_text("def beta : Nat := 1\n", encoding="utf-8")
    (tmp_path / ".ladon" / "architecture-policy.json").write_text(
        json.dumps(
            {
                "id": "discovered-policy",
                "groups": {
                    "alpha": ["Pkg.Alpha"],
                    "beta": ["Pkg.Beta"],
                },
                "rules": [
                    {
                        "id": "alpha-beta",
                        "kind": "forbid_imports",
                        "from": ["alpha"],
                        "to": ["beta"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    json_path = tmp_path / "report.json"

    status = main([
        "--repo-root",
        str(tmp_path),
        "--root",
        "Pkg",
        "--output-json",
        str(json_path),
    ])

    assert status == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["architecture_policy"]["policyId"] == "discovered-policy"
    assert payload["architecture_policy"]["source"].endswith(".ladon/architecture-policy.json")


def test_clean_cli_accepts_source_pattern_policy_json(tmp_path: Path) -> None:
    policy_path = tmp_path / "source-policy.json"
    json_path = tmp_path / "report.json"
    policy_path.write_text(
        json.dumps(
            {
                "id": "tiny-source-patterns",
                "patterns": [
                    {
                        "id": "lemma-keyword",
                        "pattern": "lemma",
                        "kind": "keyword_scan",
                        "severity": "info",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--source-pattern-policy",
            str(policy_path),
            "--output-json",
            str(json_path),
        ]
    )

    assert status == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["source_patterns"]["policyId"] == "tiny-source-patterns"
    assert payload["source_patterns"]["matches"][0]["path"] == "Tiny/Helper.lean"


def test_clean_cli_discovers_repo_local_source_pattern_policy(tmp_path: Path) -> None:
    (tmp_path / ".ladon").mkdir()
    (tmp_path / "Pkg").mkdir()
    (tmp_path / "Pkg.lean").write_text("import Pkg.Owner\n", encoding="utf-8")
    (tmp_path / "Pkg" / "Owner.lean").write_text("def legacyName : Nat := 1\n", encoding="utf-8")
    (tmp_path / ".ladon" / "source-pattern-policy.json").write_text(
        json.dumps(
            {
                "id": "discovered-source-patterns",
                "patterns": [
                    {
                        "id": "legacy-name",
                        "pattern": "legacyName",
                        "kind": "stale_term",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    json_path = tmp_path / "report.json"

    status = main([
        "--repo-root",
        str(tmp_path),
        "--root",
        "Pkg",
        "--output-json",
        str(json_path),
    ])

    assert status == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["source_patterns"]["policyId"] == "discovered-source-patterns"
    assert payload["source_patterns"]["source"].endswith(".ladon/source-pattern-policy.json")


def test_documented_policy_examples_are_valid_and_generic() -> None:
    repo_root = Path(__file__).parents[1]
    architecture_policy = json.loads(
        (repo_root / "docs" / "policies" / "architecture-policy.example.json").read_text(encoding="utf-8")
    )
    source_pattern_policy = json.loads(
        (repo_root / "docs" / "policies" / "source-pattern-policy.example.json").read_text(encoding="utf-8")
    )

    assert architecture_policy["id"] == "example-peer-boundaries"
    assert source_pattern_policy["id"] == "example-source-patterns"
    assert {
        row["kind"]
        for row in source_pattern_policy["patterns"]
    } == {"banned_prose", "stale_term", "todo_class", "trust_marker"}
    serialized = json.dumps([architecture_policy, source_pattern_policy])
    assert "Mf." not in serialized
    assert "BMinSep" not in serialized
    assert "Phase2" not in serialized
