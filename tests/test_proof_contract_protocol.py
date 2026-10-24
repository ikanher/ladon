"""Independent audit falsifications become permanent source-backed regressions."""

import json
from pathlib import Path

from ladon.proof_contract_production import produce_formal_contract

ROOT = Path(__file__).parent / "fixtures/proof_contract_protocol"


def test_source_stdout_and_early_exit_cannot_impersonate_helper_completion():
    result = produce_formal_contract(ROOT, "ForgedWorker.lean", "ForgedWorker",
                                     "ForgedWorker.actual_offset_one")
    assert result["status"] == "unavailable"
    assert result["contract"] is None
    assert result["residuals"]


def test_regularity_origin_is_the_exact_right_scale_when_names_repeat():
    result = produce_formal_contract(ROOT, "OriginCollision.lean", "OriginCollision",
                                     "OriginCollision.same_scale_head")
    assert result["status"] == "extracted"
    origin = result["featureOrigins"]["regularity"][0].split("#", 1)[1]
    current = result["observation"]
    for token in origin.lstrip("/").split("/"):
        current = current[int(token)] if isinstance(current, list) else current[token]
    assert "HAdd.hAdd" in json.dumps(current)
    assert "OriginCollision.f" not in json.dumps(current)
