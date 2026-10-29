"""The public observation path must keep convincing names semantically unadmitted."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from test_proof_contract_cli import invoke

ROOT = Path(__file__).parent / "fixtures/real_bound_observation"


@pytest.fixture(scope="module")
def snapshot():
    from ladon.proof_contract_formal import produce_formal_snapshot

    result = produce_formal_snapshot(ROOT, "NamedBound.lean", "NamedBound", "namedEstimate")
    assert result["observation"]["status"] == "observed"
    assert result["contract"] is None
    return result


def test_actual_named_fake_preserves_shape_but_never_admits_meaning(snapshot):
    from ladon.real_bound_observation import observe_bound_snapshot, verify_bound_observation

    original = deepcopy(snapshot)
    result = observe_bound_snapshot(snapshot, ROOT)
    assert result["candidate"]["loss"] == 7
    assert result["status"] == "observed"
    assert result["admission"] == "unresolved"
    assert result["contract"] is None
    assert result["authority"] == "syntax-only"
    assert result["statementSnapshot"] == original == snapshot
    assert verify_bound_observation(result, ROOT) == result


@pytest.mark.parametrize("mutation", ["loss", "admission", "extra", "implementation"])
def test_rehashed_tampering_is_rejected_by_replay(snapshot, mutation):
    from ladon.proof_contract_source import snapshot_identity
    from ladon.real_bound_observation import observe_bound_snapshot, verify_bound_observation

    result = observe_bound_snapshot(snapshot, ROOT)
    if mutation == "loss":
        result["candidate"]["loss"] = 4
    elif mutation == "admission":
        result["admission"] = "checked"
    elif mutation == "extra":
        result["uncheckedMeaning"] = "derivative-norm"
    else:
        result["implementationDigest"] = "sha256:" + "0" * 64
    result["snapshotId"] = snapshot_identity(result)
    with pytest.raises(ValueError):
        verify_bound_observation(result, ROOT)


def test_cli_observe_inspect_and_collision_keep_unresolved_exit(snapshot, tmp_path):
    source = tmp_path / "formal.json"
    output = tmp_path / "bound.json"
    source.write_text(json.dumps(snapshot))
    original = source.read_bytes()
    result = invoke("observe-bound", "--input", source, "--root", ROOT, "--output", output)
    assert result.returncode == 2, result.stdout + result.stderr
    saved = output.read_bytes()
    assert json.loads(saved)["candidate"]["loss"] == 7
    checked = invoke("inspect", "--input", output, "--root", ROOT)
    assert checked.returncode == 2, checked.stdout + checked.stderr
    assert json.loads(checked.stdout) == json.loads(saved)
    collision = invoke("observe-bound", "--input", source, "--root", ROOT, "--output", output)
    assert collision.returncode == 2
    assert output.read_bytes() == saved
    assert source.read_bytes() == original


def test_nested_snapshot_source_identity_is_checked(snapshot):
    from ladon.proof_contract_source import snapshot_identity
    from ladon.real_bound_observation import observe_bound_snapshot, verify_bound_observation

    result = observe_bound_snapshot(snapshot, ROOT)
    result["statementSnapshot"]["source"]["sha256"] = "0" * 64
    result["statementSnapshot"]["snapshotId"] = snapshot_identity(result["statementSnapshot"])
    result["snapshotId"] = snapshot_identity(result)
    with pytest.raises(ValueError, match="source|stale"):
        verify_bound_observation(result, ROOT)
