from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from ladon import lean_layout
from ladon.cli import main
from ladon.extraction import discover_modules
from ladon.lean_layout import discover_lean_source_map, lean_paths_under_root

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "lean_runtime"


def test_lake_layout_supports_multiple_libraries_srcdir_and_generated_roots() -> None:
    root = FIXTURE_ROOT / "lake_layout"

    source_map = discover_lean_source_map(root)

    assert source_map.status == "lake_declared"
    assert set(source_map.modules) == {
        "Pkg",
        "Pkg.Core",
        "Pkg.Generated",
        "Tools",
    }
    assert [item.library for item in source_map.roots] == ["Pkg", "Pkg", "Tools"]
    assert source_map.roots[1].generated is True


def test_declared_layout_maps_root_module_without_srcdir_prefix() -> None:
    root = FIXTURE_ROOT / "lake_layout"

    discovery = discover_modules(root, "Pkg")

    assert discovery.analysis_root_file == (root / "src" / "Pkg.lean").resolve()
    assert discovery.analysis_root_module == "Pkg"
    assert set(discovery.modules) == {"Pkg", "Pkg.Core", "Pkg.Generated"}
    assert discovery.discovery_status == "lake_declared"


def test_second_declared_library_can_be_selected_independently() -> None:
    root = FIXTURE_ROOT / "lake_layout"

    discovery = discover_modules(root, "Tools")

    assert discovery.analysis_root_file == (root / "lib" / "Tools.lean").resolve()
    assert set(discovery.modules) == {"Tools"}


def test_conventional_layout_fallback_is_explicit() -> None:
    root = FIXTURE_ROOT / "conventional"

    discovery = discover_modules(root, "Simple.lean")

    assert discovery.discovery_status == "conventional_fallback"
    assert discovery.diagnostics[-1]["id"] == "lean.layout.conventional_fallback"


def test_unusable_lake_layout_reports_fallback_diagnostic(tmp_path: Path) -> None:
    (tmp_path / "lakefile.toml").write_text("not = [valid", encoding="utf-8")
    (tmp_path / "Simple.lean").write_text("def value := 1\n", encoding="utf-8")

    discovery = discover_modules(tmp_path, "Simple.lean")

    assert discovery.discovery_status == "fallback_unsupported_lake"
    assert {row["id"] for row in discovery.diagnostics} == {
        "lean.layout.unsupported",
        "lean.layout.conventional_fallback",
    }


def test_default_library_root_excludes_unrelated_nested_lean_trees(
    tmp_path: Path,
) -> None:
    (tmp_path / "lakefile.toml").write_text(
        'name = "fixture"\n[[lean_lib]]\nname = "Pkg"\n',
        encoding="utf-8",
    )
    (tmp_path / "Pkg").mkdir()
    (tmp_path / "Pkg.lean").write_text("import Pkg.Core\n", encoding="utf-8")
    (tmp_path / "Pkg" / "Core.lean").write_text(
        "def core := 1\n",
        encoding="utf-8",
    )
    vendor = tmp_path / "src" / "lean4" / "tests"
    vendor.mkdir(parents=True)
    (vendor / "Unrelated.lean").write_text("def unrelated := 1\n", encoding="utf-8")

    source_map = discover_lean_source_map(tmp_path)

    assert set(source_map.modules) == {"Pkg", "Pkg.Core"}
    assert source_map.roots[0].module_roots == ("Pkg",)


def test_source_walk_prunes_ignored_trees_but_keeps_near_names(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "Main.lean").write_text("def main := 1\n", encoding="utf-8")
    for directory in (".git", ".lake", "__pycache__", "temp"):
        path = tmp_path / directory
        path.mkdir()
        (path / "Ignored.lean").write_text("def ignored := 1\n", encoding="utf-8")
    for directory in ("gitdata", "lakehouse", "pycache", "temporary"):
        path = tmp_path / directory
        path.mkdir()
        (path / "Kept.lean").write_text("def kept := 1\n", encoding="utf-8")

    visited: list[Path] = []
    real_walk = os.walk

    def recording_walk(*args, **kwargs):
        for row in real_walk(*args, **kwargs):
            visited.append(Path(row[0]))
            yield row

    monkeypatch.setattr(lean_layout.os, "walk", recording_walk)

    source_map = discover_lean_source_map(tmp_path)

    assert set(source_map.modules) == {
        "Main",
        "gitdata.Kept",
        "lakehouse.Kept",
        "pycache.Kept",
        "temporary.Kept",
    }
    assert all(
        not (
            set(path.relative_to(tmp_path).parts)
            & lean_layout.IGNORED_SOURCE_PARTS
        )
        for path in visited
    )


