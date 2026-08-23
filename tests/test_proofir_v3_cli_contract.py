from __future__ import annotations

import json
from pathlib import Path

from ladon.proof_search_cli import build_proof_search_parser
from ladon.theorem_cli import build_theorem_parser


def test_ordinary_cli_contract_is_machine_readable_and_native_only() -> None:
    contract = json.loads(
        Path("docs/proofir-v3-cli-contract.json").read_text(encoding="utf-8")
    )
    assert contract["interface"] == "ordinary-ladon-cli"
    assert set(contract["exitClasses"]) == {
        "success",
        "operational",
        "invocation",
        "policy",
        "interrupted",
    }
    assert set(contract["commands"]) == {
        "discovery",
        "validation",
        "canonicalization",
        "inspection",
        "indexing",
        "dossier",
        "derivationSlice",
        "alternatives",
        "coverage",
        "diagnostics",
        "explicitCandidateCheck",
        "fullCandidateAudit",
        "semanticArtifactExpansion",
        "semanticEnvironmentExpansion",
        "semanticCheckExpansion",
    }
    assert all(
        command.startswith("ladon ") for command in contract["commands"].values()
    )
    assert "convert" not in json.dumps(contract)
    assert contract["contract"] == "proofir-v3-native-only"
    assert contract["inputPolicy"]["accepted"] == "native ProofIR v3 artifacts only"
    assert "regenerate" in contract["inputPolicy"]["regeneration"]


def test_release_operations_are_exposed_by_existing_parsers() -> None:
    proof_search = build_proof_search_parser()
    assert set(proof_search._subparsers._group_actions[0].choices) >= {
        "index",
        "evidence",
        "search",
        "check",
    }
    theorem = build_theorem_parser()
    assert set(theorem._subparsers._group_actions[0].choices) >= {"lineage"}
