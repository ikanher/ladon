"""Independent first-gate tests for claim component focused inspection."""
from __future__ import annotations

import json
from typing import Any

import pytest
from test_result_assessments import assessment, companion, manifest
from test_result_resolution import inputs as resolved_inputs

from ladon.entrypoint import main
from ladon.result_inspection import inspect_result_manifest
from ladon.result_manifest_io import ResultManifestError, canonical_json

CLAIM_ID = "paper-theorem-1"
MAPPED = "implication"
UNMAPPED = "unrestricted-domain"
TARGET_ID = "finite-map"


def _historical(row: dict[str, Any], index: int = 0) -> dict[str, Any]:
    return {**row, "id": f"{row['id']}-historical-{index}", "claimRevision": "sha256:" + "0" * 64}


def _scoped_inputs(*, current: bool = True, historical: bool = True):
    value = manifest()
    rows = []
    if current:
        rows.append(assessment(value["claims"][0], MAPPED, targets=[TARGET_ID]))
    if historical:
        rows.append(_historical(assessment(value["claims"][0], MAPPED, targets=[TARGET_ID])))
    rows.append(assessment(value["claims"][0], UNMAPPED, kind="conventional-only"))
    return value, companion(value, rows)


def _component_view(value, *, assessments=None, artifacts=None, **kwargs):
    return inspect_result_manifest(
        value, [] if artifacts is None else artifacts,
        assessments=assessments, section="components",
        claim_id=CLAIM_ID, component_id=MAPPED, **kwargs,
    )


def _walk_references(value):
    if isinstance(value, dict):
        if {"input", "pointer"} <= value.keys():
            yield value
        for child in value.values():
            yield from _walk_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_references(child)


def _has_reference(value, input_name: str, pointer: str) -> bool:
    return any(
        row["input"] == input_name and row["pointer"] == pointer
        for row in _walk_references(value)
    )


def _pointer_value(document, pointer):
    current = document
    for token in pointer.lstrip("/").split("/") if pointer else []:
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def _assert_references_resolve(card, value, assessment_input):
    sources = {"manifest": value}
    if assessment_input is not None:
        sources["assessments"] = assessment_input
    references = list(_walk_references(card))
    assert references
    for reference in references:
        assert reference["input"] in sources
        _pointer_value(sources[reference["input"]], reference["pointer"])


def _assert_scope_descriptions(card):
    descriptions = card["componentScope"]["descriptions"]
    assert [(row["assessmentId"], row["scope"], row["currency"]) for row in descriptions] == [
        ("assessment-implication", "only this component", "current"),
        ("assessment-implication-historical-0", "only this component", "historical"),
    ]
    assert _has_reference(card, "assessments", "/assessments/0/scope")
    assert _has_reference(card, "assessments", "/assessments/1/scope")


def _assert_unresolved_target(target, source_target):
    assert target["targetId"] == TARGET_ID
    assert target["targetRevision"] == source_target["revision"]
    assert target["name"] == source_target["name"]
    assert target["typeText"] == source_target["typeText"]
    assert target["statementAuthority"] == "manifest-supplied"
    assert target["resolution"]["status"] == "unresolved"
    assert target["parameters"] == {
        "status": "unavailable", "reason": "no-bound-structured-declaration-observation",
    }
    assert target["checkingScope"] == "inspect-checking-section"
    assert target["reuseApplicability"] == "not-checked"


def _text_json(output: str) -> dict[str, Any]:
    return {
        key: json.loads(value)
        for key, value in (line.split(": ", 1) for line in output.splitlines())
    }


def test_component_card_labels_whole_statement_and_preserves_current_historical_scopes():
    value, attached = _scoped_inputs()
    result = _component_view(value, assessments=attached)
    card = result["rows"][0]

    assert card["componentId"] == MAPPED
    assert card["statement"] == value["claims"][0]["statement"]
    assert card["wholeClaimStatement"] == value["claims"][0]["statement"]
    assert card["statementScope"] == "whole-claim-context"
    assert card["componentScope"]["status"] == "reported"
    assert card["componentScope"]["basis"] == "attributed-assessment-scopes-not-extracted-statements"
    _assert_scope_descriptions(card)
    assert _has_reference(card, "manifest", "/claims/0/statement")
    assert len(canonical_json(result)) + 1 <= 32768
    _assert_references_resolve(card, value, attached)


def test_historical_scope_is_retained_but_never_marks_component_reported():
    value, attached = _scoped_inputs(current=False, historical=True)
    card = _component_view(value, assessments=attached)["rows"][0]

    assert card["componentScope"]["status"] == "unavailable"
    assert card["componentScope"]["descriptions"] == [{
        "assessmentId": "assessment-implication-historical-0",
        "scope": "only this component", "author": {"id": "reviewer-1", "kind": "human"},
        "currency": "historical",
    }]


