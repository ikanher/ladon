"""Deterministic, path-safe materialization of theorem-capsule plans."""

from __future__ import annotations

import gzip
import os
import shutil
import stat
import tarfile
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from ladon.target_build import TargetPreflightError, validate_target_repository
from ladon.theorem_capsule_inventory import discover_capsule_layout
from ladon.theorem_capsule_models import (
    GUARANTEE_LEVEL,
    NONCLAIMS,
    CapsuleContentError,
    CapsuleInvocationError,
    CapsuleManifest,
    CapsuleOperationalError,
    TheoremPlan,
    sha256_bytes,
)


MANIFEST_NAME = "capsule.json"
PLAN_NAME = "plan.json"
ARCHIVE_SUFFIXES = (".tar", ".tar.gz", ".tgz")
NORMALIZED_FILE_MODE = 0o644


def materialize_theorem_capsule(
    plan: TheoremPlan,
    output: Path,
) -> CapsuleManifest:
    """Publish one validated capsule directory or reproducible tar archive."""

    if not plan.eligible:
        kinds = ", ".join(
            str(row.get("kind"))
            for row in _rows(plan.payload.get("unsupportedFacets"))
        )
        raise CapsuleContentError(
            f"plan is ineligible for locked/rebuildable materialization: {kinds}"
        )
    repo_root = _plan_repository_root(plan)
    destination = _safe_destination(repo_root, output)
    _validate_plan_inputs(plan, repo_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.staging-",
            dir=destination.parent,
        )
    )
    archive_temporary: Path | None = None
    try:
        inventory = _populate_stage(plan, repo_root, stage)
        manifest = _write_manifest(plan, stage, inventory, destination)
        _verify_stage_accounting(stage, manifest)
        if _is_archive(destination):
            archive_temporary = _archive_temporary_path(destination)
            _write_reproducible_archive(stage, archive_temporary, destination)
            os.replace(archive_temporary, destination)
            archive_temporary = None
            shutil.rmtree(stage)
        else:
            os.replace(stage, destination)
        return manifest
    except Exception:
        if archive_temporary is not None:
            archive_temporary.unlink(missing_ok=True)
        if stage.exists():
            shutil.rmtree(stage)
        raise


def _plan_repository_root(plan: TheoremPlan) -> Path:
    raw = plan.repository.get("root")
    if not isinstance(raw, str) or not Path(raw).is_absolute():
        raise CapsuleContentError("plan repository root is not an absolute path")
    try:
        return validate_target_repository(Path(raw))
    except TargetPreflightError as exc:
        raise CapsuleOperationalError(str(exc)) from exc


def _safe_destination(repo_root: Path, output: Path) -> Path:
    if not output.name:
        raise CapsuleInvocationError("capsule output path is empty")
    destination = output.absolute()
    if destination.exists():
        raise CapsuleInvocationError(f"capsule output already exists: {destination}")
    resolved = destination.resolve(strict=False)
    if resolved == repo_root or resolved.is_relative_to(repo_root):
        raise CapsuleInvocationError(
            "capsule output must be outside the target repository"
        )
    return destination


def _validate_plan_inputs(plan: TheoremPlan, repo_root: Path) -> None:
    current = discover_capsule_layout(repo_root)
    if current.fingerprint != plan.repository["layoutFingerprint"]:
        raise CapsuleContentError(
            "repository module layout changed; create a new plan"
        )
    seen_paths: set[str] = set()
    collision_keys: set[str] = set()
    for row in (*plan.files, *plan.configuration_files):
        relative = _normalized_relative_path(row.get("path"))
        _reject_collision(relative, seen_paths, collision_keys)
        source = _safe_source(repo_root, relative)
        content = source.read_bytes()
        expected = row.get("sourceSha256", row.get("sha256"))
        if expected != sha256_bytes(content):
            raise CapsuleContentError(f"planned input changed: {relative}")


def _normalized_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise CapsuleContentError("capsule path is malformed")
    if "\\" in value:
        raise CapsuleContentError(f"capsule path uses an unsafe separator: {value}")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise CapsuleContentError(f"capsule path escapes its root: {value}")
    return pure.as_posix()


def _reject_collision(
    path: str,
    seen_paths: set[str],
    collision_keys: set[str],
) -> None:
    key = unicodedata.normalize("NFC", path).casefold()
    if path in seen_paths or key in collision_keys:
        raise CapsuleContentError(f"capsule paths collide: {path}")
    seen_paths.add(path)
    collision_keys.add(key)


def _safe_source(repo_root: Path, relative: str) -> Path:
    path = repo_root / relative
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CapsuleContentError(f"planned input is unavailable: {relative}") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise CapsuleContentError(f"planned input is a symbolic link: {relative}")
    if not stat.S_ISREG(metadata.st_mode):
        raise CapsuleContentError(f"planned input is not a regular file: {relative}")
    resolved = path.resolve()
    if not resolved.is_relative_to(repo_root):
        raise CapsuleContentError(f"planned input escapes repository: {relative}")
    return path


