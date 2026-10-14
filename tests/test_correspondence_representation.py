"""A representation function requires actual typed transport and premise supply."""

import hashlib
from pathlib import Path

from ladon.correspondence_check import check_correspondence, prepare_correspondence
from ladon.proof_slice import extract_proof_slice


def test_checked_representation_preserves_original_supply_and_transfer():
    root = Path(__file__).parent / "fixtures/correspondence_m1"
    source = root / "representation.txt"
    representation = {"tag": "app", "symbol": "val", "args": [{"tag": "var", "id": "i"}]}
    record = {"id": "bounded-representation", "source": {
        "path": source.name, "startLine": 1, "endLine": 1,
        "quote": source.read_text().strip(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
        "formula": {"tag": "forall", "binder": {"id": "i", "name": "index", "domain": "Fin 5"},
                    "body": {"tag": "lt", "left": representation,
                             "right": {"tag": "const", "name": "5"}}},
        "symbols": {"val": {"leanName": "Fin.val", "leanType": "Fin 5 → Nat"}}}
    actual = extract_proof_slice(root, "Representation.lean", "Representation",
                                "Representation.selected", "Representation.bridge", scoped=True)
    assert actual["complete"] is True
    plan = prepare_correspondence(record, actual, {"n": {"symbol": "val", "args": ["i"]}})
    assert "(_root_.Fin.val : Fin 5 → Nat) ladonNL0" in next(o["goal"] for o in plan["obligations"] if o["id"] == "premise-1")
    terms = [{"obligation": "interpretation", "term": "by intro h; exact h", "mode": "prove"},
             {"obligation": "object-map", "term": "by intro i; trivial", "mode": "prove"},
             {"obligation": "premise-1", "term": "by intro i n h; exact i.isLt", "mode": "prove"},
             {"obligation": "conclusion", "term": "by intro i n h hformal; exact hformal", "mode": "prove"}]
    result = check_correspondence(plan, terms, root)
    assert result["parentSupport"] == "supported-for-attributed-interpretation"
    assert result["methodCorrespondence"] == "unreviewed"
