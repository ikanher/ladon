"""Focused source-fidelity boundary probe using the existing review API."""

import copy
import json

from test_proof_contract_source import produce, prose_inputs

from ladon.investigation_correspondence import initialize_v3
from ladon.investigation_observations import (
    challenge_observation,
    ingest_observation_response,
    observation_finding,
    record_observation,
)
from ladon.proof_contract_source import observation_from_prose_snapshot


def _assert_unreviewed_snapshot(snapshot):
    contract_artifact = next(
        row for row in snapshot["artifacts"] if row["artifactKind"] == "proofir.contract"
    )
    assert snapshot["channel"] == "prose"
    assert snapshot["fidelity"] == "attributed-unreviewed"
    assert contract_artifact["payload"]["provenance"]["fidelity"] == "attributed-unreviewed"
    assert contract_artifact["payload"]["provenance"]["checkerAuthority"] == "none"


def _assert_blinded_challenge(packet, snapshot, assertion):
    assert packet["sourceQuote"] == snapshot["source"]["quote"]
    assert packet["assertion"] == assertion
    assert "comparison" not in packet and "evidence" not in packet
    assert packet["authority"] == "Compare the source and argument; no native proof is supplied."


def _assert_review_does_not_promote_authority(finding, snapshot, snapshot_before_review):
    assert finding["sourceFidelity"] == "faithful"
    assert finding["formalSupport"] == "not-established"
    assert finding["mathematicalFalsity"] == "not-established"
    assert snapshot == snapshot_before_review
    assert snapshot["fidelity"] == "attributed-unreviewed"


def test_prose_snapshot_requires_attributed_review_separate_from_elaboration(tmp_path):
    snapshot = produce(tmp_path, *prose_inputs(tmp_path))
    snapshot_before_review = copy.deepcopy(snapshot)
    _assert_unreviewed_snapshot(snapshot)

    plan = initialize_v3(tmp_path / "claim.txt", tmp_path)
    assertion = json.dumps(
        {"interpretation": snapshot["interpretation"],
         "contract": snapshot["contract"], "featureOrigins": snapshot["featureOrigins"]},
        sort_keys=True, separators=(",", ":"),
    )
    record = observation_from_prose_snapshot(snapshot, tmp_path)
    observed = record_observation(plan, record, tmp_path)
    subject = observed["observations"][0]["observationId"]
    packet = challenge_observation(observed, subject, tmp_path)
    _assert_blinded_challenge(packet, snapshot, assertion)

    response = {
        "reviewer": "independent-source-reader",
        "subject": subject,
        "challengeDigest": packet["challengeDigest"],
        "classification": "unresolved",
        "method": "unresolved",
        "sourceFidelity": "faithful",
        "evidence": "The interpretation preserves the quoted quantifiers and dependency claim.",
    }
    reviewed = ingest_observation_response(observed, packet, response, tmp_path)
    finding = observation_finding(reviewed["observations"][0])
    _assert_review_does_not_promote_authority(finding, snapshot, snapshot_before_review)
