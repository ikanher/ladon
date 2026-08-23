"""Append-only content registry for live semantic ProofIR evidence.

The lexical proof-search index is an atomically replaced repository generation.
Semantic checks have a different lifetime: many checks can share one exact Lean
environment and arrive incrementally.  This module therefore owns a separate,
explicitly located SQLite cache whose only public identities are canonical
ProofIR artifact IDs, environment IDs, and artifact-qualified typed references.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ladon.proofir_v3 import (
    MAX_ARTIFACTS,
    ProofIRV3Error,
    canonical_bytes,
    validate_envelope,
    validate_envelope_batch,
)

REGISTRY_SCHEMA = "ladon-semantic-evidence-registry-v1"
REGISTRY_SCHEMA_VERSION = 1
REGISTRY_APPLICATION_ID = 0x4C53454D  # ASCII "LSEM".
DEFAULT_MAX_DATABASE_BYTES = 512 * 1024 * 1024
DEFAULT_BUSY_TIMEOUT_MS = 5_000
MIN_DATABASE_BYTES = 64 * 1024
SEMANTIC_EVIDENCE_CACHE_VERSION = "semantic-evidence-v1"

_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")

_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE registry_meta (
        singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
        schema_name TEXT NOT NULL
            CHECK(schema_name = 'ladon-semantic-evidence-registry-v1'),
        schema_version INTEGER NOT NULL CHECK(schema_version = 1)
    ) STRICT
    """,
    """
    CREATE TABLE artifacts (
        artifact_ref TEXT PRIMARY KEY,
        artifact_kind TEXT NOT NULL,
        proofir_version TEXT NOT NULL,
        environment_ref TEXT NOT NULL,
        canonical_json TEXT NOT NULL CHECK(json_valid(canonical_json)),
        canonical_byte_count INTEGER NOT NULL CHECK(canonical_byte_count > 0),
        CHECK(length(artifact_ref) = 71),
        CHECK(substr(artifact_ref, 1, 7) = 'sha256:'),
        CHECK(substr(artifact_ref, 8) NOT GLOB '*[^0-9a-f]*'),
        CHECK(length(environment_ref) = 71),
        CHECK(substr(environment_ref, 1, 7) = 'sha256:'),
        CHECK(substr(environment_ref, 8) NOT GLOB '*[^0-9a-f]*'),
        CHECK(length(CAST(canonical_json AS BLOB)) = canonical_byte_count),
        FOREIGN KEY(environment_ref) REFERENCES environments(environment_ref)
            ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
    ) STRICT
    """,
    """
    CREATE TABLE environments (
        environment_ref TEXT PRIMARY KEY,
        artifact_ref TEXT UNIQUE NOT NULL,
        CHECK(length(environment_ref) = 71),
        CHECK(substr(environment_ref, 1, 7) = 'sha256:'),
        CHECK(substr(environment_ref, 8) NOT GLOB '*[^0-9a-f]*'),
        FOREIGN KEY(artifact_ref) REFERENCES artifacts(artifact_ref)
            ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
    ) STRICT
    """,
    """
    CREATE TABLE typed_refs (
        artifact_ref TEXT NOT NULL,
        kind TEXT NOT NULL CHECK(length(kind) > 0),
        local_id TEXT NOT NULL CHECK(length(local_id) > 0),
        source_pointer TEXT NOT NULL CHECK(length(source_pointer) > 0),
        PRIMARY KEY(artifact_ref, kind, local_id),
        FOREIGN KEY(artifact_ref) REFERENCES artifacts(artifact_ref)
            ON DELETE RESTRICT
    ) STRICT
    """,
    ("CREATE INDEX idx_semantic_artifact_environment ON artifacts(environment_ref, artifact_kind)"),
    ("CREATE INDEX idx_semantic_typed_ref ON typed_refs(kind, local_id, artifact_ref)"),
)


