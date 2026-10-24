"""Statement capture survives an actually unavailable selected proof body."""

from pathlib import Path

from ladon.proof_contract_formal import expand_formal_snapshot, produce_formal_snapshot


def test_real_axiom_statement_survives_body_expansion_without_a_proof():
    root = Path(__file__).parent / "fixtures/proof_contract_production"
    frozen = produce_formal_snapshot(root, "ProducerCases.lean", "ProducerCases",
                                     "ProducerCases.supported_base")
    expanded = expand_formal_snapshot(frozen, root, application="ProducerCases.f",
                                      obligation_id="provider:missing-body")
    assert frozen["status"] == "extracted"
    assert frozen["contract"]["features"]["regularity"]["offset"] == 0
    assert expanded["statementSnapshot"] == frozen
    assert expanded["slice"]["status"] == "unavailable"
    assert expanded["slice"]["complete"] is False
    assert expanded["slice"]["frontiers"]
    assert expanded["coverage"]["providers"] == "incomplete"
    assert expanded["request"]["obligationId"] == "provider:missing-body"
