"""Contract authoring uses the ordinary CLI and immutable source snapshots."""

import json
import subprocess
import sys

from support.proofir_v3_native import ENVIRONMENT
from test_proof_contract_source import prose_inputs


def invoke(*args):
    return subprocess.run([sys.executable, "-m", "ladon.entrypoint", "investigation",
                           "contract", *map(str, args)], capture_output=True,
                          text=True, check=False)


def arguments(tmp_path):
    values = prose_inputs(tmp_path)
    paths = []
    for name, value in zip(("interpretation", "contract", "origins"), values, strict=True):
        path = tmp_path / (name + ".json")
        path.write_text(json.dumps(value))
        paths.append(path)
    return ["produce", "--channel", "prose", "--root", tmp_path,
            "--interpretation", paths[0], "--record", paths[1], "--origins", paths[2],
            "--alternative-id", "reading:a", "--environment-ref", ENVIRONMENT]


def test_ordinary_produce_inspect_and_output_collision(tmp_path):
    args = arguments(tmp_path)
    destination = tmp_path / "snapshot.json"
    produced = invoke(*args, "--output", destination)
    assert produced.returncode == 0, produced.stderr + produced.stdout
    original = destination.read_bytes()
    inspected = invoke("inspect", "--input", destination, "--root", tmp_path)
    assert inspected.returncode == 0, inspected.stderr + inspected.stdout
    result = json.loads(inspected.stdout)
    assert result["channel"] == "prose"
    assert result["fidelity"] == "attributed-unreviewed"
    assert result["coverage"]["providers"] == "not-extracted"
    assert invoke(*args, "--output", destination).returncode == 2
    assert destination.read_bytes() == original


def test_snapshot_inspection_rejects_changed_original_source(tmp_path):
    destination = tmp_path / "snapshot.json"
    result = invoke(*arguments(tmp_path), "--output", destination)
    assert result.returncode == 0, result.stderr + result.stdout
    (tmp_path / "claim.txt").write_text("changed source")
    assert invoke("inspect", "--input", destination, "--root", tmp_path).returncode == 2
