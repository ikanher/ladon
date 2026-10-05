"""Red contract for bounded, attributed paragraph views."""
from __future__ import annotations

import copy
import json

import pytest
from support.result_guide import guide_inputs, reseal

from ladon.result_manifest_io import ResultManifestError

CLAIM = "paper-theorem-1"
COMPONENT = "implication"
TARGET = "finite-map"


def _api():
    from ladon.result_guides import guide_result_manifest

    return guide_result_manifest


def _case():
    return guide_inputs()


def _view(manifest, artifacts, guide, **kwargs):
    return _api()(
        manifest,
        artifacts,
        guide_inputs=guide,
        section="exposition",
        claim_id=CLAIM,
        component_id=COMPONENT,
        **kwargs,
    )


def _assert_non_verdict(row):
    assert row["checkingScope"] == "explicit-application-operation-required"
    assert row["reuseApplicability"] == "not-checked"
    assert row["mathematicalVerdict"] == "not-inferred"
    assert row["reviewStatus"] in {"current-attributed-reviews", "not-reviewed"}


def _assessment_inputs(manifest):
    from test_result_assessments import assessment, companion

    claim = manifest["claims"][0]
    rows = [assessment(claim, COMPONENT, targets=[TARGET])]
    target = next(row for row in manifest['targets'] if row['id'] == TARGET)
    rows[0]['targetRevisions'] = [{'targetId': TARGET, 'revision': target['revision']}]
    return companion(manifest, rows)


def _assert_step_review(row, guide):
    assert row["paragraph"]["revision"] == guide["steps"][0]["revision"]
    review = row["reviews"][0]
    assert review["id"] == "review-condition"
    assert review["scope"] == "explanation"
    assert review["currency"] == "current"


def _has_reference(value, input_name, pointer):
    if isinstance(value, dict):
        if value.get("input") == input_name and value.get("pointer") == pointer:
            return True
        return any(_has_reference(child, input_name, pointer) for child in value.values())
    if isinstance(value, list):
        return any(_has_reference(child, input_name, pointer) for child in value)
    return False


def _assert_component_support(row):
    component = row["selectedComponent"]
    assert component["componentId"] == COMPONENT
    assert component["associationBasis"] == "caller-selected-component-not-correspondence-review"
    assert row["supportingStatements"][0]["targetId"] == TARGET
    assert row["supportingStatements"][0]["relationship"] == (
        "guide-support-not-component-correspondence"
    )
    assert row["paragraph"]["authority"] == "attributed-annotation"
    assert row["paragraph"]["sources"][0]["digest"].startswith("sha256:")


def test_current_exposition_binds_exact_step_review_and_selected_component():
    manifest, artifacts, guide = _case()
    result = _view(manifest, artifacts, guide)

    assert result["operation"] == "guide"
    assert result["section"] == "exposition"
    assert [row["paragraph"]["stepId"] for row in result["rows"]] == ["condition"]
    row = result["rows"][0]
    _assert_step_review(row, guide)
    _assert_component_support(row)
    _assert_non_verdict(row)


def test_corrective_rationale_is_authored_without_inferred_mathematical_verdict():
    manifest, artifacts, guide = _case()
    changed = copy.deepcopy(guide)
    changed["steps"][0]["explanation"] = (
        "The finite-domain hypothesis is omitted here; this is a deliberately altered explanation."
    )
    changed["reviews"][0]["status"] = "with-differences"
    changed["reviews"][0]["rationale"] = (
        "The edited paragraph drops the finite-domain premise from the source explanation."
    )
    changed = reseal(changed)

    row = _view(manifest, artifacts, changed)["rows"][0]
    assert "deliberately altered" in row["paragraph"]["explanation"]
    assert row["reviews"][0]["status"] == "with-differences"
    assert "drops the finite-domain premise" in row["reviews"][0]["rationale"]
    assert row["reviewStatus"] == "current-attributed-reviews"
    _assert_non_verdict(row)



def test_stale_explanation_review_is_shown_as_historical_on_current_paragraph():
    manifest, artifacts, guide = _case()
    old = copy.deepcopy(guide["steps"][0])
    old["explanation"] += " older wording"
    old_revision = reseal({**copy.deepcopy(guide), "steps": [old]})["steps"][0]["revision"]
    changed = copy.deepcopy(guide)
    changed["reviews"].append({
        **copy.deepcopy(guide["reviews"][0]), "id": "review-stale",
        "stepRevision": old_revision, "status": "disputed",
        "rationale": "This disputed review is bound to the previous wording.",
    })
    changed = reseal(changed)
    changed["reviews"][-1]["stepRevision"] = old_revision

    row = _view(manifest, artifacts, changed)["rows"][0]
    assert row["paragraph"]["currency"] == "current"
    assert {review["currency"] for review in row["reviews"]} == {"current", "historical"}
    assert row["reviewStatus"] == "current-attributed-reviews"
    assert any(item["reason"] == "historical-explanation-review" for item in row["recheckNotices"])


