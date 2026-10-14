"""Unit contract controls for aggregation; these are not evaluation outcomes."""
import copy
import importlib.util
from pathlib import Path

import pytest


def load():
    path = Path(__file__).with_name('score.py')
    spec = importlib.util.spec_from_file_location('pilot_score', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def population():
    rows = []
    expected = ['argument-fault'] * 4 + ['faithful'] * 2 + ['method-difference', 'ambiguous']
    for index, kind in enumerate(expected):
        for arm in ['assisted', 'ordinary']:
            rows.append({'caseId': f'unit-{index}', 'arm': arm, 'expected': kind,
                         'verdict': kind, 'evidenceStatus': 'attributed-valid',
                         'evidenceRefs': ['unit-only-source-reference'],
                         'elapsedSeconds': 100, 'reviewerSeconds': 10,
                         'commandCount': 2, 'toolSeconds': 5,
                         'interpretationError': False, 'falseEndpointClaim': False,
                         'firstResponseRef': 'unit-only-first-reference', 'correctionRef': None})
    return [f'unit-{i}' for i in range(8)], rows


def test_counts_follow_rows_and_tied_detection_has_no_detection_benefit():
    cases, rows = population()
    rows[0]['verdict'] = 'unresolved'
    rows[0]['evidenceStatus'] = 'unresolved'
    result = load().aggregate(cases, rows)
    assert result['arms']['assisted']['justifiedFaults'] == 3
    assert result['arms']['ordinary']['justifiedFaults'] == 4
    assert result['arms']['assisted']['abstentions'] == 1
    assert result['detectionBenefit'] is False
    assert result['costBenefit'] is False
    assert result['rowCount'] == 16


def test_invalid_evidence_and_interpretation_errors_cannot_be_promoted():
    cases, rows = population()
    rows[0]['evidenceStatus'] = 'unresolved'
    rows[2]['interpretationError'] = True
    result = load().aggregate(cases, rows)
    assert result['arms']['assisted']['justifiedFaults'] == 2
    assert result['arms']['ordinary']['justifiedFaults'] == 4


def test_duplicate_missing_and_cross_arm_key_disagreement_are_rejected():
    cases, rows = population()
    bad = copy.deepcopy(rows)
    bad[1] = copy.deepcopy(bad[0])
    with pytest.raises(ValueError, match='duplicate|population'):
        load().aggregate(cases, bad)
    with pytest.raises(ValueError, match='population'):
        load().aggregate(cases, rows[:-1])
    bad = copy.deepcopy(rows)
    bad[1]['expected'] = 'faithful'
    with pytest.raises(ValueError, match='key|expected'):
        load().aggregate(cases, bad)


def test_false_alarm_and_inclusive_budget_prevent_cost_benefit():
    cases, rows = population()
    rows[8]['verdict'] = 'argument-fault'
    rows[8]['elapsedSeconds'] = 1
    result = load().aggregate(cases, rows)
    assert result['arms']['assisted']['falseAlarms'] == 1
    assert result['costBenefit'] is False
    rows[0]['elapsedSeconds'] = 895
    result = load().aggregate(cases, rows)
    assert result['arms']['assisted']['budgetExceeded'] == 1
    assert result['arms']['assisted']['justifiedFaults'] == 3
