"""Scoped interpretation regressions; presentation does not supply proof authority."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from ladon.correspondence_interpretation import lower_formula, validate_interpretation
from ladon.correspondence_source import source_positions
from ladon.proofir_correspondence import interpretation_artifacts
from ladon.proofir_correspondence_payloads import validate_native_interpretation_batch

FIXTURE = Path(__file__).parent / "fixtures/correspondence_m1"


def record():
    return json.loads((FIXTURE / "positive.json").read_text())


def test_binder_display_name_and_consistent_identity_renaming_are_invariant():
    left = record()
    right = copy.deepcopy(left)
    right["formula"]["binder"].update(id="renamed", name="a different printed name")
    for relation in (right["formula"]["body"]["premise"], right["formula"]["body"]["conclusion"]):
        relation["right"]["id"] = "renamed"
    assert lower_formula(left["formula"], {}) == lower_formula(right["formula"], {})


def test_explicit_global_symbol_cannot_be_captured_by_a_generated_binder():
    formula = {
        "tag": "forall",
        "binder": {"id": "n", "name": "n", "domain": "Nat"},
        "body": {
            "tag": "eq",
            "left": {"tag": "const", "name": "global"},
            "right": {"tag": "var", "id": "n"},
        },
    }
    result = lower_formula(formula, {"global": {"leanName": "v0", "leanType": "Nat"}})
    assert "_root_.v0" in result


def test_unknown_fields_and_escaped_variable_rejected():
    value = record()
    with pytest.raises(ValueError):
        validate_interpretation({**value, "status": "proved"}, FIXTURE)
    value["formula"]["body"]["conclusion"]["right"]["id"] = "escaped"
    with pytest.raises(ValueError, match="unbound or escaped"):
        validate_interpretation(value, FIXTURE)


def test_exact_unicode_formfeed_span_and_byte_anchor(tmp_path):
    raw = "α\fβ\n".encode()
    (tmp_path / "source.txt").write_bytes(raw)
    value = record()
    value["source"] = {
        "path": "source.txt",
        "startLine": 2,
        "endLine": 2,
        "quote": "β",
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    start, end, quote = source_positions(value, tmp_path)
    assert quote == "β"
    assert start == {"byte": 3, "line": 2, "column": 1}
    assert end == {"byte": 5, "line": 2, "column": 2}
    artifacts = list(interpretation_artifacts(value, "sha256:" + "e" * 64, source_root=tmp_path))
    ref = validate_native_interpretation_batch(
        value, artifacts, "sha256:" + "e" * 64, source_root=tmp_path
    )
    assert ref["localId"] == value["id"]
    (tmp_path / "source.txt").write_text("changed")
    with pytest.raises(ValueError, match="stale source digest"):
        validate_native_interpretation_batch(
            value, artifacts, "sha256:" + "e" * 64, source_root=tmp_path
        )
