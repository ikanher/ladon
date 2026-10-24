"""Actual formal snapshots retain separate, immutable extraction coverage."""

from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent / "fixtures/proof_contract_production"


@pytest.fixture(scope="module")
def formal_snapshot():
    from ladon.proof_contract_formal import produce_formal_snapshot

    return produce_formal_snapshot(ROOT, "ProducerCases.lean", "ProducerCases",
                                   "ProducerCases.supported_base")


def test_formal_snapshot_has_native_source_binding_and_no_fidelity_authority(formal_snapshot):
    from ladon.proofir_v3 import validate_envelope_batch

    assert formal_snapshot["status"] == "extracted"
    assert formal_snapshot["snapshotId"].startswith("sha256:")
    assert formal_snapshot["fidelity"] == "attributed-unreviewed"
    validate_envelope_batch(formal_snapshot["artifacts"])
    contract = formal_snapshot["artifacts"][-1]
    assert contract["payload"]["provenance"]["mode"] == "extracted"
    assert contract["payload"]["provenance"]["checkerAuthority"] == "none"


def test_inspection_rejects_tampering_and_environment_drift(formal_snapshot, monkeypatch):
    import ladon.proof_contract_formal as formal

    assert formal.verify_formal_snapshot(formal_snapshot, ROOT) == formal_snapshot
    altered = deepcopy(formal_snapshot)
    altered["contract"]["features"]["regularity"]["offset"] = 42
    with pytest.raises(ValueError, match="altered|identity"):
        formal.verify_formal_snapshot(altered, ROOT)
    monkeypatch.setattr(formal, "_environment", lambda _root: "sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="environment|stale"):
        formal.verify_formal_snapshot(formal_snapshot, ROOT)


def test_blocked_named_body_expansion_retains_statement_snapshot(formal_snapshot, monkeypatch):
    import ladon.proof_contract_formal as formal

    first = deepcopy(formal_snapshot)

    def blocked_slice(*_args, **_kwargs):
        return {
            "status": "unavailable", "complete": False, "nodes": [],
            "frontiers": [{"reason": "deliberately blocked body"}],
        }

    monkeypatch.setattr(formal, "_extract_slice", blocked_slice)
    result = formal.expand_formal_snapshot(
        formal_snapshot, ROOT, application="ProducerCases.f", obligation_id="premise:1",
    )
    assert result["statementSnapshot"] == first
    assert result["statementSnapshot"]["coverage"]["statementFeatures"] == "complete"
    assert result["coverage"]["providers"] == "incomplete"
    assert result["request"]["obligationId"] == "premise:1"
    assert formal_snapshot == first


def test_rehashed_authored_features_cannot_replace_observed_statement(formal_snapshot):
    import ladon.proof_contract_formal as formal
    from ladon.proof_contract_source import snapshot_identity

    altered = deepcopy(formal_snapshot)
    altered["contract"]["features"]["regularity"]["offset"] = 42
    altered["artifacts"] = formal._artifacts(altered, ROOT)
    altered["snapshotId"] = snapshot_identity(altered)
    with pytest.raises(ValueError, match="observation|summary"):
        formal.verify_formal_snapshot(altered, ROOT)
