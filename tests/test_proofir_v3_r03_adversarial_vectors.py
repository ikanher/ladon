from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from support.proofir_v3_native import native_artifacts

from ladon.proofir_v3 import ProofIRV3Error, detached_content_id, validate_envelope


def _reidentify(artifact: dict) -> dict:
    artifact["artifactId"] = detached_content_id(artifact)
    return artifact


def _mutate(kind: str, path: tuple[object, ...], replacement: object) -> dict:
    artifact = copy.deepcopy(native_artifacts()[kind])
    target = artifact["payload"]
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = replacement
    return _reidentify(artifact)


@pytest.mark.parametrize(
    ("kind", "path", "replacement"),
    [
        ("proofir.derivation", ("derivationId",), 7),
        ("proofir.derivation", ("steps", 0, "kind"), 7),
        ("proofir.derivation", ("steps", 0, "kind"), "not-a-step-kind"),
        ("proofir.plan", ("planId",), 7),
        ("proofir.plan", ("policy", "strategy"), 7),
        ("proofir.plan", ("policy", "budget", "maxSteps"), []),
        ("proofir.plan", ("policy", "selection"), 7),
        ("proofir.attempt-log", ("attemptLogId",), 7),
        ("proofir.attempt-log", ("attempts", 0, "attemptId"), 7),
        ("proofir.attempt-log", ("summary",), "incomplete"),
        ("proofir.attempt-log", ("summary", "residualPremiseRefs"), "bad"),
        ("proofir.attempt-log", ("attempts", 0, "diagnostics", 0, "message"), 7),
        ("proofir.check-run", ("checkRunId",), 7),
        ("proofir.check-run", ("operation",), 7),
        ("proofir.check-run", ("results", 0, "diagnostics"), "bad"),
        ("proofir.attachment-set", ("attachmentSetId",), 7),
        ("proofir.attachment-set", ("attachments", 0, "decisiveEvidence"), [7]),
        ("proofir.attachment-set", ("attachments", 0, "rejectionReasons"), [7]),
        ("proofir.attachment-set", ("attachments", 0, "candidates", 0, "decisiveEvidence"), [7]),
        ("proofir.governance-observation", ("diagnostics",), [{"stage": 7}]),
        ("proofir.source-map", ("anchors", 0, "start", "line"), 0),
        ("proofir.source-map", ("anchors", 0, "end"), {"byte": 0, "line": 1, "column": 0}),
    ],
)
def test_r03_nested_adversarial_vectors_are_rejected(
    kind: str, path: tuple[object, ...], replacement: object
) -> None:
    with pytest.raises(ProofIRV3Error):
        validate_envelope(_mutate(kind, path, replacement))


def test_r03_source_coordinate_policy_rejects_pathological_ranges() -> None:
    artifact = _mutate(
        "proofir.source-map",
        ("anchors", 0, "sourcePath"),
        "../escape.lean",
    )
    # Source paths are packet-local and must not escape the repository boundary.
    with pytest.raises(ProofIRV3Error):
        validate_envelope(artifact)


def test_r03_bundle_inventory_is_complete_and_every_vector_is_rejected() -> None:
    vectors = json.loads(
        Path("tests/fixtures/proofir_v3_r03_adversarial.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(vectors) == 25
    assert len({vector["name"] for vector in vectors}) == 25
    diagnostics = json.loads(
        Path("tests/fixtures/proofir_v3_r03_diagnostics.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(diagnostics) == {vector["name"] for vector in vectors}
    for vector in vectors:
        artifact = copy.deepcopy(native_artifacts()[vector["kind"]])
        target = artifact["payload"]
        for part in vector["path"][:-1]:
            target = target[part]
        target[vector["path"][-1]] = vector["replacement"]
        with pytest.raises(ProofIRV3Error) as captured:
            validate_envelope(_reidentify(artifact))
        diagnostic = captured.value.diagnostic
        assert [diagnostic.stage, diagnostic.code, diagnostic.pointer] == diagnostics[
            vector["name"]
        ]