def test_missing_guide_produces_one_unavailable_paragraph_without_support():
    manifest, artifacts, _ = _case()
    result = _api()(manifest, artifacts, guide_inputs=None, section="exposition",
                    claim_id=CLAIM, component_id=COMPONENT)
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert row.get("reason") == "no-guide-inputs-supplied"
    assert row.get("status") == "unavailable"
    assert row.get("supportingStatements", []) == []
    assert row.get("reviews", []) == []
    assert "mathematicalVerdict" not in row

def test_historical_paragraph_and_review_cannot_borrow_current_support_statements():
    manifest, artifacts, guide = _case()
    old = copy.deepcopy(guide["steps"][0])
    old["explanation"] += " An earlier paragraph revision."
    old = reseal({**copy.deepcopy(guide), "steps": [old]})["steps"][0]
    changed_manifest = copy.deepcopy(manifest)
    from ladon.result_manifest_io import content_revision

    changed_manifest["targets"][0]["typeText"] += " -- revised now"
    changed_manifest["targets"][0]["revision"] = content_revision("target", changed_manifest["targets"][0])
    changed_manifest["revision"] = content_revision("manifest", changed_manifest)
    historical = copy.deepcopy(guide)
    historical["reviews"].append({
        **copy.deepcopy(guide["reviews"][0]),
        "id": "review-old-paragraph",
        "stepRevision": old["revision"],
        "status": "disputed",
        "rationale": "This review belongs to the earlier paragraph revision.",
    })
    historical = reseal(historical)

    row = _view(changed_manifest, artifacts, historical)["rows"][0]
    assert row["paragraph"]["currency"] == "historical"
    assert row["supportingStatements"] == []
    assert row["paragraph"]["targetBindings"][0]["statementAvailability"] == "unavailable"
    assert "typeText" not in row["paragraph"]["targetBindings"][0]
    assert row["selectedComponent"]["formalStatements"] == []
    assert {review["currency"] for review in row["reviews"]} == {"historical"}
    assert any(item["reason"] == "historical-paragraph-binding" for item in row["recheckNotices"])
    assert any(item["reason"] == "historical-explanation-review" for item in row["recheckNotices"])
    _assert_non_verdict(row)


def test_historical_whole_step_hides_still_current_target_binding():
    manifest, artifacts, guide = _case()
    changed_manifest = copy.deepcopy(manifest)
    from ladon.result_manifest_io import content_revision

    changed_manifest["title"] += " unrelated manifest edit"
    changed_manifest["revision"] = content_revision("manifest", changed_manifest)

    row = _view(changed_manifest, artifacts, guide)["rows"][0]
    binding = row["paragraph"]["targetBindings"][0]
    assert row["paragraph"]["currency"] == "historical"
    assert binding["requestedRevision"] == binding["currentRevision"]
    assert binding["statementAvailability"] == "unavailable"
    assert "typeText" not in binding
    assert row["supportingStatements"] == []
    assert row["selectedComponent"]["formalStatements"] == []


def test_target_selection_is_conjunctive_and_component_selection_is_exact():
    manifest, artifacts, guide = _case()
    result = _view(manifest, artifacts, guide, target_id="supporting-lemma")
    assert result["rows"] == []
    with pytest.raises(ResultManifestError):
        _api()(manifest, artifacts, guide_inputs=guide, section="steps", component_id=COMPONENT)
    with pytest.raises(ResultManifestError):
        _api()(manifest, artifacts, guide_inputs=guide, section="exposition", component_id=COMPONENT)
    with pytest.raises(ResultManifestError):
        _api()(manifest, artifacts, guide_inputs=guide, section="exposition", claim_id=CLAIM)
    with pytest.raises(ResultManifestError):
        _api()(manifest, artifacts, guide_inputs=guide, section="exposition",
               claim_id=CLAIM, component_id="missing-component")


def _cli_parity_result(main, args, capsys):
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert main(args + ["--format", "text"]) == 0
    text = {
        key: json.loads(value)
        for key, value in (line.split(": ", 1) for line in capsys.readouterr().out.splitlines())
    }
    assert text == result
    return result


def _assert_standalone_scopes(row):
    assert row["paragraph"]["references"][""]["input"] == "guide-inputs"
    assert _has_reference(row["selectedComponent"], "assessments", "/assessments/0/scope")
    assert row["selectedComponent"]["componentScope"]["descriptions"] == [{
        "assessmentId": "assessment-implication", "scope": "only this component",
        "author": {"id": "reviewer-1", "kind": "human"}, "currency": "current",
    }]
    assert row["reviews"][0]["scope"] == "explanation"
    assert "mathematicalVerdict" not in row["selectedComponent"]
    assert row["paragraph"]["authority"] == "attributed-annotation"


