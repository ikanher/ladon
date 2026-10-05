from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ladon import authority_safe_gate
from ladon.authority_safe_gate import CHILD_EXIT_CLASSES, evaluate_authority_safe_gate

ROOT = Path(__file__).parents[1]


def _receipt(exit_class: str, candidate: str = "sha256:" + "a" * 64) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema": "ladon-child-exit-receipt-v1",
        "exitClass": CHILD_EXIT_CLASSES[exit_class],
        "status": "passed",
        "candidateIdentity": candidate,
        "analysisCompleteness": "complete",
        "omissions": [],
        "commands": [
            {
                "command": "uv run pytest -q",
                "status": "passed",
                "evidenceDigest": "sha256:" + "b" * 64,
            }
        ],
        "producerIdentity": "ladon-tests/v1",
        "sourceTreeIdentity": "sha256:" + "c" * 64,
        "environmentRef": "sha256:" + "d" * 64,
        "commandVector": ["python", "-m", "pytest"],
        "workingDirectory": "/repo",
        "resultArtifactRefs": ["sha256:" + "e" * 64],
        "logArtifactRefs": ["sha256:" + "f" * 64],
    }
    return _resign(receipt)


def _resign(receipt: dict[str, object]) -> dict[str, object]:
    receipt.pop("receiptIdentity", None)
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    receipt["receiptIdentity"] = "sha256:" + hashlib.sha256(encoded).hexdigest()
    return receipt


def _inventories() -> dict[str, dict[str, str]]:
    """Minimal inventories isolate conjunction tests from bundle validation."""
    return {role: {"exitClass": exit_class} for role, exit_class in CHILD_EXIT_CLASSES.items()}


@pytest.fixture
def verified_bundles(monkeypatch: pytest.MonkeyPatch) -> list[tuple]:
    calls: list[tuple] = []

    def validate(receipt, *, bundle_root, inventory):
        calls.append((receipt, bundle_root, inventory))

    monkeypatch.setattr(authority_safe_gate, "validate_child_bundle", validate)
    return calls


def test_authority_safe_gate_requires_matching_verified_children(
    tmp_path: Path, verified_bundles: list[tuple],
) -> None:
    correctness, authority = _receipt("correctness"), _receipt("authority")
    inventories = _inventories()
    result = evaluate_authority_safe_gate(
        correctness, authority, evidence_root=tmp_path, inventories=inventories,
    )
    assert result["status"] == "passed"
    assert verified_bundles == [
        (correctness, tmp_path, inventories["correctness"]),
        (authority, tmp_path, inventories["authority"]),
    ]
    assert result["children"] == {
        "correctness": correctness["receiptIdentity"], "authority": authority["receiptIdentity"],
    }


@pytest.mark.parametrize("missing", ["both", "root", "inventories"])
def test_authority_safe_gate_rejects_metadata_only_receipts(
    tmp_path: Path, verified_bundles: list[tuple], missing: str,
) -> None:
    result = evaluate_authority_safe_gate(
        _receipt("correctness"), _receipt("authority"),
        evidence_root=tmp_path if missing == "inventories" else None,
        inventories=_inventories() if missing == "root" else None,
    )
    assert result["status"] == "failed"
    assert "metadata is insufficient" in result["reason"]
    assert verified_bundles == []


@pytest.mark.parametrize(("field", "value", "reason"), [
    ("schema", "unknown", "unsupported schema"),
    ("exitClass", "authority", "legacy shorthand"),
    ("exitClass", CHILD_EXIT_CLASSES["correctness"], "wrong exit class"),
    ("status", "failed", "did not pass"),
    ("candidateIdentity", "not-a-digest", "exact candidate digest"),
    ("candidateIdentity", "sha256:" + "0" * 64, "same candidate"),
    ("analysisCompleteness", "partial", "partial"),
    ("omissions", ["missing suite"], "partial"),
    ("commands", [], "invalid command evidence"),
    ("sourceTreeIdentity", "sha256:" + "0" * 64, "same release scope"),
    ("environmentRef", "sha256:" + "0" * 64, "same release scope"),
    ("producerIdentity", "another-producer", "same release scope"),
    ("workingDirectory", "/another-candidate", "same release scope"),
    ("commandVector", [], "command vector"),
    ("resultArtifactRefs", [], "result artifacts"),
    ("logArtifactRefs", [], "logs"),
])
def test_authority_safe_gate_rejects_invalid_child_metadata_before_bundle_reads(
    tmp_path: Path, verified_bundles: list[tuple], field: str, value: object, reason: str,
) -> None:
    authority = _receipt("authority")
    authority[field] = value
    result = evaluate_authority_safe_gate(
        _receipt("correctness"), _resign(authority),
        evidence_root=tmp_path, inventories=_inventories(),
    )
    assert result["status"] == "failed"
    assert reason in result["reason"]
    assert verified_bundles == []


