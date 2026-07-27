from __future__ import annotations

import json
from pathlib import Path

import pytest
from ladon.source_index import build_source_index


def write_project(root: Path) -> None:
    (root / "Pkg").mkdir()
    (root / "Pkg.lean").write_text("import Pkg.Core\n", encoding="utf-8")
    (root / "Pkg" / "Core.lean").write_text(
        "def core : Nat := 1\n",
        encoding="utf-8",
    )
    (root / "Pkg" / "Feature.lean").write_text(
        "import Pkg.Core\ntheorem feature : True := by trivial\n",
        encoding="utf-8",
    )


def cached_envelope(repo: Path, cache: Path) -> tuple[Path, dict]:
    cold = build_source_index(repo, cache_dir=cache)
    assert cold.cache.cache_path is not None
    path = cold.cache.cache_path
    return path, json.loads(path.read_text(encoding="utf-8"))


def assert_full_rebuild(repo: Path, cache: Path) -> None:
    recovered = build_source_index(repo, cache_dir=cache)
    assert recovered.cache.status == "invalidation"
    assert recovered.cache.reason == "cache_payload_invalid"
    assert recovered.cache.rebuilt_entries == 3
    assert recovered.cache.reused_entries == 0


def test_complete_cache_missing_current_command_skeleton_rows_is_rebuilt(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"
    path, envelope = cached_envelope(repo, cache)
    for entry in envelope["payload"]["entries"]:
        del entry["module"]["commandSkeletons"]
    path.write_text(json.dumps(envelope), encoding="utf-8")

    recovered = build_source_index(repo, cache_dir=cache)

    assert recovered.cache.status == "invalidation"
    assert recovered.cache.reason == "cache_payload_invalid"
    assert recovered.cache.rebuilt_entries == 3
    assert recovered.cache.reused_entries == 0
    assert all(
        entry.module.command_skeletons_complete for entry in recovered.index.entries
    )


@pytest.mark.parametrize(
    ("field_index", "replacement"),
    [
        (4, "unavailable"),
        (5, "report_metadata"),
    ],
)
def test_complete_cache_with_unusable_command_skeleton_row_is_rebuilt(
    tmp_path: Path,
    field_index: int,
    replacement: str,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"
    path, envelope = cached_envelope(repo, cache)
    row = envelope["payload"]["entries"][0]["module"]["commandSkeletons"][0]
    row[field_index] = replacement
    path.write_text(json.dumps(envelope), encoding="utf-8")

    assert_full_rebuild(repo, cache)
