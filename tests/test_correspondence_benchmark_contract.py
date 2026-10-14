"""Measurement acceptance rejects missing trials and restored harness writes.

Synthetic measurements exercise the comparator; they establish no Lean result
or performance gain.
"""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / 'scripts/benchmark_correspondence_field.py'


def _load(path=SCRIPT):
    spec = importlib.util.spec_from_file_location('field_benchmark_control', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _population(module):
    trust = {'policy': 'lean-standard-no-placeholders-v1', 'coverage': 'complete',
             'observedAxioms': []}
    rows = []
    for name in module.WORKLOADS:
        for trial in range(1, 4):
            for mode in ('ordinary', 'request'):
                rows.append({'workload': name, 'trial': trial, 'requestedMode': mode,
                             'qualified': True, 'wallSeconds': 100 if mode == 'ordinary' else 60,
                             'checks': [{'obligation': 'control', 'mode': 'prove', 'goal': 'True',
                                         'status': 'supported', 'trust': trust}]})
    return rows


def test_exact_paired_grid_can_meet_declared_target():
    module = _load()
    result = module.summarize(_population(module))
    assert result['qualifiedEquivalentWork'] and result['targetMet']


@pytest.mark.parametrize('mutation', ['duplicate', 'wrong-trial', 'failed', 'changed-goal'])
def test_incomplete_or_nonequivalent_population_cannot_acquire_gain(mutation):
    module = _load()
    rows = _population(module)
    if mutation == 'duplicate':
        rows[-1] = dict(rows[-2])
    elif mutation == 'wrong-trial':
        rows[-1]['trial'] = 4
    elif mutation == 'failed':
        rows[-1]['qualified'] = False
    else:
        rows[-1]['checks'][0]['goal'] = 'False'
    result = module.summarize(rows)
    assert not result['qualifiedEquivalentWork'] and not result['targetMet']


def test_restored_harness_bytes_cannot_reuse_loaded_identity(tmp_path):
    path = tmp_path / 'benchmark.py'
    original = SCRIPT.read_bytes()
    path.write_bytes(original)
    module = _load(path)
    identity = module._harness_identity()
    assert identity['path'] == str(path)
    path.write_bytes(original + b'\n# changed\n')
    path.write_bytes(original)
    with pytest.raises(ValueError, match='harness changed'):
        module._harness_identity()
