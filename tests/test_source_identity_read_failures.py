"""Missing working-tree entries must not hide other source-read failures."""

from pathlib import Path

import pytest

import ladon.lean_toolchain as toolchain


@pytest.mark.parametrize("blocked", ["Project", "Project/Main.lean"])
def test_source_identity_rejects_permission_errors(tmp_path, monkeypatch, blocked):
    source = tmp_path / "Project/Main.lean"
    source.parent.mkdir()
    source.write_text("def value := true\n", encoding="utf-8")
    original = Path.lstat

    def denied(path, *args, **kwargs):
        if path == tmp_path / blocked:
            raise PermissionError("source access denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", denied)
    with pytest.raises((toolchain.LeanToolchainError, PermissionError)):
        toolchain._source_tree_identity(tmp_path, None)


def test_source_disappearing_after_path_observation_is_a_read_failure(tmp_path, monkeypatch):
    source = tmp_path / "Main.lean"
    source.write_text("def value := true\n", encoding="utf-8")
    original = toolchain._read_source_bytes

    def disappeared(path, relative):
        path.unlink()
        return original(path, relative)

    monkeypatch.setattr(toolchain, "_read_source_bytes", disappeared)
    with pytest.raises(toolchain.LeanToolchainError, match="cannot read source identity"):
        toolchain._source_tree_identity(tmp_path, None)


def test_absent_required_pin_still_rejects_toolchain_context(tmp_path):
    with pytest.raises(toolchain.LeanToolchainError, match="toolchain pin is missing"):
        toolchain.resolve_toolchain_context(tmp_path)
