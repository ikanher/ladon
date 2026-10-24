"""Distribution gates exercise the maintained versioned installed CLI contracts."""
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_release_gate_common import load_common

GateError = load_common().GateError


def _invoke(root, monkeypatch):
    import release_gate_distribution as distribution

    calls = []
    installed = SimpleNamespace(python=root / 'venv/bin/python', scripts=root / 'venv/bin')
    monkeypatch.setattr(distribution, 'install_locked_test_runner', lambda *_: None)
    monkeypatch.setattr(distribution, 'run_checked', lambda cmd, **kwargs: calls.append((cmd, kwargs)))
    distribution.assert_installed_process_contracts(root, installed, root, {'PYTHONPATH': '/host'})
    return calls


def test_versioned_and_sibling_installed_contracts_are_all_selected(tmp_path, monkeypatch):
    tests = tmp_path / 'tests'
    tests.mkdir()
    names = ['test_installed_cli_contract_v2.py', 'test_installed_inspection_contract.py',
             'test_installed_theorem_cli_contract.py']
    for name in names:
        (tests / name).write_text('def test_placeholder(): pass\n')
    (tests / 'test_unrelated.py').write_text('def test_unrelated(): pass\n')
    calls = _invoke(tmp_path, monkeypatch)
    command, kwargs = calls[-1]
    selected = [Path(arg).name for arg in command if arg.endswith('.py')]
    assert selected == sorted(names)
    assert 'PYTHONPATH' not in kwargs['environment']
    assert kwargs['environment']['LADON_CONSOLE'].endswith('/ladon')


def test_missing_installed_contract_population_fails_closed(tmp_path, monkeypatch):
    (tmp_path / 'tests').mkdir()
    with pytest.raises(GateError, match='installed.*contract'):
        _invoke(tmp_path, monkeypatch)
