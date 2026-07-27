"""Versioned, caller-supplied changed-set manifest input.

This reader performs local data decoding only.  In particular, a revision-like
string is treated as a manifest path; this module never invokes a version
control command to discover changes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


CHANGED_SET_MANIFEST_SCHEMA = "ladon-changed-set-v1"


@dataclass(frozen=True)
class CapturedChangedSetManifest:
    """One immutable changed-set document captured from a physical path."""

    content: bytes | None
    status: str
    error: str | None = None


@dataclass(frozen=True)
class ChangedSetManifest:
    """Normalized manifest paths, caller authority, and input diagnostics."""

    paths: tuple[str, ...]
    authority: Mapping[str, Any]
    diagnostics: tuple[Mapping[str, Any], ...]


ChangedSetManifestSource = (
    CapturedChangedSetManifest | str | Path | Mapping[str, Any]
)


def capture_changed_set_manifest(path: str | Path) -> CapturedChangedSetManifest:
    """Read one physical manifest once for later immutable consumption."""

    source = Path(path)
    try:
        return CapturedChangedSetManifest(source.read_bytes(), "present")
    except FileNotFoundError as exc:
        return CapturedChangedSetManifest(None, "absent", str(exc))
    except OSError as exc:
        return CapturedChangedSetManifest(None, "unreadable", str(exc))


def read_changed_set_manifest(
    source: ChangedSetManifestSource,
) -> ChangedSetManifest:
    """Read one versioned manifest without consulting repository state."""

    payload, encoded, diagnostics = _manifest_document(source)
    schema = payload.get("schema")
    if schema != CHANGED_SET_MANIFEST_SCHEMA:
        diagnostics.append(_version_diagnostic(schema))
    paths, path_diagnostics = _manifest_paths(
        payload.get("paths", payload.get("changedPaths", []))
    )
    diagnostics.extend(path_diagnostics)
    return ChangedSetManifest(
        tuple(paths),
        _manifest_authority(payload, schema, encoded),
        tuple(diagnostics),
    )


def _manifest_document(
    source: ChangedSetManifestSource,
) -> tuple[dict[str, Any], bytes, list[dict[str, Any]]]:
    if isinstance(source, CapturedChangedSetManifest):
        if source.content is None:
            return {}, b"", [
                _diagnostic(
                    "scope.changed_manifest_invalid",
                    f"Cannot read changed-set manifest: {source.error}",
                )
            ]
        return _decode_manifest_bytes(source.content)
    try:
        if isinstance(source, Mapping):
            payload = dict(source)
            encoded = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        else:
            return _decode_manifest_bytes(Path(source).read_bytes())
    except (OSError, TypeError, ValueError) as exc:
        return {}, b"", [
            _diagnostic(
                "scope.changed_manifest_invalid",
                f"Cannot read changed-set manifest: {exc}",
            )
        ]
    return payload, encoded, []


def _decode_manifest_bytes(
    encoded: bytes,
) -> tuple[dict[str, Any], bytes, list[dict[str, Any]]]:
    """Decode captured bytes without reopening their physical source."""

    try:
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        return {}, b"", [
            _diagnostic(
                "scope.changed_manifest_invalid",
                f"Cannot read changed-set manifest: {exc}",
            )
        ]
    payload = decoded if isinstance(decoded, dict) else {}
    return payload, encoded, []


def _version_diagnostic(schema: Any) -> dict[str, Any]:
    return _diagnostic(
        "scope.changed_manifest_version",
        (
            f"Changed-set manifest schema must be "
            f"{CHANGED_SET_MANIFEST_SCHEMA!r}; got {schema!r}."
        ),
    )


def _manifest_paths(
    raw_paths: Any,
) -> tuple[list[str], list[dict[str, Any]]]:
    if not isinstance(raw_paths, list):
        return [], [
            _diagnostic(
                "scope.changed_manifest_paths",
                "Changed-set manifest paths must be a list.",
            )
        ]
    paths: list[str] = []
    diagnostics: list[dict[str, Any]] = []
    for row in raw_paths:
        if isinstance(row, str):
            paths.append(row)
        elif isinstance(row, Mapping) and isinstance(row.get("path"), str):
            paths.append(str(row["path"]))
        else:
            diagnostics.append(
                _diagnostic(
                    "scope.changed_manifest_path",
                    (
                        "Changed-set manifest contains a path row without a "
                        "string path."
                    ),
                )
            )
    return paths, diagnostics


def _manifest_authority(
    payload: Mapping[str, Any],
    schema: Any,
    encoded: bytes,
) -> dict[str, Any]:
    authority: dict[str, Any] = {
        "kind": "caller_manifest",
        "manifestSchema": schema,
        "manifestSha256": hashlib.sha256(encoded).hexdigest() if encoded else None,
    }
    supplied_identity = payload.get("identity")
    if isinstance(supplied_identity, Mapping):
        authority["suppliedIdentity"] = _json_compatible_mapping(
            supplied_identity
        )
    return authority


def _json_compatible_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        normalized = json.loads(
            json.dumps(
                dict(value),
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )
    except (TypeError, ValueError):
        return {"status": "unavailable", "reason": "unfingerprintable_identity"}
    return normalized if isinstance(normalized, dict) else {}


def _diagnostic(identifier: str, message: str) -> dict[str, Any]:
    return {
        "id": identifier,
        "severity": "error",
        "message": message,
    }
