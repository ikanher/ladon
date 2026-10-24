"""Frozen subjects cannot drift or reuse synthetic development goals for promotion."""
from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from ladon.evaluation_corpus import (
    digest_bytes,
    validate_evaluation_plan,
    verify_repository_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/evaluation/discovery-corpus-v3.json'


def _rehash(plan):
    unsigned = {key: value for key, value in plan.items() if key != 'preregistrationIdentity'}
    plan['preregistrationIdentity'] = digest_bytes(json.dumps(unsigned, sort_keys=True, separators=(',', ':')).encode())


def _current_runtime_plan():
    """Create a new test-only registration bound to the runtime under test."""
    plan = json.loads(PLAN.read_text())
    plan['testRegistration'] = {
        'kind': 'current-runtime-behavioral-fixture',
        'purpose': 'contract validation only; no ranking measurement',
    }
    for path in plan['rankingInputs']:
        plan['rankingInputs'][path] = digest_bytes((ROOT / path).read_bytes())
    _rehash(plan)
    return plan


def test_registered_subjects_match_without_loading_optional_repositories():
    plan = _current_runtime_plan()
    validate_evaluation_plan(plan, ROOT)
    assert next(row for row in plan['repositories'] if row['id'] == 'matrix-calibration')['split'] == 'calibration'


def test_registration_cannot_change_goals_after_measurement():
    plan = _current_runtime_plan()
    plan['cases'][0]['goal'] = 'False'
    with pytest.raises(ValueError, match='identity'):
        validate_evaluation_plan(plan, ROOT)


def test_portable_fixtures_cannot_be_relabeled_as_external_promotion():
    plan = _current_runtime_plan()
    plan['repositories'][0]['split'] = 'held-out'
    for case in plan['cases']:
        if case['repository'] == plan['repositories'][0]['id']:
            case['split'] = 'held-out'
    _rehash(plan)
    with pytest.raises(ValueError, match='synthetic'):
        validate_evaluation_plan(plan, ROOT)


def test_ranking_change_invalidates_registered_study(tmp_path):
    plan = _current_runtime_plan()
    for path in plan['rankingInputs']:
        selected = tmp_path / path
        selected.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, selected)
    selected.write_text('# ranking modified after freezing\n')
    with pytest.raises(ValueError, match='ranking input changed'):
        validate_evaluation_plan(plan, tmp_path)


def test_external_unavailability_does_not_control_portable_validation(tmp_path):
    plan = _current_runtime_plan()
    optional = next(row for row in plan['repositories'] if row['optional'])
    optional['root'] = str(tmp_path / 'missing-optional-project')
    _rehash(plan)
    validate_evaluation_plan(plan, ROOT)
    with pytest.raises(FileNotFoundError):
        verify_repository_snapshot(optional, ROOT)


def test_changed_repository_bytes_are_drift_not_new_measurements(tmp_path):
    original = _current_runtime_plan()['repositories'][0]
    row = copy.deepcopy(original)
    row.update(root=str(tmp_path), pathBase='absolute-local-optional')
    for name in row['files']:
        shutil.copy2(ROOT / original['root'] / name, tmp_path / name)
    name = next(path for path in row['files'] if path.endswith('.lean'))
    (tmp_path / name).write_text('-- changed source\n')
    with pytest.raises(ValueError, match='source drift'):
        verify_repository_snapshot(row, ROOT)


def test_unchanged_historical_registration_is_rejected_on_runtime_drift():
    plan = json.loads(PLAN.read_text())
    historical = plan['rankingInputs']['src/ladon/verified_discovery.py']
    current = digest_bytes((ROOT / 'src/ladon/verified_discovery.py').read_bytes())
    assert current != historical
    with pytest.raises(ValueError, match='ranking input changed'):
        validate_evaluation_plan(plan, ROOT)
