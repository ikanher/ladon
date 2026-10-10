from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ladon.proof_search_index import (
    ProofSearchIndexError,
    build_proof_search_index,
    default_proof_search_index_path,
    inspect_proof_search_index,
    query_proof_search_index,
    update_proof_search_index,
)
from ladon.sqlite_publication import acquire_publication_lock, release_publication_lock


def test_source_delta_distinguishes_added_changed_and_removed_modules(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    built = build_proof_search_index(repo)
    initial = inspect_proof_search_index(repo)
    assert initial["freshness"] == "fresh"
    assert initial["generationIdentity"] == built.payload["generationIdentity"]
    assert initial["currentGenerationIdentity"] == built.payload["generationIdentity"]

    (repo / "Base.lean").write_text("def baseValue : Nat := 42\n", encoding="utf-8")
    (repo / "Middle.lean").unlink()
    (repo / "Fresh.lean").write_text("theorem newName : True := True.intro\n", encoding="utf-8")
    stale = inspect_proof_search_index(repo)
    assert stale["freshness"] == "stale-source"
    assert stale["sourceChanges"]["counts"] == {"added": 1, "changed": 1, "removed": 1}
    assert [row["module"] for row in stale["sourceChanges"]["samples"]["added"]] == ["Fresh"]
    assert inspect_proof_search_index(repo, verify_sources=False)["sourceChanges"]["status"] == "not-checked"


def test_source_delta_ignores_excluded_build_directory(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)
    generated = repo / ".lake/Generated.lean"
    generated.parent.mkdir()
    generated.write_text("theorem shouldNotAppear : True := True.intro\n", encoding="utf-8")
    status = inspect_proof_search_index(repo)
    assert status["freshness"] == "fresh"
    assert status["sourceChanges"]["counts"] == {"added": 0, "changed": 0, "removed": 0}


def _three_new_modules(repo: Path) -> None:
    for name in ("NewA", "NewB", "NewC"):
        (repo / f"{name}.lean").write_text(
            f"theorem {name}.result : True := True.intro\n", encoding="utf-8"
        )


def test_status_changed_listing_is_bounded(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)
    _three_new_modules(repo)
    status = inspect_proof_search_index(repo, changed_limit=1)
    assert status["sourceChanges"]["counts"]["added"] == 3
    assert status["sourceChanges"]["truncated"]["added"] is True
    assert [row["module"] for row in status["sourceChanges"]["samples"]["added"]] == ["NewA"]


def test_status_text_is_compact_and_changed_listing_is_explicit(tmp_path: Path, capsys) -> None:
    from ladon.cli import main

    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)
    _three_new_modules(repo)
    assert main(["proof-search", "index", "status", "--repo-root", str(repo), "--format", "text"]) == 0
    default_text = capsys.readouterr().out
    assert "source changes: added=3" in default_text
    assert "detailed index inventory: rerun with --details" in default_text
    assert "budget_bytes:" in default_text and "publisher:" in default_text
    assert "lookupIndexColumns:" not in default_text
    assert main([
        "proof-search", "index", "status", "--repo-root", str(repo),
        "--changed", "--format", "text",
    ]) == 0
    changed_text = capsys.readouterr().out
    assert "NewA" in changed_text and "NewB" in changed_text and "NewC" in changed_text


def test_build_refuses_source_change_before_publication(tmp_path: Path, monkeypatch) -> None:
    import ladon.proof_search_index as owner

    repo = sample_repository(tmp_path)
    previous = build_proof_search_index(repo).index_path.read_bytes()
    original = owner._write_database

    def mutate_after_write(*args, **kwargs):
        counts = original(*args, **kwargs)
        (repo / "Base.lean").write_text("def baseValue : Nat := 99\n", encoding="utf-8")
        return counts

    monkeypatch.setattr(owner, "_write_database", mutate_after_write)
    with pytest.raises(ProofSearchIndexError) as raised:
        build_proof_search_index(repo)
    assert raised.value.code == "source-changed"
    assert default_proof_search_index_path(repo).read_bytes() == previous


