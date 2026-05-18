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


def test_render_atlas_diff_markdown_includes_summary_and_sections() -> None:
    diff = diff_atlases(atlas_with_finding("A.Root", finding_count=1), atlas_with_finding("A.Root", finding_count=2))

    markdown = render_atlas_diff_markdown(diff)

    assert "# Ladon Atlas Diff" in markdown
    assert "## Categories" in markdown
    assert "## Changed" in markdown


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
