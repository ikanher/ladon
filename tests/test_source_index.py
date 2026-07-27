from __future__ import annotations

import json
from pathlib import Path

import ladon.source_index as source_index
import pytest
from ladon.source_index import (
    SOURCE_INDEX_FINGERPRINT_VERSION,
    build_source_index,
    default_source_index_cache_dir,
)


def write_project(root: Path) -> None:
    (root / "Pkg").mkdir()
    (root / "Pkg.lean").write_text(
        "import Pkg.Core\n",
        encoding="utf-8",
    )
    (root / "Pkg" / "Core.lean").write_text(
        "def core : Nat := 1\n",
        encoding="utf-8",
    )
    (root / "Pkg" / "Feature.lean").write_text(
        "import Pkg.Core\ntheorem feature : True := by trivial\n",
        encoding="utf-8",
    )


def assert_cold_index(cold, parsed: list[str]) -> None:
    assert cold.cache.status == "miss"
    assert cold.cache.reason == "cold_miss"
    assert cold.cache.committed is True
    assert cold.cache.reused_entries == 0
    assert cold.cache.rebuilt_entries == 3
    assert parsed == ["Pkg", "Pkg.Core", "Pkg.Feature"]
    assert list(cold.index.modules) == ["Pkg", "Pkg.Core", "Pkg.Feature"]


def assert_warm_index(warm, cold, parsed: list[str]) -> None:
    assert warm.cache.status == "hit"
    assert warm.cache.reused_entries == 3
    assert warm.cache.rebuilt_entries == 0
    assert parsed == []
    assert warm.index.to_payload() == cold.index.to_payload()


def assert_incremental_index(changed, cold, parsed: list[str], cache: Path) -> None:
    assert changed.cache.status == "invalidation"
    assert changed.cache.reason == "source_changed"
    assert changed.cache.reused_entries == 2
    assert changed.cache.rebuilt_entries == 1
    assert parsed == ["Pkg.Feature"]
    assert changed.index.fingerprint != cold.index.fingerprint
    assert not list(cache.rglob("*.tmp"))


def source_failures(result) -> list[dict]:
    """Return only per-source partial diagnostics."""

    return [
        dict(row)
        for row in result.index.diagnostics
        if row.get("id") == source_index.SOURCE_FAILURE_DIAGNOSTIC
    ]


def assert_partial_index(result, modules: list[str]) -> None:
    assert result.phase_status == "partial"
    assert result.index.index_status == "partial"
    assert result.index.discovery_status == "partial"
    assert result.index.to_payload()["layout"]["indexStatus"] == "partial"
    assert list(result.index.modules) == modules
    assert result.cache.committed is False


def assert_partial_cache(
    result,
    *,
    status: str,
    reused: int,
    rebuilt: int,
) -> None:
    assert result.cache.status == status
    assert result.cache.reason == "partial_index_not_cached"
    assert result.cache.cache_path is None
    assert result.cache.reused_entries == reused
    assert result.cache.rebuilt_entries == rebuilt
    assert result.cache.failed_entries == 1
    assert reused + rebuilt + result.cache.failed_entries == 3


def assert_invalid_utf8_failure(result) -> None:
    assert source_failures(result) == [
        {
            "id": "source_index.source_failed",
            "severity": "warning",
            "status": "partial",
            "subject": "Pkg.Feature",
            "module": "Pkg.Feature",
            "path": "Pkg/Feature.lean",
            "cause": "invalid_utf8",
            "detail": "byte 0: invalid start byte",
            "message": (
                "Skipped Lean source module Pkg.Feature at "
                "Pkg/Feature.lean: invalid_utf8 "
                "(byte 0: invalid start byte)."
            ),
        }
    ]


def assert_unreadable_failure(result, repo: Path) -> None:
    failure = source_failures(result)[0]
    assert failure["module"] == "Pkg.Feature"
    assert failure["path"] == "Pkg/Feature.lean"
    assert failure["cause"] == "read_error"
    assert failure["detail"] == "PermissionError(errno=13)"
    assert str(repo) not in failure["message"]
    state = next(
        row
        for row in result.index.fingerprint_manifest["sources"]
        if row["module"] == "Pkg.Feature"
    )
    assert state["status"] == "unreadable"
    assert state["cause"] == "PermissionError(errno=13)"