def test_source_walk_is_glob_equivalent_and_globally_ordered(
    tmp_path: Path,
) -> None:
    for relative in (
        "B.lean",
        "A/Z.lean",
        "A/A.lean",
        "C.lean/Nested.lean",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".lean" and relative != "C.lean/Nested.lean":
            path.write_text("def value := 1\n", encoding="utf-8")
        else:
            path.write_text("def nested := 1\n", encoding="utf-8")

    expected = tuple(
        path
        for path in sorted(tmp_path.rglob("*.lean"))
        if not lean_layout.ignored_source_path(path, tmp_path)
    )

    assert lean_paths_under_root(tmp_path) == expected


def test_overlapping_declared_roots_report_ambiguous_module_ownership(
    tmp_path: Path,
) -> None:
    (tmp_path / "lakefile.toml").write_text(
        """\
name = "fixture"
[[lean_lib]]
name = "First"
srcDir = "first"
roots = ["Pkg"]
[[lean_lib]]
name = "Second"
srcDir = "second"
roots = ["Pkg"]
""",
        encoding="utf-8",
    )
    for directory, value in (("first", "1"), ("second", "2")):
        source = tmp_path / directory / "Pkg"
        source.mkdir(parents=True)
        (source / "Core.lean").write_text(
            f"def value : Nat := {value}\n",
            encoding="utf-8",
        )

    source_map = discover_lean_source_map(tmp_path)

    assert set(source_map.modules) == {"Pkg.Core"}
    diagnostic = next(
        row
        for row in source_map.diagnostics
        if row["id"] == "lean.layout.ambiguous_module"
    )
    assert diagnostic["severity"] == "error"
    assert diagnostic["subject"] == "Pkg.Core"
    assert "first/Pkg/Core.lean" in diagnostic["message"]
    assert "second/Pkg/Core.lean" in diagnostic["message"]


SHARED_PATH = "Challenges/Preserved/HodgeHelpers/Shared.lean"
CANONICAL = "HodgeHelpers.Shared"
ALIAS = "Challenges.Preserved.HodgeHelpers.Shared"


def write_overlapping_layout(root: Path) -> None:
    (root / "lakefile.lean").write_text(
        'import Lake\nopen Lake DSL\n\npackage overlapRepro\n\n'
        'lean_lib HodgeHelpers where\n  srcDir := "Challenges/Preserved"\n'
        'lean_lib Challenges\n',
        encoding="utf-8",
    )
    shared = root / SHARED_PATH
    shared.parent.mkdir(parents=True, exist_ok=True)
    shared.write_text("theorem overlapSharedTruth : True := True.intro\n", encoding="utf-8")
    ordinary = root / "Challenges/Ordinary.lean"
    ordinary.write_text("theorem overlapOrdinaryTruth : True := True.intro\n", encoding="utf-8")


def test_one_source_path_with_two_module_names_requires_confirmation(tmp_path: Path) -> None:
    write_overlapping_layout(tmp_path)
    layout = discover_lean_source_map(tmp_path)

    assert set(layout.modules) == {"Challenges.Ordinary"}
    diagnostic = next(
        row for row in layout.diagnostics if row["id"] == "lean.layout.ambiguous_source"
    )
    assert diagnostic["subject"] == SHARED_PATH
    assert diagnostic["candidateModules"] == [ALIAS, CANONICAL]


def test_declared_source_owner_can_select_either_discovered_name(tmp_path: Path) -> None:
    write_overlapping_layout(tmp_path)
    config = tmp_path / ".ladon/source-layout.toml"
    config.parent.mkdir()
    directory = '"Challenges/Preserved/HodgeHelpers/" = "HodgeHelpers"'
    file = f'"{SHARED_PATH}" = "{ALIAS}"'
    for rule, module in ((f"{directory}\n{file}", ALIAS), (directory, CANONICAL)):
        config.write_text(f"[module_owners]\n{rule}\n", encoding="utf-8")
        layout = discover_lean_source_map(tmp_path)
        assert not {
            row["id"] for row in layout.diagnostics
        } & lean_layout.FATAL_OWNERSHIP_DIAGNOSTICS
        assert layout.modules == {
            "Challenges.Ordinary": tmp_path / "Challenges/Ordinary.lean",
            module: tmp_path / SHARED_PATH,
        }
        discovery = discover_modules(tmp_path, SHARED_PATH)
        assert discovery.analysis_root_module == module


def test_same_resolved_file_with_distinct_symlink_names_is_ambiguous(tmp_path: Path) -> None:
    (tmp_path / "Original.lean").write_text("def original := 1\n", encoding="utf-8")
    (tmp_path / "Alias.lean").symlink_to("Original.lean")

    layout = discover_lean_source_map(tmp_path, resolve_paths=True)

    assert not layout.modules
    diagnostic = next(
        row for row in layout.diagnostics if row["id"] == "lean.layout.ambiguous_source"
    )
    assert diagnostic["subject"] == "Original.lean"
    assert diagnostic["candidateModules"] == ["Alias", "Original"]


def test_static_lake_roots_can_exclude_a_candidate(tmp_path: Path) -> None:
    write_overlapping_layout(tmp_path)
    (tmp_path / "lakefile.toml").write_text(
        'name = "fixture"\n[[lean_lib]]\nname = "Challenges"\n'
        'roots = ["Challenges.Ordinary"]\n[[lean_lib]]\nname = "HodgeHelpers"\n'
        'srcDir = "Challenges/Preserved"\n',
        encoding="utf-8",
    )

    layout = discover_lean_source_map(tmp_path)

    assert set(layout.modules) == {"Challenges.Ordinary", CANONICAL}
    assert not layout.diagnostics


def test_lean_library_does_not_inherit_srcdir_from_next_library(tmp_path: Path) -> None:
    write_overlapping_layout(tmp_path)
    lakefile = tmp_path / "lakefile.lean"
    header, nested = lakefile.read_text().split("lean_lib HodgeHelpers", 1)
    nested_body, broader_body = nested.split("lean_lib Challenges", 1)
    lakefile.write_text(
        header + "lean_lib Challenges" + broader_body + "\nlean_lib HodgeHelpers" + nested_body
    )
    layout = discover_lean_source_map(tmp_path)

    assert set(layout.modules) == {"Challenges.Ordinary"}
    assert layout.diagnostics[0]["candidateModules"] == [ALIAS, CANONICAL]


def invoke_index(tmp_path, capsys, *args):
    result = main([
        "proof-search", *args, "--repo-root", str(tmp_path),
        "--index", str(tmp_path / "index.sqlite"), "--format", "json", "--output", "-",
    ])
    captured = capsys.readouterr()
    if result:
        assert not captured.out
        return result, json.loads(captured.err.splitlines()[-1])
    return result, json.loads(captured.out)


def confirm_owner(tmp_path: Path) -> Path:
    config = tmp_path / ".ladon/source-layout.toml"
    config.parent.mkdir()
    config.write_text('[module_owners]\n"Challenges/Preserved/HodgeHelpers/" = "HodgeHelpers"\n')
    return config


def scoped_search(tmp_path, capsys, name, module, freshness="verify"):
    status, result = invoke_index(
        tmp_path, capsys, "search", "name", "--text", name, "--scope", "module",
        "--root", module, "--freshness", freshness,
    )
    assert status == 0
    return result


def test_overlapping_index_build_reports_candidates(tmp_path: Path, capsys):
    write_overlapping_layout(tmp_path)

    status, error = invoke_index(tmp_path, capsys, "index", "build")

    assert status == 1 and not (tmp_path / "index.sqlite").exists()
    diagnostic = error["diagnostic"]
    assert diagnostic["code"] == "ambiguous-source"
    assert diagnostic["details"] == {"path": SHARED_PATH, "candidateModules": [ALIAS, CANONICAL]}
    assert ".ladon/source-layout.toml" in diagnostic["remediation"]


def test_confirmed_index_publishes_selected_module_and_unaffected_sources(tmp_path: Path, capsys):
    write_overlapping_layout(tmp_path)
    confirm_owner(tmp_path)

    status, built = invoke_index(tmp_path, capsys, "index", "build")

    assert status == 0 and built["counts"]["modules"] == 2
    with sqlite3.connect(tmp_path / "index.sqlite") as connection:
        assert connection.execute("SELECT name,path,package FROM modules ORDER BY name").fetchall() == [
            ("Challenges.Ordinary", "Challenges/Ordinary.lean", "Challenges"),
            (CANONICAL, SHARED_PATH, "HodgeHelpers"),
        ]
        detail, = connection.execute(
            "SELECT details_json FROM omissions WHERE reason='lean.layout.source_owner_selected'"
        ).fetchone()
        assert json.loads(detail)["candidateModules"] == [ALIAS, CANONICAL]

    shared = scoped_search(tmp_path, capsys, "overlapSharedTruth", CANONICAL)
    assert shared["matchSummary"]["exactMatches"] == 1
    assert shared["results"][0]["module"] == CANONICAL
    ordinary = scoped_search(tmp_path, capsys, "overlapOrdinaryTruth", "Challenges.Ordinary")
    assert ordinary["matchSummary"]["exactMatches"] == 1
    assert scoped_search(tmp_path, capsys, "overlapSharedTruth", ALIAS)["results"] == []


def test_confirmed_index_updates_and_reports_freshness(tmp_path: Path, capsys):
    write_overlapping_layout(tmp_path)
    config = confirm_owner(tmp_path)
    status, built = invoke_index(tmp_path, capsys, "index", "build")
    assert status == 0
    changed = tmp_path / SHARED_PATH
    changed.write_text(changed.read_text() + "theorem anotherSharedTruth : True := True.intro\n")

    status, updated = invoke_index(tmp_path, capsys, "index", "update")

    assert status == 0 and updated["extractedModules"] == 1
    assert updated["generationIdentity"] != built["generationIdentity"]
    assert scoped_search(tmp_path, capsys, "anotherSharedTruth", CANONICAL)[
        "matchSummary"
    ]["exactMatches"] == 1
    status, current = invoke_index(tmp_path, capsys, "index", "status", "--changed")
    assert status == 0 and current["freshness"] == "fresh"

    config.write_text(f'[module_owners]\n"{SHARED_PATH}" = "{ALIAS}"\n')
    status, stale = invoke_index(tmp_path, capsys, "index", "status", "--changed")
    assert status == 0 and stale["freshness"] == "stale-configuration"
    status, error = invoke_index(tmp_path, capsys, "index", "update")
    assert status == 1 and error["diagnostic"]["code"] == "full-build-required"


def test_unresolved_or_invalid_replacement_preserves_published_index(tmp_path: Path, capsys):
    write_overlapping_layout(tmp_path)
    config = confirm_owner(tmp_path)
    status, _ = invoke_index(tmp_path, capsys, "index", "build")
    assert status == 0
    index = tmp_path / "index.sqlite"
    published = index.read_bytes()

    config.write_text(config.read_text().replace('"HodgeHelpers"', '"Unknown"'))
    status, error = invoke_index(tmp_path, capsys, "index", "build")
    assert status == 1 and error["diagnostic"]["code"] == "invalid-source-owner"
    assert index.read_bytes() == published
    config.unlink()
    status, error = invoke_index(tmp_path, capsys, "index", "update")
    assert status == 1 and error["diagnostic"]["code"] == "ambiguous-source"
    assert error["diagnostic"]["details"]["candidateModules"] == [ALIAS, CANONICAL]
    assert index.read_bytes() == published
    stored = scoped_search(tmp_path, capsys, "overlapSharedTruth", CANONICAL, "stored")
    assert stored["matchSummary"]["exactMatches"] == 1