def test_verified_status_rejects_unstable_observation(tmp_path: Path, monkeypatch) -> None:
    import ladon.proof_search_index as owner

    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)
    original = owner.capture_repository_snapshot
    calls = 0

    def move_source(root):
        nonlocal calls
        calls += 1
        if calls == 2:
            (repo / "Base.lean").write_text("def baseValue : Nat := 18\n", encoding="utf-8")
        return original(root)

    monkeypatch.setattr(owner, "capture_repository_snapshot", move_source)
    status = inspect_proof_search_index(repo)
    assert status["freshness"] == "unstable-source"
    assert status["sourceChanges"]["status"] == "unstable"
    assert status["currentGenerationIdentity"] is None


def test_status_exposes_live_configuration_identity(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)
    (repo / "lakefile.toml").write_text("-- newly added configuration\n", encoding="utf-8")
    status = inspect_proof_search_index(repo)
    assert status["freshness"] == "stale-configuration"
    assert status["sourceChanges"]["counts"] == {"added": 0, "changed": 0, "removed": 0}
    assert status["sourceChanges"]["currentConfigurationFingerprint"] != status["configurationFingerprint"]


def test_incremental_update_matches_clean_build_after_source_changes(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path / "repo")
    old = build_proof_search_index(repo)
    (repo / "Base.lean").write_text("def baseNew : Nat := 9\n", encoding="utf-8")
    (repo / "Middle.lean").unlink()
    (repo / "New.lean").write_text("theorem freshResult : True := True.intro\n", encoding="utf-8")

    updated = update_proof_search_index(repo)
    assert updated.payload["operation"] == "update"
    assert updated.payload["generationIdentity"] != old.payload["generationIdentity"]
    assert updated.payload["reusedModules"] == 1
    assert updated.payload["extractedModules"] == 2
    _assert_update_accounting(updated.payload, old.payload["generationIdentity"])
    assert inspect_proof_search_index(repo)["freshness"] == "fresh"
    clean = build_proof_search_index(repo, index_path=tmp_path / "clean.sqlite")
    _assert_same_searches(repo, clean.index_path, ("baseValue", "baseNew", "freshResult"))
    _assert_lexical_tables_equal(updated.index_path, clean.index_path)
    assert updated.payload["generationIdentity"] == clean.payload["generationIdentity"]

    unchanged_bytes = updated.index_path.read_bytes()
    noop = update_proof_search_index(repo)
    assert noop.payload["status"] == "unchanged"
    assert updated.index_path.read_bytes() == unchanged_bytes


def _assert_same_searches(repo: Path, clean: Path, names: tuple[str, ...]) -> None:
    for name in names:
        before = query_proof_search_index(repo, text=name)["results"]
        after = query_proof_search_index(repo, index_path=clean, text=name)["results"]
        assert before == after


def _assert_update_accounting(payload: dict, base_generation: str) -> None:
    assert payload["baseGenerationIdentity"] == base_generation
    assert payload["sourceChanges"] == {"added": 1, "changed": 1, "removed": 1}
    assert payload["temporaryDatabaseBytes"] > 0


def _assert_lexical_tables_equal(updated: Path, clean: Path) -> None:
    queries = (
        "SELECT name,path,source_sha256 FROM modules ORDER BY name",
        "SELECT candidate_name,module,type_text FROM declarations ORDER BY candidate_name",
        "SELECT source,target FROM module_imports ORDER BY source,target",
        "SELECT name,module FROM structures ORDER BY module,name",
        "SELECT name,declaration_id FROM symbols ORDER BY name,declaration_id",
    )
    with sqlite3.connect(updated) as left, sqlite3.connect(clean) as right:
        for query in queries:
            assert left.execute(query).fetchall() == right.execute(query).fetchall()


@pytest.mark.parametrize("retained_kind", [
    "proofir", "binder", "lineage", "diagnostic", "v3-environment", "future-proofir",
])
def test_incremental_update_refuses_retained_evidence_and_keeps_base(
    tmp_path: Path, retained_kind: str
) -> None:
    repo = sample_repository(tmp_path)
    database = build_proof_search_index(repo).index_path
    with sqlite3.connect(database) as connection:
        generation = connection.execute(
            "SELECT value FROM metadata WHERE key='generationIdentity'"
        ).fetchone()[0]
        _insert_retained_evidence(connection, retained_kind, generation, repo)
    previous = database.read_bytes()
    assert update_proof_search_index(repo).payload["status"] == "unchanged"
    assert database.read_bytes() == previous
    (repo / "Base.lean").write_text("def another : Nat := 1\n", encoding="utf-8")
    with pytest.raises(ProofSearchIndexError) as raised:
        update_proof_search_index(repo)
    assert raised.value.code == "full-build-required"
    assert database.read_bytes() == previous


