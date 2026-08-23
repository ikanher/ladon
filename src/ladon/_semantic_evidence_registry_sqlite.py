"""SQLite lifecycle and exact schema ownership for semantic evidence."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from ladon._semantic_evidence_registry_types import (
    REGISTRY_APPLICATION_ID,
    REGISTRY_SCHEMA,
    REGISTRY_SCHEMA_VERSION,
    SemanticEvidenceRegistryCapacity,
    SemanticEvidenceRegistryError,
    SemanticEvidenceRegistrySchemaError,
    raise_registry_operational_error,
)

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
    (
        "CREATE INDEX idx_semantic_artifact_environment "
        "ON artifacts(environment_ref, artifact_kind)"
    ),
    "CREATE INDEX idx_semantic_typed_ref ON typed_refs(kind, local_id, artifact_ref)",
)


class SemanticRegistryDatabase:
    """Own one bounded, private SQLite registry generation."""

    def __init__(
        self,
        path: Path,
        *,
        max_database_bytes: int,
        busy_timeout_ms: int,
    ) -> None:
        self.path = path
        self.max_database_bytes = max_database_bytes
        self.busy_timeout_ms = busy_timeout_ms

    def initialize(self) -> None:
        """Create or validate the exact registry generation."""

        parent_created = not self.path.parent.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if parent_created:
            self._secure_new_parent()
        connection = self._raw_connection()
        try:
            self._initialize_connection(connection)
        except BaseException as error:
            connection.rollback()
            raise_registry_operational_error(error)
            raise
        finally:
            connection.close()
        os.chmod(self.path, 0o600)

    def connect(self) -> sqlite3.Connection:
        """Open a validated connection after checking pathname ownership."""

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

    def inspect(self, connection: sqlite3.Connection) -> dict[str, Any]:
        """Describe the active connection's durability and bounded size."""

        page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        max_pages = int(connection.execute("PRAGMA max_page_count").fetchone()[0])
        counts = {
            label: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for label, table in (
                ("artifacts", "artifacts"),
                ("environments", "environments"),
                ("typedRefs", "typed_refs"),
            )
        }
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
            "counts": counts,
        }

    def _initialize_connection(self, connection: sqlite3.Connection) -> None:
        mode = str(connection.execute("PRAGMA journal_mode=WAL").fetchone()[0])
        if mode.lower() != "wal":
            raise SemanticEvidenceRegistrySchemaError(
                f"semantic evidence registry requires WAL mode, observed {mode}"
            )
        connection.execute("BEGIN IMMEDIATE")
        if self._is_uninitialized(connection):
            self._create_schema(connection)
        self._validate_schema(connection)
        self._apply_page_limit(connection)
        connection.commit()

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

    def _secure_new_parent(self) -> None:
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass

    def _create_schema(self, connection: sqlite3.Connection) -> None:
        for statement in _SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.execute(
            "INSERT INTO registry_meta(singleton,schema_name,schema_version) VALUES(1,?,?)",
            (REGISTRY_SCHEMA, REGISTRY_SCHEMA_VERSION),
        )
        connection.execute(f"PRAGMA application_id={REGISTRY_APPLICATION_ID}")
        connection.execute(f"PRAGMA user_version={REGISTRY_SCHEMA_VERSION}")

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
            str(found[0])
            for found in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")
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
