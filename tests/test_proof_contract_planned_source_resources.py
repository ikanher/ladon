"""Pure regressions for malformed planner input and staging deadline boundaries."""
from types import SimpleNamespace

import pytest

import ladon._proof_contract_source_obligations_staging as staging
from ladon._proof_contract_planned_source_inputs import _planned_input_size
from ladon.proof_contract_obligation_planner import ContractObligationPlanRequest


def test_dataclass_class_is_rejected_without_attribute_error():
    with pytest.raises((ValueError, TypeError)):
        _planned_input_size({'planRequest': ContractObligationPlanRequest})


def test_deadline_expiring_in_prefix_read_stages_no_probe(tmp_path, monkeypatch):
    clock = [0.0]
    parent = {'snapshotId': 'parent', 'selection': {'declaration': 'Source.parent',
                                                  'module': 'Source'}}
    provider = {'snapshotId': 'provider'}

    def expired_prefix(*_args):
        clock[0] = 2.0
        return b'', b''

    monkeypatch.setattr(staging, '_source_prefix', expired_prefix)
    monkeypatch.setattr(staging.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(staging, 'pinned_toolchain',
                        lambda _root: SimpleNamespace(context_identity='env'))
    expected = {'leftOperator': 'Source.N', 'map': 'Source.F', 'constantName': 'Source.C',
                'inputScale': 'Source.N', 'offset': 0}
    with pytest.raises(TimeoutError):
        staging._stage_source(tmp_path, parent, provider, expected, {}, 1.0)
    assert not list((tmp_path / '.ladon/contract-obligations').rglob('Probe.lean'))
