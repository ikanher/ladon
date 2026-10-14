"""Existing native projections must rebuild before adopting changed constraints."""

import sqlite3
from pathlib import Path

import pytest

from ladon.proofir_sqlite_v3 import create_v3_schema, project_envelopes

OLD_SCHEMA = Path(__file__).parent / "fixtures/correspondence_v8_schema.sql"


def snapshot(connection):
    return (connection.execute("PRAGMA user_version").fetchone(), tuple(connection.iterdump()))


@pytest.mark.parametrize("version,manage", [(8, True), (9, True), (42, False)])
@pytest.mark.parametrize("operation", ["create", "project"])
def test_old_constraints_require_rebuild_without_relabeling_or_data_loss(version, manage, operation):
    with sqlite3.connect(":memory:") as connection:
        connection.executescript(OLD_SCHEMA.read_text())
        connection.execute(f"PRAGMA user_version = {version}")
        connection.execute(
            "INSERT INTO proofir_v3_environments VALUES (?,NULL,NULL,'unresolved')",
            ("sha256:" + "1" * 64,),
        )
        connection.commit()
        before = snapshot(connection)
        with pytest.raises(RuntimeError, match="disposable rebuild"):
            if operation == "create":
                create_v3_schema(connection, manage_user_version=manage)
            else:
                project_envelopes(connection, [], manage_user_version=manage)
        assert snapshot(connection) == before


def test_current_embedded_projection_preserves_its_owners_version():
    with sqlite3.connect(":memory:") as connection:
        connection.execute("PRAGMA user_version = 42")
        create_v3_schema(connection, manage_user_version=False)
        project_envelopes(connection, [], manage_user_version=False)
        assert connection.execute("PRAGMA user_version").fetchone() == (42,)


def test_current_projection_creation_is_idempotent():
    with sqlite3.connect(":memory:") as connection:
        create_v3_schema(connection)
        before = snapshot(connection)
        create_v3_schema(connection)
        assert snapshot(connection) == before


def test_standalone_unknown_version_is_not_silently_downgraded():
    with sqlite3.connect(":memory:") as connection:
        create_v3_schema(connection)
        connection.execute("PRAGMA user_version = 10")
        before = snapshot(connection)
        with pytest.raises(RuntimeError, match="disposable rebuild"):
            create_v3_schema(connection)
        assert snapshot(connection) == before
