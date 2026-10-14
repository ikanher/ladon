"""Structured review is source-bound bookkeeping with explicit formal gaps."""

import copy
import hashlib

import pytest

from ladon.correspondence_interpretation import lower_formula
from ladon.proofir_correspondence import interpretation_artifacts


def input_bundle(tmp_path):
    source = tmp_path / "claim.txt"
    source.write_text("Every positive natural is positive.\n")
    record = {"id": "claim", "source": {"path": source.name, "startLine": 1, "endLine": 1,
              "quote": source.read_text().strip(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
              "formula": {"tag": "const", "name": "True"}, "symbols": {}}
    bundle = {"schema": "ladon-interpretation-v1", "record": record,
              "loweredFormula": lower_formula(record["formula"], {}),
              "fidelity": "attributed-unreviewed", "residuals": [],
              "artifacts": interpretation_artifacts(record, "sha256:" + "0" * 64, source_root=tmp_path)}
    return source, bundle


def response(packet, classification="aligned"):
    return {"reviewer": "independent-label", "subject": packet["subject"],
            "challengeDigest": packet["challengeDigest"], "classification": classification,
            "method": "different", "sourceFidelity": "faithful", "evidence": "Exact source comparison."}


def test_no_counterpart_preserves_first_response_and_separate_completion(tmp_path):
    from ladon.investigation_correspondence import (
        assess_v3,
        attach_bundle,
        challenge_packet_v3,
        ingest_response,
        initialize_v3,
    )
    source, bundle = input_bundle(tmp_path)
    plan = initialize_v3(source, tmp_path)
    plan["units"][0].update(inventory="done", note="Attributed complete local inventory.")
    attached = attach_bundle(plan, bundle, tmp_path)
    subject = attached["correspondenceBundles"][0]["subject"]
    assert subject == next(a["artifactId"] for a in bundle["artifacts"]
                           if a["artifactKind"] == "proofir.interpretation")
    packet = challenge_packet_v3(attached, subject, tmp_path)
    assert "fidelity" not in packet["observedContext"]
    assert "checks" not in packet and "repairs" not in packet
    first = ingest_response(attached, packet, response(packet, "mismatch"), tmp_path)
    original = copy.deepcopy(first["responses"][0])
    corrected = ingest_response(first, packet, response(packet), tmp_path, first=original["responseId"])
    assert corrected["responses"][0] == original
    assert corrected["reconciliations"][0]["firstResponseId"] == original["responseId"]
    status = assess_v3(corrected, tmp_path)
    assert status["mathematicalReview"] == "complete-attributed"
    assert status["formalCorrespondence"] == "incomplete-no-counterpart"
    assert status["mayFinalize"] is False
    assert status["bundles"][0]["methodReview"] == "different-attributed"


def test_mutated_first_response_cannot_inherit_current_review(tmp_path):
    from ladon.investigation_correspondence import (
        assess_v3,
        attach_bundle,
        challenge_packet_v3,
        ingest_response,
        initialize_v3,
    )
    source, bundle = input_bundle(tmp_path)
    plan = attach_bundle(initialize_v3(source, tmp_path), bundle, tmp_path)
    packet = challenge_packet_v3(plan, plan["correspondenceBundles"][0]["subject"], tmp_path)
    reviewed = ingest_response(plan, packet, response(packet), tmp_path)
    reviewed["responses"][0]["classification"] = "mismatch"
    with pytest.raises(ValueError, match="response.*identity|altered.*response"):
        assess_v3(reviewed, tmp_path)


def test_altered_challenge_and_outside_scope_cannot_be_ingested(tmp_path):
    from ladon.investigation_correspondence import (
        attach_bundle,
        challenge_packet_v3,
        ingest_response,
        initialize_v3,
    )
    source, bundle = input_bundle(tmp_path)
    plan = attach_bundle(initialize_v3(source, tmp_path), bundle, tmp_path)
    packet = challenge_packet_v3(plan, plan["correspondenceBundles"][0]["subject"], tmp_path)
    wrong = response(packet)
    wrong["challengeDigest"] = "0" * 64
    with pytest.raises(ValueError, match="binding|challenge"):
        ingest_response(plan, packet, wrong, tmp_path)
    other = tmp_path / "other.txt"
    other.write_text("Other source.\n")
    with pytest.raises(ValueError, match="scope"):
        attach_bundle(initialize_v3(other, tmp_path), bundle, tmp_path)
