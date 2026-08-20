"""Configured ProofIR artifact discovery and catalog normalization.

The catalog deliberately records identity and coverage only. Semantic adapters
own surfaces, replay provenance, and obligation graphs in later packets.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from ladon.proofir_identity import ContentArtifactId, FileDigest
from ladon.proofir_v3 import (
    LEGACY_ARTIFACT_KINDS,
    SUPPORTED_ARTIFACT_KINDS,
    ProofIRV3Error,
    validate_envelope,
)

PROOFIR_CONFIG_RELATIVE_PATH = ".ladon/proofir.json"
DEFAULT_LIMITS = {
    "maxFiles": 256,
    "maxArtifactBytes": 8 * 1024 * 1024,
    "maxTotalBytes": 64 * 1024 * 1024,
    "maxMetadataBytes": 16 * 1024,
}
CATALOG_STATES = frozenset({"cataloged", "unsupported", "malformed"})


class ProofIRCatalogError(ValueError):
    """Configured ProofIR inputs cannot be safely cataloged."""


@dataclass(frozen=True)
class ProofIRConfig:
    """Repository-owned bounded ProofIR input configuration."""

    configured: bool
    patterns: tuple[str, ...]
    limits: tuple[tuple[str, int], ...]
    relationships: tuple[tuple[str, str, str, str], ...] = ()

    @property
    def limit_map(self) -> dict[str, int]:
        return dict(self.limits)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "patterns": list(self.patterns),
            "limits": dict(self.limits),
            "relationships": [
                {"source": source, "target": target, "kind": kind, "details": details}
                for source, target, kind, details in self.relationships
            ],
        }


@dataclass(frozen=True)
class CatalogArtifact:
    """One bounded immutable artifact observation."""

    relative_path: str
    path: Path
    byte_size: int
    sha256: str
    artifact_kind: str
    schema_version: str
    state: str
    metadata_json: str
    diagnostic: str | None = None
    validation_stage: str = "projected"
    content_artifact_id: ContentArtifactId | None = None

    @property
    def file_digest(self) -> FileDigest:
        """Return the digest of the exact bytes captured for this path."""
        return FileDigest("sha256:" + self.sha256)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "path": self.relative_path,
            "bytes": self.byte_size,
            "sha256": self.sha256,
            "fileDigest": str(self.file_digest),
            "contentArtifactId": (
                str(self.content_artifact_id) if self.content_artifact_id else None
            ),
            "artifactKind": self.artifact_kind,
            "schemaVersion": self.schema_version,
            "state": self.state,
        }


def load_proofir_config(repo_root: Path) -> ProofIRConfig:
    """Load the optional repository-owned ProofIR manifest."""

    path = repo_root.resolve() / PROOFIR_CONFIG_RELATIVE_PATH
    if not path.exists():
        return ProofIRConfig(False, (), tuple(sorted(DEFAULT_LIMITS.items())))
    if not path.is_file():
        raise ProofIRCatalogError(f"ProofIR configuration is not a file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProofIRCatalogError(f"invalid ProofIR configuration: {path}") from exc
    if not isinstance(payload, dict):
        raise ProofIRCatalogError("ProofIR configuration must be a JSON object")
    patterns = _config_patterns(payload)
    limits = _config_limits(payload)
    relationships = _config_relationships(payload)
    return ProofIRConfig(
        True, patterns, tuple(sorted(limits.items())), tuple(sorted(relationships))
    )


def _config_patterns(payload: dict[str, Any]) -> tuple[str, ...]:
    raw = payload.get("artifacts", [])
    if not isinstance(raw, list) or not all(
        isinstance(pattern, str) and pattern for pattern in raw
    ):
        raise ProofIRCatalogError(
            "ProofIR configuration artifacts must be non-empty strings"
        )
    patterns = tuple(sorted(set(raw)))
    if any(Path(pattern).is_absolute() for pattern in patterns):
        raise ProofIRCatalogError("ProofIR artifact paths must be repository-relative")
    return patterns


def _config_limits(payload: dict[str, Any]) -> dict[str, int]:
    raw = payload.get("limits", {})
    if not isinstance(raw, dict):
        raise ProofIRCatalogError("ProofIR configuration limits must be an object")
    limits = dict(DEFAULT_LIMITS)
    for key, value in raw.items():
        if key not in limits or not isinstance(value, int) or value < 1:
            raise ProofIRCatalogError(f"invalid ProofIR limit: {key}")
        limits[key] = value
    return limits


def _config_relationships(
    payload: dict[str, Any],
) -> tuple[tuple[str, str, str, str], ...]:
    raw = payload.get("relationships", [])
    if not isinstance(raw, list):
        raise ProofIRCatalogError(
            "ProofIR configuration relationships must be an array"
        )
    rows = []
    for row in raw:
        if not isinstance(row, dict):
            raise ProofIRCatalogError("ProofIR relationships must be objects")
        source, target, kind = row.get("source"), row.get("target"), row.get("kind")
        if not all(
            isinstance(value, str) and value for value in (source, target, kind)
        ):
            raise ProofIRCatalogError(
                "ProofIR relationships require source, target, and kind"
            )
        source, target, kind = cast(tuple[str, str, str], (source, target, kind))
        rows.append(
            (
                source,
                target,
                kind,
                json.dumps(
                    row.get("details", {}), sort_keys=True, separators=(",", ":")
                ),
            )
        )
    return tuple(sorted(rows))


def discover_catalog_artifacts(
    repo_root: Path,
    config: ProofIRConfig | None = None,
) -> tuple[ProofIRConfig, tuple[CatalogArtifact, ...]]:
    """Expand configured paths and inspect bounded artifact identities."""

    root = repo_root.resolve()
    config = config or load_proofir_config(root)
    if not config.configured:
        return config, ()
    limit_map = config.limit_map
    paths = _expand_paths(root, config.patterns)
    if len(paths) > limit_map["maxFiles"]:
        raise ProofIRCatalogError(
            f"ProofIR file-count limit exceeded: {len(paths)} > {limit_map['maxFiles']}"
        )
    return config, tuple(_read_artifacts(root, sorted(paths), limit_map))


def _expand_paths(root: Path, patterns: tuple[str, ...]) -> set[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        matches = list(root.glob(pattern)) or (
            [root / pattern]
            if not any(character in pattern for character in "*?[")
            else []
        )
        for path in matches:
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                raise ProofIRCatalogError(
                    f"ProofIR artifact path escapes repository: {pattern}"
                )
            if resolved.is_file():
                paths.add(resolved)
    return paths


def _read_artifacts(
    root: Path, paths: list[Path], limits: dict[str, int]
) -> list[CatalogArtifact]:
    artifacts, total_bytes = [], 0
    for path in paths:
        raw = path.read_bytes()
        if len(raw) > limits["maxArtifactBytes"]:
            raise ProofIRCatalogError(
                f"ProofIR artifact byte limit exceeded: {path.relative_to(root)}"
            )
        total_bytes += len(raw)
        if total_bytes > limits["maxTotalBytes"]:
            raise ProofIRCatalogError(
                f"ProofIR total byte limit exceeded: {total_bytes} > {limits['maxTotalBytes']}"
            )
        artifacts.append(_inspect_artifact(root, path, raw, limits["maxMetadataBytes"]))
    return artifacts


def _inspect_artifact(
    root: Path,
    path: Path,
    raw: bytes,
    max_metadata_bytes: int,
) -> CatalogArtifact:
    """Inspect one artifact without retaining its raw payload."""

    relative = path.relative_to(root).as_posix()
    digest = hashlib.sha256(raw).hexdigest()
    decoded = _decode_artifact(relative, path, raw, digest)
    if isinstance(decoded, CatalogArtifact):
        return decoded
    payload = decoded
    kind = str(payload.get("artifactKind", ""))
    schema = str(payload.get("schemaVersion", payload.get("proofirVersion", "")))
    encoded, metadata_diagnostic = _bounded_metadata(payload, max_metadata_bytes)
    state, diagnostic, stage = _catalog_validation(
        payload, kind, schema, metadata_diagnostic
    )
    content_artifact_id = (
        ContentArtifactId(str(payload["artifactId"]))
        if state == "cataloged" and isinstance(payload.get("artifactId"), str)
        else None
    )
    return CatalogArtifact(
        relative,
        path,
        len(raw),
        digest,
        kind,
        schema,
        state,
        encoded,
        diagnostic,
        stage,
        content_artifact_id,
    )


def _decode_artifact(
    relative: str, path: Path, raw: bytes, digest: str
) -> dict[str, Any] | CatalogArtifact:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return CatalogArtifact(
            relative,
            path,
            len(raw),
            digest,
            "",
            "",
            "malformed",
            "{}",
            str(exc),
            "decoded",
        )
    if not isinstance(payload, dict):
        return CatalogArtifact(
            relative,
            path,
            len(raw),
            digest,
            "",
            "",
            "malformed",
            "{}",
            "top-level JSON is not an object",
            "envelope-valid",
        )
    return payload


def _bounded_metadata(
    payload: dict[str, Any], max_metadata_bytes: int
) -> tuple[str, str | None]:
    metadata = {
        key: payload[key]
        for key in ("module", "dagId", "provenanceId", "status", "guarantee", "checker")
        if key in payload
        and isinstance(payload[key], (str, int, float, bool, type(None)))
    }
    encoded = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    metadata_bytes = encoded.encode("utf-8")
    if len(metadata_bytes) <= max_metadata_bytes:
        return encoded, None
    sentinel = json.dumps(
        {
            "truncated": True,
            "originalBytes": len(metadata_bytes),
            "sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sentinel, "catalog metadata truncated"


def _catalog_validation(
    payload: dict[str, Any],
    kind: str,
    schema: str,
    metadata_diagnostic: str | None,
) -> tuple[str, str | None, str]:
    state = "cataloged" if _supported_kind_version(kind, schema) else "unsupported"
    if state == "cataloged":
        try:
            validate_envelope(payload)
        except ProofIRV3Error as exc:
            diagnostic = json.dumps(
                exc.diagnostic.to_dict(), sort_keys=True, separators=(",", ":")
            )
            return "malformed", diagnostic, exc.diagnostic.stage
        return "cataloged", metadata_diagnostic, "projected"
    diagnostic = _unsupported_diagnostic(
        kind, schema, artifact_id=str(payload.get("artifactId", "<unbound>"))
    )
    return "unsupported", diagnostic, "kind-schema-valid"


def _supported_kind_version(kind: str, schema: str) -> bool:
    """Accept only the closed native-v3 kind/version registry."""

    return schema == "3.0" and kind in SUPPORTED_ARTIFACT_KINDS


def _unsupported_diagnostic(kind: str, schema: str, *, artifact_id: str) -> str:
    """Return a stable diagnostic for retired v2/compatibility routes."""

    if kind in LEGACY_ARTIFACT_KINDS or kind == "proofir.compatibility.v2":
        diagnostic = {
            "artifactId": artifact_id,
            "stage": "kind-schema-valid",
            "code": "legacy-artifact-kind",
            "pointer": "/artifactKind",
            "message": f"legacy ProofIR artifact kind is unsupported: {kind}",
        }
    else:
        diagnostic = {
            "artifactId": artifact_id,
            "stage": "kind-schema-valid",
            "code": "unsupported-kind-version",
            "pointer": "/artifactKind" if kind else "/proofirVersion",
            "message": f"unsupported ProofIR kind/version: {kind!r}/{schema!r}",
        }
    return json.dumps(diagnostic, sort_keys=True, separators=(",", ":"))


def catalog_generation_identity(
    config: ProofIRConfig,
    artifacts: tuple[CatalogArtifact, ...],
) -> dict[str, Any]:
    """Return stable configuration/identity material for generation hashing."""

    return {
        "config": config.identity_payload(),
        "artifacts": [artifact.identity_payload() for artifact in artifacts],
    }


__all__ = [
    "CATALOG_STATES",
    "PROOFIR_CONFIG_RELATIVE_PATH",
    "CatalogArtifact",
    "ProofIRCatalogError",
    "ProofIRConfig",
    "catalog_generation_identity",
    "discover_catalog_artifacts",
    "load_proofir_config",
]
