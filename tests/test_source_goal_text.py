"""Rendering controls, without claiming that a constructed transport fixture is a proof."""
from __future__ import annotations

from ladon.proof_search_cli import _render_text


def _capture_payload():
    return {
        "schema": "ladon-source-goal-capture-result-v1", "status": "captured",
        "capture": {
            "captureId": "sha256:fixture", "source": {"path": "Owner.lean", "position": {"line": 3, "column": 6}},
            "goal": {"typeDisplay": "x = x", "goalId": "goal:observed", "ordinal": 0,
                     "localContext": [
                         {"userName": "x", "typeDisplay": "Nat", "valueDisplay": "",
                          "implementationDetail": False, "localId": "fvar:x", "binderInfo": "default"},
                         {"userName": "_example", "typeDisplay": "x = x", "valueDisplay": "",
                          "implementationDetail": True, "localId": "fvar:self", "binderInfo": "default"},
                         {"userName": "y", "typeDisplay": "Nat", "valueDisplay": "x",
                          "implementationDetail": False, "localId": "fvar:y", "binderInfo": "default"},
                     ]},
        },
    }


def test_direct_api_capture_text_foregrounds_actual_goal_and_ordered_context():
    text = _render_text(_capture_payload())
    assert "goal: x = x" in text
    assert text.index("goal: x = x") < text.index("source selection:")
    assert text.index("fvar:x") < text.index("fvar:self") < text.index("fvar:y")
    assert "[internal]" in text
    assert "y: Nat := x" in text
    assert "x: Nat := " not in text


def test_text_preserves_capture_scope_and_exact_complete_json_reference():
    text = _render_text(_capture_payload())
    assert "replay: not-run" in text
    assert "sha256:fixture" in text
    assert "#/capture/goal/localContext" in text


def test_diagnostic_wrapper_keeps_supplied_expected_type_separate():
    payload = {
        "schema": "ladon-source-goal-query-result-v1", "status": "captured",
        "queryEvidence": {"selected": {"expression": "term", "actualType": "Nat", "expectedType": "Bool"}},
        "captureResult": _capture_payload(),
    }
    text = _render_text(payload)
    assert "caller-supplied compiler fragments (not an observed goal)" in text
    assert "expected Bool" in text
    assert "goal: x = x" in text
    assert "#/captureResult/capture/goal/localContext" in text


def test_unavailable_capture_text_keeps_failure_without_a_goal():
    text = _render_text({
        "schema": "ladon-source-goal-capture-result-v1", "status": "stale", "capture": None,
        "diagnostic": {"code": "source-changed", "message": "bytes changed"},
    })
    assert "status: stale" in text
    assert "diagnostic: source-changed: bytes changed" in text
    assert "goal: x = x" not in text
