from __future__ import annotations

from ladon.inspection_models import ArtifactIdentity
from ladon.inspection_report_adapter import _declaration_rows
from ladon.render_generated_family_candidates import (
    generated_family_candidate_lines,
)


def test_report_declarations_preserve_parser_and_lean_authority() -> None:
    artifact = ArtifactIdentity(
        kind="report",
        schema="ladon-report-v3",
        fingerprint="sha256:report",
        source_fingerprint="sha256:source",
    )
    dag = {
        "analysis_scope": {"effectiveScope": "selected"},
        "module_metadata": {
            "Parser": {
                "path": "Parser.lean",
                "textDeclarations": [
                    {
                        "id": "lexical-parser",
                        "name": "value",
                        "candidateName": "Parser.value",
                        "candidateStatus": "lexical_candidate",
                        "authority": "lexical_text",
                    }
                ],
            }
        },
    }
    sections = {
        "module_dag": dag,
        "declaration_graph": {
            "declarations": [
                {
                    "id": "graph-parser",
                    "declaration": "Parser.value",
                    "module": "Parser",
                    "extractionBackend": "lean_parser_helper",
                    "surface": {
                        "status": "unavailable",
                        "backend": "lean_elaborator",
                    },
                },
                {
                    "id": "graph-unavailable",
                    "declaration": "Unavailable.value",
                    "module": "Unavailable",
                },
                {
                    "id": "graph-lean",
                    "declaration": "Lean.value",
                    "module": "Lean",
                    "extractionBackend": "lean_elaborated_helper",
                    "surface": {
                        "status": "complete",
                        "backend": "lean_elaborator",
                        "leanVersion": "4.test",
                    },
                },
            ]
        },
    }

    rows, available = _declaration_rows(sections, dag, artifact)
    by_id = {row.identifier: row for row in rows}
    parser = by_id["graph-parser"]
    lexical = by_id["lexical-parser"]
    unavailable = by_id["graph-unavailable"]
    lean = by_id["graph-lean"]
    assert {
        "available": available,
        "parserAuthority": parser.authority,
        "parserStatus": parser.fields["candidate-status"],
        "lexicalAuthority": lexical.authority,
        "linkedAuthority": lexical.enrichments[0]["authority"],
        "linkedOverclaimsLean": (
            "Lean-resolved" in lexical.enrichments[0]["relationship"]
        ),
        "unavailableAuthority": unavailable.authority,
        "unavailableStatus": unavailable.fields["candidate-status"],
        "unavailableSurface": unavailable.enrichments[0]["status"],
        "unavailableBackend": unavailable.enrichments[0]["backend"],
        "leanAuthority": lean.authority,
        "leanStatus": lean.fields["candidate-status"],
    } == {
        "available": True,
        "parserAuthority": "lean_parser",
        "parserStatus": "parser_candidate",
        "lexicalAuthority": "lexical_text",
        "linkedAuthority": "lean_parser",
        "linkedOverclaimsLean": False,
        "unavailableAuthority": "unavailable",
        "unavailableStatus": "unavailable",
        "unavailableSurface": "unavailable",
        "unavailableBackend": "unavailable",
        "leanAuthority": "lean_environment",
        "leanStatus": "lean_resolved",
    }


def test_generated_family_text_renders_every_visible_candidate() -> None:
    candidate_ids = [f"generated-family-candidate-{index:02d}" for index in range(12)]
    module_dag = {
        "generated_family_candidates": {
            "profile": {
                "profileVersion": "test-profile-v1",
                "profileDigest": "sha256:test-profile",
            },
            "candidates": [
                {
                    "id": identifier,
                    "sequence": {
                        "parent": "Neutral.Rows",
                        "basenamePrefix": "Cell",
                        "memberCount": 4,
                    },
                    "clauses": [],
                    "memberPopulations": {"target_owned": 4},
                }
                for identifier in candidate_ids
            ],
            "coverage": {
                "candidates": {
                    "visible": len(candidate_ids),
                    "totalKnown": True,
                    "total": len(candidate_ids),
                }
            },
            "nonclaims": [
                {
                    "id": "advisory-only",
                    "text": "Generated-family evidence is advisory only.",
                }
            ],
        }
    }

    lines = generated_family_candidate_lines(module_dag)
    candidate_lines = [
        line for line in lines if line.startswith("- generated-family-candidate-")
    ]

    assert len(candidate_lines) == len(candidate_ids)
    for identifier in candidate_ids:
        assert any(line.startswith(f"- {identifier}:") for line in lines)
    assert "text projection omitted" not in "\n".join(lines)
