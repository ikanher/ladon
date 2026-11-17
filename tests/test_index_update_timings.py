"""Incremental updates expose actual work phases on changed and no-op paths."""
from ladon.proof_search_index import build_proof_search_index, update_proof_search_index


def test_update_times_changed_and_noop_phases(tmp_path):
    (tmp_path / 'Main.lean').write_text('def before : Nat := 1\n')
    build_proof_search_index(tmp_path)
    (tmp_path / 'Main.lean').write_text('def after : Nat := 2\n')
    changed = update_proof_search_index(tmp_path).payload
    noop = update_proof_search_index(tmp_path).payload
    for result in (changed, noop):
        assert set(result['phaseSeconds']) == {'enumeration', 'hashing', 'extraction', 'database'}
        assert all(value >= 0 for value in result['phaseSeconds'].values())
        assert sum(result['phaseSeconds'].values()) <= result['elapsedSeconds'] + 0.01
    assert changed['phaseSeconds']['extraction'] > 0
    assert noop['phaseSeconds']['extraction'] == 0


def test_nested_phases_are_exclusive_and_request_local(monkeypatch):
    from ladon import proof_search_timing as timing

    clock = iter([0, 1, 3, 5])
    monkeypatch.setattr(timing, 'monotonic', lambda: next(clock))
    with timing.update_timing() as first, timing.phase('database'), timing.phase('extraction'):
        pass
    assert first['database'] == 3
    assert first['extraction'] == 2
    with timing.update_timing() as second:
        assert all(value == 0 for value in second.values())
    assert timing._ACTIVE.get() is None
