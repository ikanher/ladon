"""Study failures cannot erase native baselines or select another installed console."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def driver():
    path = Path(__file__).resolve().parents[1] / 'scripts/run_discovery_evaluation.py'
    spec = importlib.util.spec_from_file_location('discovery_evaluation_driver', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_index_failure_keeps_native_baselines_and_cannot_supply_ladon_success(driver, tmp_path, monkeypatch):
    case = {'id': 'case', 'split': 'held-out', 'expectedAcceptableCandidates': ['expected']}
    plan = {'methods': ['ladon', 'exact?', 'editor-search'], 'policy': {'bounds': {}}}
    calls = []

    def baseline(method, *_):
        calls.append(method)
        return {'status': 'unavailable', 'reason': 'explicit fixture result'}

    monkeypatch.setattr(driver, 'run_baseline', baseline)
    monkeypatch.setattr(driver, 'run_ladon', lambda *_a, **_k: pytest.fail('failed index cannot run Ladon'))
    row = driver.measure_case(case, object(), None, plan, SimpleNamespace(ladon=tmp_path / 'ladon'), tmp_path)
    assert calls == ['exact?', 'editor-search']
    assert row['methods']['ladon']['status'] == 'failed'
    assert row['methods']['ladon']['metrics']['verifiedCandidateRecall'] == 0
    assert row['methods']['exact?']['metrics']['verifiedCandidateRecall'] is None


def test_missing_optional_repository_records_nulls_without_running_methods(driver, tmp_path, monkeypatch):
    repository = {'id': 'optional', 'split': 'held-out'}
    case = {'id': 'case', 'repository': 'optional', 'expectedAcceptableCandidates': ['expected']}
    plan = {'cases': [case], 'methods': ['ladon', 'exact?']}
    monkeypatch.setattr(driver, 'prepare_repository', lambda *_: (_ for _ in ()).throw(FileNotFoundError('missing pin')))
    monkeypatch.setattr(driver, 'measure_case', lambda *_: pytest.fail('unavailable source cannot be measured'))
    row = driver.measure_repository(repository, plan, SimpleNamespace(), tmp_path)
    assert row['status'] == 'unavailable'
    assert all(result['metrics']['verifiedCandidateRecall'] is None
               for result in row['cases'][0]['methods'].values())


def test_optional_project_is_never_implicitly_built_even_with_portable_preparation(driver, tmp_path, monkeypatch):
    repo = tmp_path / 'external'
    repo.mkdir()
    output = tmp_path / 'captures'
    output.mkdir()
    monkeypatch.setattr(driver, 'verify_repository_snapshot', lambda *_: repo)
    monkeypatch.setattr(driver, 'selected_tools', lambda *_: (tmp_path / 'lean', tmp_path / 'lake'))
    monkeypatch.setattr(driver, 'measure_command', lambda *_a, **_k: pytest.fail('external build is forbidden'))
    args = SimpleNamespace(output=output, prepare_portable=True)
    with pytest.raises(FileNotFoundError, match='compiled module'):
        driver.prepare_repository({'id': 'external', 'optional': True},
                                  [{'module': 'Missing', 'id': 'case'}], {}, args, tmp_path)


@pytest.mark.parametrize('defect', ['other-console', 'outside-prefix', 'checkout-import', 'nonisolated'])
def test_study_rejects_mixed_console_or_import_environment(driver, tmp_path, monkeypatch, defect):
    prefix = tmp_path / 'installed'
    root = tmp_path / 'candidate'
    origin = prefix / 'lib/ladon/__init__.py'
    console = prefix / 'bin/ladon'
    monkeypatch.setattr(driver.sys, 'prefix', str(prefix))
    monkeypatch.setattr(driver.sys, 'executable', str(prefix / 'bin/python'))
    monkeypatch.setattr(driver.sys, 'flags', SimpleNamespace(isolated=defect != 'nonisolated'))
    if defect == 'outside-prefix':
        origin = tmp_path / 'another-install/ladon/__init__.py'
    if defect == 'checkout-import':
        origin = root / 'src/ladon/__init__.py'
    if defect == 'other-console':
        console = tmp_path / 'another-install/bin/ladon'
    monkeypatch.setattr(driver.ladon, '__file__', str(origin))
    with pytest.raises(ValueError, match='installed|interpreter'):
        driver.require_installed_python(root, console)