class SemanticEvidenceRegistryError(RuntimeError):
    """Base class for persistent semantic-evidence failures."""


class SemanticEvidenceRegistrySchemaError(SemanticEvidenceRegistryError):
    """The selected path is not this registry's exact schema generation."""


class SemanticEvidenceRegistryConflict(SemanticEvidenceRegistryError):
    """Stored content conflicts with an immutable content identity."""


class SemanticEvidenceRegistryNotFound(SemanticEvidenceRegistryError):
    """A requested artifact, environment, or typed reference is absent."""


class SemanticEvidenceRegistryBusy(SemanticEvidenceRegistryError):
    """Another writer retained SQLite ownership beyond the finite timeout."""


class SemanticEvidenceRegistryCapacity(SemanticEvidenceRegistryError):
    """The configured complete-database byte ceiling prevented an append."""


class SemanticEvidenceRegistry:
    """One explicit-path, append-only registry for canonical ProofIR envelopes."""

    def __init__(
        self,
        path: Path,
        *,
        max_database_bytes: int = DEFAULT_MAX_DATABASE_BYTES,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    ) -> None:
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
        requested = Path(path).expanduser()
        if requested.is_symlink():
            raise SemanticEvidenceRegistryError(
                "semantic evidence registry path must not be a symbolic link"
            )
        if requested.exists() and not requested.is_file():
            raise SemanticEvidenceRegistryError(
                "semantic evidence registry path must name a regular file"
            )
        self.path = requested.resolve()
        self.max_database_bytes = max_database_bytes
        self.busy_timeout_ms = busy_timeout_ms
        self._initialize()

    def register_bundle(self, artifacts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """Atomically append a closed bundle, hydrating already-stored references."""

        if not isinstance(artifacts, Sequence) or isinstance(artifacts, (str, bytes, bytearray)):
            raise TypeError("semantic evidence bundle must be a sequence")
        if not artifacts:
            raise ValueError("semantic evidence bundle must not be empty")
        incoming = self._validated_incoming(artifacts)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            closure = self._hydrate_reference_closure(connection, incoming)
            validate_envelope_batch(
                [closure[key] for key in sorted(closure)],
                max_artifacts=MAX_ARTIFACTS,
            )
            inserted, existing = self._insert_artifacts(connection, incoming)
            self._validate_all_environment_bindings(connection, incoming)
            connection.commit()
        except BaseException as error:
            connection.rollback()
            self._raise_operational(error)
            raise
        finally:
            connection.close()
        return self._registration_result(incoming, inserted, existing)

    def resolve_artifact(self, artifact_ref: str) -> dict[str, Any]:
        """Return one revalidated canonical envelope by content artifact ID."""

        self._validate_digest("artifactRef", artifact_ref)
        connection = self._connect()
        try:
            artifact = self._load_artifact(connection, artifact_ref)
            self._validate_registered_environment(connection, artifact)
            return artifact
        finally:
            connection.close()

    def resolve_environment(self, environment_ref: str) -> dict[str, Any]:
        """Resolve a semantic environment ID to its exact environment envelope."""

        self._validate_digest("environmentRef", environment_ref)
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT artifact_ref FROM environments WHERE environment_ref=?",
                (environment_ref,),
            ).fetchone()
            if row is None:
                raise SemanticEvidenceRegistryNotFound(
                    f"semantic environment is not registered: {environment_ref}"
                )
            artifact = self._load_artifact(connection, str(row[0]))
            if (
                artifact["artifactKind"] != "proofir.environment"
                or artifact["environmentRef"] != environment_ref
            ):
                raise SemanticEvidenceRegistryConflict(
                    f"semantic environment mapping is inconsistent: {environment_ref}"
                )
            self._validate_registered_environment(connection, artifact)
            return artifact
        finally:
            connection.close()

    def resolve_typed_ref(self, reference: Mapping[str, Any]) -> dict[str, Any]:
        """Resolve one strict artifact-qualified reference and revalidate its owner."""

        if not isinstance(reference, Mapping) or set(reference) != {
            "artifactRef",
            "kind",
            "localId",
        }:
            raise ValueError("typed reference must contain artifactRef, kind, and localId")
        artifact_ref = reference["artifactRef"]
        kind = reference["kind"]
        local_id = reference["localId"]
        self._validate_digest("artifactRef", artifact_ref)
        if not isinstance(kind, str) or not kind:
            raise ValueError("typed reference kind must be a non-empty string")
        if not isinstance(local_id, str) or not local_id:
            raise ValueError("typed reference localId must be a non-empty string")
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT source_pointer FROM typed_refs "
                "WHERE artifact_ref=? AND kind=? AND local_id=?",
                (artifact_ref, kind, local_id),
            ).fetchone()
            if row is None:
                raise SemanticEvidenceRegistryNotFound("semantic typed reference is not registered")
            artifact = self._load_artifact(connection, artifact_ref)
            self._validate_resolved_typed_ref(artifact, kind, local_id)
            self._validate_registered_environment(connection, artifact)
            return {
                "reference": {
                    "artifactRef": artifact_ref,
                    "kind": kind,
                    "localId": local_id,
                },
                "sourcePointer": str(row[0]),
                "artifact": artifact,
            }
        finally:
            connection.close()

    def inspect(self) -> dict[str, Any]:
        """Return the active connection's bounded durability configuration."""

        connection = self._connect()
        try:
            page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
            page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
            max_pages = int(connection.execute("PRAGMA max_page_count").fetchone()[0])
            return {
                "schema": REGISTRY_SCHEMA,
                "schemaVersion": REGISTRY_SCHEMA_VERSION,
                "path": str(self.path),
                "journalMode": str(connection.execute("PRAGMA journal_mode").fetchone()[0]),
                "synchronous": int(connection.execute("PRAGMA synchronous").fetchone()[0]),
                "foreignKeys": bool(connection.execute("PRAGMA foreign_keys").fetchone()[0]),
                "busyTimeoutMs": int(connection.execute("PRAGMA busy_timeout").fetchone()[0]),
                "pageSize": page_size,
                "pageCount": page_count,
                "maxPageCount": max_pages,
                "databaseBytes": page_size * page_count,
                "databaseByteLimit": self.max_database_bytes,
            }
        finally:
            connection.close()

    def _initialize(self) -> None:
        parent_created = not self.path.parent.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if parent_created:
            try:
                os.chmod(self.path.parent, 0o700)
            except OSError:
                pass
        connection = self._raw_connection()
        try:
            mode = str(connection.execute("PRAGMA journal_mode=WAL").fetchone()[0])
            if mode.lower() != "wal":
                raise SemanticEvidenceRegistrySchemaError(
                    f"semantic evidence registry requires WAL mode, observed {mode}"
                )
            connection.execute("BEGIN IMMEDIATE")
            if self._is_uninitialized(connection):
                for statement in _SCHEMA_STATEMENTS:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO registry_meta(singleton,schema_name,schema_version) VALUES(1,?,?)",
                    (REGISTRY_SCHEMA, REGISTRY_SCHEMA_VERSION),
                )
                connection.execute(f"PRAGMA application_id={REGISTRY_APPLICATION_ID}")
                connection.execute(f"PRAGMA user_version={REGISTRY_SCHEMA_VERSION}")
            self._validate_schema(connection)
            self._apply_page_limit(connection)
            connection.commit()
        except BaseException as error:
            connection.rollback()
            self._raise_operational(error)
            raise
        finally:
            connection.close()
        os.chmod(self.path, 0o600)

    def _raw_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _connect(self) -> sqlite3.Connection:
        if self.path.is_symlink() or not self.path.is_file():
            raise SemanticEvidenceRegistryError(
                "semantic evidence registry path changed after initialization"
            )
        connection = self._raw_connection()
        try:
            self._validate_schema(connection)
            self._apply_page_limit(connection)
        except BaseException:
            connection.close()
            raise
        return connection

    @staticmethod
    def _is_uninitialized(connection: sqlite3.Connection) -> bool:
        objects = int(
            connection.execute(
                "SELECT COUNT(*) FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'"
            ).fetchone()[0]
        )
        application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if objects == 0 and application_id == 0 and user_version == 0:
            return True
        if application_id == 0 and user_version == 0:
            raise SemanticEvidenceRegistrySchemaError(
                "selected SQLite file is not an empty semantic evidence registry"
            )
        return False

    @staticmethod
    def _validate_schema(connection: sqlite3.Connection) -> None:
        application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if application_id != REGISTRY_APPLICATION_ID or user_version != REGISTRY_SCHEMA_VERSION:
            raise SemanticEvidenceRegistrySchemaError(
                "semantic evidence registry schema identity is unsupported"
            )
        row = connection.execute(
            "SELECT schema_name,schema_version FROM registry_meta WHERE singleton=1"
        ).fetchone()
        if row is None or (str(row[0]), int(row[1])) != (
            REGISTRY_SCHEMA,
            REGISTRY_SCHEMA_VERSION,
        ):
            raise SemanticEvidenceRegistrySchemaError(
                "semantic evidence registry metadata is inconsistent"
            )
        required = {"registry_meta", "artifacts", "environments", "typed_refs"}
        present = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        }
        if not required <= present:
            raise SemanticEvidenceRegistrySchemaError(
                "semantic evidence registry is missing required tables"
            )

    def _apply_page_limit(self, connection: sqlite3.Connection) -> None:
        page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        if page_size * page_count > self.max_database_bytes:
            raise SemanticEvidenceRegistryCapacity(
                "existing semantic evidence registry exceeds the configured byte limit"
            )
        requested_pages = max(1, self.max_database_bytes // page_size)
        actual_pages = int(
            connection.execute(f"PRAGMA max_page_count={requested_pages}").fetchone()[0]
        )
        if actual_pages > requested_pages:
            raise SemanticEvidenceRegistryCapacity(
                "semantic evidence registry cannot enforce the configured byte limit"
            )

    @staticmethod
    def _validated_incoming(
        artifacts: Sequence[Mapping[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        incoming: dict[str, dict[str, Any]] = {}
        encodings: dict[str, bytes] = {}
        for raw in artifacts:
            checked = validate_envelope(dict(raw)).to_dict()
            artifact_ref = str(checked["artifactId"])
            encoded = canonical_bytes(checked)
            prior = encodings.get(artifact_ref)
            if prior is not None and prior != encoded:
                raise SemanticEvidenceRegistryConflict(
                    f"conflicting bundle artifacts share {artifact_ref}"
                )
            incoming[artifact_ref] = checked
            encodings[artifact_ref] = encoded
        if len(incoming) > MAX_ARTIFACTS:
            raise ProofIRV3Error(
                f"semantic evidence bundle exceeds artifact limit: {MAX_ARTIFACTS}"
            )
        return incoming

    def _hydrate_reference_closure(
        self,
        connection: sqlite3.Connection,
        incoming: Mapping[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        closure = dict(incoming)
        while True:
            required = self._required_artifact_refs(connection, closure)
            missing = sorted(required - closure.keys())
            if not missing:
                return closure
            if len(closure) + len(missing) > MAX_ARTIFACTS:
                raise ProofIRV3Error(
                    f"semantic evidence closure exceeds artifact limit: {MAX_ARTIFACTS}"
                )
            for artifact_ref in missing:
                closure[artifact_ref] = self._load_artifact(connection, artifact_ref)

    def _required_artifact_refs(
        self,
        connection: sqlite3.Connection,
        artifacts: Mapping[str, Mapping[str, Any]],
    ) -> set[str]:
        required: set[str] = set()
        environments = {
            str(row["environmentRef"]): artifact_ref
            for artifact_ref, row in artifacts.items()
            if row["artifactKind"] == "proofir.environment"
        }
        for artifact in artifacts.values():
            required.update(_external_artifact_refs(artifact))
            if artifact["artifactKind"] == "proofir.environment":
                continue
            environment_ref = str(artifact["environmentRef"])
            environment_artifact_ref = environments.get(environment_ref)
            if environment_artifact_ref is None:
                row = connection.execute(
                    "SELECT artifact_ref FROM environments WHERE environment_ref=?",
                    (environment_ref,),
                ).fetchone()
                if row is None:
                    raise SemanticEvidenceRegistryNotFound(
                        f"semantic environment is not registered: {environment_ref}"
                    )
                environment_artifact_ref = str(row[0])
            required.add(environment_artifact_ref)
        return required

    def _load_artifact(self, connection: sqlite3.Connection, artifact_ref: str) -> dict[str, Any]:
        row = connection.execute(
            "SELECT artifact_kind,proofir_version,environment_ref,canonical_json,"
            "canonical_byte_count FROM artifacts WHERE artifact_ref=?",
            (artifact_ref,),
        ).fetchone()
        if row is None:
            raise SemanticEvidenceRegistryNotFound(
                f"semantic artifact is not registered: {artifact_ref}"
            )
        try:
            raw = str(row[3]).encode("utf-8")
            value = json.loads(raw)
            artifact = validate_envelope(value).to_dict()
        except (UnicodeError, json.JSONDecodeError, ProofIRV3Error) as error:
            raise SemanticEvidenceRegistryConflict(
                f"stored semantic artifact is invalid: {artifact_ref}"
            ) from error
        if (
            len(raw) != int(row[4])
            or raw != canonical_bytes(artifact)
            or artifact["artifactId"] != artifact_ref
            or artifact["artifactKind"] != row[0]
            or artifact["proofirVersion"] != row[1]
            or artifact["environmentRef"] != row[2]
        ):
            raise SemanticEvidenceRegistryConflict(
                f"stored semantic artifact metadata is inconsistent: {artifact_ref}"
            )
        return artifact

    def _insert_artifacts(
        self,
        connection: sqlite3.Connection,
        incoming: Mapping[str, dict[str, Any]],
    ) -> tuple[list[str], list[str]]:
        inserted: list[str] = []
        existing: list[str] = []
        for artifact_ref in sorted(incoming):
            artifact = incoming[artifact_ref]
            encoded = canonical_bytes(artifact)
            row = connection.execute(
                "SELECT 1 FROM artifacts WHERE artifact_ref=?",
                (artifact_ref,),
            ).fetchone()
            if row is not None:
                stored = self._load_artifact(connection, artifact_ref)
                if canonical_bytes(stored) != encoded:
                    raise SemanticEvidenceRegistryConflict(
                        f"stored semantic artifact conflicts with {artifact_ref}"
                    )
                self._validate_existing_projection(connection, artifact)
                existing.append(artifact_ref)
                continue
            connection.execute(
                "INSERT INTO artifacts(artifact_ref,artifact_kind,proofir_version,"
                "environment_ref,canonical_json,canonical_byte_count) "
                "VALUES(?,?,?,?,?,?)",
                (
                    artifact_ref,
                    artifact["artifactKind"],
                    artifact["proofirVersion"],
                    artifact["environmentRef"],
                    encoded.decode("utf-8"),
                    len(encoded),
                ),
            )
            inserted.append(artifact_ref)
        for artifact_ref in sorted(incoming):
            artifact = incoming[artifact_ref]
            if artifact["artifactKind"] == "proofir.environment":
                self._insert_environment(connection, artifact)
            self._insert_typed_refs(connection, artifact)
        return inserted, existing

    def _insert_environment(
        self, connection: sqlite3.Connection, artifact: Mapping[str, Any]
    ) -> None:
        environment_ref = str(artifact["environmentRef"])
        artifact_ref = str(artifact["artifactId"])
        row = connection.execute(
            "SELECT artifact_ref FROM environments WHERE environment_ref=?",
            (environment_ref,),
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO environments(environment_ref,artifact_ref) VALUES(?,?)",
                (environment_ref, artifact_ref),
            )
        elif str(row[0]) != artifact_ref:
            raise SemanticEvidenceRegistryConflict(
                f"multiple environment artifacts claim {environment_ref}"
            )

    def _insert_typed_refs(
        self, connection: sqlite3.Connection, artifact: Mapping[str, Any]
    ) -> None:
        artifact_ref = str(artifact["artifactId"])
        for (kind, local_id), pointer in sorted(_typed_reference_rows(artifact).items()):
            row = connection.execute(
                "SELECT source_pointer FROM typed_refs "
                "WHERE artifact_ref=? AND kind=? AND local_id=?",
                (artifact_ref, kind, local_id),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO typed_refs(artifact_ref,kind,local_id,source_pointer) "
                    "VALUES(?,?,?,?)",
                    (artifact_ref, kind, local_id, pointer),
                )
            elif str(row[0]) != pointer:
                raise SemanticEvidenceRegistryConflict(
                    f"typed reference projection conflicts for {artifact_ref}"
                )

    def _validate_existing_projection(
        self, connection: sqlite3.Connection, artifact: Mapping[str, Any]
    ) -> None:
        artifact_ref = str(artifact["artifactId"])
        stored = {
            (str(row[0]), str(row[1])): str(row[2])
            for row in connection.execute(
                "SELECT kind,local_id,source_pointer FROM typed_refs WHERE artifact_ref=?",
                (artifact_ref,),
            )
        }
        expected = _typed_reference_rows(artifact)
        if stored != expected:
            raise SemanticEvidenceRegistryConflict(
                f"typed reference projection is inconsistent for {artifact_ref}"
            )
        if artifact["artifactKind"] == "proofir.environment":
            row = connection.execute(
                "SELECT artifact_ref FROM environments WHERE environment_ref=?",
                (artifact["environmentRef"],),
            ).fetchone()
            if row is None or str(row[0]) != artifact_ref:
                raise SemanticEvidenceRegistryConflict(
                    f"environment projection is inconsistent for {artifact_ref}"
                )

    @staticmethod
    def _validate_all_environment_bindings(
        connection: sqlite3.Connection,
        incoming: Mapping[str, Mapping[str, Any]],
    ) -> None:
        for artifact in incoming.values():
            row = connection.execute(
                "SELECT environment.artifact_ref FROM environments AS environment "
                "JOIN artifacts AS artifact "
                "ON artifact.artifact_ref=environment.artifact_ref "
                "WHERE environment.environment_ref=? "
                "AND artifact.artifact_kind='proofir.environment' "
                "AND artifact.environment_ref=environment.environment_ref",
                (artifact["environmentRef"],),
            ).fetchone()
            if row is None:
                raise SemanticEvidenceRegistryNotFound(
                    f"semantic environment is not registered: {artifact['environmentRef']}"
                )

    def _validate_registered_environment(
        self,
        connection: sqlite3.Connection,
        artifact: Mapping[str, Any],
    ) -> None:
        environment_ref = str(artifact["environmentRef"])
        row = connection.execute(
            "SELECT artifact_ref FROM environments WHERE environment_ref=?",
            (environment_ref,),
        ).fetchone()
        if row is None:
            raise SemanticEvidenceRegistryConflict(
                f"artifact environment is unresolved: {environment_ref}"
            )
        environment = self._load_artifact(connection, str(row[0]))
        if (
            environment["artifactKind"] != "proofir.environment"
            or environment["environmentRef"] != environment_ref
        ):
            raise SemanticEvidenceRegistryConflict(
                f"artifact environment mapping is inconsistent: {environment_ref}"
            )

    @staticmethod
    def _validate_resolved_typed_ref(artifact: Mapping[str, Any], kind: str, local_id: str) -> None:
        if kind == "check-run":
            if (
                artifact["artifactKind"] != "proofir.check-run"
                or artifact["payload"].get("checkRunId") != local_id
            ):
                raise SemanticEvidenceRegistryConflict(
                    "typed check reference does not match its check artifact"
                )
            return
        identities = {(str(row["kind"]), str(row["localId"])) for row in artifact["subjectRefs"]}
        if (kind, local_id) not in identities:
            raise SemanticEvidenceRegistryConflict(
                "typed subject reference does not match its owner artifact"
            )

    @staticmethod
    def _registration_result(
        incoming: Mapping[str, Mapping[str, Any]],
        inserted: list[str],
        existing: list[str],
    ) -> dict[str, Any]:
        check_refs = [
            {
                "artifactRef": artifact_ref,
                "kind": "check-run",
                "localId": str(artifact["payload"]["checkRunId"]),
            }
            for artifact_ref, artifact in sorted(incoming.items())
            if artifact["artifactKind"] == "proofir.check-run"
        ]
        return {
            "schema": "ladon-semantic-evidence-registration-v1",
            "insertedArtifactRefs": inserted,
            "existingArtifactRefs": existing,
            "environmentRefs": sorted(
                {str(artifact["environmentRef"]) for artifact in incoming.values()}
            ),
            "checkRunRefs": check_refs,
        }

    @staticmethod
    def _validate_digest(field: str, value: Any) -> None:
        if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
            raise ValueError(f"{field} must be a lowercase SHA-256 digest")

    @staticmethod
    def _raise_operational(error: BaseException) -> None:
        if not isinstance(error, sqlite3.OperationalError):
            return
        message = str(error).lower()
        if "locked" in message or "busy" in message:
            raise SemanticEvidenceRegistryBusy(
                "semantic evidence registry remained busy beyond its timeout"
            ) from error
        if "full" in message or "max_page_count" in message:
            raise SemanticEvidenceRegistryCapacity(
                "semantic evidence registry reached its configured byte limit"
            ) from error


def _external_artifact_refs(artifact: Mapping[str, Any]) -> set[str]:
    """Return the explicit external owners checked by ProofIR batch validation."""

    references: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            if set(value) == {"artifactRef", "kind", "localId"}:
                references.add(str(value["artifactRef"]))
                return
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    payload = artifact["payload"]
    visit(payload)
    if artifact["artifactKind"] == "proofir.check-run":
        inputs = payload.get("inputs")
        if isinstance(inputs, Mapping):
            references.update(str(item) for item in inputs.get("artifactRefs", []))
    return references


def _typed_reference_rows(
    artifact: Mapping[str, Any],
) -> dict[tuple[str, str], str]:
    rows = {
        (str(subject["kind"]), str(subject["localId"])): f"/subjectRefs/{index}"
        for index, subject in enumerate(artifact["subjectRefs"])
    }
    if artifact["artifactKind"] == "proofir.check-run":
        rows[("check-run", str(artifact["payload"]["checkRunId"]))] = "/payload/checkRunId"
    return rows


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
    if system.startswith("win"):
        configured = values.get("LOCALAPPDATA")
        cache_root = Path(configured) if configured else user_home / "AppData" / "Local"
    elif system == "darwin":
        cache_root = user_home / "Library" / "Caches"
    else:
        configured = values.get("XDG_CACHE_HOME")
        cache_root = Path(configured) if configured else user_home / ".cache"
    repository_identity = hashlib.sha256(
        str(Path(repo_root).expanduser().resolve()).encode("utf-8")
    ).hexdigest()
    return (
        cache_root.expanduser()
        / "ladon"
        / SEMANTIC_EVIDENCE_CACHE_VERSION
        / f"{repository_identity}.sqlite"
    )


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
