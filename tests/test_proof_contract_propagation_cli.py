"""Ordinary propagation commands preserve native replay and immutable outputs."""

import json

from test_proof_contract_cli import invoke
from test_proof_contract_propagation_native import inputs


def files(tmp_path, *, missing=False, expired=False):
    graph, contracts, request = inputs()
    request = {
        "goalRef": request["goal_ref"], "ruleBindings": request["rule_bindings"],
        "endpointInterfaces": request["endpoint_interfaces"],
        "scopeBindings": [] if missing else request["scope_bindings"],
        "bounds": {"deadlineUtc": "2000-01-01T00:00:00Z"} if expired else {},
    }
    values = {"graph": graph, "contract": contracts[0], "request": request,
              "context": {"artifacts": [graph, *contracts]}}
    paths = {key: tmp_path / (key + ".json") for key in values}
    for key, value in values.items():
        paths[key].write_text(json.dumps(value))
    return paths


def propagate(paths, destination):
    return invoke("propagate", "--derivation", paths["graph"],
                  "--contract", paths["contract"], "--request", paths["request"],
                  "--analysis-id", "analysis:cli", "--output", destination)


def test_cli_propagation_and_native_inspection_replay_exact_inputs(tmp_path):
    paths = files(tmp_path)
    destination = tmp_path / "analysis.json"
    produced = propagate(paths, destination)
    assert produced.returncode == 0, produced.stdout + produced.stderr
    original = destination.read_bytes()
    inspected = invoke("inspect", "--input", destination, "--context", paths["context"])
    assert inspected.returncode == 0, inspected.stdout + inspected.stderr
    artifact = json.loads(inspected.stdout)
    assert artifact["payload"]["result"]["complete"] is True
    assert artifact["payload"]["result"]["mathematicalFalsity"] == "not-established"
    assert propagate(paths, destination).returncode == 2
    assert destination.read_bytes() == original


def test_cli_native_inspection_requires_exact_input_owners(tmp_path):
    paths = files(tmp_path)
    destination = tmp_path / "analysis.json"
    assert propagate(paths, destination).returncode == 0
    paths["context"].write_text(json.dumps({"artifacts": []}))
    checked = invoke("inspect", "--input", destination, "--context", paths["context"])
    assert checked.returncode == 2
    assert json.loads(checked.stdout)["status"] == "invalid"


def test_cli_partial_propagation_retains_pending_work(tmp_path):
    paths = files(tmp_path, missing=True)
    destination = tmp_path / "analysis.json"
    produced = propagate(paths, destination)
    assert produced.returncode == 0, produced.stdout + produced.stderr
    result = json.loads(destination.read_text())["payload"]["result"]
    assert result["complete"] is False
    assert result["residuals"] or result["coverage"]["pending"]


def test_cli_expired_analysis_is_inspectable_as_historical_partial(tmp_path):
    paths = files(tmp_path, expired=True)
    destination = tmp_path / "analysis.json"
    assert propagate(paths, destination).returncode == 0
    checked = invoke("inspect", "--input", destination, "--context", paths["context"])
    assert checked.returncode == 0, checked.stdout + checked.stderr
    result = json.loads(checked.stdout)["payload"]["result"]
    assert result["complete"] is False
    assert result["deadlineObservation"]["firstExceededCheck"] is not None


def test_cli_rejects_extra_request_fields_without_creating_output(tmp_path):
    paths = files(tmp_path)
    request = json.loads(paths["request"].read_text())
    request["proofAccepted"] = True
    paths["request"].write_text(json.dumps(request))
    destination = tmp_path / "analysis.json"
    result = propagate(paths, destination)
    assert result.returncode == 2
    assert not destination.exists()
