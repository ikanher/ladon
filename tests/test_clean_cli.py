from __future__ import annotations

import json
import sys
from pathlib import Path

from ladon.cli import build_parser, main


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def test_import_ladon_uses_clean_entrypoint() -> None:
    sys.modules.pop("ladon.ladon", None)

    import ladon

    assert callable(ladon.main)
    assert "ladon.ladon" not in sys.modules


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


def run_tiny_cli(json_path: Path, text_path: Path) -> int:
    """Run the CLI on the tiny fixture."""

    return main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--root",
            "Tiny.lean",
            "--skip-build",
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
