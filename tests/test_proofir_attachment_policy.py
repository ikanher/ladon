from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ladon.proofir_attachment_policy import (
    MAX_CANDIDATES,
    POLICY_DIGEST,
    POLICY_VERSION,
    resolve_attachment,
    resolve_source_map_anchor,
)

FIXTURES = Path(__file__).parent / "fixtures/proofir_attachments/resolver-cases-v3.json"


def _digest(character: str) -> str:
    return "sha256:" + character * 64


def _surface(**overrides: Any) -> dict[str, Any]:
    value = {
        "declarationName": "M.goal",
        "environmentRef": _digest("e"),
        "declarationFingerprint": _digest("f"),
        "declarationRef": "lean-decl:M.goal",
        "sourcePath": "M.lean",
        "contentHash": _digest("c"),
        "sourceRange": {"startLine": 10, "endLine": 12},
        "module": "M",
    }
    value.update(overrides)
    return value


def _declaration(identifier: str = "decl:goal", **overrides: Any) -> dict[str, Any]:
    value = {
        "id": identifier,
        "declaration": "M.goal",
        "declarationRef": "lean-decl:M.goal",
        "environmentRef": _digest("e"),
        "declarationFingerprint": _digest("f"),
        "sourceRef": {"kind": "surface", "localId": f"surface:{identifier}"},
        "sourcePath": "M.lean",
        "contentHash": _digest("c"),
        "sourceRange": {"startLine": 10, "endLine": 12},
        "module": "M",
    }
    value.update(overrides)
    return value


def test_policy_identity_is_versioned_and_content_addressed() -> None:
    assert POLICY_VERSION == "proofir-attachment-policy-v1"
    assert POLICY_DIGEST.startswith("sha256:") and len(POLICY_DIGEST) == 71


def test_type_fingerprint_alone_does_not_override_qualified_name() -> None:
    decision = resolve_attachment(
        _surface(declarationName="Alias"),
        [_declaration(declaration="Qualified.Alias")],
    )
    assert decision["selectionDecision"] == "unresolved"
    assert decision["selectedCandidateId"] is None
    assert decision["candidates"][0]["method"] == "identity-conflict-diagnostic"
    assert "declaration-name-mismatch" in decision["candidates"][0]["rejectionReasons"]


def test_exact_fingerprint_requires_the_same_qualified_name() -> None:
    decision = resolve_attachment(
        _surface(),
        [_declaration(declaration="M.goal")],
    )
    assert decision["selectionDecision"] == "selected"
    assert decision["candidates"][0]["method"] == "environment-fingerprint"


def test_emitted_declaration_reference_selects_with_same_environment() -> None:
    surface = _surface(
        declarationName="Alias", declarationFingerprint=None, declarationRef="decl:42"
    )
    declaration = _declaration(
        declaration="Qualified.Alias",
        declarationFingerprint=None,
        declarationRef="decl:42",
    )
    decision = resolve_attachment(surface, [declaration])
    assert decision["selectionDecision"] == "selected"
    assert decision["candidates"][0]["method"] == "producer-declaration"


def test_environment_conflict_retains_candidate_but_never_selects_it() -> None:
    decision = resolve_attachment(
        _surface(), [_declaration(environmentRef=_digest("x"))]
    )
    assert decision["selectionDecision"] == "unresolved"
    assert decision["selectedCandidateId"] is None
    assert decision["candidates"][0]["method"] == "identity-conflict-diagnostic"
    assert "environment-mismatch" in decision["candidates"][0]["rejectionReasons"]


def test_duplicate_strongest_candidates_are_ambiguous_and_all_retained() -> None:
    decision = resolve_attachment(
        _surface(), [_declaration("decl:a"), _declaration("decl:b")]
    )
    assert decision["selectionDecision"] == "ambiguous"
    assert decision["selectedCandidateId"] is None
    assert [row["declarationId"] for row in decision["candidates"]] == [
        "decl:a",
        "decl:b",
    ]
    assert decision["rejectionReasons"] == ["multiple-strongest-candidates"]


def test_duplicate_content_without_identity_is_ambiguous() -> None:
    surface = _surface(
        environmentRef=None, declarationFingerprint=None, declarationRef=None
    )
    declarations = [
        _declaration(
            identifier,
            environmentRef=None,
            declarationFingerprint=None,
            declarationRef=None,
        )
        for identifier in ("decl:a", "decl:b")
    ]
    decision = resolve_attachment(surface, declarations)
    assert decision["selectionDecision"] == "ambiguous"
    assert {row["method"] for row in decision["candidates"]} == {"content-range"}


