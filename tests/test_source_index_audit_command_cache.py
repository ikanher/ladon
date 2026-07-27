from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.source_index import build_source_index


def write_audit_project(root: Path) -> None:
    (root / "Audit.lean").write_text("#check Nat\n", encoding="utf-8")


def cached_envelope(repo: Path, cache: Path) -> tuple[Path, dict]:
    cold = build_source_index(repo, cache_dir=cache)
    assert cold.cache.cache_path is not None
    path = cold.cache.cache_path
    return path, json.loads(path.read_text(encoding="utf-8"))


def assert_audit_cache_rebuilt(repo: Path, cache: Path) -> None:
    recovered = build_source_index(repo, cache_dir=cache)
    assert recovered.cache.status == "invalidation"
    assert recovered.cache.reason == "cache_payload_invalid"
    assert recovered.cache.rebuilt_entries == 1
    assert recovered.cache.reused_entries == 0
    assert [row.subject for row in recovered.index.entries[0].module.audit_commands] == [
        "Nat"
    ]


def test_complete_cache_missing_current_audit_rows_is_rebuilt(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_audit_project(repo)
    cache = tmp_path / "cache"
    path, envelope = cached_envelope(repo, cache)
    module = envelope["payload"]["entries"][0]["module"]
    del module["auditCommands"]
    del module["auditCommandsComplete"]
    path.write_text(json.dumps(envelope), encoding="utf-8")

    assert_audit_cache_rebuilt(repo, cache)


@pytest.mark.parametrize(
    ("field_index", "replacement"),
    [
        (6, "unavailable"),
        (9, "report_metadata"),
        (12, "complete"),
    ],
)
def test_complete_cache_with_unusable_audit_row_is_rebuilt(
    tmp_path: Path,
    field_index: int,
    replacement: str,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_audit_project(repo)
    cache = tmp_path / "cache"
    path, envelope = cached_envelope(repo, cache)
    command = envelope["payload"]["entries"][0]["module"]["auditCommands"][0]
    command[field_index] = replacement
    path.write_text(json.dumps(envelope), encoding="utf-8")

    assert_audit_cache_rebuilt(repo, cache)