def _insert_retained_evidence(
    connection: sqlite3.Connection, kind: str, generation: str, repo: Path
) -> None:
    if kind == "proofir":
        connection.execute(
            "INSERT INTO proofir_artifacts VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("artifact", generation, "evidence.json", "sha256:abc", 1, "other", "v1", "cataloged", "{}", None),
        )
    elif kind == "binder":
        declaration = connection.execute("SELECT id FROM declarations LIMIT 1").fetchone()[0]
        connection.execute(
            "INSERT INTO binders VALUES (?,?,?,?,?,?,?,?)",
            (declaration, 0, "h", "explicit", "True", 1, "lexical", "True"),
        )
    elif kind == "lineage":
        connection.execute(
            "INSERT INTO lineage_closures VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "closure", "baseValue", "Base", "Base.lean", "plan", "fingerprint",
                str(repo), "source", "config", "toolchain", "helper", generation,
                "schema", "lean_environment", "complete", 1, "[]", 0, 0, "created",
            ),
        )
    elif kind == "diagnostic":
        connection.execute(
            "INSERT INTO proofir_diagnostics VALUES (?,?,?,?,?,?,?)",
            ("diagnostic", generation, None, "configuration", "catalog", "missing", "{}"),
        )
    elif kind == "v3-environment":
        connection.execute(
            "INSERT INTO proofir_v3_environments VALUES (?,?,?,?)",
            ("sha256:environment", None, None, "unresolved"),
        )
    else:
        connection.execute("CREATE TABLE proofir_future (payload TEXT NOT NULL)")
        connection.execute("INSERT INTO proofir_future VALUES ('retained')")
@pytest.mark.parametrize("filename,content", [
    ("lakefile.toml", "-- changed\n"),
    ("lean-toolchain", "leanprover/lean4:v4.0.0\n"),
])
def test_incremental_update_rejects_changed_configuration(
    tmp_path: Path, filename: str, content: str
) -> None:
    repo = sample_repository(tmp_path)
    database = build_proof_search_index(repo).index_path
    previous = database.read_bytes()
    (repo / filename).write_text(content, encoding="utf-8")
    with pytest.raises(ProofSearchIndexError) as raised:
        update_proof_search_index(repo)
    assert raised.value.code == "full-build-required"
    assert database.read_bytes() == previous


