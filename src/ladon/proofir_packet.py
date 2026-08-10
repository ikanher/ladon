"""Content-addressed evidence manifests for ProofIR review packets.

The packet manifest is deliberately a small, filesystem-only projection.  It
does not claim that a command succeeded; command records retain exit status and
the hashes of bounded stdout/stderr logs so a reviewer can replay or reject it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _untracked_content_digest(root: Path) -> str:
    """Hash untracked paths together with their current bytes, not names alone."""

    rows = []
    for relative in filter(None, _git(root, "ls-files", "--others", "--exclude-standard").splitlines()):
        path = root / relative
        if path.is_file():
            rows.append(
                {
                    "path": relative,
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_packet_manifest(
    root: Path, files: Iterable[tuple[str, str, str]], *, builder: str = "ladon"
) -> dict[str, Any]:
    """Build a deterministic inventory with source-state provenance.

    ``files`` contains ``(relative path, role, source classification)``.  A
    missing path is an error: omission must be visible at packet construction,
    not discovered by a reviewer after extraction.
    """
    root = Path(root).resolve()
    entries = []
    for relative, role, classification in sorted(files):
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        entries.append(
            {
                "path": relative,
                "role": role,
                "source": classification,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    lock_files = []
    for name in ("lean-toolchain", "lake-manifest.json", "pyproject.toml", "uv.lock"):
        path = root / name
        if path.is_file():
            lock_files.append({"path": name, "bytes": path.stat().st_size, "sha256": _sha256(path)})
    manifest = {
        "format": "proofir-review-packet-manifest-v2",
        "builder": builder,
        # Observation time is provenance only; identity is derived from the
        # deterministic inventory below and never from this timestamp.
        "observedAt": datetime.now(UTC).isoformat(),
        "files": entries,
        "sourceState": {
            "head": _git(root, "rev-parse", "HEAD") or "unavailable",
            "dirtyTreeDigest": hashlib.sha256(_git(root, "diff", "--binary").encode()).hexdigest(),
            "untrackedDigest": _untracked_content_digest(root),
            "toolchainFiles": lock_files,
        },
        "strictInventory": True,
    }
    manifest["inventoryDigest"] = _inventory_digest(manifest)
    return manifest


def _inventory_digest(manifest: dict[str, Any]) -> str:
    identity = {key: value for key, value in manifest.items() if key not in {"inventoryDigest", "observedAt"}}
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_packet_manifest(root: Path, manifest: dict[str, Any]) -> None:
    """Fail closed on an incomplete, stale, or vacuous packet manifest."""
    _validate_manifest_header(manifest)
    seen: set[str] = set()
    for entry in manifest["files"]:
        relative = _validate_manifest_entry(entry, seen)
        path = Path(root) / relative
        if not path.is_file():
            raise ValueError(f"packet file missing: {relative}")
        if path.stat().st_size != entry["bytes"] or _sha256(path) != entry["sha256"]:
            raise ValueError(f"packet file changed: {relative}")
    actual = {
        path.relative_to(root).as_posix()
        for path in Path(root).rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() != "data/content-manifest.json"
    }
    extra = sorted(actual - seen)
    if extra:
        raise ValueError(f"packet contains unadvertised file: {extra[0]}")


def _validate_manifest_header(manifest: dict[str, Any]) -> None:
    if manifest.get("format") != "proofir-review-packet-manifest-v2":
        raise ValueError("unsupported or legacy packet manifest format")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("packet manifest must advertise a non-empty files collection")
    if manifest.get("inventoryDigest") != _inventory_digest(manifest):
        raise ValueError("packet manifest inventory digest is invalid")


def _validate_manifest_entry(entry: Any, seen: set[str]) -> str:
    _require_manifest_shape(entry)
    relative = str(entry["path"])
    _require_manifest_path(relative, seen)
    seen.add(relative)
    _require_manifest_metadata(entry, relative)
    return relative


def _require_manifest_shape(entry: Any) -> None:
    if not isinstance(entry, dict) or set(entry) != {"path", "role", "source", "bytes", "sha256"}:
        raise ValueError("packet manifest contains an invalid file entry")


def _require_manifest_path(relative: str, seen: set[str]) -> None:
    if relative in seen or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"packet manifest contains an unsafe or duplicate path: {relative}")


def _require_manifest_metadata(entry: dict[str, Any], relative: str) -> None:
    if not isinstance(entry["role"], str) or not entry["role"] or not isinstance(entry["source"], str) or not entry["source"]:
        raise ValueError(f"packet manifest contains invalid metadata: {relative}")
    if not isinstance(entry["bytes"], int) or entry["bytes"] < 0 or not isinstance(entry["sha256"], str) or len(entry["sha256"]) != 64:
        raise ValueError(f"packet manifest contains invalid digest metadata: {relative}")


__all__ = ["build_packet_manifest", "verify_packet_manifest"]
