"""Append-only content registry for live semantic ProofIR evidence.

The lexical proof-search index is an atomically replaced repository generation.
Semantic checks have a different lifetime: many checks can share one exact Lean
environment and arrive incrementally. This public facade owns transaction and
input boundaries; private modules own SQLite lifecycle and artifact projection.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ladon._semantic_evidence_registry_artifacts import (
    SemanticArtifactRepository,
    registration_result,
    validated_incoming,
)
from ladon._semantic_evidence_registry_sqlite import SemanticRegistryDatabase
from ladon._semantic_evidence_registry_types import (
    DEFAULT_BUSY_TIMEOUT_MS,
    DEFAULT_MAX_DATABASE_BYTES,
    MIN_DATABASE_BYTES,
    REGISTRY_APPLICATION_ID,
    REGISTRY_SCHEMA,
    REGISTRY_SCHEMA_VERSION,
    SEMANTIC_EVIDENCE_CACHE_VERSION,
    SemanticEvidenceRegistryBusy,
    SemanticEvidenceRegistryCapacity,
    SemanticEvidenceRegistryConflict,
    SemanticEvidenceRegistryError,
    SemanticEvidenceRegistryNotFound,
    SemanticEvidenceRegistrySchemaError,
    raise_registry_operational_error,
)
from ladon.proofir_v3 import MAX_ARTIFACTS, validate_envelope_batch

_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")


class SemanticEvidenceRegistry:
    """One explicit-path, append-only registry for canonical ProofIR envelopes."""

    def __init__(
        self,
        path: Path,
        *,
        max_database_bytes: int = DEFAULT_MAX_DATABASE_BYTES,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    ) -> None:
        _validate_limits(max_database_bytes, busy_timeout_ms)
        requested = Path(path).expanduser()
        _validate_requested_path(requested)
        self.path = requested.resolve()
        self.max_database_bytes = max_database_bytes
        self.busy_timeout_ms = busy_timeout_ms
        self._database = SemanticRegistryDatabase(
            self.path,
            max_database_bytes=max_database_bytes,
            busy_timeout_ms=busy_timeout_ms,
        )
        self._database.initialize()

    def register_bundle(self, artifacts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Atomically append a closed bundle, hydrating already-stored references."""

        _validate_bundle_container(artifacts)
        incoming = validated_incoming(artifacts)
        connection = self._database.connect()
        try:
            result = self._register_transaction(connection, incoming)
        except BaseException as error:
            connection.rollback()
            raise_registry_operational_error(error)
            raise
        finally:
            connection.close()
        return result

    def resolve_artifact(self, artifact_ref: str) -> dict[str, Any]:
        """Return one revalidated canonical envelope by content artifact ID."""

        _validate_digest("artifactRef", artifact_ref)
        connection = self._database.connect()
        try:
            repository = SemanticArtifactRepository(connection)
            artifact = repository.load_artifact(artifact_ref)
            repository.validate_registered_environment(artifact)
            return artifact
        finally:
            connection.close()

    def resolve_environment(self, environment_ref: str) -> dict[str, Any]:
        """Resolve a semantic environment ID to its exact environment envelope."""

        _validate_digest("environmentRef", environment_ref)
        connection = self._database.connect()
        try:
            return SemanticArtifactRepository(connection).resolve_environment(environment_ref)
        finally:
            connection.close()

    def resolve_typed_ref(self, reference: Mapping[str, Any]) -> dict[str, Any]:
        """Resolve one strict artifact-qualified reference and revalidate its owner."""

        artifact_ref, kind, local_id = _validate_typed_reference(reference)
        connection = self._database.connect()
        try:
            return SemanticArtifactRepository(connection).resolve_typed_ref(
                artifact_ref,
                kind,
                local_id,
            )
        finally:
            connection.close()

    def inspect(self) -> dict[str, Any]:
        """Return the active connection's bounded durability configuration."""

        connection = self._database.connect()
        try:
            return self._database.inspect(connection)
        finally:
            connection.close()

    def _register_transaction(
        self,
        connection: sqlite3.Connection,
        incoming: Mapping[str, dict[str, Any]],
    ) -> dict[str, Any]:
        connection.execute("BEGIN IMMEDIATE")
        repository = SemanticArtifactRepository(connection)
        closure = repository.hydrate_reference_closure(incoming)
        validate_envelope_batch(
            [closure[key] for key in sorted(closure)],
            max_artifacts=MAX_ARTIFACTS,
        )
        inserted, existing = repository.insert_artifacts(incoming)
        repository.validate_all_environment_bindings(incoming)
        connection.commit()
        return registration_result(incoming, inserted, existing)


