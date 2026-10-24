"""Retain actual public-API observations for the controlled Nat atom fixture."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from time import monotonic

from test_proof_contract_source_obligations import FIXTURE, _complete, _request

from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_contract_source_obligations import instantiate_source_bound_premise


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def observe_inputs(root, output):
    snapshots = {}
    for name in ("parent", "provider"):
        snapshot = produce_formal_snapshot(
            root, "SourceAtoms.lean", "SourceAtoms", "SourceAtoms." + name,
            timeout_seconds=30,
        )
        if snapshot["status"] != "extracted":
            raise RuntimeError("controlled statement observation failed: " + name)
        write_json(output / (name + "-snapshot.json"), snapshot)
        snapshots[name] = snapshot
    return snapshots


def require_candidate(result):
    if result["status"] != "candidate-goal":
        raise RuntimeError("controlled atomic construction failed: " + str(result["diagnostic"]))


def check_repeat(first, second):
    for key in ("requestDigest", "prefixDigest", "generatedSourceDigest", "selectedRequirement"):
        if first[key] != second[key]:
            raise RuntimeError("repeat changed stable construction binding: " + key)
    if first["capture"]["captureId"] != second["capture"]["captureId"]:
        raise RuntimeError("repeat changed the exact source goal observation")


def run(output):
    started = monotonic()
    output.mkdir(parents=True, exist_ok=False)
    root = output / "repo"
    root.mkdir()
    for name in ("SourceAtoms.lean", "lean-toolchain"):
        shutil.copyfile(FIXTURE / name, root / name)
    original = (root / "SourceAtoms.lean").read_bytes()
    snapshots = observe_inputs(root, output)
    request = _request((root, snapshots))
    first = instantiate_source_bound_premise(request)
    write_json(output / "construction-first.json", first)
    require_candidate(first)
    completion = _complete(request, first["capture"], (
        "by intro s x; simpa [SourceAtoms.A, SourceAtoms.B, SourceAtoms.C] "
        "using SourceAtoms.provider s x"
    ))
    write_json(output / "completion.json", completion)
    if (completion["status"] != "completed" or completion["replay"]["status"] != "accepted"
            or completion["trust"]["accepted"] is not True):
        raise RuntimeError("controlled actual bridge replay was not accepted")
    second = instantiate_source_bound_premise(request)
    write_json(output / "construction-repeat.json", second)
    require_candidate(second)
    check_repeat(first, second)
    if (root / "SourceAtoms.lean").read_bytes() != original:
        raise RuntimeError("original source changed")
    summary = {
        "scope": "constructed-atomic-premise-development-control",
        "sourceFidelity": "attributed-unreviewed", "wholeMethodAuthority": "none",
        "mathematicalFalsity": "not-established", "elapsedSeconds": monotonic() - started,
        "inputSourceDigest": "sha256:" + hashlib.sha256(original).hexdigest(),
        "requestDigest": first["requestDigest"], "captureId": first["capture"]["captureId"],
        "constructionStatus": first["status"], "repeatBindingsIdentical": True,
        "selectedOffset": first["selectedRequirement"]["contractRecord"]["features"]["regularity"]["offset"],
        "providerOffset": snapshots["provider"]["contract"]["features"]["regularity"]["offset"],
        "completionStatus": completion["status"], "replayStatus": completion["replay"]["status"],
        "trustAccepted": completion["trust"]["accepted"],
        "observedAxioms": completion["trust"]["observedAxioms"],
        "limits": request["limits"], "rawRecords": [
            "parent-snapshot.json", "provider-snapshot.json", "construction-first.json",
            "completion.json", "construction-repeat.json"],
    }
    write_json(output / "SUMMARY.json", summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output.resolve())