def test_citations_and_component_assessments_remain_separate_attributed_inputs(tmp_path, capsys):
    from ladon.entrypoint import main

    manifest, _artifacts, guide = _case()
    assessment = _assessment_inputs(manifest)
    paths = {"manifest": tmp_path / "manifest.json", "guide": tmp_path / "guide.json",
             "assessments": tmp_path / "assessments.json"}
    for name, value in (("manifest", manifest), ("guide", guide), ("assessments", assessment)):
        paths[name].write_text(json.dumps(value), encoding="utf-8")
    args = ["result", "guide", str(paths["manifest"]), "--guide-inputs", str(paths["guide"]),
            "--assessments", str(paths["assessments"]), "--section", "exposition",
            "--claim", CLAIM, "--component", COMPONENT]
    result = _cli_parity_result(main, args, capsys)
    _assert_standalone_scopes(result["rows"][0])


def test_bundle_exposition_uses_bundled_assessments_without_importing_check_authority(
    tmp_path, capsys
):
    from ladon.entrypoint import main
    from ladon.result_bundles import export_result_bundle

    manifest, _, guide = _case()
    assessment = _assessment_inputs(manifest)
    paths = {"manifest": tmp_path / "manifest.json", "guide": tmp_path / "guide.json",
             "assessments": tmp_path / "assessments.json"}
    for key, value in (("manifest", manifest), ("guide", guide), ("assessments", assessment)):
        paths[key].write_text(json.dumps(value), encoding="utf-8")
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({
        "schema": "ladon-result-bundle-selection-v1",
        "supplier": {"identity": "paragraph-fixture", "kind": "human"},
        "entries": [
            {"id": "guide", "role": "guide", "path": str(paths["guide"]),
             "disclosure": "supplied", "permission": "include"},
            {"id": "assessments", "role": "assessments", "path": str(paths["assessments"]),
             "disclosure": "supplied", "permission": "include"},
        ], "lineageBindings": [], "identifiers": [], "externalDependencies": [],
    }), encoding="utf-8")
    bundle = tmp_path / "result.zip"
    export_result_bundle(paths["manifest"], selection, bundle)
    assert main(["result", "guide", str(bundle), "--section", "exposition",
                 "--claim", CLAIM, "--component", COMPONENT]) == 0
    row = json.loads(capsys.readouterr().out)["rows"][0]
    assert row["selectedComponent"]["componentScope"]["descriptions"][0]["assessmentId"] == (
        "assessment-implication"
    )
    assert _has_reference(row["selectedComponent"], "assessments", "/assessments/0/scope")
    assert row["reviews"][0]["scope"] == "explanation"
    _assert_non_verdict(row)


def _large_guide(guide):
    expanded = copy.deepcopy(guide)
    base = copy.deepcopy(expanded["steps"][0])
    expanded["steps"] = []
    for index in range(125):
        row = copy.deepcopy(base)
        row.update(id="condition" if index == 0 else f"paragraph-{index:03d}",
                   explanation=("Authored λ " * 3200))
        expanded["steps"].append(row)
        if index:
            expanded["reviews"].append({
                **copy.deepcopy(guide["reviews"][0]), "id": f"review-{index:03d}",
                "stepId": row["id"], "stepRevision": row["revision"],
            })
    return reseal(expanded)


def _assert_bounded_page(page, guide):
    from ladon.result_inspection_page import text_projection

    assert len(json.dumps(page, ensure_ascii=False, separators=(",", ":")).encode()) + 1 <= 32 * 1024
    assert len(text_projection(page).encode()) + 1 <= 32 * 1024
    for row in page["rows"]:
        ref = row["paragraph"]["references"][""]
        assert ref["input"] == "guide-inputs"
        assert ref["pointer"].startswith("/steps/")
        index = int(ref["pointer"].split("/")[2])
        assert guide["steps"][index]["id"] == row["paragraph"]["stepId"]


def test_exposition_pages_bind_component_guide_and_assessment_inputs_and_stay_bounded():
    manifest, artifacts, guide = _case()
    expanded = _large_guide(guide)
    project = _api()
    first_page = project(manifest, artifacts, guide_inputs=expanded, section="exposition",
                         claim_id=CLAIM, component_id=COMPONENT, limit=100)
    assert first_page["pagination"]["total"] == 125
    assert len(first_page["rows"]) <= 100
    assert first_page["pagination"]["nextCursor"]
    assert first_page["query"]["projectionVersion"] == 2
    assert first_page["inputBinding"].startswith("sha256:")
    assert first_page["rows"][0]["fieldOmissions"]
    _assert_bounded_page(first_page, expanded)

    old_page = project(manifest, artifacts, guide_inputs=expanded, section="steps",
                       claim_id=CLAIM, limit=1)
    with pytest.raises(ResultManifestError):
        project(manifest, artifacts, guide_inputs=expanded, section="exposition",
                claim_id=CLAIM, component_id=COMPONENT, limit=1,
                cursor=old_page["pagination"]["nextCursor"])

    edited = copy.deepcopy(expanded)
    edited["steps"][0]["explanation"] += " changed"
    edited = reseal(edited)
    with pytest.raises(ResultManifestError):
        project(manifest, artifacts, guide_inputs=edited, section="exposition",
                claim_id=CLAIM, component_id=COMPONENT, limit=100,
                cursor=first_page["pagination"]["nextCursor"])
