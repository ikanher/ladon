"""Canonical population reuse must keep validation complete and bounded."""
from __future__ import annotations

from support.proofir_v3_native import claim_artifact
from support.semantic_evidence import semantic_evidence

from ladon.proofir_v3 import detached_content_id, validate_envelope_batch
from ladon.result_manifest_io import ResultManifestError
from ladon.result_resolution import _catalog


def _environment_extra_check():
    artifacts, _, _ = semantic_evidence("population-reuse")
    environment, check = artifacts
    extra = claim_artifact()
    extra["environmentRef"] = environment["environmentRef"]
    extra["artifactId"] = detached_content_id(extra)
    check["payload"]["inputs"]["artifactRefs"].append(extra["artifactId"])
    check["artifactId"] = detached_content_id(check)
    return [environment, extra, check]


def test_full_population_closes_environment_extra_and_check_before_subset():
    environment, extra, check = _environment_extra_check()
    # The complete owner population is valid. The exact environment/check subset is
    # not closed because the check also names the third artifact.
    validated = validate_envelope_batch([environment, extra, check])
    assert len(validated) == 3
    try:
        _catalog([environment, check])
    except ResultManifestError as error:
        assert "invalid supplied canonical evidence" in str(error)
    else:
        raise AssertionError("selected [environment, check] subset lost required closure")


def test_raw_stored_receipt_owner_cannot_bypass_missing_extra_artifact():
    from ladon.evidence_receipt_readers import stored_check_receipt

    environment, extra, check = _environment_extra_check()
    validate_envelope_batch([environment, extra, check])
    try:
        stored_check_receipt(check, environment_artifacts=[environment])
    except ValueError:
        pass
    else:
        raise AssertionError("raw receipt owner accepted a check with a missing input artifact")