def _populate_stage(
    plan: TheoremPlan,
    repo_root: Path,
    stage: Path,
) -> tuple[dict[str, Any], ...]:
    inventory: list[dict[str, Any]] = []
    _write_stage_file(
        stage,
        PLAN_NAME,
        plan.to_bytes(),
        role="plan",
        reason="validated_materialization_authority",
        origin="generated_from_plan",
        inventory=inventory,
    )
    for row in plan.configuration_files:
        relative = _normalized_relative_path(row["path"])
        _write_stage_file(
            stage,
            relative,
            _safe_source(repo_root, relative).read_bytes(),
            role=str(row["role"]),
            reason="pinned_build_configuration",
            origin=relative,
            inventory=inventory,
        )
    for row in plan.files:
        _copy_planned_source(plan, row, repo_root, stage, inventory)
    return tuple(sorted(inventory, key=lambda row: str(row["path"])))


def _copy_planned_source(
    plan: TheoremPlan,
    row: Mapping[str, Any],
    repo_root: Path,
    stage: Path,
    inventory: list[dict[str, Any]],
) -> None:
    relative = _normalized_relative_path(row["path"])
    content = _safe_source(repo_root, relative).read_bytes()
    if row.get("role") == "target_prefix":
        prefix_end = plan.target["prefixEndOffset"]
        if not isinstance(prefix_end, int) or prefix_end > len(content):
            raise CapsuleContentError("target prefix boundary is outside source bytes")
        content = content[:prefix_end]
    if sha256_bytes(content) != row.get("materializedSha256"):
        raise CapsuleContentError(f"materialized bytes disagree with plan: {relative}")
    _write_stage_file(
        stage,
        relative,
        content,
        role=str(row["role"]),
        reason=str(row["inclusionReason"]),
        origin=relative,
        inventory=inventory,
        module=str(row["module"]),
    )


def _write_stage_file(
    stage: Path,
    relative: str,
    content: bytes,
    *,
    role: str,
    reason: str,
    origin: str,
    inventory: list[dict[str, Any]],
    module: str | None = None,
) -> None:
    destination = stage / _normalized_relative_path(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    destination.chmod(NORMALIZED_FILE_MODE)
    row: dict[str, Any] = {
        "path": relative,
        "role": role,
        "inclusionReason": reason,
        "origin": origin,
        "sha256": sha256_bytes(content),
        "bytes": len(content),
        "mode": "0644",
    }
    if module is not None:
        row["module"] = module
    inventory.append(row)


def _write_manifest(
    plan: TheoremPlan,
    stage: Path,
    inventory: tuple[dict[str, Any], ...],
    destination: Path,
) -> CapsuleManifest:
    manifest = CapsuleManifest.create(
        {
            "status": "materialized_unverified",
            "guaranteeLevel": GUARANTEE_LEVEL,
            "planIdentity": plan.identity,
            "target": dict(plan.target),
            "sourceRoots": list(plan.repository.get("sourceRoots", [])),
            "semanticClosureIdentity": plan.payload["semanticGraph"][
                "closureFingerprint"
            ],
            "buildGraph": dict(plan.payload["buildGraph"]),
            "externalFrontier": list(
                plan.payload["buildGraph"].get("externalImports", [])
            ),
            "outputKind": "archive" if _is_archive(destination) else "directory",
            "files": list(inventory),
            "manifestAccounting": {
                "path": MANIFEST_NAME,
                "role": "manifest",
                "hashMode": "capsule_identity_over_canonical_manifest_body",
            },
            "expectedReplay": {
                "theorem": plan.target["name"],
                "toolchain": dict(plan.payload["toolchain"]),
                "semanticClosureIdentity": plan.payload["semanticGraph"][
                    "closureFingerprint"
                ],
            },
            "unsupportedFacets": list(plan.payload.get("unsupportedFacets", [])),
            "nonclaims": list(NONCLAIMS),
        }
    )
    path = stage / MANIFEST_NAME
    path.write_bytes(manifest.to_bytes())
    path.chmod(NORMALIZED_FILE_MODE)
    return manifest


def _verify_stage_accounting(
    stage: Path,
    manifest: CapsuleManifest,
) -> None:
    expected = {
        MANIFEST_NAME,
        *(str(row["path"]) for row in manifest.files),
    }
    actual = {
        path.relative_to(stage).as_posix()
        for path in stage.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise CapsuleContentError(
            "staged capsule contains missing or unaccounted files"
        )


def _is_archive(path: Path) -> bool:
    return any(str(path).endswith(suffix) for suffix in ARCHIVE_SUFFIXES)


def _archive_temporary_path(destination: Path) -> Path:
    handle, raw = tempfile.mkstemp(
        prefix=f".{destination.name}.archive-",
        dir=destination.parent,
    )
    os.close(handle)
    return Path(raw)


def _write_reproducible_archive(
    stage: Path,
    temporary: Path,
    destination: Path,
) -> None:
    if str(destination).endswith((".tar.gz", ".tgz")):
        with temporary.open("wb") as output:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=output,
                mtime=0,
            ) as compressed:
                _write_tar(stage, compressed)
        return
    with temporary.open("wb") as output:
        _write_tar(stage, output)


def _write_tar(stage: Path, output: Any) -> None:
    with tarfile.open(fileobj=output, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path in sorted(item for item in stage.rglob("*") if item.is_file()):
            relative = path.relative_to(stage).as_posix()
            content = path.read_bytes()
            info = tarfile.TarInfo(relative)
            info.size = len(content)
            info.mode = NORMALIZED_FILE_MODE
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, _bytes_reader(content))


def _bytes_reader(content: bytes):
    import io

    return io.BytesIO(content)


def _rows(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise CapsuleContentError("plan row collection is malformed")
    return tuple(value)


__all__ = ["materialize_theorem_capsule"]
