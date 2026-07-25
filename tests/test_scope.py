from __future__ import annotations

import subprocess
from pathlib import Path

from ladon.scope import CHANGED_SET_MANIFEST_SCHEMA, ScopeRequest, plan_scope
from ladon.source_index import build_source_index


def indexed_project(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "Pkg" / "Feature").mkdir(parents=True)
    (repo / "Pkg.lean").write_text("import Pkg.Owner\n", encoding="utf-8")
    (repo / "Pkg" / "Owner.lean").write_text(
        "import Pkg.Core\nimport External.Lib\ntheorem owner : True := by trivial\n",
        encoding="utf-8",
    )
    (repo / "Pkg" / "Core.lean").write_text(
        "import Pkg.Shared\ndef core : Nat := 1\n",
        encoding="utf-8",
    )
    (repo / "Pkg" / "Shared.lean").write_text(
        "def shared : Nat := 1\n",
        encoding="utf-8",
    )
    (repo / "Pkg" / "Other.lean").write_text(
        "import Pkg.Shared\ndef other : Nat := 1\n",
        encoding="utf-8",
    )
    (repo / "Pkg" / "Feature" / "One.lean").write_text(
        "import Pkg.Core\ndef one : Nat := 1\n",
        encoding="utf-8",
    )
    (repo / "Pkg" / "FeatureExtra.lean").write_text(
        "def extra : Nat := 1\n",
        encoding="utf-8",
    )
    return repo, build_source_index(repo, use_cache=False).index


def assert_owner_plan(owner) -> None:
    assert owner.primary_modules == ("Pkg.Owner",)
    assert owner.context_modules == ("Pkg.Core",)
    assert owner.external_boundaries == ("External.Lib",)
    assert owner.helper_batch_estimate == 2
    assert owner.completeness == "complete"


def assert_scope_variants(closure, namespace, inventory, index) -> None:
    assert set(closure.primary_modules) == {"Pkg.Owner", "Pkg.Core", "Pkg.Shared"}
    assert closure.context_modules == ()
    assert namespace.primary_modules == ("Pkg.Feature.One",)
    assert namespace.context_modules == ("Pkg.Core",)
    assert "Pkg.FeatureExtra" not in namespace.primary_modules
    assert set(inventory.primary_modules) == set(index.modules)
    assert inventory.context_modules == ()


def test_owner_closure_namespace_and_inventory_populations(tmp_path: Path) -> None:
    _, index = indexed_project(tmp_path)

    owner = plan_scope(
        index,
        kind="owner",
        roots=("Pkg.Owner",),
        lean_batch_size=1,
    )
    closure = plan_scope(index, kind="closure", roots=("Pkg.Owner",))
    namespace = plan_scope(index, kind="namespace", roots=("Pkg.Feature",))
    inventory = plan_scope(index, kind="inventory")

    assert_owner_plan(owner)
    assert_scope_variants(closure, namespace, inventory, index)


def test_multi_root_is_order_independent_and_retains_attribution(
    tmp_path: Path,
) -> None:
    _, index = indexed_project(tmp_path)

    first = plan_scope(
        index,
        kind="multi-root",
        roots=("Pkg.Owner", "Pkg.Other"),
    )
    second = plan_scope(
        index,
        kind="multi-root",
        roots=("Pkg.Other", "Pkg.Owner"),
    )

    assert first.fingerprint == second.fingerprint
    assert first.to_payload() == second.to_payload()
    assert set(first.primary_modules) == {
        "Pkg.Owner",
        "Pkg.Other",
        "Pkg.Core",
        "Pkg.Shared",
    }
    assert first.root_attribution["Pkg.Shared"] == ("Pkg.Other", "Pkg.Owner")


def test_changed_set_uses_only_caller_paths_or_versioned_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo, index = indexed_project(tmp_path)
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError("scope preview started an external process")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    direct = plan_scope(
        index,
        ScopeRequest(
            kind="changed-set",
            changed_paths=("Pkg/Owner.lean", "README.md"),
        ),
    )
    manifest = {
        "schema": CHANGED_SET_MANIFEST_SCHEMA,
        "identity": {"before": "abc", "after": "def"},
        "paths": [{"path": "Pkg/Other.lean"}],
    }
    from_manifest = plan_scope(
        index,
        kind="changed-set",
        changed_manifest=manifest,
    )

    assert_direct_changed_plan(calls, direct)
    assert_manifest_changed_plan(from_manifest)
    assert repo.is_dir()


def assert_direct_changed_plan(calls: list[object], direct) -> None:
    assert calls == []
    assert direct.primary_modules == ("Pkg.Owner",)
    assert direct.context_modules == ("Pkg.Core",)
    assert any(
        row.identifier == "scope.changed_path_unmapped"
        and row.subject == "README.md"
        for row in direct.diagnostics
    )


def assert_manifest_changed_plan(from_manifest) -> None:
    assert from_manifest.primary_modules == ("Pkg.Other",)
    assert from_manifest.context_modules == ("Pkg.Shared",)
    assert from_manifest.changed_authority is not None
    assert from_manifest.changed_authority["manifestSchema"] == (
        CHANGED_SET_MANIFEST_SCHEMA
    )
    assert from_manifest.changed_authority["suppliedIdentity"] == {
        "after": "def",
        "before": "abc",
    }


def test_scope_path_resolution_truncation_and_invalid_changed_paths(
    tmp_path: Path,
) -> None:
    _, index = indexed_project(tmp_path)

    owner = plan_scope(index, kind="owner", roots=("Pkg/Owner.lean",))
    namespace = plan_scope(index, kind="namespace", roots=("Pkg/Feature",))
    truncated = plan_scope(
        index,
        kind="closure",
        roots=("Pkg.Owner",),
        max_modules=2,
    )
    invalid = plan_scope(
        index,
        kind="changed-set",
        changed_paths=("../outside.lean",),
    )

    assert owner.resolved_roots == ("Pkg.Owner",)
    assert namespace.primary_modules == ("Pkg.Feature.One",)
    assert truncated.primary_modules[0] == "Pkg.Owner"
    assert truncated.omitted_primary_count == 1
    assert truncated.truncated is True
    assert truncated.completeness == "truncated"
    assert invalid.completeness == "invalid"
    assert invalid.primary_modules == ()
    assert any(
        row.identifier == "scope.changed_path_invalid"
        for row in invalid.diagnostics
    )
