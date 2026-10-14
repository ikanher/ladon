"""Required real-Lean M1 gate: no skips or authored extraction substitutes."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from ladon.correspondence_check import check_correspondence, prepare_correspondence
from ladon.proof_slice import digest, extract_proof_slice

FIXTURE = Path(__file__).parent / "fixtures/correspondence_m1"


def _repo(path):
    shutil.copytree(FIXTURE, path, ignore=shutil.ignore_patterns(".ladon", "*.olean"))
    return path


def test_real_tactic_and_term_applications_and_scope_adversaries(tmp_path):
    root = _repo(tmp_path / "repo")
    term = extract_proof_slice(root, "Proof.lean", "Proof", "Correspondence.term", "bridge")
    tactic = extract_proof_slice(root, "Proof.lean", "Proof", "Correspondence.tactic", "bridge")
    assert term["complete"] and tactic["complete"]
    assert [a["isProp"] for a in term["nodes"][0]["arguments"]] == [False, True]
    record = json.loads((root / "positive.json").read_text())
    plan = prepare_correspondence(record, term, {"n": "n"})
    with pytest.raises(ValueError, match="unknown object map reference or escaped binder"):
        prepare_correspondence(record, term, {"h": "n"})
    with pytest.raises(ValueError):
        prepare_correspondence(record, term, {"n": "later-witness"})
    altered = copy.deepcopy(plan)
    altered["obligations"][-1]["goal"] = "True"
    altered["planId"] = digest({k: v for k, v in altered.items() if k != "planId"})
    with pytest.raises(ValueError, match="original contract changed"):
        check_correspondence(altered, [], root)
    extra = copy.deepcopy(term)
    extra["nodes"][0]["hypotheses"] = ["False"]
    with pytest.raises(ValueError, match="requires exactly"):
        prepare_correspondence(record, extra, {"n": "n"})
    erased = copy.deepcopy(term)
    erased["frontiers"] = []
    with pytest.raises(ValueError):
        prepare_correspondence(record, erased, {"n": "n"})


def test_actual_lean_rejects_wrong_object_type_and_placeholder_proof(tmp_path):
    root = _repo(tmp_path / "repo")
    observed = extract_proof_slice(root, "Proof.lean", "Proof", "Correspondence.term", "bridge")
    record = json.loads((root / "positive.json").read_text())
    record["formula"]["binder"]["domain"] = "Int"
    plan = prepare_correspondence(record, observed, {"n": "n"})
    result = check_correspondence(
        plan, [{"obligation": "object-map", "mode": "prove", "term": "by intro n; trivial"}], root
    )
    statuses = {r["obligation"]: r["status"] for r in result["checks"]}
    assert statuses["conditional"] == "supported"
    assert statuses["object-map"] == "unresolved"
    assert result["parentSupport"] == "unresolved"
    record["formula"]["binder"]["domain"] = "Nat"
    record["formula"]["body"]["conclusion"] = {
        "tag": "eq",
        "left": {"tag": "var", "id": "n"},
        "right": {"tag": "const", "name": "0"},
    }
    plan = prepare_correspondence(record, observed, {"n": "n"})
    result = check_correspondence(
        plan, [{"obligation": "conclusion", "mode": "prove", "term": "by sorry"}], root
    )
    row = next(r for r in result["checks"] if r["obligation"] == "conclusion")
    assert row["status"] == "unresolved"
    assert result["conditionalValidity"] == "supported"
    assert result["parentSupport"] == "unresolved"
