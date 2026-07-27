from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.audit_enrichment import (
    audit_queries_from_elaborated_payload,
    unavailable_audit_queries,
)
from ladon.elaborated_extraction import run_elaborated_helper
from ladon.ir import LeanAuditQuery


REPO_ROOT = Path(__file__).parents[1]
REAL_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "lean_declarations"


def fake_payload() -> dict:
    return {
        "version": "2",
        "helperVersion": "fixture-elaborated-helper",
        "leanVersion": "4.fixture",
        "declarations": [
            {
                "fullyQualifiedName": "Root.theorem",
                "ownerModule": "Root",
                "status": "complete",
                "renderedType": "True",
                "renderedTypeTruncated": False,
                "axioms": {
                    "items": ["Root.axiom"],
                    "total": 1,
                    "truncated": False,
                    "status": "complete",
                },
            },
            {
                "fullyQualifiedName": "Root.partial",
                "ownerModule": "Root",
                "status": "complete",
                "renderedType": "True",
                "axioms": {
                    "items": ["Root.axiom"],
                    "total": 2,
                    "truncated": True,
                    "status": "partial",
                    "reason": "fixture axiom cap reached",
                },
            },
        ],
    }


def test_fake_helper_evidence_resolves_exact_check_and_axiom_queries() -> None:
    source = "\n".join(
        [
            "#check Root.theorem",
            "#print axioms Root.theorem",
            "#check Root.missing",
            "#print axioms Root.partial",
            "#check Root.theorem True",
            "",
        ]
    )

    queries = audit_queries_from_elaborated_payload(
        "Root.Audit",
        "Root/Audit.lean",
        source,
        fake_payload(),
    )
    by_kind_subject = {
        (row.kind, row.subject): row
        for row in queries.values()
    }

    assert_complete_check(by_kind_subject[("check", "Root.theorem")])
    assert_complete_axiom_query(
        by_kind_subject[("print_axioms", "Root.theorem")]
    )
    assert_incomplete_query_states(by_kind_subject)


def assert_complete_check(check: LeanAuditQuery) -> None:
    """Require exact identity, type, owner, and authority evidence."""

    assert check.status == "complete"
    assert check.referenced_declaration == "Root.theorem"
    assert check.referenced_owner == "Root"
    assert check.rendered_type == "True"
    assert check.backend == "lean_elaborated_helper"
    assert check.authority == "lean_environment"
    assert "theorem truth" in check.nonclaim


def assert_complete_axiom_query(axioms: LeanAuditQuery) -> None:
    """Require one bounded Lean-reported axiom result."""

    assert axioms.status == "complete"
    assert axioms.axioms.items == ("Root.axiom",)
    assert axioms.axioms.authority == "lean_environment"
    assert "theorem truth" in axioms.nonclaim


def assert_incomplete_query_states(
    by_kind_subject: dict[tuple[str, str], LeanAuditQuery],
) -> None:
    """Require unresolved, partial, and unsupported states to stay distinct."""

    unresolved = by_kind_subject[("check", "Root.missing")]
    assert unresolved.status == "unresolved"
    assert unresolved.referenced_declaration is None

    partial = by_kind_subject[("print_axioms", "Root.partial")]
    assert partial.status == "partial"
    assert partial.reason == "fixture axiom cap reached"

    unsupported = by_kind_subject[("check", "Root.theorem True")]
    assert unsupported.status == "unavailable"
    assert "bare declaration identity" in unsupported.reason


def test_failed_helper_preserves_timeout_and_lexical_identity() -> None:
    queries = unavailable_audit_queries(
        "Root.Audit",
        "Root/Audit.lean",
        "#check Root.theorem\n#print axioms Root.theorem\n",
        "Lean elaborated helper timed out for Root/Audit.lean",
    )

    assert len(queries) == 2
    assert {row.status for row in queries.values()} == {"timeout"}
    assert {row.authority for row in queries.values()} == {"lean_runtime"}
    assert all(row.referenced_declaration is None for row in queries.values())
    assert all("lexical command remains" in row.nonclaim for row in queries.values())


@pytest.mark.skipif(shutil.which("lake") is None, reason="lake is unavailable")
def test_real_helper_supplies_exact_check_and_axiom_results(
    tmp_path: Path,
) -> None:
    fixture = built_real_fixture(tmp_path)
    source_path = fixture / "LadonDeclarationFixture.lean"
    payload = run_elaborated_helper(
        fixture,
        source_path,
        "LadonDeclarationFixture",
    )

    queries = audit_queries_from_elaborated_payload(
        "LadonDeclarationFixture",
        "LadonDeclarationFixture.lean",
        source_path.read_text(encoding="utf-8"),
        payload,
    )
    by_kind = {row.kind: row for row in queries.values()}

    check = by_kind["check"]
    assert check.status == "complete"
    assert check.referenced_declaration == (
        "LadonDeclarationFixture.theoremKind"
    )
    assert check.referenced_owner == "LadonDeclarationFixture"
    assert check.rendered_type == "True"

    axioms = by_kind["print_axioms"]
    assert axioms.status == "complete"
    assert axioms.referenced_declaration == (
        "LadonDeclarationFixture.directAxiomReference"
    )
    assert "LadonDeclarationFixture.axiomKind" in axioms.axioms.items


def built_real_fixture(tmp_path: Path) -> Path:
    """Copy and explicitly build the Lean fixture without checkout-local state."""

    fixture = tmp_path / "lean_declarations"
    shutil.copytree(
        REAL_FIXTURE,
        fixture,
        ignore=shutil.ignore_patterns(".lake"),
    )
    process = subprocess.run(
        ["lake", "build"],
        cwd=fixture,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert process.returncode == 0, process.stderr or process.stdout
    return fixture