def test_same_content_at_different_path_never_claims_exact_path_evidence() -> None:
    surface = _surface(
        environmentRef=None,
        declarationFingerprint=None,
        declarationRef=None,
        sourcePath="Other.lean",
    )
    declaration = _declaration(
        environmentRef=None, declarationFingerprint=None, declarationRef=None
    )
    decision = resolve_attachment(surface, [declaration])
    candidate = decision["candidates"][0]
    assert candidate["method"] == "content-range"
    assert "path" not in candidate["method"]


def test_name_only_match_is_a_diagnostic_and_not_an_attachment() -> None:
    decision = resolve_attachment(
        _surface(
            environmentRef=None,
            declarationFingerprint=None,
            declarationRef=None,
            sourcePath=None,
            contentHash=None,
            sourceRange=None,
            module=None,
        ),
        [
            _declaration(
                environmentRef=None,
                declarationFingerprint=None,
                declarationRef=None,
                sourcePath=None,
                contentHash=None,
                sourceRange=None,
                module=None,
            )
        ],
    )
    assert decision["selectionDecision"] == "none"
    assert decision["selectedCandidateId"] is None
    assert decision["candidates"][0]["method"] == "name-only-diagnostic"


def test_content_and_path_evidence_cannot_claim_exact_identity() -> None:
    declaration = _declaration(
        environmentRef=None, declarationFingerprint=None, declarationRef=None
    )
    surface = _surface(
        environmentRef=None, declarationFingerprint=None, declarationRef=None
    )
    decision = resolve_attachment(surface, [declaration])
    assert decision["selectionDecision"] == "selected"
    assert decision["candidates"][0]["method"] == "content-range"
    assert decision["candidates"][0]["confidence"] == "strong"
    assert decision["semanticAcceptance"] is False


def test_stale_source_is_retained_without_freshness_promotion() -> None:
    surface = _surface(
        environmentRef=None,
        declarationFingerprint=None,
        declarationRef=None,
        contentHash=_digest("s"),
    )
    declaration = _declaration(
        environmentRef=None, declarationFingerprint=None, declarationRef=None
    )
    decision = resolve_attachment(surface, [declaration])
    assert decision["selectionDecision"] == "selected"
    assert decision["candidates"][0]["method"] == "path-range"
    assert decision["candidates"][0]["freshness"] == "stale"
    assert "content-digest-mismatch" in decision["candidates"][0]["rejectionReasons"]


@pytest.mark.parametrize("unsafe_path", ["../Escape.lean", "/tmp/Escape.lean"])
def test_escaping_or_absolute_paths_are_diagnostic_only(unsafe_path: str) -> None:
    decision = resolve_attachment(_surface(sourcePath=unsafe_path), [_declaration()])
    assert decision["selectionDecision"] == "unresolved"
    assert "unsafe-source-path" in decision["rejectionReasons"]


def test_candidate_bound_is_enforced_before_work() -> None:
    with pytest.raises(ValueError, match="candidate bound"):
        resolve_attachment(
            _surface(), [_declaration(f"decl:{index}") for index in range(MAX_CANDIDATES + 1)]
        )


def test_native_source_map_adapter_uses_the_same_resolver_result() -> None:
    anchor = {
        "declName": "M.goal",
        "sourcePath": "M.lean",
        "contentDigest": _digest("c"),
        "start": {"line": 10},
        "end": {"line": 12},
        "module": "M",
    }
    declaration = _declaration(
        declarationFingerprint=None,
        declarationRef=None,
        sourceRange={"start": {"line": 10}, "end": {"line": 12}},
    )
    adapted = resolve_source_map_anchor(
        anchor, [declaration], environment_ref=_digest("e")
    )
    direct = resolve_attachment(
        {
            "declarationName": "M.goal",
            "environmentRef": _digest("e"),
            "declarationFingerprint": None,
            "declarationRef": None,
            "sourcePath": "M.lean",
            "contentHash": _digest("c"),
            "sourceRange": {"start": {"line": 10}, "end": {"line": 12}},
            "module": "M",
        },
        [declaration],
    )
    assert adapted == direct


def test_json_fixture_covers_required_resolver_families() -> None:
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert {row["case"] for row in fixtures} == {
        "environment-fingerprint",
        "producer-declaration",
        "content-range",
        "duplicate-content",
        "ambiguous-name",
        "stale-source",
        "escaping-path",
    }
