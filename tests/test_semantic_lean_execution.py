from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ladon.lean_toolchain import LeanToolchainContext, LeanToolchainError, compiled_library_roots
from ladon.semantic_lean_execution import (
    DirectLeanPreflightError,
    prepare_direct_lean_execution,
)


def _toolchain(root: Path) -> LeanToolchainContext:
    lake = root / "lake"
    lean = root / "lean"
    lake.write_bytes(b"lake")
    lean.write_bytes(b"lean")
    roots = compiled_library_roots(root)
    environment = {"PATH": str(root)}
    if roots:
        environment["LEAN_PATH"] = os.pathsep.join(str(path) for path in roots)
    return LeanToolchainContext(
        root.resolve(),
        lake.resolve(),
        lean.resolve(),
        "leanprover/lean4:v4.20.0",
        "sha256:pin",
        "sha256:lake",
        "sha256:lean",
        "sha256:source",
        "4.20.0",
        None,
        "explicit",
        ("PATH",),
        environment,
        roots,
    )


def test_direct_execution_uses_existing_compiled_roots_without_lake(tmp_path: Path) -> None:
    local = tmp_path / ".lake" / "build" / "lib" / "lean"
    dependency = tmp_path / ".lake" / "packages" / "dep" / ".lake" / "build" / "lib" / "lean"
    local.mkdir(parents=True)
    dependency.mkdir(parents=True)
    (local / "Main.olean").write_bytes(b"compiled")
    marker = dependency / "Dependency.olean"
    marker.write_bytes(b"dependency")
    context = _toolchain(tmp_path)

    execution = prepare_direct_lean_execution(tmp_path, "Main", context)

    assert execution.command == (str(context.lean_path),)
    assert "lake" not in execution.command
    assert execution.library_roots == (local.resolve(), dependency.resolve())
    assert execution.environment["LEAN_PATH"].split(os.pathsep) == [
        str(local.resolve()),
        str(dependency.resolve()),
    ]
    assert marker.read_bytes() == b"dependency"


def test_direct_execution_fails_before_process_when_module_is_not_compiled(
    tmp_path: Path,
) -> None:
    (tmp_path / ".lake" / "build" / "lib" / "lean").mkdir(parents=True)
    context = _toolchain(tmp_path)

    with pytest.raises(LeanToolchainError, match="compiled module is unavailable"):
        prepare_direct_lean_execution(tmp_path, "Missing.Module", context)


def test_direct_execution_reports_missing_manifest_dependency_without_lake(
    tmp_path: Path,
) -> None:
    (tmp_path / ".lake" / "build" / "lib" / "lean").mkdir(parents=True)
    (tmp_path / "lake-manifest.json").write_text(
        json.dumps(
            {
                "packagesDir": ".lake/packages",
                "packages": [{"name": "mathlib", "type": "git"}],
            }
        ),
        encoding="utf-8",
    )
    context = _toolchain(tmp_path)

    with pytest.raises(
        DirectLeanPreflightError,
        match="mathlib; restore dependencies explicitly outside Ladon",
    ) as failure:
        prepare_direct_lean_execution(tmp_path, "Main", context)
    assert failure.value.code == "dependency-state-unavailable"
