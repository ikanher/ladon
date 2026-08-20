from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pytest

from ladon.lean_toolchain import LeanToolchainError, resolve_toolchain_context
from ladon.proof_search_cli import _dispatch_explain
from ladon.proof_search_type import TypeSearchRequest, query_type_shortlist
from ladon.proofir_result_dimensions import project_dimensions


def _declaration_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE declarations("
            "id TEXT,name TEXT,candidate_name TEXT,type_text TEXT,type_text_truncated INTEGER,"
            "type_status TEXT,authority TEXT,module TEXT,path TEXT,line INTEGER,"
            "namespace TEXT,package TEXT,rendered_type TEXT,conclusion_text TEXT)"
        )
        connection.execute(
            "INSERT INTO declarations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "id",
                "Demo.proof",
                "Demo.proof",
                "True",
                0,
                "lean-rendered",
                "lean_environment",
                "Demo",
                "Demo.lean",
                1,
                "Demo",
                "project",
                "True",
                "True",
            ),
        )


def test_explain_compares_indexed_type_not_declaration_name(tmp_path: Path) -> None:
    database = tmp_path / "proof.sqlite"
    _declaration_database(database)
    args = argparse.Namespace(
        goal="True",
        candidate="Demo.proof",
        module="Demo",
        assumption=[],
        suggestion_cap=10,
        freshness="stored",
        raw_signature=False,
    )

    result = _dispatch_explain(args, tmp_path, database)

    assert result["classification"] == "applicable"
    assert result["normalization"]["peeledConclusion"] == "True"


def test_type_text_scope_requires_a_population_root() -> None:
    with pytest.raises(ValueError, match="scope"):
        TypeSearchRequest("Nat", scope="module")


def test_type_text_module_scope_requires_and_uses_module_filter() -> None:
    request = TypeSearchRequest("Nat", scope="module", module="Demo")
    assert request.scope == "module"


def test_type_text_freshness_verification_is_not_echoed() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE declarations("
        "id TEXT,name TEXT,candidate_name TEXT,namespace TEXT,module TEXT,package TEXT,"
        "path TEXT,line INTEGER,type_status TEXT,rendered_type TEXT,conclusion_text TEXT,type_text TEXT)"
    )
    with pytest.raises(ValueError, match="freshness"):
        query_type_shortlist(
            connection,
            TypeSearchRequest("Nat", freshness="verify"),
        )


@pytest.mark.parametrize(
    ("parent", "child"),
    [
        ("ambient-selected-application-check", "explicit-pinned-application-check"),
        ("not-assessed", "explicit-pinned-application-check"),
    ],
)
def test_authority_cannot_promote_to_explicit_pinned(
    parent: str, child: str
) -> None:
    with pytest.raises(ValueError, match="authority"):
        project_dimensions(
            child,
            "partial",
            parent_authority=parent,
            parent_completeness="partial",
        )


def test_toolchain_preflight_uses_worker_environment(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "lean-toolchain").write_text(
        "leanprover/lean4:v4.20.0\n", encoding="utf-8"
    )
    for name, label in (("lake", "Lake"), ("lean", "Lean")):
        executable = repo / name
        executable.write_text(
            "#!/bin/sh\n"
            "if [ \"$SECRET\" = allow ]; then "
            f"echo '{label} version 4.20.0'; "
            f"else echo '{label} version 0.0.0'; fi\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)

    with pytest.raises(LeanToolchainError, match="pin mismatch"):
        resolve_toolchain_context(
            repo,
            lake_path=repo / "lake",
            lean_path=repo / "lean",
            selection_mode="explicit",
            environment={"PATH": str(repo), "HOME": str(tmp_path), "SECRET": "allow"},
        )
