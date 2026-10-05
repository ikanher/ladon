from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.semantic_lean_execution import prepare_direct_lean_execution


def _repository(root: Path) -> tuple[Path, Path]:
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n")
    for name in ("lake", "lean"):
        path = root / name
        path.write_text("#!/bin/sh\nprintf 'Lean version 4.20.0\\n'\n")
        path.chmod(0o755)
    return root / "lake", root / "lean"


def test_explicit_empty_environment_does_not_inherit_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lake, lean = _repository(tmp_path)
    monkeypatch.setenv("HOME", "/synthetic-host-home")
    monkeypatch.setenv("LANG", "synthetic-host-locale")
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean, environment={})
    assert set(context.environment) == {"PATH"}


def test_empty_environment_cannot_resolve_ambient_host_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _repository(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(LeanToolchainError, match="executable is unavailable"):
        resolve_toolchain_context(tmp_path, selection_mode="ambient", environment={})


def test_direct_context_rejects_unallowlisted_keys_without_echoing_them(tmp_path: Path) -> None:
    lake, lean = _repository(tmp_path)
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean)
    key, value = "SYNTHETIC_PRIVATE_NAME", "synthetic-private-value-7251"
    with pytest.raises(LeanToolchainError) as caught:
        replace(context, environment={**context.environment, key: value})
    assert key not in str(caught.value)
    assert value not in str(caught.value)


@pytest.mark.parametrize("key", [
    "SYNTHETIC_PRIVATE_NAME", "API_TOKEN", "LD_PRELOAD", "PYTHONPATH", "LEAN_PATH",
    "ELAN_TOOLCHAIN", "BASH_ENV", "GIT_CONFIG_COUNT", "LANGUAGE", "LC_MESSAGES",
])
def test_discarded_environment_cannot_change_identity_or_direct_launch(
    tmp_path: Path, key: str
) -> None:
    lake, lean = _repository(tmp_path)
    clean = {"PATH": "/unselected", "HOME": str(tmp_path), "LANG": "C", "LC_ALL": "C"}
    value = "synthetic-private-value-7251"
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean, environment=clean)
    poisoned = resolve_toolchain_context(
        tmp_path, lake_path=lake, lean_path=lean, environment={**clean, key: value}
    )
    assert poisoned.context_identity == context.context_identity
    assert poisoned.to_dict() == context.to_dict()
    execution = prepare_direct_lean_execution(tmp_path, None, poisoned, require_compiled_module=False)
    assert key not in execution.environment
    assert value not in json.dumps(poisoned.to_dict())
    assert value not in repr(execution.environment)


def test_context_owns_its_environment_and_locale_identity(tmp_path: Path) -> None:
    lake, lean = _repository(tmp_path)
    source = {"HOME": str(tmp_path), "LANG": "C", "LC_ALL": "C"}
    context = resolve_toolchain_context(tmp_path, lake_path=lake, lean_path=lean, environment=source)
    identity = context.context_identity
    source["LANG"] = "changed"
    assert context.context_identity == identity
    assert context.environment["LANG"] == "C"
    with pytest.raises(TypeError):
        context.environment["LANG"] = "changed"  # type: ignore[index]
    changed = resolve_toolchain_context(
        tmp_path, lake_path=lake, lean_path=lean,
        environment={**context.environment, "LANG": "changed"},
    )
    assert changed.context_identity != identity
    assert "changed" not in json.dumps(changed.to_dict())