def test_authority_safe_gate_rejects_tampered_receipt(
    tmp_path: Path, verified_bundles: list[tuple],
) -> None:
    correctness = _receipt("correctness")
    correctness["commandVector"] = ["a different command"]
    result = evaluate_authority_safe_gate(
        correctness, _receipt("authority"), evidence_root=tmp_path, inventories=_inventories(),
    )
    assert result["status"] == "failed"
    assert "identity is invalid" in result["reason"]
    assert verified_bundles == []


@pytest.mark.parametrize("role", ["correctness", "authority"])
def test_authority_safe_gate_requires_each_role_inventory(
    tmp_path: Path, verified_bundles: list[tuple], role: str,
) -> None:
    inventories = _inventories()
    inventories.pop(role)
    result = evaluate_authority_safe_gate(
        _receipt("correctness"), _receipt("authority"),
        evidence_root=tmp_path, inventories=inventories,
    )
    assert result["status"] == "failed"
    assert result["reason"] == f"{role} acceptance inventory is required"
    assert len(verified_bundles) == int(role == "authority")


def test_authority_safe_gate_rejects_an_inventory_for_another_exit(
    tmp_path: Path, verified_bundles: list[tuple],
) -> None:
    inventories = _inventories()
    inventories["correctness"] = inventories["authority"]
    result = evaluate_authority_safe_gate(
        _receipt("correctness"), _receipt("authority"),
        evidence_root=tmp_path, inventories=inventories,
    )
    assert result["status"] == "failed"
    assert result["reason"] == "correctness acceptance inventory has the wrong exit class"
    assert verified_bundles == []


@pytest.mark.parametrize("role", ["correctness", "authority"])
def test_either_bundle_failure_blocks_the_integration_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: str,
) -> None:
    def validate(receipt, *, bundle_root, inventory):
        assert bundle_root == tmp_path
        if inventory["exitClass"] == CHILD_EXIT_CLASSES[role]:
            raise ValueError("required evidence bytes are missing")

    monkeypatch.setattr(authority_safe_gate, "validate_child_bundle", validate)
    result = evaluate_authority_safe_gate(
        _receipt("correctness"), _receipt("authority"),
        evidence_root=tmp_path, inventories=_inventories(),
    )
    assert result["status"] == "failed"
    assert result["reason"] == f"{role} child evidence is invalid: required evidence bytes are missing"
    assert "children" not in result


def test_authority_alone_cannot_establish_integration(
    tmp_path: Path, verified_bundles: list[tuple],
) -> None:
    result = evaluate_authority_safe_gate(
        {}, _receipt("authority"), evidence_root=tmp_path, inventories=_inventories(),
    )
    assert result["status"] == "failed"
    assert verified_bundles == []


def test_empty_evidence_directory_cannot_qualify_synthetic_metadata(tmp_path: Path) -> None:
    result = evaluate_authority_safe_gate(
        _receipt("correctness"), _receipt("authority"),
        evidence_root=tmp_path, inventories=_inventories(),
    )
    assert result["status"] == "failed"
    assert "child evidence is invalid" in result["reason"]


def test_child_exit_classes_match_the_normative_dependency_ledger() -> None:
    path = ROOT / "openspec/changes/ladon-authority-safe-verified-discovery-umbrella"
    ledger = json.loads((path / "children/dependency-ledger.json").read_text())
    exits = {row["change"]: row["exitClass"] for row in ledger["children"]}
    assert CHILD_EXIT_CLASSES == {
        "correctness": exits["ladon-proof-discovery-correctness-repairs"],
        "authority": exits["ladon-execution-authority-integrity"],
    }


def test_gate_cli_requires_evidence_and_independent_inventories() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/authority_safe_gate.py"),
         "--correctness", "correctness.json", "--authority", "authority.json"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert "--evidence-root" in result.stderr
    assert "--correctness-inventory" in result.stderr
    assert "--authority-inventory" in result.stderr
