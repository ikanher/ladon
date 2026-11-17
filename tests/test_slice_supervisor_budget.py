"""Resource controls reach the supervisor, rather than just the receipt."""
from types import SimpleNamespace

import pytest

from ladon._proof_slice_runtime import SliceRunner


def test_runner_forwards_selected_limits(tmp_path, monkeypatch):
    from ladon import _proof_slice_runtime as runtime

    seen = {}

    def stop(command, **kwargs):
        seen.update(kwargs)
        raise RuntimeError('supervisor reached')

    monkeypatch.setattr(runtime, 'run_bounded_target_process', stop)
    runner = SliceRunner(tmp_path, SimpleNamespace(command=['lean']), {}, {
        'limits': {'secondsPerProcess': 123, 'rssBytes': 23456789}, 'processReceipts': [],
    })
    with pytest.raises(RuntimeError, match='supervisor reached'):
        runner.run(['Probe.lean'])
    assert seen['timeout_seconds'] == 123
    assert seen['max_rss_bytes'] == 23456789
