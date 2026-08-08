from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from ladon.cli import main
from ladon.proof_search_index import (
    ProofSearchIndexError,
    build_proof_search_index,
    default_proof_search_index_path,
    inspect_proof_search_index,
    query_proof_search_index,
)
from ladon.proof_search_schema import (
    EXPECTED_FOREIGN_KEYS,
    REQUIRED_LOOKUP_INDEX_COLUMNS,
    REQUIRED_LOOKUP_INDEXES,
    REQUIRED_QUERY_SURFACES,
    schema_foreign_keys,
    schema_index_columns,
    schema_lookup_indexes,
    schema_query_surfaces,
)


def test_v2_index_builds_repository_local_lexical_navigation(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)

    result = build_proof_search_index(repo)

    assert result.index_path == default_proof_search_index_path(repo)
    assert result.index_path.is_file()
    assert result.payload["status"] == "complete"
    assert result.payload["freshness"] == "fresh"
    assert result.payload["evidenceStatus"] == "lexical-fallback"
    assert result.payload["counts"] == {
        "modules": 3,
        "declarations": 4,
        "moduleImports": 2,
        "structures": 1,
        "declarationDependencies": 0,
        "binders": 0,
        "structureFields": 0,
        "lineageClosures": 0,
        "lineageNodes": 0,
        "lineageEdges": 0,
        "lineageTrust": 0,
        "lineageSccMembers": 0,
        "lineageOmissions": 0,
        "typeTextTruncations": 0,
        "proofirArtifacts": 0,
        "proofirRelations": 0,
        "proofirDiagnostics": 0,
        "proofirSurfaces": 0,
        "proofirClaims": 0,
        "proofirSurfaceClaims": 0,
        "proofirReplayRuns": 0,
        "proofirReplaySurfaces": 0,
        "proofirDags": 0,
        "proofirDagNodes": 0,
        "proofirDagEdges": 0,
        "proofirDagAuthorities": 0,
        "proofirDagWitnesses": 0,
        "proofirDagOmissions": 0,
        "proofirAttachmentCandidates": 0,
        "proofirAttachments": 0,
    }


def test_v1_schema_has_both_graph_directions_and_navigation_indexes(
    tmp_path: Path,
) -> None:
    result = build_proof_search_index(sample_repository(tmp_path))

    with sqlite3.connect(result.index_path) as connection:
        indexes = schema_lookup_indexes(connection)
        index_columns = schema_index_columns(connection)
        query_surfaces = schema_query_surfaces(connection)
        foreign_keys = schema_foreign_keys(connection)
        reverse_plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT source FROM module_imports WHERE target = ?",
            ("Base",),
        ).fetchall()
        package_plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT id FROM declarations WHERE package = ?",
            ("conventional",),
        ).fetchall()
        alias_plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT source FROM aliases WHERE target = ?",
            ("Demo.bounded",),
        ).fetchall()
        dependency_plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT source FROM declaration_dependencies WHERE target = ?",
            ("Demo.bounded",),
        ).fetchall()

    assert REQUIRED_LOOKUP_INDEXES <= indexes
    assert index_columns == REQUIRED_LOOKUP_INDEX_COLUMNS
    assert REQUIRED_QUERY_SURFACES <= query_surfaces
    assert EXPECTED_FOREIGN_KEYS <= foreign_keys
    assert any("idx_import_target" in str(row) for row in reverse_plan)
    assert any("idx_declarations_package" in str(row) for row in package_plan)
    assert any("idx_alias_target" in str(row) for row in alias_plan)
    assert any("idx_dependency_target" in str(row) for row in dependency_plan)


