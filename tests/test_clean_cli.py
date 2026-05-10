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

    status = main(
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

    assert status == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["analysis_root_module"] == "Tiny"
    assert payload["module_dag"]["module_count"] == 3
    assert payload["module_dag"]["edge_count"] == 3
    assert payload["module_dag"]["acyclic"] is True
    assert "pipeline" in payload
    text = text_path.read_text(encoding="utf-8")
    assert "Module DAG" in text
    assert "Pipeline Phases" in text
    assert "Declaration Graph" not in text


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
