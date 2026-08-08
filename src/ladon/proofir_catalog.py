"""Configured ProofIR artifact discovery and catalog normalization.

The catalog deliberately records identity and coverage only. Semantic adapters
own surfaces, replay provenance, and obligation graphs in later packets.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROOFIR_CONFIG_RELATIVE_PATH = ".ladon/proofir.json"
SUPPORTED_CATALOG_KINDS = frozenset(
    {
        "proofir_bridge_index",
        "proof_ir_lean_surface_bundle",
        "proof_ir_lean_replay_provenance",
        "proof_ir_v2_obligation_dag",
        "proof_ir_v2_obligation_dag_check_witness",
    }
)
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

    def identity_payload(self) -> dict[str, Any]:
        return {
            "path": self.relative_path,
            "bytes": self.byte_size,
            "sha256": self.sha256,
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
    raw_patterns = payload.get("artifacts", [])
    if not isinstance(raw_patterns, list) or not all(
        isinstance(pattern, str) and pattern for pattern in raw_patterns
    ):
        raise ProofIRCatalogError("ProofIR configuration artifacts must be non-empty strings")
    patterns = tuple(sorted(set(raw_patterns)))
    if any(Path(pattern).is_absolute() for pattern in patterns):
        raise ProofIRCatalogError("ProofIR artifact paths must be repository-relative")
    raw_limits = payload.get("limits", {})
    if not isinstance(raw_limits, dict):
        raise ProofIRCatalogError("ProofIR configuration limits must be an object")
    limits = dict(DEFAULT_LIMITS)
    for key, value in raw_limits.items():
        if key not in limits or not isinstance(value, int) or value < 1:
            raise ProofIRCatalogError(f"invalid ProofIR limit: {key}")
        limits[key] = value
    raw_relationships = payload.get("relationships", [])
    if not isinstance(raw_relationships, list):
        raise ProofIRCatalogError("ProofIR configuration relationships must be an array")
    relationships: list[tuple[str, str, str, str]] = []
    for row in raw_relationships:
        if not isinstance(row, dict):
            raise ProofIRCatalogError("ProofIR relationships must be objects")
        source = row.get("source")
        target = row.get("target")
        kind = row.get("kind")
        if not all(isinstance(value, str) and value for value in (source, target, kind)):
            raise ProofIRCatalogError("ProofIR relationships require source, target, and kind")
        details = json.dumps(row.get("details", {}), sort_keys=True, separators=(",", ":"))
        relationships.append((source, target, kind, details))
    return ProofIRConfig(True, patterns, tuple(sorted(limits.items())), tuple(sorted(relationships)))


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
    paths: set[Path] = set()
    for pattern in config.patterns:
        matches = list(root.glob(pattern))
        if not matches and not any(character in pattern for character in "*?["):
            matches = [root / pattern]
        for path in matches:
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                raise ProofIRCatalogError(
                    f"ProofIR artifact path escapes repository: {pattern}"
                )
            if resolved.is_file():
                paths.add(resolved)
    if len(paths) > limit_map["maxFiles"]:
        raise ProofIRCatalogError(
            f"ProofIR file-count limit exceeded: {len(paths)} > {limit_map['maxFiles']}"
        )
    artifacts: list[CatalogArtifact] = []
    total_bytes = 0
    for path in sorted(paths):
        raw = path.read_bytes()
        size = len(raw)
        if size > limit_map["maxArtifactBytes"]:
            raise ProofIRCatalogError(
                f"ProofIR artifact byte limit exceeded: {path.relative_to(root)}"
            )
        total_bytes += size
        if total_bytes > limit_map["maxTotalBytes"]:
            raise ProofIRCatalogError(
                f"ProofIR total byte limit exceeded: {total_bytes} > {limit_map['maxTotalBytes']}"
            )
        artifacts.append(_inspect_artifact(root, path, raw, limit_map["maxMetadataBytes"]))
    return config, tuple(artifacts)


def _inspect_artifact(
    root: Path,
    path: Path,
    raw: bytes,
    max_metadata_bytes: int,
) -> CatalogArtifact:
    """Inspect one artifact without retaining its raw payload."""

    relative = path.relative_to(root).as_posix()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return CatalogArtifact(
            relative, path, len(raw), digest, "", "", "malformed", "{}", str(exc)
        )
    if not isinstance(payload, dict):
        return CatalogArtifact(
            relative, path, len(raw), digest, "", "", "malformed", "{}", "top-level JSON is not an object"
        )
    kind = str(payload.get("artifactKind", ""))
    schema = str(payload.get("schemaVersion", ""))
    metadata = {
        key: payload[key]
        for key in ("module", "dagId", "provenanceId", "status", "guarantee", "checker")
        if key in payload and isinstance(payload[key], (str, int, float, bool, type(None)))
    }
    encoded = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > max_metadata_bytes:
        encoded = encoded.encode("utf-8")[:max_metadata_bytes].decode("utf-8", errors="ignore")
        diagnostic = "catalog metadata truncated"
    else:
        diagnostic = None
    state = "cataloged" if kind in SUPPORTED_CATALOG_KINDS else "unsupported"
    return CatalogArtifact(relative, path, len(raw), digest, kind, schema, state, encoded, diagnostic)


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
    "CatalogArtifact",
    "ProofIRCatalogError",
    "ProofIRConfig",
    "PROOFIR_CONFIG_RELATIVE_PATH",
    "SUPPORTED_CATALOG_KINDS",
    "catalog_generation_identity",
    "discover_catalog_artifacts",
    "load_proofir_config",
]
