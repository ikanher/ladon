from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / ".codex" / "skills" / "pro-review-packet" / "scripts" / "create_pro_review_packet.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("create_pro_review_packet", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validation_summary_separates_skipped_source_paths_from_archive_entries(tmp_path: Path) -> None:
    helper = load_helper()
    root = tmp_path / "packet"
    root.mkdir()

    helper.write_packet_data(
        root,
        "topic",
        "question",
        ["README.md"],
        [],
        [{"repositoryPath": "src/__pycache__/x.pyc", "reason": "refusing cache/build path"}],
        [],
        False,
    )

    summary = json.loads((root / "data" / "validation-summary.json").read_text(encoding="utf-8"))

    assert summary["sourceRepositoryScan"]["status"] == "skipped_paths_recorded"
    assert summary["sourceRepositoryScan"]["skippedSourcePaths"][0]["repositoryPath"] == "src/__pycache__/x.pyc"
    assert summary["archiveIntegrityScan"]["forbiddenArchiveEntries"] == []
    assert summary["renderedArtifactScan"]["found"] == []


def test_validation_summary_reports_forbidden_archive_entries(tmp_path: Path) -> None:
    helper = load_helper()
    root = tmp_path / "packet"
    (root / "__pycache__").mkdir(parents=True)
    (root / "__pycache__" / "x.pyc").write_bytes(b"cache")

    helper.write_packet_data(
        root,
        "topic",
        "question",
        ["README.md"],
        [],
        [],
        [],
        False,
    )

    summary = json.loads((root / "data" / "validation-summary.json").read_text(encoding="utf-8"))

    assert summary["archiveIntegrityScan"]["status"] == "failed"
    assert summary["archiveIntegrityScan"]["forbiddenArchiveEntries"][0]["archivePath"] == "__pycache__/x.pyc"
    assert summary["renderedArtifactScan"]["status"] == "forbidden_archive_entries"
