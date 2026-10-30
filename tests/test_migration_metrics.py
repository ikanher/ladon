"""Adversarial preservation checks, written before the migration implementation."""

import sqlite3

import pytest

from ladon.migration_metrics import compare_databases


def pair(tmp_path):
    before, after = tmp_path / "before.sqlite", tmp_path / "after.sqlite"
    with sqlite3.connect(before) as db:
        db.executescript("""
            CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
            INSERT INTO metadata VALUES('schemaVersion','6'),('generationIdentity','original');
            CREATE TABLE declarations(id TEXT PRIMARY KEY,authority TEXT,type_text TEXT);
            INSERT INTO declarations VALUES('a','lexical_text','True'),('b','lean_environment','False → True');
            CREATE TABLE declaration_dependencies(source TEXT,target TEXT,
                FOREIGN KEY(source) REFERENCES declarations(id),
                FOREIGN KEY(target) REFERENCES declarations(id));
            INSERT INTO declaration_dependencies VALUES('b','a');
        """)
        db.commit()
        with sqlite3.connect(after) as out:
            db.backup(out)
    return before, after


def change(path, sql):
    with sqlite3.connect(path) as db:
        db.executescript(sql)


def test_additive_schema_with_exact_declared_metadata_change_is_lossless(tmp_path):
    before, after = pair(tmp_path)
    change(
        after,
        "CREATE TABLE ideas(id TEXT PRIMARY KEY); UPDATE metadata SET value='7' WHERE key='schemaVersion';",
    )
    result = compare_databases(
        before,
        after,
        expected_metadata={"schemaVersion": "7"},
        queries={"names": "SELECT id FROM declarations ORDER BY id"},
    )
    assert result["accepted"]
    assert result["hardViolationCount"] == 0
    assert result["dataLoss"]["failed"] == result["linkLoss"]["failed"] == 0
    assert result["queryLoss"] == {"failed": 0, "checked": 1, "fraction": 0.0}


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM declarations WHERE id='a';",
        "UPDATE declarations SET type_text='False' WHERE id='a';",
        "UPDATE declarations SET authority='lean_environment' WHERE id='a';",
        "UPDATE declarations SET type_text=CASE id WHEN 'a' THEN 'False → True' ELSE 'True' END;",
        "UPDATE metadata SET value='new' WHERE key='generationIdentity';",
        "DROP TABLE declaration_dependencies;",
    ],
)
def test_equal_counts_or_apparent_authority_improvement_do_not_hide_damage(tmp_path, sql):
    before, after = pair(tmp_path)
    change(after, sql)
    result = compare_databases(before, after)
    assert not result["accepted"]
    assert result["hardViolationCount"] > 0


def test_swapped_dependency_is_detected_without_row_count_change(tmp_path):
    before, after = pair(tmp_path)
    change(after, "UPDATE declaration_dependencies SET source='a',target='b';")
    result = compare_databases(before, after)
    assert result["linkLoss"]["failed"] == 1
    assert not result["accepted"]


def test_allowlist_requires_exact_expected_value(tmp_path):
    before, after = pair(tmp_path)
    change(after, "UPDATE metadata SET value='999' WHERE key='schemaVersion';")
    assert not compare_databases(before, after, expected_metadata={"schemaVersion": "7"})[
        "accepted"
    ]


def test_query_mismatch_and_cycle_are_independent_hard_failures(tmp_path):
    before, after = pair(tmp_path)
    change(
        after,
        """
        CREATE TABLE idea_dependencies(parent_idea_id TEXT,child_idea_id TEXT);
        INSERT INTO idea_dependencies VALUES('x','y'),('y','x');
        CREATE TABLE extra(value TEXT);
    """,
    )
    result = compare_databases(
        before,
        after,
        queries={"tables": "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"},
    )
    assert not result["accepted"]
    assert result["queryLoss"]["failed"] == 1
    assert any("cycle" in reason for reason in result["violations"])


def test_missing_database_does_not_get_created(tmp_path):
    before, _ = pair(tmp_path)
    missing = tmp_path / "missing.sqlite"
    with pytest.raises((OSError, sqlite3.Error)):
        compare_databases(before, missing)
    assert not missing.exists()


def test_zero_queries_are_unassessed_not_perfect_coverage(tmp_path):
    result = compare_databases(*pair(tmp_path))
    assert result["queryLoss"] == {"failed": 0, "checked": 0, "fraction": None}


def test_same_rows_without_foreign_keys_are_not_preserved(tmp_path):
    before, after = pair(tmp_path)
    with sqlite3.connect(after) as db:
        db.executescript("""
            ALTER TABLE declaration_dependencies RENAME TO old_dependencies;
            CREATE TABLE declaration_dependencies(source TEXT,target TEXT);
            INSERT INTO declaration_dependencies SELECT * FROM old_dependencies;
            DROP TABLE old_dependencies;
        """)
    result = compare_databases(before, after)
    assert not result["accepted"]
    assert result["linkLoss"]["failed"] == 1


def test_dropped_lookup_index_is_a_hard_failure(tmp_path):
    before, after = pair(tmp_path)
    with sqlite3.connect(before) as db:
        db.execute("CREATE INDEX lookup_type ON declarations(type_text)")
    assert not compare_databases(before, after)["accepted"]
