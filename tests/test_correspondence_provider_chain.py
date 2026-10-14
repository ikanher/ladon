"""A missing predecessor affects correspondence, not the valid formal conditional."""

import hashlib
from pathlib import Path

from ladon.correspondence_check import check_correspondence, prepare_correspondence
from ladon.proof_slice import extract_proof_slice


def test_false_predecessor_keeps_conditional_and_provider_replay_separate():
    root = Path(__file__).parent / "fixtures/correspondence_m1"
    source = root / "predecessor.txt"
    def positive(identity):
        return {"tag": "lt", "left": {"tag": "const", "name": "0"},
                "right": {"tag": "var", "id": identity}}
    formula = {"tag": "implies", "premise": positive("n"),
               "conclusion": {"tag": "and", "items": [positive("n"), positive("m")]}}
    for identity in ("m", "n"):
        formula = {"tag": "forall", "binder": {"id": identity, "name": identity, "domain": "Nat"},
                   "body": formula}
    record = {"id": "missing-second-provider", "source": {
        "path": source.name, "startLine": 1, "endLine": 1,
        "quote": source.read_text().strip(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
        "formula": formula, "symbols": {}}
    actual = extract_proof_slice(root, "Scoped.lean", "Scoped", "Scoped.chain",
                                "Scoped.combine", scoped=True)
    assert actual["complete"] is True
    plan = prepare_correspondence(record, actual, {"n": "n", "m": "m"})
    assert {"provider-2", "provider-3"} <= {o["id"] for o in plan["obligations"]}
    terms = [{"obligation": "premise-3", "mode": "refute", "term":
              "by intro h; have bad := h 1 0 (by decide); exact (Nat.lt_irrefl 0) bad"}]
    result = check_correspondence(plan, terms, root)
    assert result["conditionalValidity"] == "supported"
    assert result["providerValidity"] == "conditionally-supported"
    assert result["premiseEstablishment"] == "refuted"
    assert result["parentSupport"] == "refuted-correspondence"
    assert result["methodCorrespondence"] == "unreviewed"


def test_earlier_have_rhs_does_not_include_later_facts():
    root = Path(__file__).parent / "fixtures/correspondence_m1"
    first = extract_proof_slice(root, "Scoped.lean", "Scoped", "Scoped.chain", "Scoped.bridge",
                               0, scoped=True)
    second = extract_proof_slice(root, "Scoped.lean", "Scoped", "Scoped.chain", "Scoped.bridge",
                                1, scoped=True)
    assert first["complete"] and second["complete"]
    assert {row["name"] for row in first["localContext"]} == {"n", "m", "hn", "hm"}
    assert {row["name"] for row in second["localContext"]} == {"n", "m", "hn", "hm", "first"}
