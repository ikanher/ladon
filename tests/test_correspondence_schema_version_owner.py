"""Standalone schema creation must not adopt an unrelated database version."""

import sqlite3

import pytest

from ladon.proofir_sqlite_v3 import create_v3_schema


def owner_database(version):
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE owner_data (payload TEXT)")
    connection.execute("INSERT INTO owner_data VALUES ('retained')")
    connection.execute(f"PRAGMA user_version = {version}")
    connection.commit()
    return connection


@pytest.mark.parametrize("version", [1, 8, 10, 42])
def test_unknown_standalone_version_is_preserved_without_native_tables(version):
    with owner_database(version) as connection:
        before = tuple(connection.iterdump())
        with pytest.raises(RuntimeError, match="disposable rebuild"):
            create_v3_schema(connection)
        assert tuple(connection.iterdump()) == before
        assert connection.execute("PRAGMA user_version").fetchone() == (version,)


def test_first_embedded_creation_preserves_database_owner_without_native_tables():
    with owner_database(42) as connection:
        create_v3_schema(connection, manage_user_version=False)
        assert connection.execute("PRAGMA user_version").fetchone() == (42,)
        assert connection.execute("SELECT payload FROM owner_data").fetchall() == [("retained",)]
