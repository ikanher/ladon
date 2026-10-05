"""Observable projection contracts for authored result guides."""

from __future__ import annotations

import copy
import json

import pytest
from support.result_guide import guide_inputs, reseal


def _api():
    from ladon.result_guides import guide_result_manifest

    return guide_result_manifest


def _case():
    return guide_inputs()


def _revisions(manifest):
    from ladon.result_manifest_io import content_revision

    for claim in manifest["claims"]:
        claim["revision"] = content_revision("claim", claim)
    for target in manifest["targets"]:
        target["revision"] = content_revision("target", target)
    manifest["revision"] = content_revision("manifest", manifest)


def _long_guide(guide, count=125):
    expanded = copy.deepcopy(guide)
    base = copy.deepcopy(expanded["steps"][0])
    expanded["steps"] = [base]
    for index in range(1, count):
        row = copy.deepcopy(base)
        row.update(
            id=f"long-step-{index:03d}",
            purpose=f"authored step {index}",
            explanation=(f"Authored explanation {index}. " + "λ" * 3200),
        )
        expanded["steps"].append(row)
    return reseal(expanded)


def test_guide_preserves_authored_order_and_exact_conjunctive_selectors():
    manifest, artifacts, guide = _case()
    project = _api()
    result = project(manifest, artifacts, guide_inputs=guide, section="steps", limit=100)

    _assert_guide_header_and_order(result)

    selected = project(
        manifest,
        artifacts,
        guide_inputs=guide,
        section="steps",
        claim_id="paper-lemma-2",
        target_id="supporting-lemma",
        limit=100,
    )
    assert [row["id"] for row in selected["rows"]] == ["argument"]
    assert selected["query"]["claim"] == "paper-lemma-2"
    assert selected["query"]["target"] == "supporting-lemma"

    disjoint = project(
        manifest,
        artifacts,
        guide_inputs=guide,
        section="steps",
        claim_id=manifest["claims"][0]["id"],
        target_id="supporting-lemma",
        limit=100,
    )
    assert disjoint["rows"] == []


def _assert_guide_header_and_order(result):
    assert result["operation"] == "guide"
    assert result["schema"] == "ladon-result-guide-view-v1"
    assert result["scope"] == "offline-supplied-evidence"
    assert result["readingOrder"] == "authored"
    assert result["reuseApplicability"] == "not-checked"
    assert [row["id"] for row in result["rows"]] == ["condition", "argument"]
    assert [row["position"] for row in result["rows"]] == [1, 2]
    assert result["rows"][0]["authority"] == "attributed-annotation"
    assert result["rows"][1]["prerequisites"][0]["stepId"] == "condition"


def test_current_guide_supporting_target_is_navigable_without_correspondence_link():
    manifest, artifacts, guide = _case()
    assert all("supporting-lemma" not in link["targetIds"] for link in manifest["links"])
    result = _api()(
        manifest,
        artifacts,
        guide_inputs=guide,
        section="targets",
        claim_id="paper-lemma-2",
        target_id="supporting-lemma",
        limit=100,
    )
    assert [row["id"] for row in result["rows"]] == ["supporting-lemma"]


def test_historical_target_does_not_supply_current_text_or_current_claim_navigation():
    manifest, artifacts, guide = _case()
    target = next(row for row in manifest["targets"] if row["id"] == "supporting-lemma")
    target["typeText"] = "Changed after the authored revision."
    _revisions(manifest)

    project = _api()
    result = project(manifest, artifacts, guide_inputs=guide, section="steps", limit=100)
    row = next(row for row in result["rows"] if row["id"] == "argument")
    binding = next(item for item in row["targetBindings"] if item["targetId"] == "supporting-lemma")
    assert binding["status"] == "historical"
    assert binding["requestedRevision"] != binding["currentRevision"]
    assert "Changed after the authored revision." not in str(row)

    _assert_no_historical_support(project, manifest, artifacts, guide)


def _assert_no_historical_support(project, manifest, artifacts, guide):
    targets = project(
        manifest,
        artifacts,
        guide_inputs=guide,
        section="targets",
        claim_id="paper-lemma-2",
        limit=100,
    )
    assert all(row["id"] != "supporting-lemma" for row in targets["rows"])


def test_missing_guide_keeps_structural_navigation_available():
    manifest, artifacts, _ = _case()
    project = _api()
    explanation = project(manifest, artifacts, guide_inputs=None, section="steps", limit=100)
    assert explanation["guideStatus"] == "unavailable"
    assert len(explanation["rows"]) == 1
    assert explanation["rows"][0]["status"] == "unavailable"

    targets = project(manifest, artifacts, guide_inputs=None, section="targets", limit=100)
    assert targets["rows"]
    assert targets["guideStatus"] == "unavailable"


