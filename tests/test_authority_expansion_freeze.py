"""Blocked exit waves cannot acquire unreviewed release prerequisites."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ladon.analysis.openspec_backlog import summarize_openspec_backlog

PROGRAM = 'ladon-authority-safe-verified-discovery-umbrella'


def _program(tmp_path: Path) -> tuple[Path, Path, dict]:
    source = Path(__file__).resolve().parents[1] / 'openspec/changes' / PROGRAM
    target = tmp_path / 'openspec/changes' / PROGRAM
    shutil.copytree(source, target)
    ledger = target / 'children/dependency-ledger.json'
    return tmp_path / 'openspec', ledger, json.loads(ledger.read_text())


def _freeze_findings(root: Path) -> list[dict]:
    return [row for row in summarize_openspec_backlog(root)['findings']
            if row['kind'] == 'expansion_freeze_violation']


@pytest.mark.parametrize('dependency', [
    'new-proofir-family', 'rust-parity-owner', 'lean-daemon',
    'broad-service-extraction', 'optional-atlas-release',
])
def test_backlog_rejects_new_critical_path_dependencies(tmp_path: Path, dependency: str) -> None:
    root, path, ledger = _program(tmp_path)
    ledger['children'][2]['integrationDependsOn'].append(dependency)
    path.write_text(json.dumps(ledger))
    findings = _freeze_findings(root)
    assert findings and any(dependency in row['detail'] for row in findings)


@pytest.mark.parametrize('damage', [
    'missing-ledger', 'malformed-json', 'new-child', 'new-owner',
    'missing-exit-wave', 'unknown-edge-field', 'duplicate-key', 'self-unlock',
])
def test_backlog_fails_closed_on_freeze_bypass(tmp_path: Path, damage: str) -> None:
    root, path, ledger = _program(tmp_path)
    if damage == 'missing-ledger':
        path.unlink()
    elif damage == 'malformed-json':
        path.write_text('{')
    elif damage == 'duplicate-key':
        text = json.dumps(ledger)
        path.write_text(text[:-1] + ',"children":[] }')
    else:
        if damage == 'new-child':
            ledger['children'].append(dict(ledger['children'][0], change='innocent-new-owner'))
        elif damage == 'new-owner':
            ledger['existingOwners'].append({'owner': 'innocent-new-owner', 'concern': 'maintenance'})
        elif damage == 'missing-exit-wave':
            ledger['children'][3]['startAfter'] = []
        elif damage == 'unknown-edge-field':
            ledger['children'][0]['prerequisites'] = ['optional-release']
        else:
            ledger['freezeState'] = 'complete'
        path.write_text(json.dumps(ledger))
    assert _freeze_findings(root)


def test_valid_local_child_plans_are_not_stale_external_packets(tmp_path: Path) -> None:
    root, _path, _ledger = _program(tmp_path)
    summary = summarize_openspec_backlog(root)
    assert summary['findings'] == []


def test_correctness_maintenance_does_not_expand_the_dependency_graph(tmp_path: Path) -> None:
    root, path, ledger = _program(tmp_path)
    ledger['historicalReconstructionPolicy']['maintenanceNote'] = 'A scoped regression fix in an existing child.'
    path.write_text(json.dumps(ledger))
    assert not _freeze_findings(root)


def test_owner_metadata_cannot_hide_an_extra_prerequisite(tmp_path: Path) -> None:
    root, path, ledger = _program(tmp_path)
    ledger['existingOwners'][0]['requires'] = ['optional-layer']
    path.write_text(json.dumps(ledger))
    assert _freeze_findings(root)
