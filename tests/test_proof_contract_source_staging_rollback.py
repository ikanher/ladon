"""Deadline rollback removes only files exclusively created by the current attempt."""
from types import SimpleNamespace

import pytest

import ladon._proof_contract_source_obligations_staging as staging


@pytest.mark.parametrize('preexisting', [False, True])
def test_expiry_after_main_probe_write_preserves_prior_files(tmp_path, monkeypatch, preexisting):
    clock = [0.0]
    parent = {'snapshotId': 'parent', 'environment': 'env',
              'selection': {'declaration': 'Source.parent', 'module': 'Source'}}
    provider = {'snapshotId': 'provider'}
    expected = {'leftOperator': 'Source.N', 'map': 'Source.F', 'constantName': 'Source.C',
                'inputScale': 'Source.N', 'offset': 0}
    monkeypatch.setattr(staging, '_source_prefix', lambda *_args: (b'', b''))
    monkeypatch.setattr(staging.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(staging, 'pinned_toolchain',
                        lambda _root: SimpleNamespace(context_identity='env'))
    directory = tmp_path / '.ladon/contract-obligations'
    if preexisting:
        staging._stage_source(tmp_path, parent, provider, expected, {}, 1.0)
    before = {p: p.read_bytes() for p in directory.rglob('Probe.lean')}
    write = staging._write_probe

    def expires_after_write(path, generated, **kwargs):
        write(path, generated, **kwargs)
        clock[0] = 2.0

    monkeypatch.setattr(staging, '_write_probe', expires_after_write)
    with pytest.raises(TimeoutError):
        staging._stage_source(tmp_path, parent, provider, expected, {}, 1.0)
    assert {p: p.read_bytes() for p in directory.rglob('Probe.lean')} == before
