"""Atomic durable storage for runset reports, state, and bundles."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from ladon.runset_contract import (
    STATE_ARTIFACT_KIND,
    STATE_SCHEMA,
    STATE_SCHEMA_VERSION,
    BundleEntry,
    RunsetManifest,
    canonical_json_bytes,
)


RUNSET_STATE_NAME = ".ladon-runset-state.json"


def load_state(path: Path, manifest: RunsetManifest) -> dict[str, Any]:
    """Load compatible durable state or start an inspectible empty state."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_state(manifest)
    if not _state_header_matches(payload, manifest):
        return empty_state(manifest)
    return payload


def _state_header_matches(payload: Any, manifest: RunsetManifest) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("artifactKind") == STATE_ARTIFACT_KIND
        and payload.get("schema") == STATE_SCHEMA
        and payload.get("schemaVersion") == STATE_SCHEMA_VERSION
        and payload.get("name") == manifest.name
        and payload.get("runsetFingerprint") == manifest.fingerprint
        and isinstance(payload.get("entries"), dict)
    )


def empty_state(manifest: RunsetManifest) -> dict[str, Any]:
    """Return a new versioned state document."""

    return {
        "artifactKind": STATE_ARTIFACT_KIND,
        "schema": STATE_SCHEMA,
        "schemaVersion": STATE_SCHEMA_VERSION,
        "name": manifest.name,
        "runsetFingerprint": manifest.fingerprint,
        "entries": {},
    }


def commit_state_entry(
    path: Path,
    state: dict[str, Any],
    manifest: RunsetManifest,
    entry: BundleEntry,
) -> None:
    """Atomically commit state after one terminal entry."""

    state["runsetFingerprint"] = manifest.fingerprint
    rows = state["entries"]
    payload = entry.to_payload()
    if entry.status == "resume-hit":
        payload["status"] = "complete"
    rows[entry.identifier] = payload
    atomic_write_bytes(path, canonical_json_bytes(state))


def atomic_write_bytes(
    path: Path,
    content: bytes,
    *,
    max_bytes: int | None = None,
) -> None:
    """Commit bytes by replace only after limits, flush, and file fsync."""

    if max_bytes is not None and len(content) > max_bytes:
        raise ValueError(
            f"artifact has {len(content)} bytes, exceeding limit {max_bytes}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def fsync_directory(path: Path) -> None:
    """Flush the containing directory when the platform supports it."""

    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
