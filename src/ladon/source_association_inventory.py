"""Source association inventory for exact source-to-compiled observations."""

from __future__ import annotations

import hashlib
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ladon.lean_toolchain import LeanToolchainContext
from ladon.proofir_v3 import (
    canonical_bytes,
)
from ladon.source_association_io import (
    _MODULE,
    MAX_AUXILIARY_OBSERVED_BYTES,
    MAX_COMPILED_ENVIRONMENT_BYTES,
    MAX_EVIDENCE_FILE_BYTES,
    MAX_MODULES,
    _AssociationError,
    _digest,
    _file_identity,
)


def _resolve_compiled_files(context: LeanToolchainContext, environment: Mapping[str, Any]) -> dict[str, Path]:
    rows = environment["payload"]["compiledModules"]
    if not rows or len(rows) > MAX_MODULES:
        raise _AssociationError("unavailable", "compiled-module-bound", "environment compiled-module list is empty or exceeds its item limit")
    roots = _compiled_roots(context)
    result: dict[str, Path] = {}
    for row in rows:
        module = row["module"]
        result[module] = _resolve_one_compiled_module(module, roots)
    return result


def _compiled_roots(context: LeanToolchainContext) -> tuple[Path, ...]:
    prefix_lib = context.lean_path.resolve().parent.parent / "lib" / "lean"
    return tuple(dict.fromkeys((*context.library_roots, prefix_lib.resolve())))


def _resolve_one_compiled_module(module: str, roots: Sequence[Path]) -> Path:
    if not _MODULE.fullmatch(module):
        raise _AssociationError("unavailable", "invalid-compiled-module", "environment contains a malformed module name")
    relative = Path(*module.split(".")).with_suffix(".olean")
    found = [root / relative for root in roots if (root / relative).is_file()]
    if len(found) != 1:
        raise _AssociationError("unavailable", "compiled-module-resolution", f"compiled module {module} is unavailable or ambiguous")
    path = found[0]
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise _AssociationError("unavailable", "compiled-module-path", f"compiled module {module} is not a regular file")
    if path.stat().st_size > MAX_EVIDENCE_FILE_BYTES:
        raise _AssociationError("unavailable", "compiled-byte-bound", "compiled environment exceeds its byte limit")
    return path.resolve()


def _inventory(files: Mapping[str, Path], environment: Mapping[str, Any]) -> dict[str, Any]:
    primary_hasher = hashlib.sha256()
    sidecar_hasher = hashlib.sha256()
    primary_bytes = 0
    sidecar_bytes = 0
    sidecar_count = 0
    recorded = {
        row["module"]: row["digest"]
        for row in environment["payload"]["compiledModules"]
    }
    for module, path in sorted(files.items()):
        reported_size = path.stat().st_size
        if reported_size > MAX_EVIDENCE_FILE_BYTES:
            raise _AssociationError("unavailable", "compiled-byte-bound", "compiled evidence file exceeds its per-file byte limit")
        if primary_bytes + reported_size > MAX_COMPILED_ENVIRONMENT_BYTES:
            raise _AssociationError("unavailable", "compiled-byte-bound", "primary compiled modules exceed their byte limit")
        primary_digest, size = _file_identity(path)
        primary_bytes += size
        if primary_bytes > MAX_COMPILED_ENVIRONMENT_BYTES:
            raise _AssociationError("unavailable", "compiled-byte-bound", "primary compiled modules exceed their byte limit")
        if primary_digest != recorded[module]:
            raise _AssociationError("stale", "compiled-module-stale", f"compiled module {module} differs from its canonical digest")
        primary_hasher.update(f"{module}\0{primary_digest}\0{size}\n".encode())
        sidecars = (
            (".server", Path(str(path) + ".server")),
            (".private", Path(str(path) + ".private")),
            (".ir", path.with_suffix(".ir")),
            (".ir.sig", path.with_suffix(".ir.sig")),
        )
        for suffix, candidate in sidecars:
            try:
                candidate.lstat()
            except FileNotFoundError:
                sidecar_hasher.update(f"{module}\0{suffix}\0absent\n".encode())
                continue
            digest, size = _file_identity(candidate)
            sidecar_count += 1
            sidecar_bytes += size
            if sidecar_bytes > MAX_AUXILIARY_OBSERVED_BYTES:
                raise _AssociationError("unavailable", "sidecar-byte-bound", "compiled sidecars exceed the auxiliary observation limit")
            sidecar_hasher.update(f"{module}\0{suffix}\0{digest}\0{size}\n".encode())
    primary_digest = "sha256:" + primary_hasher.hexdigest()
    sidecar_digest = "sha256:" + sidecar_hasher.hexdigest()
    return {
        "moduleCount": len(files),
        "primaryBytes": primary_bytes,
        "primaryDigest": primary_digest,
        "sidecarCount": sidecar_count,
        "sidecarBytes": sidecar_bytes,
        "sidecarSnapshotDigest": sidecar_digest,
        "snapshotDigest": _digest(canonical_bytes({
            "modules": len(files),
            "primaryBytes": primary_bytes,
            "primaryDigest": primary_digest,
            "sidecars": sidecar_count,
            "sidecarBytes": sidecar_bytes,
            "sidecarSnapshotDigest": sidecar_digest,
        })),
    }


def _recorded_module(environment: Mapping[str, Any], module: str) -> Mapping[str, Any]:
    rows = [row for row in environment["payload"]["compiledModules"] if row["module"] == module]
    if len(rows) != 1:
        raise _AssociationError("unavailable", "owner-module-missing", "environment does not contain the selected module exactly once")
    return rows[0]
