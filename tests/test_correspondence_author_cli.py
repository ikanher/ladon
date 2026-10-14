"""Source binding and closed interpretations through the ordinary entrypoint."""

import copy
import json
import shutil
from pathlib import Path

from ladon.entrypoint import main
from ladon.proofir_v3 import validate_envelope_batch


def test_public_authoring_keeps_alpha_names_and_rejects_stale_or_unknown(tmp_path, capsys):
    fixture = Path(__file__).parent / "fixtures/correspondence_m1"
    root = tmp_path / "repo"
    shutil.copytree(fixture, root, ignore=shutil.ignore_patterns(".ladon", "*.olean"))
    original = json.loads((root / "positive.json").read_text())

    def invoke(record, name):
        path, output = tmp_path / (name + ".json"), tmp_path / (name + ".out.json")
        path.write_text(json.dumps(record))
        code = main(
            [
                "investigation",
                "interpret",
                "--record",
                str(path),
                "--root",
                str(root),
                "--output",
                str(output),
            ]
        )
        return code, json.loads(output.read_text()) if output.exists() else None

    code, first = invoke(original, "first")
    assert code == 0
    renamed = copy.deepcopy(original)
    renamed["formula"]["binder"]["name"] = "a different display"
    code, second = invoke(renamed, "second")
    assert code == 0 and first["loweredFormula"] == second["loweredFormula"]
    assert first["artifacts"] != second["artifacts"]  # attributed source record remains exact
    validate_envelope_batch(first["artifacts"])
    opaque = copy.deepcopy(original)
    opaque["formula"] = {"tag": "opaque", "text": "unsupported analysis", "reason": "not lowered"}
    code, residual = invoke(opaque, "opaque")
    assert code == 0 and residual["loweredFormula"] is None and residual["residuals"]
    malformed = copy.deepcopy(original)
    malformed["inventedHypothesis"] = "False"
    assert invoke(malformed, "unknown")[0] == 2
    (root / "claim.txt").write_text("changed source\n")
    assert invoke(original, "stale")[0] == 2
    assert '"status": "invalid"' in capsys.readouterr().out