def assert_parser_partial(result, repeated, repo: Path) -> None:
    assert_partial_index(result, ["Pkg", "Pkg.Core"])
    assert_partial_cache(
        result,
        status="invalidation",
        reused=2,
        rebuilt=0,
    )
    assert source_failures(result) == source_failures(repeated)
    failure = source_failures(result)[0]
    assert failure["cause"] == "parse_error"
    assert failure["detail"].startswith("ValueError: fixture parser failure")
    assert str(repo) not in failure["detail"]


def assert_repaired_cache(repaired, warm) -> None:
    assert repaired.index.index_status == "complete"
    assert repaired.cache.committed is True
    assert (repaired.cache.reused_entries, repaired.cache.rebuilt_entries) == (
        2,
        1,
    )
    assert repaired.cache.failed_entries == 0
    assert warm.cache.status == "hit"
    assert warm.cache.reused_entries == 3


def test_source_index_cold_warm_and_incremental_invalidation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"
    original = source_index.parse_lean_module
    parsed: list[str] = []

    def counted(*args, **kwargs):
        parsed.append(str(kwargs["resolved_name"]))
        return original(*args, **kwargs)

    monkeypatch.setattr(source_index, "parse_lean_module", counted)

    cold = build_source_index(repo, cache_dir=cache)

    assert_cold_index(cold, parsed)

    parsed.clear()
    warm = build_source_index(repo, cache_dir=cache)

    assert_warm_index(warm, cold, parsed)

    (repo / "Pkg" / "Feature.lean").write_text(
        "import Pkg.Core\ntheorem feature : True := by\n  trivial\n",
        encoding="utf-8",
    )
    parsed.clear()
    changed = build_source_index(repo, cache_dir=cache)

    assert_incremental_index(changed, cold, parsed, cache)


