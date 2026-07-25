from __future__ import annotations

from pathlib import Path

from ladon.extraction import discover_modules
from ladon.lean_layout import discover_lean_source_map


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
