"""Portable controls for protocol-gated shadowed-name fallback validation."""
from __future__ import annotations

import pytest

from ladon._semantic_observation_contract import (
    _validate_context_subject,
    _validate_scratch_notation,
)
from ladon.semantic_projection_core import SemanticProjectionError

V3 = "ladon-lean-semantic-v3/check-candidate"
V4 = "ladon-lean-semantic-v4/check-candidate"
REQUESTED = [{"name": "n", "type": "Nat"}]


def _row(local_id: str, name: str, display: str, structural: str) -> dict:
    return {
        "localId": local_id,
        "userName": name,
        "binderInfo": "Lean.BinderInfo.default",
        "typeDisplay": display,
        "typeStructural": structural,
        "valueDisplay": "",
        "valueStructural": "",
        "dependencies": [],
        "origin": "goal-introduced",
    }


def _validate(protocol: str, rows: list[dict]) -> None:
    observed = [{"name": row["userName"], "type": row["typeDisplay"]} for row in rows]
    subject = {"localContext": observed}
    check = {"callerLocalContext": REQUESTED, "semanticProtocol": protocol}
    if protocol == V4:
        check["applicationObservationVersion"] = 4
    owner = {
        "subjectRefs": [
            {"kind": "local-context", "searchShape": {"localContext": rows}}
        ]
    }
    _validate_context_subject(subject, check, None, check_artifact=owner)


def _notation_shadowed_rows(second_local_id: str = "local:1") -> list[dict]:
    return [
        _row("local:0", "n", "ℕ", "Lean.Expr.const `Nat []"),
        _row(second_local_id, "n", "Bool", "Lean.Expr.const `Bool []"),
    ]


def test_v4_notation_fallback_accepts_a_shadowed_display_name():
    """V4 owner evidence disambiguates repeated names by unique raw local IDs."""
    _validate(V4, _notation_shadowed_rows())


def test_v3_notation_fallback_still_rejects_shadowed_display_names():
    with pytest.raises(SemanticProjectionError, match="requested prefix"):
        _validate(V3, _notation_shadowed_rows())


def test_v4_shadowed_names_do_not_allow_duplicate_raw_local_ids():
    with pytest.raises(SemanticProjectionError, match="requested prefix"):
        _validate(V4, _notation_shadowed_rows(second_local_id="local:0"))


@pytest.mark.parametrize("protocol,duplicate,valid", [(V4, False, True), (V3, False, False), (V4, True, False)])
def test_scratch_notation_uses_parent_context_protocol(protocol, duplicate, valid):
    rows = _notation_shadowed_rows("local:0" if duplicate else "local:1")
    observed = [{"name": row["userName"], "type": row["typeDisplay"]} for row in rows]
    shape = {"localContext": rows}
    if protocol == V4:
        shape.update(applicationObservationVersion=4, semanticProtocol=protocol)
    parent = {"subjectRefs": [{"kind": "candidate-application", "searchShape": shape}]}
    if valid:
        _validate_scratch_notation(observed, REQUESTED, parent)
    else:
        with pytest.raises(SemanticProjectionError, match="parent structural evidence"):
            _validate_scratch_notation(observed, REQUESTED, parent)
