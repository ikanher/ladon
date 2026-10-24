"""Generated contexts cannot recover past a failed exclusion guard."""

import importlib
import shutil

import pytest
from test_proof_contract_source_obligations import FIXTURE, _request

from ladon.proof_contract_formal import produce_formal_snapshot

FAIL_IN_GENERATED_MODULE = """
run_cmd do
  if (← Lean.getEnv).mainModule == `Probe then
    throwError "controlled generated-prefix failure"

"""


def test_earlier_command_failure_cannot_be_ignored_before_selected_goal(tmp_path):
    api = importlib.import_module("ladon.proof_contract_source_obligations")
    shutil.copyfile(FIXTURE / "lean-toolchain", tmp_path / "lean-toolchain")
    original = (FIXTURE / "SourceAtoms.lean").read_text()
    source = "import Lean\n" + original.replace(
        "theorem parent", FAIL_IN_GENERATED_MODULE + "theorem parent",
    )
    (tmp_path / "SourceAtoms.lean").write_text(source)
    snapshots = {}
    for name in ("parent", "provider"):
        snapshots[name] = produce_formal_snapshot(
            tmp_path, "SourceAtoms.lean", "SourceAtoms", "SourceAtoms." + name,
            timeout_seconds=30,
        )
        assert snapshots[name]["status"] == "extracted"
    result = api.instantiate_source_bound_premise(_request((tmp_path, snapshots)))
    assert result["status"] != "candidate-goal", result
    assert result.get("capture") is None


@pytest.mark.parametrize("field", ["branchIndex", "premiseOrdinal"])
def test_rejected_metadata_is_bounded_even_before_occurrence_validation(field):
    from test_proof_contract_source_obligation_boundaries import _invalid_request

    api = importlib.import_module("ladon.proof_contract_source_obligations")
    request = _invalid_request()
    request[field] = "x" * (9 * 1024**2)
    result = api.instantiate_source_bound_premise(request)
    assert result["status"] == "rejected"
    assert result[field] is None
