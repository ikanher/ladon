from __future__ import annotations

from ladon.atlas_diff import diff_atlases, render_atlas_diff_markdown


def test_diff_atlases_reports_added_removed_and_changed_rows() -> None:
    before = atlas_with_finding("A.Root", finding_count=1, signal_count=1)
    after = atlas_with_finding("A.Root", finding_count=2, signal_count=3)
    after["nodes"].append(
        {
            "id": "finding:repo/owner.json:1",
            "kind": "finding",
            "label": "new_kind: New.Subject",
            "data": {"kind": "new_kind", "subject": "New.Subject", "count": 1},
        }
    )
    after["edges"].append(
        {
            "source": "report:repo/owner.json",
            "target": "finding:repo/owner.json:1",
            "kind": "has_finding",
        }
    )
    before["nodes"].append(
        {
            "id": "finding:repo/owner.json:old",
            "kind": "finding",
            "label": "old_kind: Old.Subject",
            "data": {"kind": "old_kind", "subject": "Old.Subject", "count": 1},
        }
    )
    before["edges"].append(
        {
            "source": "report:repo/owner.json",
            "target": "finding:repo/owner.json:old",
            "kind": "has_finding",
        }
    )

    diff = diff_atlases(before, after)

    assert diff["summary"]["added"] == 1
    assert diff["summary"]["removed"] == 1
    assert diff["summary"]["changed"] == 3
    assert diff["added"][0]["key"] == "repo/owner.json|new_kind|New.Subject"
    assert diff["removed"][0]["key"] == "repo/owner.json|old_kind|Old.Subject"


def test_diff_atlases_specializes_proof_family_and_unresolved_reference_categories() -> None:
    before = atlas_with_finding("A.Root", signal_count=1)
    after = atlas_with_finding("A.Root", signal_count=2)
    after["nodes"].append(
        {
            "id": "finding:repo/owner.json:unresolved",
            "kind": "finding",
            "label": "unresolved_reference_class: unknown",
            "data": {"kind": "unresolved_reference_class", "subject": "unknown", "count": 4},
        }
    )
    after["edges"].append(
        {
            "source": "report:repo/owner.json",
            "target": "finding:repo/owner.json:unresolved",
            "kind": "has_finding",
        }
    )

    diff = diff_atlases(before, after)

    assert diff["summary"]["by_category"]["proof_family_pressure"]["changed"] == 1
    assert diff["summary"]["by_category"]["unresolved_reference_classes"]["added"] == 1


def test_diff_atlases_specializes_evidence_and_bridge_categories() -> None:
    before = atlas_with_finding("A.Root")
    after = atlas_with_finding("A.Root")
    after["nodes"][0]["data"]["packet_evidence"] = {
        "rows": 1,
        "incomplete": 1,
        "stale": 0,
    }
    after["nodes"][0]["data"]["declaration_evidence"] = {
        "rows": 2,
        "content_hashes": 1,
    }
    after["nodes"][0]["data"]["bridge_diagnostics"] = {
        "diagnostic_counts": {"proofir.name_only_join_warning": 1}
    }

    diff = diff_atlases(before, after)

    assert diff["summary"]["by_category"]["evidence_status"]["changed"] == 1
    assert diff["summary"]["by_category"]["bridge_diagnostics"]["added"] == 1


def test_diff_atlases_keeps_unreported_workflow_state_explicit() -> None:
    before = atlas_with_finding("A.Root")
    after = atlas_with_finding("A.Root")
    after["workflowDiagnostics"] = [
        {
            "authority": "ladon_analysis_bundle",
            "bundleStatus": "failed",
            "entryId": "owner",
            "nonclaim": "Workflow state only; no analysis evidence.",
            "reason": "runner failed",
            "required": True,
            "root": "A.lean",
            "state": "failed",
        }
    ]

    diff = diff_atlases(before, after)

    row = diff["added"][0]
    assert diff["summary"]["by_category"]["workflow_diagnostics"]["added"] == 1
    assert row["key"] == "owner"
    assert row["payload"]["state"] == "failed"
    assert row["payload"]["nonclaim"] == (
        "Workflow state only; no analysis evidence."
    )


