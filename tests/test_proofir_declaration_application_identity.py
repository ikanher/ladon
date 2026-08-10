from __future__ import annotations

from ladon.semantic_candidate_worker import _application_subject, _subject


def _row(name: str) -> dict[str, str]:
    return {"name": name, "typeDisplay": "Nat → Nat", "typeStructural": "forallE Nat Nat"}


def test_equal_types_do_not_collapse_declaration_identity() -> None:
    first = _subject("declaration", _row("Pkg.First"))
    second = _subject("declaration", _row("Pkg.Second"))
    statement = _subject("statement", _row("goal"))
    assert first["fingerprint"] != second["fingerprint"]
    assert first["localId"] != second["localId"]
    assert statement["fingerprint"]["scheme"]["name"] == "lean-expr-structural"


def test_candidate_application_is_distinct_from_goal_statement() -> None:
    statement = _subject("statement", _row("goal"))
    declaration = _subject("declaration", _row("Pkg.rule"))
    application = _application_subject(statement, declaration, [])
    assert application["kind"] == "candidate-application"
    assert application["localId"] != statement["localId"]
    assert application["fingerprint"]["scheme"]["name"] == "lean-candidate-application"


def test_application_identity_changes_with_ordered_substitutions_and_context() -> None:
    statement = _subject("statement", _row("goal"))
    declaration = _subject("declaration", _row("Pkg.rule"))
    context_a = {
        "kind": "local-context",
        "localId": "context:a",
        "fingerprint": {"scheme": {"name": "lean-local-context", "version": "1"}, "digest": "sha256:" + "a" * 64},
    }
    context_b = {**context_a, "localId": "context:b"}
    substitutions = [{"variable": "x", "termDisplay": "0", "termStructural": "OfNat 0"}]
    reordered = [{"variable": "x", "termDisplay": "1", "termStructural": "OfNat 1"}]
    first = _application_subject(statement, declaration, [], substitutions, context_a)
    second = _application_subject(statement, declaration, [], reordered, context_a)
    third = _application_subject(statement, declaration, [], substitutions, context_b)
    assert len({first["localId"], second["localId"], third["localId"]}) == 3