def test_citations_reviews_and_conflicting_attribution_assertions_stay_separate():
    manifest, artifacts, guide = _case()
    contested = copy.deepcopy(guide)
    second = copy.deepcopy(contested["citations"][0])
    second.update(
        id="other-origin-assertion",
        locator="Other paper, section 2",
        assertion="A different source is claimed as the origin.",
        submitter="another-author",
    )
    contested["citations"].append(second)
    contested["reviews"].append(
        {
            "id": "review-dispute",
            "scope": "attribution",
            "stepId": "condition",
            "stepRevision": contested["steps"][0]["revision"],
            "targetRevisions": copy.deepcopy(contested["steps"][0]["targetRevisions"]),
            "citationId": "other-origin-assertion",
            "citationRevision": "",
            "reviewer": {"identity": "reviewer-2", "kind": "human"},
            "status": "disputed",
            "rationale": "The attribution conflicts with another supplied assertion.",
            "timestamp": "2026-09-29T11:00:00Z",
        }
    )
    contested = reseal(contested)
    disputed = next(row for row in contested["citations"] if row["id"] == "other-origin-assertion")
    contested["reviews"][-1]["citationRevision"] = disputed["revision"]

    project = _api()
    citations = project(manifest, artifacts, guide_inputs=contested, section="citations", limit=100)
    assert [row["id"] for row in citations["rows"]] == ["paper-citation", "other-origin-assertion"]
    assert all(row["currency"] == "current" for row in citations["rows"])
    assert all(row["authority"] == "attributed-annotation" for row in citations["rows"])
    reviews = project(manifest, artifacts, guide_inputs=contested, section="reviews", limit=100)
    assert {row["status"] for row in reviews["rows"]} == {"approved", "disputed"}
    assert all(row["authority"] == "attributed-review" for row in reviews["rows"])
    assert not any(
        row.get("verified") is True or row.get("badge") == "verified" for row in reviews["rows"]
    )


def test_selected_view_rejects_malformed_unselected_guide_rows():
    manifest, artifacts, guide = _case()
    malformed = copy.deepcopy(guide)
    malformed["citations"][0]["revision"] = "sha256:" + "0" * 64
    with pytest.raises((ValueError, TypeError)):
        _api()(
            manifest,
            artifacts,
            guide_inputs=malformed,
            section="steps",
            claim_id=manifest["claims"][0]["id"],
            limit=100,
        )


def test_paginated_guide_is_complete_bounded_and_cursor_binds_companion():
    manifest, artifacts, guide = _case()
    expanded = _long_guide(guide)
    project = _api()
    first = project(manifest, artifacts, guide_inputs=expanded, section="steps", limit=100)
    _assert_first_page(first)

    _assert_complete_traversal(project, manifest, artifacts, expanded, first)

    edited = copy.deepcopy(expanded)
    edited["citations"][0]["assertion"] += " Edited."
    edited = reseal(edited)
    with pytest.raises((ValueError, TypeError)):
        project(
            manifest,
            artifacts,
            guide_inputs=edited,
            section="steps",
            limit=100,
            cursor=first["pagination"]["nextCursor"],
        )


def _assert_first_page(first):
    assert first["pagination"]["total"] == 125
    assert len(first["rows"]) <= 100
    _assert_first_page_bounds(first)
    assert first["pagination"]["nextCursor"]
    omitted = next(row for row in first["rows"] if row.get("fieldOmissions"))
    explanation = next(
        item for item in omitted["fieldOmissions"] if item["path"].endswith("/explanation")
    )
    assert explanation["reference"]["input"] == "guide-inputs"
    assert explanation["reference"]["pointer"].startswith("/steps/")



def _assert_complete_traversal(project, manifest, artifacts, expanded, first):
    from ladon.result_inspection_page import text_projection

    observed = [row["id"] for row in first["rows"]]
    cursor = first["pagination"]["nextCursor"]
    while cursor:
        page = project(
            manifest, artifacts, guide_inputs=expanded, section="steps", limit=100, cursor=cursor
        )
        assert (
            len(json.dumps(page, ensure_ascii=False, separators=(",", ":")).encode()) + 1
            <= 32 * 1024
        )
        assert len(text_projection(page).encode()) + 1 <= 32 * 1024
        assert page["pagination"]["offset"] == len(observed)
        observed.extend(row["id"] for row in page["rows"])
        cursor = page["pagination"]["nextCursor"]
    assert len(observed) == 125
    assert len(set(observed)) == 125
    assert observed[0] == "condition" and observed[-1] == "long-step-124"



def _assert_first_page_bounds(first):
    assert (
        len(json.dumps(first, ensure_ascii=False, separators=(",", ":")).encode()) + 1 <= 32 * 1024
    )
    from ladon.result_inspection_page import text_projection

    assert len(text_projection(first).encode()) + 1 <= 32 * 1024
