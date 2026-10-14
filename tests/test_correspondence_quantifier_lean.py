"""An actual pointwise proof cannot establish one common witness."""

import hashlib
import shutil
from pathlib import Path

from ladon.correspondence_check import check_correspondence, prepare_correspondence
from ladon.proof_slice import extract_proof_slice


def test_uniform_reading_is_refuted_by_actual_lean(tmp_path):
    fixture = Path(__file__).parent / "fixtures/correspondence_m1"
    root = tmp_path / "repo"
    shutil.copytree(fixture, root, ignore=shutil.ignore_patterns(".ladon", "*.olean"))
    quote = "A separate upper bound for each natural number gives one bound for all of them."
    raw = (quote + "\n").encode()
    (root / "claim.txt").write_bytes(raw)
    formula = {"tag": "lt", "left": {"tag": "var", "id": "n"}, "right": {"tag": "var", "id": "k"}}
    for tag, identity in [("forall", "n"), ("exists", "k"), ("forall", "d")]:
        formula = {
            "tag": tag,
            "binder": {"id": identity, "name": identity, "domain": "Nat"},
            "body": formula,
        }
    record = {
        "id": "uniform",
        "source": {
            "path": "claim.txt",
            "startLine": 1,
            "endLine": 1,
            "quote": quote,
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "formula": formula,
        "symbols": {},
    }
    actual = extract_proof_slice(
        root,
        "Pointwise.lean",
        "Pointwise",
        "QuantifierFixture.selected",
        "QuantifierFixture.pointwise",
    )
    assert actual["complete"]
    plan = prepare_correspondence(record, actual, {"d": "d"})
    term = (
        "by intro h; have u := h 0 trivial (QuantifierFixture.pointwise 0); "
        "obtain ⟨k, hk⟩ := u; exact Nat.lt_irrefl k (hk k)"
    )
    result = check_correspondence(
        plan, [{"obligation": "conclusion", "mode": "refute", "term": term}], root
    )
    assert result["conditionalValidity"] == "supported"
    assert result["parentSupport"] == "refuted-correspondence"
    assert result["checks"][0]["status"] == "refuted"
