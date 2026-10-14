"""Validate incoming owners and preserve pointers across internal selection."""

import pytest

from ladon.report_contract import ReportModelError
from ladon.report_declaration_compaction import compact_declaration_collections
from ladon.report_projection import project_sections


def test_internal_stratified_reorder_has_consumable_destination_references():
    raw = {"records": [
        {"role": role, "declarations": [{"declaration": f"Fixture.{role}",
                                       "authority": "lean_environment"}]}
        for role in ("z", "a")
    ]}
    compact = compact_declaration_collections(raw, pointer="#/sections")
    projected = project_sections(compact, projection="review",
                                 summary_item_limit=1, review_item_limit=1)[0]
    assert [row["role"] for row in projected["records"]] == ["a", "z"]
    # This actual canonical consumer rejects stale pointers, unlike presentation.
    assert compact_declaration_collections(projected, pointer="#/sections") == projected
    for index, row in enumerate(projected["records"]):
        assert row["declarations"][0]["evidenceRef"].startswith(
            f"#/sections/records/{index}/_declarationEvidence/"
        )


@pytest.mark.parametrize("value", [
    {"_declarationEvidence": []},
    {"_declarationEvidence": {"orphan": {}}, "declarations": []},
])
def test_projection_rejects_malformed_reserved_containers(value):
    with pytest.raises(ReportModelError, match="reserved _declarationEvidence key"):
        project_sections({"records": [value]}, projection="review",
                         summary_item_limit=1, review_item_limit=1)


def test_projection_accepts_valid_empty_reserved_container():
    value = {"_declarationEvidence": {}, "declarations": [{"declaration": "Fixture.valid"}]}
    projected = project_sections({"records": [value]}, projection="review",
                                 summary_item_limit=1, review_item_limit=1)[0]
    assert projected["records"][0]["declarations"][0]["declaration"] == "Fixture.valid"
