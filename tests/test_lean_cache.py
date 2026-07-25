from __future__ import annotations

from pathlib import Path

import pytest

from ladon.ir import LeanModule
from ladon.lean_cache import (
    CACHE_FINGERPRINT_VERSION,
    FileHashMemo,
    LeanCacheStore,
    build_cache_fingerprint,
    resolved_local_import_closure,
)


def test_resolved_import_closure_is_transitive_sorted_and_cycle_safe() -> None:
    modules = {
        "Pkg.A": LeanModule("Pkg.A", "Pkg/A.lean", ("Pkg.B",)),
        "Pkg.B": LeanModule("Pkg.B", "Pkg/B.lean", ("Pkg.C",)),
        "Pkg.C": LeanModule("Pkg.C", "Pkg/C.lean", ("Pkg.A",)),
    }

    assert resolved_local_import_closure("Pkg.A", modules) == (
        "Pkg.B",
        "Pkg.C",
    )


def test_sound_fingerprint_round_trips_through_versioned_namespace(
    tmp_path: Path,
) -> None:
    repo, helper, modules = runtime_repo(tmp_path)
    cache_fingerprint = fingerprint(repo, helper, modules)
    store = LeanCacheStore(repo / "cache")

    miss = store.lookup("Pkg.A", cache_fingerprint)
    store.store("Pkg.A", cache_fingerprint, {"version": "payload"})
    hit = store.lookup("Pkg.A", cache_fingerprint)

    assert miss.status == "miss"
    assert miss.invalidation_reason == "cold_miss"
    assert hit.status == "hit"
    assert hit.payload == {"version": "payload"}
    assert CACHE_FINGERPRINT_VERSION in str(store.entry_path(cache_fingerprint))


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("source", "source_changed"),
        ("import", "transitive_import_changed"),
        ("helper", "helper_changed"),
        ("options", "options_changed"),
        ("lean", "lean_version_changed"),
        ("toolchain", "toolchain_changed"),
        ("lake", "lake_state_changed"),
        ("compiled", "compiled_state_changed"),
    ],
)
def test_cache_fingerprint_classifies_required_invalidation_inputs(
    tmp_path: Path,
    case: str,
    reason: str,
) -> None:
    repo, helper, modules = runtime_repo(tmp_path)
    store = LeanCacheStore(repo / "cache")
    baseline = fingerprint(repo, helper, modules)
    store.store("Pkg.A", baseline, {"baseline": True})

    options, lean_version = mutate_case(case, repo, helper)
    changed = fingerprint(
        repo,
        helper,
        modules,
        options=options,
        lean_version=lean_version,
    )
    lookup = store.lookup("Pkg.A", changed)

    assert lookup.status == "miss"
    assert lookup.invalidation_reason == reason


def test_unfingerprintable_compiled_state_bypasses_cache(tmp_path: Path) -> None:
    repo, helper, modules = runtime_repo(tmp_path, compiled=False)

    result = LeanCacheStore(repo / "cache").lookup(
        "Pkg.A",
        fingerprint(repo, helper, modules),
    )

    assert result.status == "bypassed"
    assert result.fingerprint.manifest["cacheSafety"]["status"] == "bypassed"
    assert "compiled state is unavailable" in str(result.invalidation_reason)


def runtime_repo(
    tmp_path: Path,
    *,
    compiled: bool = True,
) -> tuple[Path, Path, dict[str, LeanModule]]:
    """Create one cache-validity fixture with local and compiled state."""

    repo = tmp_path / "repo"
    (repo / "Pkg").mkdir(parents=True)
    (repo / "Pkg" / "A.lean").write_text("import Pkg.B\ndef a := B.b\n", encoding="utf-8")
    (repo / "Pkg" / "B.lean").write_text("def b := 1\n", encoding="utf-8")
    (repo / "lean-toolchain").write_text("leanprover/lean4:v4.test\n", encoding="utf-8")
    (repo / "lake-manifest.json").write_text('{"version":"1"}\n', encoding="utf-8")
    helper = tmp_path / "helper.lean"
    helper.write_text("-- helper v1\n", encoding="utf-8")
    if compiled:
        compiled_root = repo / ".lake" / "build" / "lib" / "lean" / "Pkg"
        compiled_root.mkdir(parents=True)
        (compiled_root / "A.olean").write_bytes(b"compiled-a-v1")
        (compiled_root / "B.olean").write_bytes(b"compiled-b-v1")
    modules = {
        "Pkg.A": LeanModule("Pkg.A", "Pkg/A.lean", ("Pkg.B",)),
        "Pkg.B": LeanModule("Pkg.B", "Pkg/B.lean"),
    }
    return repo, helper, modules


def fingerprint(
    repo: Path,
    helper: Path,
    modules: dict[str, LeanModule],
    *,
    options: dict | None = None,
    lean_version: str = "Lean 4.test",
):
    """Build one fixture fingerprint."""

    return build_cache_fingerprint(
        repo_root=repo,
        module="Pkg.A",
        source_path=repo / "Pkg" / "A.lean",
        helper_path=helper,
        modules=modules,
        lean_version=lean_version,
        extraction_options=options or {"scope": "inventory", "batchSize": 8},
        hashes=FileHashMemo(),
    )


def mutate_case(
    case: str,
    repo: Path,
    helper: Path,
) -> tuple[dict, str]:
    """Mutate exactly one cache-validity dimension."""

    options = {"scope": "inventory", "batchSize": 8}
    lean_version = "Lean 4.test"
    if case == "source":
        (repo / "Pkg" / "A.lean").write_text("import Pkg.B\ndef a := 2\n", encoding="utf-8")
    elif case == "import":
        (repo / "Pkg" / "B.lean").write_text("def b := 2\n", encoding="utf-8")
    elif case == "helper":
        helper.write_text("-- helper v2\n", encoding="utf-8")
    elif case == "options":
        options["batchSize"] = 4
    elif case == "lean":
        lean_version = "Lean 4.next"
    elif case == "toolchain":
        (repo / "lean-toolchain").write_text("leanprover/lean4:v4.next\n", encoding="utf-8")
    elif case == "lake":
        (repo / "lake-manifest.json").write_text('{"version":"2"}\n', encoding="utf-8")
    elif case == "compiled":
        (repo / ".lake" / "build" / "lib" / "lean" / "Pkg" / "B.olean").write_bytes(
            b"compiled-b-v2"
        )
    return options, lean_version
