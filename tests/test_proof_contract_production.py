"""Independent actual-source acceptance tests for the formal producer.

The file intentionally imports the proposed producer inside the call helper,
so a missing implementation fails each case clearly instead of preventing test
collection.  The producer invocation is the semantic path: expected feature
records are derived from the Lean declarations in ProducerCases.lean.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent / "fixtures/proof_contract_production"


def produce(declaration: str) -> dict:
    module = importlib.import_module("ladon.proof_contract_production")
    return module.produce_formal_contract(
        ROOT,
        "ProducerCases.lean",
        "ProducerCases",
        f"ProducerCases.{declaration}",
        timeout_seconds=60,
        max_rss_bytes=12 * 1024**3,
    )


def extracted_contract(declaration: str) -> tuple[dict, dict]:
    observation = produce(declaration)
    assert observation["schema"] == "ladon-contract-production-v1"
    assert observation["channel"] == "formal"
    assert observation["status"] == "extracted"
    contract = observation["contract"]
    assert isinstance(contract, dict)
    from ladon.proof_contracts import validate_contract

    checked = validate_contract(contract)
    assert observation["coverage"]["statementFeatures"] == "complete"
    assert observation["coverage"]["providers"] == "not-extracted"
    assert observation["coverage"]["proofBody"] == "not-extracted"
    assert observation["fidelity"] == "attributed-unreviewed"
    assert set(observation["featureOrigins"]) == {
        "regularity", "constantDependencies", "witnessDependencies"
    }
    return observation, checked


def _offset(contract: dict) -> int:
    return contract["features"]["regularity"]["offset"]


def _witness(contract: dict) -> dict:
    rows = contract["features"]["witnessDependencies"]
    assert len(rows) == 1
    return rows[0]


def _assert_contract_features(contract: dict) -> None:
    assert [row["quantifier"] for row in contract["telescope"]] == ["forall", "forall"]
    assert _offset(contract) == 0


def _assert_exact_source(observation: dict) -> None:
    assert observation["source"]["path"] == "ProducerCases.lean"
    assert observation["selection"]["module"] == "ProducerCases"
    assert observation["selection"]["declaration"] == "ProducerCases.supported_base"
    expected_hash = hashlib.sha256((ROOT / "ProducerCases.lean").read_bytes()).hexdigest()
    assert observation["source"]["sha256"] == expected_hash


def _assert_capture_receipts(observation: dict) -> None:
    assert observation["environment"]
    assert observation["helper"]["sha256"]
    assert observation["processReceipts"]
    assert observation["observation"]
    assert observation.get("residuals") == []


def test_core_statement_is_extracted_from_the_exact_lean_declaration() -> None:
    observation, contract = extracted_contract("supported_base")
    _assert_contract_features(contract)
    _assert_exact_source(observation)
    _assert_capture_receipts(observation)


def test_alpha_renaming_preserves_the_scoped_features() -> None:
    _, base = extracted_contract("supported_base")
    _, renamed = extracted_contract("supported_alpha")

    assert [row["quantifier"] for row in renamed["telescope"]] == ["forall", "forall"]
    assert [row["typeId"] for row in renamed["telescope"]] == [
        row["typeId"] for row in base["telescope"]
    ]
    assert renamed["context"] == base["context"]
    assert _offset(renamed) == _offset(base)
    assert renamed["features"]["regularity"] == base["features"]["regularity"]
    assert renamed["features"]["constantDependencies"]["state"] == \
        base["features"]["constantDependencies"]["state"]


@pytest.mark.parametrize(
    ("declaration", "expected_offset"),
    [("supported_let_alias", 2), ("supported_scale_input", 3)],
)
def test_safe_let_reduction_and_explicit_offsets(
    declaration: str, expected_offset: int
) -> None:
    _, contract = extracted_contract(declaration)
    assert _offset(contract) == expected_offset


@pytest.mark.parametrize(
    ("declaration", "expected_permissions"),
    [
        ("supported_witness_after_scale", 1),
        ("supported_witness_before_scale", 0),
    ],
)
def test_existential_order_controls_only_permitted_witness_dependencies(
    declaration: str, expected_permissions: int
) -> None:
    _, contract = extracted_contract(declaration)
    telescope = contract["telescope"]
    assert [row["quantifier"] for row in telescope] == (
        ["forall", "exists", "forall"]
        if declaration.endswith("after_scale")
        else ["exists", "forall", "forall"]
    )
    witness = _witness(contract)
    assert witness["state"] == "known"
    assert len(witness["allowedBinderIds"]) == expected_permissions
    assert all(
        next(row for row in telescope if row["binderId"] == binder)["quantifier"]
        == "forall"
        for binder in witness["allowedBinderIds"]
    )
    constant = contract["features"]["constantDependencies"]
    assert constant.get("binderId") == witness["binderId"]
    if constant["state"] == "known":
        assert set(constant["allowedBinderIds"]) == set(witness["allowedBinderIds"])


@pytest.mark.parametrize(
    ("declaration", "residual_hint"),
    [
        ("unsupported_dependent_domain", "domain"),
        ("unsupported_membership", "membership"),
    ],
)
def test_unsupported_domains_remain_explicit_and_never_become_complete(
    declaration: str, residual_hint: str
) -> None:
    observation = produce(declaration)

    assert observation["schema"] == "ladon-contract-production-v1"
    assert observation["channel"] == "formal"
    assert observation["status"] in {"partial", "unsupported"}
    residuals = observation["residuals"]
    assert residuals
    assert all({"code", "message", "feature"} == set(row) for row in residuals)
    assert residual_hint.lower() in str(residuals).lower()
    assert observation["coverage"]["statementFeatures"] in {"partial", "unsupported"}
    if observation["contract"] is not None:
        assert observation["status"] == "partial"


def test_api_has_no_caller_supplied_contract_or_feature_override() -> None:
    module = importlib.import_module("ladon.proof_contract_production")
    parameters = inspect.signature(module.produce_formal_contract).parameters

    assert "contract" not in parameters
    assert "features" not in parameters
    with pytest.raises(TypeError):
        inspect.signature(module.produce_formal_contract).bind(
            ROOT,
            "ProducerCases.lean",
            "ProducerCases",
            "ProducerCases.supported_base",
            features={"regularity": {"offset": 0}},
        )

