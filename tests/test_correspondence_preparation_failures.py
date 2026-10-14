"""Failure-route ownership controls; no fabricated Lean proof results."""
from types import SimpleNamespace

import pytest

from ladon import correspondence_preparation as preparation
from ladon.correspondence_check import _check_goal


def _owner(tmp_path):
    owner = object.__new__(preparation.PreparedSourceContext)
    owner.root = tmp_path
    owner.toolchain = SimpleNamespace()
    owner.helper = preparation.typed_helper()
    owner.source_digest = preparation.hashlib.sha256(b'import Lean\n').hexdigest()
    owner.source_path = tmp_path / 'LadonPreparedFailure.lean'
    owner.olean = tmp_path / 'LadonPreparedFailure.olean'
    owner.outputs = [owner.source_path, *preparation._artifact_paths(owner.olean)]
    owner.owned = {}
    owner.closed = False
    owner.stale = False
    return owner


def test_launch_preparation_failure_cleans_created_source(tmp_path, monkeypatch):
    owner = _owner(tmp_path)
    def fail(*args, **kwargs):
        raise RuntimeError('execution preparation failed')
    monkeypatch.setattr(preparation, 'prepare_direct_lean_execution', fail)
    try:
        with pytest.raises(RuntimeError, match='execution preparation failed'):
            owner.compile(b'import Lean\n')
    finally:
        owner.cleanup()
    assert not owner.source_path.exists()


def test_checker_rejects_source_from_another_prepared_context(tmp_path, monkeypatch):
    owner = _owner(tmp_path)
    owner.source_digest = preparation.hashlib.sha256(b'import Lean\n').hexdigest()
    monkeypatch.setattr(owner, 'verify', lambda **kwargs: None)
    with pytest.raises(ValueError, match='(?i)(source|identity|context)'):
        _check_goal('True', 'True.intro', tmp_path, b'import Lean\n-- different\n',
                    {}, owner.toolchain, prepared=owner)
    assert not (tmp_path / '.ladon/correspondence').exists()


def test_checker_rejects_other_toolchain_context(tmp_path, monkeypatch):
    owner = _owner(tmp_path)
    owner.source_digest = preparation.hashlib.sha256(b'import Lean\n').hexdigest()
    monkeypatch.setattr(owner, 'verify', lambda **kwargs: None)
    with pytest.raises(ValueError, match='(?i)(toolchain|identity|context)'):
        _check_goal('True', 'True.intro', tmp_path, b'import Lean\n', {},
                    SimpleNamespace(selection_mode='other'), prepared=owner)
    assert not (tmp_path / '.ladon/correspondence').exists()


def test_compiler_rejects_a_source_other_than_constructor_snapshot(tmp_path):
    owner = _owner(tmp_path)
    owner.source_digest = preparation.hashlib.sha256(b'import Lean\n').hexdigest()
    with pytest.raises(ValueError, match='(?i)(source|identity|context)'):
        owner.compile(b'import Lean\naxiom extra : False\n')
    assert not owner.source_path.exists()