def test_source_index_options_are_strong_and_unfingerprintable_options_bypass(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"

    baseline = build_source_index(
        repo,
        cache_dir=cache,
        options={"policyDigest": "a"},
    )
    changed = build_source_index(
        repo,
        cache_dir=cache,
        options={"policyDigest": "b"},
    )
    bypassed = build_source_index(
        repo,
        cache_dir=cache,
        options={"invalid": object()},
    )

    assert baseline.index.fingerprint != changed.index.fingerprint
    assert changed.cache.status == "invalidation"
    assert changed.cache.reason == "options_changed"
    assert changed.cache.reused_entries == 0
    assert bypassed.cache.status == "bypass"
    assert bypassed.cache.reason == "unfingerprintable_options"
    assert bypassed.cache.committed is False
    assert bypassed.cache.fingerprint_version == SOURCE_INDEX_FINGERPRINT_VERSION


def test_corrupt_source_index_entry_is_rebuilt_atomically(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"
    cold = build_source_index(repo, cache_dir=cache)
    assert cold.cache.cache_path is not None
    cold.cache.cache_path.write_text("{not-json", encoding="utf-8")

    recovered = build_source_index(repo, cache_dir=cache)

    assert recovered.cache.status == "invalidation"
    assert recovered.cache.reason == "cache_entry_invalid"
    assert recovered.cache.committed is True
    assert recovered.cache.rebuilt_entries == 3
    assert set(recovered.index.modules) == {"Pkg", "Pkg.Core", "Pkg.Feature"}


def test_complete_cache_without_additive_index_status_remains_compatible(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cold = build_source_index(repo, cache_dir=tmp_path / "cache")
    assert cold.cache.cache_path is not None
    envelope = json.loads(cold.cache.cache_path.read_text(encoding="utf-8"))
    del envelope["payload"]["indexStatus"]
    del envelope["payload"]["layout"]["indexStatus"]
    cold.cache.cache_path.write_text(
        json.dumps(envelope),
        encoding="utf-8",
    )

    compatible = build_source_index(repo, cache_dir=tmp_path / "cache")

    assert compatible.cache.status == "hit"
    assert compatible.index.index_status == "complete"
    assert compatible.cache.reused_entries == 3


def test_non_utf8_source_retains_stable_partial_index_without_cache(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    (repo / "Pkg" / "Feature.lean").write_bytes(b"\xffinvalid")
    cache = tmp_path / "cache"

    first = build_source_index(repo, cache_dir=cache)
    second = build_source_index(repo, cache_dir=cache)

    assert_partial_index(first, ["Pkg", "Pkg.Core"])
    assert first.index.layout_status == "conventional_fallback"
    assert_partial_cache(first, status="miss", reused=0, rebuilt=2)
    assert first.index.to_payload() == second.index.to_payload()
    assert second.cache.status == "miss"
    assert second.cache.reused_entries == 0
    assert not list(cache.rglob("*.json"))
    with pytest.raises(
        source_index.SourceIndexError,
        match="partial source indexes must not be cached",
    ):
        source_index.SourceIndexCache(cache).store(repo, first.index)
    assert_invalid_utf8_failure(first)


def test_unreadable_source_records_relative_module_path_and_cause(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    denied = (repo / "Pkg" / "Feature.lean").resolve()
    original = Path.read_bytes

    def selectively_denied(path: Path) -> bytes:
        if path.resolve() == denied:
            raise PermissionError(13, "fixture denied", str(path))
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", selectively_denied)

    result = build_source_index(repo, use_cache=False)

    assert_partial_index(result, ["Pkg", "Pkg.Core"])
    assert result.cache.status == "bypass"
    assert result.cache.failed_entries == 1
    assert_unreadable_failure(result, repo)


def test_multiple_source_failures_have_stable_module_order(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    (repo / "Pkg" / "Core.lean").write_bytes(b"\xffinvalid")
    original = source_index.parse_lean_module

    def fail_feature(*args, **kwargs):
        if kwargs["resolved_name"] == "Pkg.Feature":
            raise RuntimeError("fixture parser failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(source_index, "parse_lean_module", fail_feature)

    result = build_source_index(repo, use_cache=False)

    assert list(result.index.modules) == ["Pkg"]
    assert [
        (row["module"], row["path"], row["cause"]) for row in source_failures(result)
    ] == [
        ("Pkg.Core", "Pkg/Core.lean", "invalid_utf8"),
        ("Pkg.Feature", "Pkg/Feature.lean", "parse_error"),
    ]
    assert (result.cache.rebuilt_entries, result.cache.failed_entries) == (1, 2)


def test_parser_failure_retries_without_committing_partial_cache(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"
    complete = build_source_index(repo, cache_dir=cache)
    (repo / "Pkg" / "Feature.lean").write_text(
        "import Pkg.Core\ntheorem changed : True := by trivial\n",
        encoding="utf-8",
    )
    original = source_index.parse_lean_module
    parsed: list[str] = []

    def fail_feature(*args, **kwargs):
        name = str(kwargs["resolved_name"])
        parsed.append(name)
        if name == "Pkg.Feature":
            raise ValueError(f"fixture parser failure in {repo}/Pkg/Feature.lean")
        return original(*args, **kwargs)

    monkeypatch.setattr(source_index, "parse_lean_module", fail_feature)

    first = build_source_index(repo, cache_dir=cache)
    parsed.clear()
    second = build_source_index(repo, cache_dir=cache)

    assert_parser_partial(first, second, repo)
    assert parsed == ["Pkg.Feature"]
    partial_path = source_index.SourceIndexCache(cache).entry_path(
        first.index.fingerprint
    )
    assert not partial_path.exists()
    assert complete.cache.cache_path is not None
    assert complete.cache.cache_path.exists()

    monkeypatch.setattr(source_index, "parse_lean_module", original)
    repaired = build_source_index(repo, cache_dir=cache)
    warm = build_source_index(repo, cache_dir=cache)

    assert_repaired_cache(repaired, warm)


def test_default_source_index_cache_dir_uses_platform_conventions(
    tmp_path: Path,
) -> None:
    assert (
        default_source_index_cache_dir(
            environ={"XDG_CACHE_HOME": str(tmp_path / "xdg")},
            platform="linux",
            home=tmp_path / "home",
        )
        == tmp_path / "xdg" / "ladon" / "source-index"
    )
    assert (
        default_source_index_cache_dir(
            environ={},
            platform="linux",
            home=tmp_path / "home",
        )
        == tmp_path / "home" / ".cache" / "ladon" / "source-index"
    )
    assert (
        default_source_index_cache_dir(
            environ={},
            platform="darwin",
            home=tmp_path / "home",
        )
        == tmp_path / "home" / "Library" / "Caches" / "ladon" / "source-index"
    )
    assert (
        default_source_index_cache_dir(
            environ={"LOCALAPPDATA": str(tmp_path / "local")},
            platform="win32",
            home=tmp_path / "home",
        )
        == tmp_path / "local" / "ladon" / "source-index"
    )
