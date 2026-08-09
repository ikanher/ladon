from __future__ import annotations

import json
from pathlib import Path

from support.proofir_v3_native import claim_artifact

from ladon.proofir_v3_cli import proofir_v3_main


def test_validate_and_inspect_results_have_explicit_schemas(
    tmp_path: Path, capsys
) -> None:
    source = tmp_path / "claim.json"
    source.write_text(json.dumps(claim_artifact()), encoding="utf-8")

    assert proofir_v3_main(["validate", str(source)]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["schema"] == "ladon-proofir-validate-result-v1"
    assert validated["operation"] == "validate"
    assert validated["proofirVersion"] == "3.0"

    assert proofir_v3_main(["inspect", str(source)]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["schema"] == "ladon-proofir-inspect-result-v1"
    assert inspected["operation"] == "inspect"
    assert inspected["proofirVersion"] == "3.0"
