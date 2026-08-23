"""SQLite lifecycle and exact schema ownership for semantic evidence."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from functools import lru_cache
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
    ("CREATE INDEX idx_semantic_artifact_environment ON artifacts(environment_ref, artifact_kind)"),
    "CREATE INDEX idx_semantic_typed_ref ON typed_refs(kind, local_id, artifact_ref)",
)

_REGISTRY_TABLES = (
    "registry_meta",
    "artifacts",
    "environments",
    "typed_refs",
)

_MIN_SQLITE_VERSION = (3, 37, 0)


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

        # Probe lazily so importing Ladon remains usable on hosts whose SQLite
        # cannot own this private STRICT-schema generation.  In particular,
        # lexical proof-search commands import the registry module but never
        # construct a registry.
        _expected_schema_fingerprint()
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
        uninitialized = self._is_uninitialized(connection)
        if uninitialized:
            mode = str(connection.execute("PRAGMA journal_mode=WAL").fetchone()[0])
            if mode.lower() != "wal":
                raise SemanticEvidenceRegistrySchemaError(
                    f"semantic evidence registry requires WAL mode, observed {mode}"
                )
        connection.execute("BEGIN IMMEDIATE")
        if uninitialized:
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

    def _validate_schema(self, connection: sqlite3.Connection) -> None:
        try:
            self._validate_schema_identity(connection)
            self._validate_schema_fingerprint(connection)
            self._validate_registry_metadata(connection)
            self._validate_required_pragmas(connection)
        except SemanticEvidenceRegistrySchemaError:
            raise
        except (LookupError, TypeError, ValueError, sqlite3.DatabaseError) as error:
            raise SemanticEvidenceRegistrySchemaError(
                "semantic evidence registry schema cannot be validated"
            ) from error

    @staticmethod
    def _validate_schema_identity(connection: sqlite3.Connection) -> None:
        application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
        user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if application_id != REGISTRY_APPLICATION_ID or user_version != REGISTRY_SCHEMA_VERSION:
            raise SemanticEvidenceRegistrySchemaError(
                "semantic evidence registry schema identity is unsupported"
            )

    @staticmethod
    def _validate_registry_metadata(connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            "SELECT schema_name,schema_version FROM registry_meta WHERE singleton=1"
        ).fetchall()
        if len(rows) != 1 or (str(rows[0][0]), int(rows[0][1])) != (
            REGISTRY_SCHEMA,
            REGISTRY_SCHEMA_VERSION,
        ):
            raise SemanticEvidenceRegistrySchemaError(
                "semantic evidence registry metadata is inconsistent"
            )

    @staticmethod
    def _validate_schema_fingerprint(connection: sqlite3.Connection) -> None:
        observed = _schema_fingerprint(connection)
        if observed != _expected_schema_fingerprint():
            raise SemanticEvidenceRegistrySchemaError(
                "semantic evidence registry schema structure is inconsistent"
            )

    def _validate_required_pragmas(self, connection: sqlite3.Connection) -> None:
        observed = {
            "journalMode": str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower(),
            "synchronous": int(connection.execute("PRAGMA synchronous").fetchone()[0]),
            "foreignKeys": int(connection.execute("PRAGMA foreign_keys").fetchone()[0]),
            "busyTimeoutMs": int(connection.execute("PRAGMA busy_timeout").fetchone()[0]),
            "encoding": str(connection.execute("PRAGMA encoding").fetchone()[0]),
        }
        expected = {
            "journalMode": "wal",
            "synchronous": 2,
            "foreignKeys": 1,
            "busyTimeoutMs": self.busy_timeout_ms,
            "encoding": "UTF-8",
        }
        if observed != expected:
            raise SemanticEvidenceRegistrySchemaError(
                "semantic evidence registry durability pragmas are inconsistent"
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


def _schema_fingerprint(connection: sqlite3.Connection) -> str:
    projection = {
        "objects": _schema_objects(connection),
        "tables": {
            table: _table_schema_projection(connection, table) for table in _REGISTRY_TABLES
        },
    }
    encoded = json.dumps(
        projection,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _schema_objects(connection: sqlite3.Connection) -> list[list[Any]]:
    return [
        [str(row[0]), str(row[1]), str(row[2]), _normalized_sql(row[3])]
        for row in connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_schema "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        )
    ]


def _table_schema_projection(
    connection: sqlite3.Connection,
    table: str,
) -> dict[str, Any]:
    table_state = [
        list(row)
        for row in connection.execute("PRAGMA main.table_list")
        if str(row[0]) == "main" and str(row[1]) == table
    ]
    return {
        "tableState": table_state,
        "columns": [
            list(row) for row in connection.execute("SELECT * FROM pragma_table_xinfo(?)", (table,))
        ],
        "foreignKeys": [
            list(row)
            for row in connection.execute("SELECT * FROM pragma_foreign_key_list(?)", (table,))
        ],
        "indexes": _index_schema_projection(connection, table),
    }


def _index_schema_projection(
    connection: sqlite3.Connection,
    table: str,
) -> list[dict[str, Any]]:
    rows = sorted(
        (list(row) for row in connection.execute("SELECT * FROM pragma_index_list(?)", (table,))),
        key=lambda row: str(row[1]),
    )
    return [
        {
            "index": row,
            "columns": [
                list(column)
                for column in connection.execute(
                    "SELECT * FROM pragma_index_xinfo(?)",
                    (row[1],),
                )
            ],
        }
        for row in rows
    ]


def _normalized_sql(value: Any) -> str | None:
    if value is None:
        return None
    return " ".join(str(value).split())


def _canonical_schema_fingerprint() -> str:
    connection = sqlite3.connect(":memory:")
    try:
        for statement in _SCHEMA_STATEMENTS:
            connection.execute(statement)
        return _schema_fingerprint(connection)
    finally:
        connection.close()


@lru_cache(maxsize=1)
def _expected_schema_fingerprint() -> str:
    """Return the owned schema identity or a stable SQLite capability error."""

    if sqlite3.sqlite_version_info < _MIN_SQLITE_VERSION:
        required = ".".join(str(part) for part in _MIN_SQLITE_VERSION)
        observed = sqlite3.sqlite_version
        raise SemanticEvidenceRegistrySchemaError(
            "semantic evidence registry requires SQLite "
            f"{required} or newer with STRICT-table and JSON support; "
            f"observed {observed}"
        )
    try:
        return _canonical_schema_fingerprint()
    except (LookupError, TypeError, ValueError, sqlite3.DatabaseError) as error:
        raise SemanticEvidenceRegistrySchemaError(
            "semantic evidence registry requires SQLite STRICT-table, JSON, "
            "and schema-introspection support"
        ) from error