def test_selected_component_keeps_full_sibling_mapping_coverage():
    value, attached = _scoped_inputs()
    card = _component_view(value, assessments=attached)["rows"][0]
    coverage = card["claimComponentCoverage"]

    assert coverage["mapped"] == 1
    assert coverage["unmapped"] == 1
    assert coverage["components"] == [
        {"componentId": MAPPED, "mappingStatus": "mapped", "targetIds": [TARGET_ID]},
        {"componentId": UNMAPPED, "mappingStatus": "unmapped", "targetIds": []},
    ]
    assert _has_reference(card, "manifest", "/claims/0/components")
    assert _has_reference(card, "manifest", "/links/0/componentIds")
    _assert_references_resolve(card, value, attached)


def test_unresolved_formal_statement_uses_only_manifest_authority():
    value = manifest()
    unresolved = _component_view(value)["rows"][0]["formalStatements"][0]

    _assert_unresolved_target(unresolved, value["targets"][0])
    unresolved_card = _component_view(value)["rows"][0]
    assert _has_reference(unresolved_card, "manifest", "/targets/0/typeText")

    _assert_references_resolve(_component_view(value)["rows"][0], value, None)


def test_resolved_formal_statement_uses_exact_stored_canonical_type():
    resolved_manifest, artifacts = resolved_inputs()
    resolved_card = _component_view(resolved_manifest, artifacts=artifacts)["rows"][0]
    resolved = resolved_card["formalStatements"][0]
    assert resolved["resolution"]["status"] == "resolved"
    assert resolved["typeText"] == "True"
    assert resolved["statementAuthority"] == "stored-canonical-type-text"
    assert _has_reference(resolved_card, "manifest", "/targets/0/typeText")
    _assert_references_resolve(
        resolved_card, resolved_manifest, None,
    )


def test_target_selector_cannot_lend_mapped_evidence_to_unmapped_sibling():
    value, attached = _scoped_inputs()
    result = inspect_result_manifest(
        value, [], assessments=attached, section="components", claim_id=CLAIM_ID,
        component_id=UNMAPPED, target_id=TARGET_ID,
    )

    assert result["rows"] == []
    assert result["pagination"]["total"] == 0


@pytest.mark.parametrize(("component", "section", "claim"), [
    (MAPPED, "claims", CLAIM_ID),
    ("missing-component", "components", CLAIM_ID),
    (MAPPED, "components", "missing-claim"),
    (MAPPED, "components", None),
])
def test_component_selection_requires_components_exact_claim_and_known_component(component, section, claim):
    value = manifest()
    with pytest.raises(ResultManifestError):
        inspect_result_manifest(
            value, [], section=section, claim_id=claim, component_id=component,
        )


def test_old_and_unfocused_cursors_are_rejected_for_component_projection():
    value = manifest()
    full = inspect_result_manifest(value, [], section="components", claim_id=CLAIM_ID, limit=1)
    legacy_cursor = full["pagination"]["nextCursor"]
    with pytest.raises(ResultManifestError):
        inspect_result_manifest(
            value, [], section="components", claim_id=CLAIM_ID,
            component_id=MAPPED, limit=1, cursor=legacy_cursor,
        )

    # A version-2 general page cannot be resumed under a focused selector;
    # component selection is part of cursor identity.
    modern_page = inspect_result_manifest(value, [], section="components", claim_id=CLAIM_ID, limit=1)
    modern_cursor = modern_page["pagination"]["nextCursor"]
    assert modern_cursor
    focused = _component_view(value, limit=1)
    assert focused["pagination"]["total"] == 1
    assert focused["pagination"]["nextCursor"] is None
    for component in (MAPPED, UNMAPPED):
        with pytest.raises(ResultManifestError):
            inspect_result_manifest(
                value, [], section="components", claim_id=CLAIM_ID,
                component_id=component, limit=1, cursor=modern_cursor,
            )


def test_component_cli_json_text_and_references_have_parity(tmp_path, capsys):
    value, attached = _scoped_inputs()
    manifest_path = tmp_path / "manifest.json"
    assessment_path = tmp_path / "assessments.json"
    manifest_path.write_bytes(canonical_json(value))
    assessment_path.write_bytes(canonical_json(attached))
    outputs = []
    for fmt in ("json", "text"):
        code = main([
            "result", "inspect", str(manifest_path), "--assessments", str(assessment_path),
            "--section", "components", "--claim", CLAIM_ID, "--component", MAPPED,
            "--format", fmt,
        ])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.err == ""
        assert len(captured.out.encode()) <= 32768
        outputs.append(captured.out)

    decoded = _text_json(outputs[1])
    assert decoded == json.loads(outputs[0])
    assert decoded["rows"][0]["componentScope"]["status"] == "reported"
    _assert_references_resolve(decoded["rows"][0], value, attached)
