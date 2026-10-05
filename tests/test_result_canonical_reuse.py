"""Result inspection and guide paths should share their owned canonical population."""
from __future__ import annotations

import copy

from support.result_guide import guide_inputs
from support.semantic_evidence import semantic_evidence

from ladon import proofir_v3
from ladon.result_guides import guide_result_manifest
from ladon.result_inspection import inspect_result_manifest
from ladon.result_manifest_io import ResultManifestError


def test_inspect_and_guide_reuse_population_preparations(monkeypatch):
    manifest, artifacts, guide = guide_inputs()
    check_env, check = semantic_evidence("population-reuse-count")[0]
    artifacts = [row for row in artifacts if row["artifactKind"] != "proofir.environment"]
    artifacts.extend([check_env, check])
    original = proofir_v3._prepare_envelope
    prepared = []

    def counted(value, max_artifact_bytes):
        prepared.append(value.get("artifactId") if isinstance(value, dict) else None)
        return original(value, max_artifact_bytes)

    monkeypatch.setattr(proofir_v3, "_prepare_envelope", counted)
    inspection = inspect_result_manifest(manifest, artifacts, section="targets")
    inspect_count = len(prepared)
    prepared.clear()
    guided = guide_result_manifest(manifest, artifacts, guide_inputs=guide, section="steps")
    guide_count = len(prepared)

    assert inspection["operation"] == "inspect"
    assert guided["operation"] == "guide"
    # Each supplied occurrence is prepared once for full-population validation;
    # selected projections should consume that owner-controlled snapshot.
    assert inspect_count <= len(artifacts) and guide_count <= len(artifacts), (
        f"canonical preparations inspect={inspect_count}, guide={guide_count}, "
        f"occurrences={len(artifacts)}"
    )


def test_no_receipt_and_malformed_unselected_population_keep_legacy_semantics():
    manifest, artifacts, _guide = guide_inputs()
    artifacts = copy.deepcopy(artifacts)
    check_env, check = semantic_evidence("population-reuse-no-receipt")[0]
    check["extensions"]["ladon.process-observation/v1"].pop("evidenceReceipt")
    from ladon.proofir_v3 import detached_content_id
    check["artifactId"] = detached_content_id(check)
    artifacts = [row for row in artifacts if row["artifactKind"] != "proofir.environment"]
    artifacts.extend([check_env, check])
    # No check receipt is a supported legacy case and must remain inspectable.
    result = inspect_result_manifest(manifest, artifacts, section="targets")
    assert result["operation"] == "inspect"
    # Every supplied row remains subject to validation even if this page selects
    # only targets; malformed off-page evidence cannot be hidden by selection.
    malformed = copy.deepcopy(artifacts)
    environment = next(row for row in malformed if row["artifactKind"] == "proofir.environment")
    environment["payload"]["dependencies"].append({"broken": True})
    try:
        inspect_result_manifest(manifest, malformed, section="targets")
    except ResultManifestError as error:
        assert "invalid supplied canonical evidence" in str(error)
    else:
        raise AssertionError("selected inspection skipped malformed off-page canonical input")
