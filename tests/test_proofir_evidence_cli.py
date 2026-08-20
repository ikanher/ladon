from __future__ import annotations

from ladon.proof_search_cli import _render_text, build_proof_search_parser


def test_evidence_cli_has_caller_neutral_selectors_and_route_bounds() -> None:
    parser = build_proof_search_parser()
    theorem = parser.parse_args(["evidence", "theorem", "Theorem.Name", "--repo-root", ".", "--format", "json"])
    route = parser.parse_args(["evidence", "route", "dag.id:route", "--start", "fact.id", "--end", "claim.id"])
    triage = parser.parse_args(["evidence", "triage", "all", "--limit", "7"])
    assert theorem.kind == "theorem"
    assert route.start == "fact.id"
    assert route.end == "claim.id"
    assert triage.kind == "triage"
    assert triage.limit == 7


def test_text_renderer_includes_sections_and_nonclaims() -> None:
    text = _render_text({"operation": "evidence", "schema": "v1", "surfaces": {"rows": [{"surfaceId": "s", "status": "quoted"}], "returned": 1, "matched": 1, "truncated": False}, "nonclaims": ["quoted only"]})
    assert "surfaces: returned=1" in text
    assert "nonclaim: quoted only" in text
