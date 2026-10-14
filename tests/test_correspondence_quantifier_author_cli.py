"""Different dependency readings remain distinct through native public authoring."""

import hashlib
import json

from ladon.entrypoint import main
from ladon.proofir_v3 import validate_envelope_batch


def test_public_quantifier_order_has_distinct_native_subjects(tmp_path):
    quote = "There is an upper bound for each input."
    raw = (quote + "\n").encode()
    (tmp_path / "source.txt").write_bytes(raw)
    relation = {
        "tag": "lt",
        "left": {"tag": "var", "id": "n"},
        "right": {"tag": "var", "id": "k"},
    }
    readings = []
    for label, order in [
        ("pointwise", [("exists", "k"), ("forall", "n")]),
        ("uniform", [("forall", "n"), ("exists", "k")]),
    ]:
        formula = relation
        for tag, identity in order:
            formula = {
                "tag": tag,
                "binder": {"id": identity, "name": identity, "domain": "Nat"},
                "body": formula,
            }
        record = {
            "id": label,
            "source": {
                "path": "source.txt",
                "startLine": 1,
                "endLine": 1,
                "quote": quote,
                "sha256": hashlib.sha256(raw).hexdigest(),
            },
            "formula": formula,
            "symbols": {},
        }
        path, output = tmp_path / (label + ".json"), tmp_path / (label + ".out.json")
        path.write_text(json.dumps(record))
        assert (
            main(
                [
                    "investigation",
                    "interpret",
                    "--record",
                    str(path),
                    "--root",
                    str(tmp_path),
                    "--output",
                    str(output),
                ]
            )
            == 0
        )
        reading = json.loads(output.read_text())
        validate_envelope_batch(reading["artifacts"])
        readings.append(reading)
    assert readings[0]["loweredFormula"] != readings[1]["loweredFormula"]
    subjects = [
        next(
            row["artifactId"]
            for row in reading["artifacts"]
            if row["artifactKind"] == "proofir.interpretation"
        )
        for reading in readings
    ]
    assert subjects[0] != subjects[1]
