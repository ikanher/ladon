"""Observe the complete loaded import inventory around source elaboration."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.lean_toolchain import LeanToolchainContext
from ladon.source_association_inventory import (
    _compiled_roots,
    _inventory,
    _resolve_one_compiled_module,
)
from ladon.source_association_io import (
    MAX_COMPILED_ENVIRONMENT_BYTES,
    MAX_MODULES,
    _AssociationError,
    _file_identity,
)


def capture_inventory(
    context: LeanToolchainContext, frame: Mapping[str, Any],
) -> tuple[dict[str, Path], dict[str, Any], dict[str, Any]]:
    names = frame["importedModules"]
    if not names or len(names) > MAX_MODULES or len(names) != len(set(names)):
        raise _AssociationError("unavailable", "compiled-closure", "import closure is empty, duplicate or oversized")
    roots = _compiled_roots(context)
    files = {row["module"]: _bound_path(row, roots) for row in frame["compiledModulePaths"]}
    if sum(path.stat().st_size for path in files.values()) > MAX_COMPILED_ENVIRONMENT_BYTES:
        raise _AssociationError("unavailable", "compiled-byte-bound", "compiled import closure exceeds its byte limit")
    recorded = [{"module": name, "digest": _file_identity(path)[0]} for name, path in files.items()]
    environment = {"payload": {"compiledModules": recorded}}
    inventory = _inventory(files, environment)
    inventory["modules"] = [
        {"module": row["module"], "path": str(files[row["module"]]), "digest": row["digest"]}
        for row in sorted(recorded, key=lambda row: row["module"])
    ]
    return files, environment, inventory


def _bound_path(row: Mapping[str, str], roots: tuple[Path, ...]) -> Path:
    resolved = _resolve_one_compiled_module(row["module"], roots)
    observed = Path(row["path"])
    if (
        not observed.is_absolute() or observed.is_symlink()
        or observed.resolve(strict=True) != resolved
    ):
        raise _AssociationError("unavailable", "compiled-path-mismatch", "Lean resolved an import outside its unique selected root")
    return resolved


def verify_inventory(
    files: Mapping[str, Path], environment: Mapping[str, Any], before: Mapping[str, Any],
) -> None:
    expected = {key: value for key, value in before.items() if key != "modules"}
    if _inventory(files, environment) != expected:
        raise _AssociationError("stale", "compiled-inventory-changed", "compiled module or sidecar inventory changed during capture")
