"""Native rule publication must report deadline expiry even before worker startup."""

import pytest


@pytest.mark.parametrize('kind', ['coefficient', 'transfer'])
def test_native_rule_expired_preflight_is_unresolved(monkeypatch, kind):
    from importlib import import_module

    bundles = import_module('ladon.real_bound_native_' + kind + '_bundle')

    def expired(_deadline):
        raise TimeoutError('expired before launch')

    monkeypatch.setattr(bundles, '_remaining', expired)
    operation = getattr(bundles, 'produce_' + kind + '_bundle')
    inputs = [{}, {}] if kind == 'transfer' else [{}]
    result = operation(*inputs, '/root')
    assert result['status'] == 'unresolved'
    assert result['authority'] == 'none'
    assert 'artifacts' not in result
