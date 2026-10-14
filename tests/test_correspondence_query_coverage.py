"""Untrusted disposable projections must not hide missing tables or omissions."""

import sqlite3

from ladon.proofir_sqlite_v3 import create_v3_schema
from ladon.proofir_v3_queries import query_v3_correspondence

OWNER = "sha256:" + "a" * 64
REF = {"artifactRef": OWNER, "kind": "correspondence", "localId": "c"}


def database():
    db = sqlite3.connect(":memory:")
    create_v3_schema(db)
    # This is a query-only corrupt/untrusted projection fixture, not producer evidence.
    db.execute("PRAGMA foreign_keys=OFF")
    db.execute("INSERT INTO proofir_v3_correspondences VALUES(?,?,?,?,?,?,?,?,?)",
               (OWNER, "c", "sha256:" + "b" * 64, "interpretation", "i", "{}", "{}", "{}", "/"))
    return db


def test_missing_child_table_is_explicitly_unavailable():
    db = database()
    db.execute("DROP TABLE proofir_v3_correspondence_checks")
    result = query_v3_correspondence(db, REF, limit=1)
    assert result["status"] == "unavailable"
    assert result["coverage"]["complete"] is False


def test_stored_extension_omission_prevents_complete_inspection():
    db = database()
    for index in range(3):
        db.execute("INSERT INTO proofir_v3_omissions VALUES(?,?,?,?,?,?)",
                   (OWNER, index, "/extensions/evidence", "projection", "extension-size", "{}"))
    result = query_v3_correspondence(db, REF, limit=1)
    assert result["status"] == "observed"
    assert result["coverage"]["complete"] is False
    assert result["omissions"]["total"] == 3
    assert len(result["omissions"]["rows"]) == 1
    assert result["omissions"]["omitted"] == 2