def test_incremental_update_requires_compatible_base(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    with pytest.raises(ProofSearchIndexError) as missing:
        update_proof_search_index(repo)
    assert missing.value.code == "full-build-required"
    database = default_proof_search_index_path(repo)
    database.parent.mkdir(parents=True)
    database.write_bytes(b"not a SQLite database")
    with pytest.raises(ProofSearchIndexError) as incompatible:
        update_proof_search_index(repo)
    assert incompatible.value.code == "full-build-required"
    assert database.read_bytes() == b"not a SQLite database"


def test_incremental_update_rebuilds_import_scope_and_fts(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path / "repo")
    build_proof_search_index(repo)
    (repo / "Middle.lean").unlink()
    (repo / "New.lean").write_text(
        "theorem uniqueReplacement : True := True.intro\n", encoding="utf-8"
    )
    (repo / "Main.lean").write_text(
        "import New\ntheorem mainReplacement : True := True.intro\n", encoding="utf-8"
    )
    updated = update_proof_search_index(repo)
    assert updated.payload["status"] == "complete"
    closure = query_proof_search_index(repo, scope="closure", roots=("Main",))
    assert {row["candidateName"] for row in closure["rows"]} == {
        "uniqueReplacement", "mainReplacement"
    }
    assert query_proof_search_index(repo, text="bounded")["results"] == []
    clean = build_proof_search_index(repo, index_path=tmp_path / "clean.sqlite")
    assert clean.payload["generationIdentity"] == updated.payload["generationIdentity"]
    assert query_proof_search_index(
        repo, index_path=clean.index_path, scope="closure", roots=("Main",)
    )["results"] == closure["results"]


def test_incremental_update_rejects_source_race_and_preserves_open_reader(
    tmp_path: Path, monkeypatch
) -> None:
    import ladon.proof_search_index_update as owner

    repo = sample_repository(tmp_path)
    database = build_proof_search_index(repo).index_path
    previous = database.read_bytes()
    (repo / "Fresh.lean").write_text(
        "theorem freshResult : True := True.intro\n", encoding="utf-8"
    )
    original = owner._insert_source

    def mutate_after_insert(connection, source):
        counts = original(connection, source)
        if source.module == "Fresh":
            (repo / "Fresh.lean").write_text(
                "theorem racedResult : True := True.intro\n", encoding="utf-8"
            )
        return counts

    monkeypatch.setattr(owner, "_insert_source", mutate_after_insert)
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as reader:
        with pytest.raises(ProofSearchIndexError) as raised:
            update_proof_search_index(repo)
        assert raised.value.code == "source-changed"
        assert reader.execute("SELECT value FROM metadata WHERE key='generationIdentity'").fetchone()[0]
    assert database.read_bytes() == previous


def test_incremental_update_keeps_open_reader_on_complete_old_generation(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    database = build_proof_search_index(repo).index_path
    (repo / "Fresh.lean").write_text("theorem fresh : True := True.intro\n", encoding="utf-8")
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as reader:
        old_generation = reader.execute(
            "SELECT value FROM metadata WHERE key='generationIdentity'"
        ).fetchone()[0]
        updated = update_proof_search_index(repo)
        assert reader.execute(
            "SELECT value FROM metadata WHERE key='generationIdentity'"
        ).fetchone()[0] == old_generation
    assert updated.payload["generationIdentity"] != old_generation
    assert query_proof_search_index(repo, text="fresh")["returned"] == 1


def test_incremental_update_refuses_busy_publisher(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    database = build_proof_search_index(repo).index_path
    original = database.read_bytes()
    (repo / "Fresh.lean").write_text("theorem fresh : True := True.intro\n", encoding="utf-8")
    lock = acquire_publication_lock(database)
    try:
        with pytest.raises(ProofSearchIndexError):
            update_proof_search_index(repo)
    finally:
        release_publication_lock(lock)
    assert database.read_bytes() == original


def test_incremental_update_publication_failure_preserves_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ladon.proof_search_index_update as owner

    repo = sample_repository(tmp_path)
    database = build_proof_search_index(repo).index_path
    original = database.read_bytes()
    (repo / "Fresh.lean").write_text("theorem fresh : True := True.intro\n", encoding="utf-8")

    def fail_publication(_source, _destination):
        raise OSError("injected publication failure")

    monkeypatch.setattr(owner, "durable_replace", fail_publication)
    with pytest.raises(OSError, match="injected publication failure"):
        update_proof_search_index(repo)
    assert database.read_bytes() == original
    assert not list(database.parent.glob(".proof-search.sqlite.*.tmp"))


def test_incremental_update_integrity_failure_preserves_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ladon.proof_search_index_update as owner

    repo = sample_repository(tmp_path)
    database = build_proof_search_index(repo).index_path
    original = database.read_bytes()
    (repo / "Fresh.lean").write_text("theorem fresh : True := True.intro\n", encoding="utf-8")

    def fail_integrity(_connection):
        raise ProofSearchIndexError("injected integrity failure")

    monkeypatch.setattr(owner, "_validate_database", fail_integrity)
    with pytest.raises(ProofSearchIndexError, match="injected integrity failure"):
        update_proof_search_index(repo)
    assert database.read_bytes() == original


def test_incremental_update_size_budget_preserves_base(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    database = build_proof_search_index(repo, max_index_bytes=2 * 1024 * 1024).index_path
    original = database.read_bytes()
    (repo / "Large.lean").write_text(
        "\n".join(f"theorem added_{number} : True := True.intro" for number in range(3000))
        + "\n", encoding="utf-8"
    )
    with pytest.raises(ProofSearchIndexError) as raised:
        update_proof_search_index(repo)
    assert raised.value.code == "index-storage-limit"
    assert database.read_bytes() == original



def sample_repository(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "Base.lean").write_text(
        "def baseValue : Nat := 1\n",
        encoding="utf-8",
    )
    (root / "Middle.lean").write_text(
        "import Base\nstructure Box where\n  value : Nat\n",
        encoding="utf-8",
    )
    (root / "Main.lean").write_text(
        """import Middle
namespace Demo
theorem bounded : baseValue ≤ 2 := by omega
theorem bounded_again : baseValue ≤ 3 := by omega
end Demo
""",
        encoding="utf-8",
    )
    return root
