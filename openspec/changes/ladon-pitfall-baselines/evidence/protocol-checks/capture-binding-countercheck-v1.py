"""Negative controls for successful capture source identity."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


CHECK_DIR = Path(__file__).resolve().parent
RUNNER = CHECK_DIR.parents[1] / "scripts" / "feasibility_baseline.py"
EXPECTED = "sha256:expected-source"


def load_runner():
    spec = importlib.util.spec_from_file_location("feasibility_baseline", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load feasibility runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    valid = {"status": "captured", "capture": {"source": {"digest": EXPECTED}}}
    assert runner._capture_source_binding_valid(valid, 0, EXPECTED)

    unavailable = {"status": "unavailable", "diagnostic": {"code": "no-goal"}}
    assert not runner._capture_source_binding_valid(unavailable, 1, EXPECTED)

    controls = {
        "wrongDigest": {"status": "captured", "capture": {"source": {"digest": "sha256:other"}}},
        "missingCapture": {"status": "captured", "capture": None},
        "missingSource": {"status": "captured", "capture": {"source": None}},
    }
    rejected = {}
    for name, value in controls.items():
        try:
            runner._capture_source_binding_valid(value, 0, EXPECTED)
        except runner.BaselineError as error:
            rejected[name] = str(error)
        else:
            raise AssertionError(f"claimed successful capture passed {name} control")
    try:
        runner._capture_source_binding_valid(valid, 1, EXPECTED)
    except runner.BaselineError as error:
        rejected["nonzeroReturnCode"] = str(error)
    else:
        raise AssertionError("nonzero capture exit passed successful-capture control")

    result = {
        "schema": "ladon-feasibility-capture-binding-countercheck-v1",
        "runnerSha256": hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
        "validCaptureAccepted": True,
        "unavailableCaptureRemainsUnresolved": True,
        "invalidSuccessControlsRejected": sorted(rejected),
        "result": "passed",
    }
    (CHECK_DIR / "capture-binding-countercheck-v1.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