def _validate_limits(max_database_bytes: int, busy_timeout_ms: int) -> None:
    if not isinstance(max_database_bytes, int) or isinstance(max_database_bytes, bool):
        raise TypeError("max_database_bytes must be an integer")
    if max_database_bytes < MIN_DATABASE_BYTES:
        raise ValueError(f"max_database_bytes must be at least {MIN_DATABASE_BYTES}")
    if (
        not isinstance(busy_timeout_ms, int)
        or isinstance(busy_timeout_ms, bool)
        or not 1 <= busy_timeout_ms <= 60_000
    ):
        raise ValueError("busy_timeout_ms must be an integer from 1 through 60000")


def _validate_requested_path(requested: Path) -> None:
    if requested.is_symlink():
        raise SemanticEvidenceRegistryError(
            "semantic evidence registry path must not be a symbolic link"
        )
    if requested.exists() and not requested.is_file():
        raise SemanticEvidenceRegistryError(
            "semantic evidence registry path must name a regular file"
        )


def _validate_bundle_container(artifacts: Sequence[Mapping[str, Any]]) -> None:
    if not isinstance(artifacts, Sequence) or isinstance(artifacts, (str, bytes, bytearray)):
        raise TypeError("semantic evidence bundle must be a sequence")
    if not artifacts:
        raise ValueError("semantic evidence bundle must not be empty")


def _validate_typed_reference(reference: Mapping[str, Any]) -> tuple[str, str, str]:
    if not isinstance(reference, Mapping) or set(reference) != {
        "artifactRef",
        "kind",
        "localId",
    }:
        raise ValueError("typed reference must contain artifactRef, kind, and localId")
    artifact_ref = reference["artifactRef"]
    kind = reference["kind"]
    local_id = reference["localId"]
    _validate_digest("artifactRef", artifact_ref)
    if not isinstance(kind, str) or not kind:
        raise ValueError("typed reference kind must be a non-empty string")
    if not isinstance(local_id, str) or not local_id:
        raise ValueError("typed reference localId must be a non-empty string")
    return artifact_ref, kind, local_id


def _validate_digest(field: str, value: Any) -> None:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")


def default_semantic_evidence_registry_path(
    repo_root: Path,
    *,
    environ: Mapping[str, str] | None = None,
    platform: str | None = None,
    home: Path | None = None,
) -> Path:
    """Return one repository-scoped user-cache path without touching disk."""

    values = os.environ if environ is None else environ
    system = sys.platform if platform is None else platform
    user_home = Path.home() if home is None else Path(home)
    cache_root = _platform_cache_root(values, system, user_home)
    repository_identity = hashlib.sha256(
        str(Path(repo_root).expanduser().resolve()).encode("utf-8")
    ).hexdigest()
    return (
        cache_root.expanduser()
        / "ladon"
        / SEMANTIC_EVIDENCE_CACHE_VERSION
        / f"{repository_identity}.sqlite"
    )


def _platform_cache_root(
    environ: Mapping[str, str],
    platform: str,
    home: Path,
) -> Path:
    if platform.startswith("win"):
        configured = environ.get("LOCALAPPDATA")
        return Path(configured) if configured else home / "AppData" / "Local"
    if platform == "darwin":
        return home / "Library" / "Caches"
    configured = environ.get("XDG_CACHE_HOME")
    return Path(configured) if configured else home / ".cache"


__all__ = [
    "DEFAULT_BUSY_TIMEOUT_MS",
    "DEFAULT_MAX_DATABASE_BYTES",
    "REGISTRY_APPLICATION_ID",
    "REGISTRY_SCHEMA",
    "REGISTRY_SCHEMA_VERSION",
    "SEMANTIC_EVIDENCE_CACHE_VERSION",
    "SemanticEvidenceRegistry",
    "SemanticEvidenceRegistryBusy",
    "SemanticEvidenceRegistryCapacity",
    "SemanticEvidenceRegistryConflict",
    "SemanticEvidenceRegistryError",
    "SemanticEvidenceRegistryNotFound",
    "SemanticEvidenceRegistrySchemaError",
    "default_semantic_evidence_registry_path",
]