def test_diff_atlases_keeps_declaration_dependency_kinds_separate() -> None:
    before = atlas_with_finding("A.Root")
    after = atlas_with_finding("A.Root")
    for atlas in (before, after):
        atlas["nodes"].extend(declaration_nodes())
    after["edges"].extend(
        {
            "source": "declaration:repo:A.root",
            "target": "declaration:repo:A.target",
            "kind": kind,
            "data": {"authority": authority},
        }
        for kind, authority in (
            ("parser_candidate_dependency", "lean_parser"),
            ("type_dependency", "lean_environment"),
            ("value_dependency", "lean_environment"),
        )
    )

    diff = diff_atlases(before, after)

    categories = diff["summary"]["by_category"]
    assert categories["parser_candidate_dependency_edges"]["added"] == 1
    assert categories["type_dependency_edges"]["added"] == 1
    assert categories["value_dependency_edges"]["added"] == 1
    assert {
        (row["payload"]["kind"], row["payload"]["authority"])
        for row in diff["added"]
        if row["category"].endswith("_dependency_edges")
    } == {
        ("parser_candidate_dependency", "lean_parser"),
        ("type_dependency", "lean_environment"),
        ("value_dependency", "lean_environment"),
    }


def test_render_atlas_diff_markdown_includes_summary_and_sections() -> None:
    diff = diff_atlases(atlas_with_finding("A.Root", finding_count=1), atlas_with_finding("A.Root", finding_count=2))

    markdown = render_atlas_diff_markdown(diff)

    assert "# Ladon Atlas Diff" in markdown
    assert "## Categories" in markdown
    assert "## Changed" in markdown


def declaration_nodes() -> list[dict]:
    """Return stable declaration endpoints for typed dependency edges."""

    return [
        {
            "id": f"declaration:repo:{name}",
            "kind": "declaration",
            "label": name,
            "data": {},
        }
        for name in ("A.root", "A.target")
    ]


def atlas_with_finding(root: str, *, finding_count: int = 1, signal_count: int = 1) -> dict:
    return {
        "schema": "ladon-report-atlas-v1",
        "summary": {},
        "nodes": [
            {
                "id": "report:repo/owner.json",
                "kind": "report",
                "label": "repo/owner.json",
                "data": {
                    "analysis_root_module": root,
                    "module_count": 3,
                    "declaration_count": 1,
                    "finding_count": 1,
                    "review_region_count": 1,
                },
            },
            {
                "id": "finding:repo/owner.json:0",
                "kind": "finding",
                "label": "hotspot: Shared.Subject",
                "data": {"kind": "hotspot", "subject": "Shared.Subject", "count": finding_count},
            },
            {
                "id": "region:repo/owner.json:proof_region",
                "kind": "review_region",
                "label": "Proof region",
                "data": {"kind": "proof_region", "signal_count": signal_count},
            },
            {
                "id": "signal:repo/owner.json:proof_region:0",
                "kind": "signal",
                "label": "proof_family_similarity: repeated suffix",
                "data": {
                    "kind": "proof_family_similarity",
                    "subject": "repeated suffix",
                    "count": signal_count,
                },
            },
        ],
        "edges": [
            {
                "source": "report:repo/owner.json",
                "target": "finding:repo/owner.json:0",
                "kind": "has_finding",
            },
            {
                "source": "report:repo/owner.json",
                "target": "region:repo/owner.json:proof_region",
                "kind": "has_review_region",
            },
            {
                "source": "region:repo/owner.json:proof_region",
                "target": "signal:repo/owner.json:proof_region:0",
                "kind": "has_signal",
            },
        ],
    }