def test_sql_constraints_reject_invalid_owned_rows(tmp_path: Path) -> None:
    result = build_proof_search_index(sample_repository(tmp_path))

    with sqlite3.connect(result.index_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            connection.execute(
                """
                INSERT INTO declarations(
                    id, name, candidate_name, namespace, kind, module, package,
                    path, line, column_number, start_offset, end_offset,
                    block_sha256, type_text, type_text_bytes, type_text_truncated,
                    type_status, authority, privacy, locality, structure_name
                ) VALUES (
                    'bad', 'bad', 'bad', '', 'theorem', 'Missing.Module',
                    'missing', 'Missing.lean', 1, 1, 0, 1, NULL, ': True', 6,
                    0, 'lexical-signature', 'lexical_text', 'public', 'global', NULL
                )
                """
            )
        except sqlite3.IntegrityError as exc:
            assert "FOREIGN KEY constraint failed" in str(exc)
        else:
            raise AssertionError("declaration with a missing owner was accepted")


def test_index_status_detects_source_drift(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)

    assert inspect_proof_search_index(repo)["freshness"] == "fresh"

    (repo / "Base.lean").write_text(
        "def baseValue : Nat := 2\n",
        encoding="utf-8",
    )

    stale = inspect_proof_search_index(repo)
    assert stale["freshness"] == "stale-source"
    assert stale["generationIdentity"] != stale["currentGenerationIdentity"]


def test_size_limit_refuses_publish_and_preserves_previous_generation(
    tmp_path: Path,
) -> None:
    repo = sample_repository(tmp_path)
    completed = build_proof_search_index(repo)
    database = completed.index_path
    previous = database.read_bytes()

    try:
        build_proof_search_index(repo, max_index_bytes=64 * 1024)
    except ProofSearchIndexError as exc:
        assert "SQLite index build failed" in str(exc) or "configured limit" in str(exc)
    else:
        raise AssertionError("constrained build unexpectedly succeeded")

    assert database.read_bytes() == previous


def test_live_project_local_build_lock_reports_owner_pid(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)
    database = default_proof_search_index_path(repo)
    lock = database.with_name(f"{database.name}.lock")
    lock.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")

    status = inspect_proof_search_index(repo)
    assert status["buildLock"] == {
        "path": str(lock),
        "pid": os.getpid(),
        "status": "active",
    }

    try:
        build_proof_search_index(repo)
    except ProofSearchIndexError as exc:
        assert str(os.getpid()) in str(exc)
        assert "already active" in str(exc)
    else:
        raise AssertionError("concurrent index build unexpectedly started")


def test_explicit_external_index_retains_repository_identity(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path / "repo")
    external = tmp_path / "state" / "proof.sqlite"

    result = build_proof_search_index(repo, index_path=external)
    status = inspect_proof_search_index(repo, index_path=external)

    assert result.index_path == external
    assert status["repository"] == str(repo.resolve())
    assert status["freshness"] == "fresh"


def test_query_is_bounded_source_linked_and_authority_labeled(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)

    result = query_proof_search_index(repo, text="bounded", limit=1)

    assert result["returned"] == 1
    assert result["truncated"] is True
    assert result["rows"][0]["candidateName"] == "Demo.bounded"
    assert result["rows"][0]["authority"] == "lexical_text"
    assert "not Lean-resolved" in result["nonclaim"]


def test_module_import_and_closure_scopes_are_explicit(tmp_path: Path) -> None:
    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)

    direct = query_proof_search_index(
        repo,
        scope="imports",
        roots=("Main",),
        limit=20,
    )
    closure = query_proof_search_index(
        repo,
        scope="closure",
        roots=("Main",),
        limit=20,
    )

    assert {row["module"] for row in direct["rows"]} == {"Main", "Middle"}
    assert {row["module"] for row in closure["rows"]} == {
        "Base",
        "Main",
        "Middle",
    }
    assert direct["scope"]["includedModules"] == 2
    assert closure["scope"]["includedModules"] == 3


def test_external_scope_returns_omission_evidence_not_global_absence(
    tmp_path: Path,
) -> None:
    repo = sample_repository(tmp_path)
    build_proof_search_index(repo)

    result = query_proof_search_index(repo, scope="external")

    assert result["rows"] == []
    assert result["scope"]["omissions"] == [
        {
            "kind": "package",
            "subject": "external",
            "reason": "external_declarations_not_indexed_v1",
        }
    ]


def test_installed_cli_contract_uses_canonical_output_options(
    tmp_path: Path,
    capsys,
) -> None:
    repo = sample_repository(tmp_path)

    status = main(
        [
            "proof-search",
            "index",
            "build",
            "--repo-root",
            str(repo),
            "--format",
            "json",
            "--output",
            "-",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["schema"] == "ladon-proof-search-index-result-v1"
    assert payload["operation"] == "build"


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
