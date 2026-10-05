from __future__ import annotations

from pathlib import Path

import pytest

from ladon.lean_toolchain import (
    SOURCE_PATH_BYTE_LIMIT,
    SOURCE_PATH_DEPTH_LIMIT,
    LeanToolchainError,
    _filter_source_material,
    _source_tree_identity,
    _validate_source_relative_path,
)


def test_filter_normalizes_lexical_forms_deduplicates_and_consumes_once() -> None:
    supplied = iter(("./src//Core.lean", "src/Core.lean", "src/./Core.lean", "tests//test_core.py"))
    assert _filter_source_material(supplied) == ("src/Core.lean", "tests/test_core.py")
    with pytest.raises(StopIteration):
        next(supplied)


def test_filter_selects_configuration_source_and_tooling_paths() -> None:
    paths = (
        "lean-toolchain", "lake-manifest.json", "lakefile.lean", "lakefile.toml",
        "lakefile.json", "Project.lean", "src/data.txt", "tests/helper.py",
        "scripts/Probe.txt", "src/helper.lean", "tests/Probe.lean",
        "scripts/Scratch.lean", "docs/readme.md",
    )
    assert _filter_source_material(paths) == (
        "Project.lean", "lake-manifest.json", "lakefile.json", "lakefile.lean",
        "lakefile.toml", "lean-toolchain", "scripts/Probe.txt", "scripts/Scratch.lean",
        "src/data.txt", "src/helper.lean", "tests/Probe.lean", "tests/helper.py",
    )


def test_filter_preserves_overlapping_suffix_and_nested_config_selectors() -> None:
    paths = (
        ".lake/generated/Generated.lean", "vendor/nested/lakefile.toml",
        "Project/helper.lean",
    )
    assert _filter_source_material(paths) == (
        ".lake/generated/Generated.lean", "vendor/nested/lakefile.toml",
    )


@pytest.mark.parametrize(
    "raw",
    (
        "docs/../secret.txt", "../outside", "/src/Main.lean",
        "docs/" + "x" * SOURCE_PATH_BYTE_LIMIT,
        "/".join(["docs"] + ["x"] * SOURCE_PATH_DEPTH_LIMIT),
    ),
)
def test_filter_rejects_unsafe_paths_even_when_they_would_be_excluded(raw: str) -> None:
    with pytest.raises(LeanToolchainError, match="safety bounds"):
        _filter_source_material(("docs/readme.md", raw))


def test_validation_precedes_classification_for_dot_then_traversal() -> None:
    with pytest.raises(LeanToolchainError, match="safety bounds"):
        _filter_source_material((".", "../bad.txt"))


def test_validation_bounds_normalized_utf8_bytes_and_depth() -> None:
    with pytest.raises(LeanToolchainError, match="safety bounds"):
        _validate_source_relative_path("é" * (SOURCE_PATH_BYTE_LIMIT // 2 + 1))
    with pytest.raises(LeanToolchainError, match="safety bounds"):
        _validate_source_relative_path("/".join(["x"] * (SOURCE_PATH_DEPTH_LIMIT + 1)))
    assert _validate_source_relative_path("src/雪.lean") == "src/雪.lean"
    byte_boundary = "/".join(["x"] * 63 + ["é" * 1985])
    assert len(byte_boundary.encode("utf-8")) == SOURCE_PATH_BYTE_LIMIT
    assert len(Path(byte_boundary).parts) == SOURCE_PATH_DEPTH_LIMIT
    assert _validate_source_relative_path(byte_boundary) == byte_boundary


def test_fallback_keeps_os_walk_file_before_child_order(tmp_path: Path) -> None:
    from ladon.lean_toolchain import _fallback_source_material_paths

    (tmp_path / "z.lean").write_text("root", encoding="utf-8")
    nested = tmp_path / "a"
    nested.mkdir()
    (nested / "Z.lean").write_text("child", encoding="utf-8")
    assert _fallback_source_material_paths(tmp_path) == ("z.lean", "a/Z.lean")


def test_symlink_and_content_changes_remain_bound_in_source_identity(tmp_path: Path) -> None:
    source = tmp_path / "scripts" / "run.py"
    target = source.with_name("payload")
    source.parent.mkdir()
    target.write_text("initial", encoding="utf-8")
    source.symlink_to("payload")
    before = _source_tree_identity(tmp_path, None)
    target.write_text("changed", encoding="utf-8")
    after_content = _source_tree_identity(tmp_path, None)
    assert before != after_content
    source.unlink()
    source.write_text("changed", encoding="utf-8")
    after_replacement = _source_tree_identity(tmp_path, None)
    assert after_content != after_replacement
