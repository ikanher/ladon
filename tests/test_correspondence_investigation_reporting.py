"""Checked transport and attributed application differences stay distinct in reports."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from ladon.correspondence_check import check_correspondence, prepare_correspondence
from ladon.correspondence_evidence import completion_artifacts
from ladon.investigation_correspondence import (
    attach_bundle,
    challenge_packet_v3,
    ingest_response,
    initialize_v3,
)
from ladon.investigation_observations import (
    challenge_observation,
    ingest_observation_response,
    record_observation,
)
from ladon.investigation_reporting import aggregate_report
from ladon.proof_slice import extract_proof_slice
from ladon.proofir_correspondence import (
    bind_native_interpretation,
    correspondence_artifacts,
    interpretation_artifacts,
)
from ladon.proofir_v3 import validate_envelope_batch

NOW = datetime(2026, 10, 17, 19, 1, tzinfo=UTC)


def _checked_fin_representation_bundle(root):
    source = root / "representation.txt"
    representation = {"tag": "app", "symbol": "val",
                       "args": [{"tag": "var", "id": "i"}]}
    record = {
        "id": "bounded-representation",
        "source": {
            "path": source.name,
            "startLine": 1,
            "endLine": 1,
            "quote": source.read_text().strip(),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        },
        "formula": {
            "tag": "forall",
            "binder": {"id": "i", "name": "index", "domain": "Fin 5"},
            "body": {
                "tag": "lt",
                "left": representation,
                "right": {"tag": "const", "name": "5"},
            },
        },
        "symbols": {"val": {"leanName": "Fin.val", "leanType": "Fin 5 → Nat"}},
    }
    proof_slice = extract_proof_slice(
        root, "Representation.lean", "Representation", "Representation.selected",
        "Representation.bridge", scoped=True,
    )
    assert proof_slice["complete"] is True
    plan = prepare_correspondence(record, proof_slice, {"n": {"symbol": "val", "args": ["i"]}})
    artifacts = list(interpretation_artifacts(record, proof_slice["environment"], source_root=root))
    plan = bind_native_interpretation(plan, artifacts, source_root=root)
    artifacts.append(correspondence_artifacts(plan))
    terms = [
        {"obligation": "interpretation", "term": "by intro h; exact h", "mode": "prove"},
        {"obligation": "object-map", "term": "by intro i; trivial", "mode": "prove"},
        {"obligation": "premise-1", "term": "by intro i n h; exact i.isLt", "mode": "prove"},
        {"obligation": "conclusion", "term": "by intro i n h hformal; exact hformal", "mode": "prove"},
    ]
    checked = check_correspondence(
        plan, terms, root, source_root=root, native_artifacts=artifacts,
    )
    assert checked["parentSupport"] == "supported-for-attributed-interpretation"
    assert all(row["status"] == "supported" for row in checked["checks"])
    checks, refs = completion_artifacts(plan, checked)
    checked["checkRunRefs"] = refs
    checked.update(
        schema="ladon-correspondence-check-v1",
        checkRunRefs=refs,
        artifacts=[*artifacts, *checks, correspondence_artifacts(plan, checked)],
        plan=plan,
    )
    validate_envelope_batch(checked["artifacts"])
    return checked


def _reviewed_transport_control(fixture_root, source, checked_bundle):
    plan = attach_bundle(initialize_v3(source, fixture_root, now=NOW), checked_bundle, fixture_root)
    subject = plan["correspondenceBundles"][0]["subject"]
    packet = challenge_packet_v3(plan, subject, fixture_root)
    aligned_different_method = {
        "reviewer": "reviewer-method-control",
        "subject": subject,
        "challengeDigest": packet["challengeDigest"],
        "classification": "aligned",
        "method": "different",
        "sourceFidelity": "faithful",
        "evidence": "The bounded Fin index is transported through Fin.val; the selected route differs.",
    }
    return ingest_response(plan, packet, aligned_different_method, fixture_root), subject


def _reviewed_application_difference(control, fixture_root, source):
    application_record = {
        "schema": "ladon-investigation-observation-v1",
        "id": "application-difference-without-separation",
        "source": {
            **control["scope"],
            "quote": source.read_text().strip(),
        },
        "author": "source-reader",
        "assertion": "Every bounded index has a natural representation below five.",
        "comparison": "The application-level comparison differs, but no accepted semantic separator is attached.",
        "evidence": "Attributed application difference only; no check receipt is associated with this finding.",
        "formalSources": [],
        "dependencies": "The original stated assumptions only.",
    }
    application = record_observation(control, application_record, fixture_root)
    app_subject = application["observations"][0]["observationId"]
    app_packet = challenge_observation(application, app_subject, fixture_root)
    app_response = {
        "reviewer": "reviewer-application",
        "subject": app_subject,
        "challengeDigest": app_packet["challengeDigest"],
        "classification": "mismatch",
        "method": "different",
        "sourceFidelity": "faithful",
        "evidence": "Attributed application discrepancy; the separate checked theorem is unrelated.",
    }
    return ingest_observation_response(application, app_packet, app_response, fixture_root)


def _assert_method_control(report, subject):
    checked_branch = next(
        branch for branch in report["branches"]
        if branch.get("formalCorrespondence") == "recorded-links-complete-unreplayed"
    )
    control_finding = next(
        finding for finding in checked_branch["findings"] if finding.get("subject") == subject
    )
    assert control_finding["statementRelation"] == "aligned"
    assert control_finding["methodRelation"] == "different"


def _assert_application_difference_unresolved(report):
    application_finding = next(
        finding for finding in report["findings"] if finding.get("kind") == "observation"
    )
    assert application_finding["statementRelation"] == "mismatch"
    assert application_finding["formalSupport"] == "not-established"
    assert application_finding["mathematicalFalsity"] == "not-established"
    assert report["mathematicalFalsity"] == "not-established"
    assert report["wholePaperCertified"] is False
    assert application_finding["formalSupport"] != "recorded-links-only"


def _assert_report_preserves_separate_evidence(report, subject):
    _assert_method_control(report, subject)
    _assert_application_difference_unresolved(report)


def test_checked_fin_transport_and_unchecked_application_difference_report_separately():
    fixture_root = Path(__file__).parent / "fixtures/correspondence_m1"
    source = fixture_root / "representation.txt"
    checked_bundle = _checked_fin_representation_bundle(fixture_root)

    # The exact membership-erasure non-equivalence in
    # tests/test_proof_contract_transport.py is a separate checked control; it
    # is deliberately not attached here and cannot prove this mismatch.
    control, subject = _reviewed_transport_control(fixture_root, source, checked_bundle)
    application = _reviewed_application_difference(control, fixture_root, source)
    report = aggregate_report([control, application], fixture_root, now=NOW)
    _assert_report_preserves_separate_evidence(report, subject)

    # Input custody contains the actual checker receipts, while the report is
    # only a read-only projection and makes no semantic join to the application row.
    assert checked_bundle["checkRunRefs"]
    assert checked_bundle["artifacts"]
