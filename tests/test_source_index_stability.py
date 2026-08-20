from __future__ import annotations

from pathlib import Path

import pytest

from ladon import source_index
from ladon.source_index import build_source_index


def write_project(root: Path) -> None:
    """Write three conventional modules under one declared library root."""

    (root / "Pkg").mkdir()
    (root / "Pkg.lean").write_text("import Pkg.Core\n", encoding="utf-8")
    (root / "Pkg" / "Core.lean").write_text("def core := 1\n", encoding="utf-8")
    (root / "Pkg" / "Feature.lean").write_text(
        "import Pkg.Core\ntheorem feature : True := by trivial\n",
        encoding="utf-8",
    )


def test_source_index_reports_each_completed_module_prefix(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    updates: list[tuple[int, int]] = []

    result = build_source_index(
        repo,
        use_cache=False,
        progress_callback=lambda completed, total: updates.append(
            (completed, total)
        ),
    )

    assert updates == [(1, 3), (2, 3), (3, 3)]
    assert len(result.index.entries) == 3


def test_source_index_preserves_symlink_source_identity(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "lakefile.toml").write_text(
        'name = "fixture"\n[[lean_lib]]\nname = "Pkg"\n',
        encoding="utf-8",
    )
    package = repo / "Pkg"
    package.mkdir()
    (repo / "Pkg.lean").write_text("import Pkg.Alias\n", encoding="utf-8")
    (package / "Original.lean").write_text("def value := 1\n", encoding="utf-8")
    (package / "Alias.lean").symlink_to("Original.lean")

    result = build_source_index(repo, use_cache=False)
    entries = {entry.name: entry for entry in result.index.entries}

    assert result.index.index_status == "complete"
    assert entries["Pkg.Alias"].path == "Pkg/Alias.lean"
    assert entries["Pkg.Original"].path == "Pkg/Original.lean"


def test_source_index_incrementally_stabilizes_one_concurrent_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    feature = repo / "Pkg" / "Feature.lean"
    original_manifest = source_index._fingerprint_manifest
    original_parser = source_index.parse_lean_module
    manifest_calls = 0
    parsed: list[str] = []

    def drifting_manifest(*args, **kwargs):
        nonlocal manifest_calls
        manifest_calls += 1
        if manifest_calls == 2:
            feature.write_text(
                "import Pkg.Core\ntheorem changed : True := by trivial\n",
                encoding="utf-8",
            )
        return original_manifest(*args, **kwargs)

    def counted_parser(*args, **kwargs):
        parsed.append(str(kwargs["resolved_name"]))
        return original_parser(*args, **kwargs)

    monkeypatch.setattr(source_index, "_fingerprint_manifest", drifting_manifest)
    monkeypatch.setattr(source_index, "parse_lean_module", counted_parser)

    result = build_source_index(repo, use_cache=False)

    assert result.index.index_status == "complete"
    assert parsed.count("Pkg") == 1
    assert parsed.count("Pkg.Core") == 1
    assert parsed.count("Pkg.Feature") == 2
    assert result.cache.rebuilt_entries == 3
    assert result.cache.reused_entries == 0
