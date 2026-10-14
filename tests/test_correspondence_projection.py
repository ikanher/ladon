"""Native correspondence querying must preserve owner identity and omissions."""

import sqlite3

import pytest

from ladon import proofir_v3_queries as queries


def test_missing_correspondence_projection_is_unavailable():
    value = queries.query_v3_correspondence(
        sqlite3.connect(":memory:"),
        {"artifactRef": "sha256:" + "a" * 64, "kind": "correspondence", "localId": "c"},
        limit=1,
    )
    assert value["status"] == "unavailable"
    assert value["coverage"]["complete"] is False


def test_correspondence_reference_must_be_owner_qualified():
    with pytest.raises(ValueError):
        queries.query_v3_correspondence(sqlite3.connect(":memory:"), {"localId": "c"}, limit=1)
