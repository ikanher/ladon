"""Bounded inspection preserves missing evidence and recoverable pagination."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ladon.result_inspection import inspect_result_manifest
from ladon.result_manifest_io import content_revision

FIXTURE = Path(__file__).parent / "fixtures/result_manifest/finite-map.json"


def manifest():
    return json.loads(FIXTURE.read_text())


def seal(value):
    for target in value["targets"]:
        target["revision"] = content_revision("target", target)
    for claim in value["claims"]:
        claim["revision"] = content_revision("claim", claim)
    value["revision"] = content_revision("manifest", value)


def test_missing_canonical_artifacts_remain_unresolved_and_not_formalized():
    value = manifest()
    result = inspect_result_manifest(value, [])
    component = next(row for row in result["rows"] if row["componentId"] == "implication")

    assert component["mapping"] == {"status": "mapped", "targetIds": ["finite-map"]}
    assert component["resolution"]["statuses"] == {"unresolved": 1}
    assert component["assessments"] == []
    assert component["assessmentStatus"] == "unassessed"
    assert result["coverage"]["proofCoverage"] == "unknown"
    assert "fullyFormalized" not in result
    assert len(json.dumps(result, separators=(",", ":"), ensure_ascii=False).encode()) <= 32 * 1024


def test_component_page_cursor_recovers_omitted_rows():
    value = manifest()
    result = inspect_result_manifest(value, [], section="components", limit=1)
    assert result["pagination"]["total"] == 2
    assert result["pagination"]["returned"] == 1
    assert result["pagination"]["omitted"] == 1
    assert result["pagination"]["nextCursor"]

    next_page = inspect_result_manifest(value, [], section="components", limit=1,
                                        cursor=result["pagination"]["nextCursor"])
    assert next_page["pagination"]["returned"] == 1
    assert next_page["pagination"]["omitted"] == 0
    assert next_page["rows"][0]["componentId"] != result["rows"][0]["componentId"]


def test_cursor_is_bound_to_manifest_revision_and_query():
    value = manifest()
    first = inspect_result_manifest(value, [], section="components", limit=1)
    cursor = first["pagination"]["nextCursor"]
    with pytest.raises(ValueError):
        inspect_result_manifest(value, [], section="claims", limit=1, cursor=cursor)

    changed = copy.deepcopy(value)
    changed["title"] = "Changed title"
    changed["revision"] = content_revision("manifest", changed)
    with pytest.raises(ValueError):
        inspect_result_manifest(changed, [], section="components", limit=1, cursor=cursor)


def test_statement_larger_than_card_budget_has_exact_input_pointer():
    value = manifest()
    value["claims"][0]["statement"] = "x" * (64 * 1024)
    value["claims"][0]["revision"] = content_revision("claim", value["claims"][0])
    value["revision"] = content_revision("manifest", value)
    result = inspect_result_manifest(value, [], section="components")
    row = next(row for row in result["rows"] if row["componentId"] == "implication")

    assert len(json.dumps(result, separators=(",", ":"), ensure_ascii=False).encode()) <= 32 * 1024
    assert row["statement"] != value["claims"][0]["statement"]
    serialized = json.dumps(result, separators=(",", ":"), ensure_ascii=False)
    assert "/claims/0/statement" in serialized
    assert "omitted" in serialized.lower()
