"""Validate same-candidate child coverage and complete integration gate records.

Inputs are local content-addressed evidence and independently selected inventories.
Validation rejects incomplete or inconsistent records. It does not authenticate
producers, establish OS isolation or grant public distribution authority.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.authority_safe_gate import evaluate_authority_safe_gate
from ladon.child_acceptance import _json_object, _read_evidence, validate_child_bundle

SCOPE_FIELDS = ('candidateIdentity', 'sourceTreeIdentity', 'wheelDigest',
                'workingDirectory', 'producerIdentity', 'environmentRef')
GATE_IDS = frozenset({'clean-candidate', 'installed-distribution', 'required-lean',
                      'required-benchmarks', 'feature-matrix', 'openspec',
                      'backlog-freeze', 'openspec-hygiene', 'diff-hygiene', 'lock', 'compile'})
EXIT_CLASS = 'same-candidate-conjunctive-authority-safe-integration'


def evaluate_integration_gate(
    integration: Mapping[str, Any], correctness: Mapping[str, Any], authority: Mapping[str, Any],
    *, bundle_root: Path, inventories: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Return a candidate-specific qualification or raise ValueError on any gap."""
    conjunction = evaluate_authority_safe_gate(
        correctness, authority, evidence_root=bundle_root, inventories=inventories,
    )
    if conjunction['status'] != 'passed':
        raise ValueError('both independently qualified child receipts are required')
    inventory = inventories['integration']
    if integration.get('exitClass') != EXIT_CLASS or inventory.get('exitClass') != EXIT_CLASS:
        raise ValueError('integration exit class differs from the selected contract')
    validate_child_bundle(integration, bundle_root=bundle_root, inventory=inventory)
    for child in (correctness, authority):
        if any(integration.get(field) != child.get(field) for field in SCOPE_FIELDS):
            raise ValueError('integration and child qualification scopes differ')
    # Reuse the child owner's bounded, duplicate-key-safe evidence reader.
    evidence = _read_evidence(integration['evidenceFiles'], bundle_root)
    candidate = _json_object(evidence[integration['candidateArtifactRef']])
    if integration.get('candidateCommit') != candidate.get('candidateCommit'):
        raise ValueError('integration commit differs from the candidate artifact')
    _validate_prerequisites(inventory, integration, evidence)
    return {
        'schema': 'ladon-integration-qualification-v1', 'status': 'passed',
        'exitClass': EXIT_CLASS, 'candidateCommit': integration['candidateCommit'],
        **{field: integration[field] for field in SCOPE_FIELDS},
        'children': conjunction['children'], 'integrationReceipt': integration['receiptIdentity'],
        'prerequisites': sorted(GATE_IDS), 'omissions': [],
        'limitations': [
            'Local integrity and recorded coverage do not authenticate the evidence producer.',
            'Trusted-repository posture is not operating-system isolation.',
            'Discovery vertical-slice and external capability readiness exits remain separate.',
            'Public distribution authority is not granted.',
        ],
    }


def _validate_prerequisites(inventory, receipt, evidence) -> None:
    try:
        _validate_prerequisite_records(inventory, receipt, evidence)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError('integration prerequisite records are incomplete or invalid') from error


def _validate_prerequisite_records(inventory, receipt, evidence) -> None:
    _validate_output(receipt)
    gates = inventory['integrationPrerequisites']
    _validate_gate_names([gate['gateId'] for gate in gates])
    rows = [_json_object(evidence[ref]) for ref in receipt['integrationPrerequisiteArtifactRefs']]
    recorded = [row['gateId'] for row in rows]
    _validate_gate_names(recorded)
    expected = {gate['gateId']: gate for gate in gates}
    for row in rows:
        _validate_record(row, expected[row['gateId']], receipt, evidence)


def _validate_output(receipt) -> None:
    output = Path(receipt['outputDirectory'])
    candidate = Path(receipt['workingDirectory'])
    if not output.is_absolute() or output.resolve().is_relative_to(candidate.resolve()):
        raise ValueError('integration logs must be outside the candidate')


def _validate_gate_names(names) -> None:
    if len(names) != len(GATE_IDS) or set(names) != GATE_IDS:
        raise ValueError('integration prerequisites are incomplete, duplicated or unreviewed')


def _validate_record(row, gate, receipt, evidence) -> None:
    fields = {*SCOPE_FIELDS, 'candidateCommit', 'gateId', 'argv', 'exitCode', 'status', 'logArtifactRef'}
    if set(row) != fields or type(row['exitCode']) is not int or row['exitCode'] != 0 or row['status'] != 'passed':
        raise ValueError('integration prerequisite is failed or has unrecognized fields')
    if any(row[field] != receipt[field] for field in (*SCOPE_FIELDS, 'candidateCommit')):
        raise ValueError('integration prerequisite scope differs from the receipt')
    argv = [part.format(candidateCommit=receipt['candidateCommit'],
                        outputDirectory=receipt['outputDirectory']) for part in gate['argvTemplate']]
    if row['argv'] != argv:
        raise ValueError('integration prerequisite command differs from the reviewed inventory')
    if not evidence[row['logArtifactRef']]:
        raise ValueError('integration prerequisite has no retained execution log')


__all__ = ['evaluate_integration_gate']
