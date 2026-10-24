"""Immutable, bounded raw evidence custody for compact route responses."""
import importlib
import json

import pytest


def _storage():
    return importlib.import_module('ladon._proof_contract_route_context_evidence')


def test_unresolved_raw_evidence_round_trips_and_is_content_bound(tmp_path):
    # This is an unresolved protocol document, with no Lean receipt or authority.
    raw = {'status': 'unresolved', 'diagnostic': {'code': 'no-proof'}, 'capture': None}
    compact = _storage().store_goal_evidence(tmp_path, raw)
    ref = compact['evidenceRef']
    assert ref['path'].startswith('.ladon/contract-obligations/')
    assert compact['status'] == 'unresolved'
    assert compact.get('completion') is None
    assert json.loads((tmp_path / ref['path']).read_text()) == raw
    assert _storage().load_goal_evidence(tmp_path, compact) == raw
    assert _storage().store_goal_evidence(tmp_path, raw) == compact


def test_changed_raw_evidence_cannot_reuse_reference(tmp_path):
    compact = _storage().store_goal_evidence(tmp_path, {'status': 'unresolved'})
    (tmp_path / compact['evidenceRef']['path']).write_text('{}')
    with pytest.raises(ValueError):
        _storage().load_goal_evidence(tmp_path, compact)
    with pytest.raises(ValueError):
        _storage().store_goal_evidence(tmp_path, {'status': 'unresolved'})


def test_projection_never_treats_process_success_as_proof(tmp_path):
    raw = {'status': 'completed', 'returnCode': 0}
    compact = _storage().store_goal_evidence(tmp_path, raw)
    from ladon.proof_contract_bridge import _accepted_check

    assert not _accepted_check(compact)
    assert compact.get('completion') is None


def test_oversized_raw_evidence_is_refused_before_writing(tmp_path):
    with pytest.raises(ValueError, match='8 MiB'):
        _storage().store_goal_evidence(tmp_path, {'evidence': 'x' * (8 * 1024**2)})
    assert not (tmp_path / '.ladon').exists()
