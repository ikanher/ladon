"""An expired shared deadline stops validation and final source loops promptly."""

import pytest


def test_admission_preflight_checks_deadline_before_source_io(monkeypatch):
    from ladon import real_bound_native_chain as live

    calls = []

    def expired(_deadline):
        raise TimeoutError('expired')

    monkeypatch.setattr(live, '_remaining', expired)
    monkeypatch.setattr(live.production_api, '_verify_production', lambda p: calls.append('verify'))
    monkeypatch.setattr(live.production_api, '_current_source', lambda p, r: calls.append('source'))
    with pytest.raises(TimeoutError):
        live._admit([{}], '/root', 0)
    assert calls == []
