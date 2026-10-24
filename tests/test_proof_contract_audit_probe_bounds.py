"""Probe adapters reject nested bounds rather than silently replacing them."""
import json

import pytest
from test_proof_contract_application_probe_contract import TEMPLATE, fixture
from test_proof_contract_audit_admission_recovery import _source_plan
from test_proof_contract_audit_driver import _write_plan


@pytest.mark.parametrize('operation', ['probe', 'check-probe'])
def test_probe_request_cannot_silently_override_a_smaller_nested_cap(tmp_path, operation):
    from ladon.proof_contract_audit import run_contract_audit

    path, source_runner = _source_plan(tmp_path)
    data = fixture()
    request = {'context': data['context'], 'left': data['sides'][0],
               'right': data['sides'][1], 'template': TEMPLATE,
               'limits': {'timeout_seconds': 1, 'max_rss_bytes': 1024**2,
                          'max_output_bytes': 1024}}
    if operation == 'check-probe':
        request = {'request': request, 'planId': 'sha256:' + '0' * 64, 'terms': {}}
    plan = json.loads(path.read_bytes())
    plan['stages'] = [{'id': 'probe', 'operation': operation, 'request': request}]
    _write_plan(path, plan)

    def reject_algorithm(command, **kwargs):
        if json.loads(kwargs['input_bytes'])['operation'] == 'audit-stage':
            pytest.fail('adapter admitted a nested cap that it will silently overwrite')
        return source_runner(command, **kwargs)

    with pytest.raises((ValueError, TypeError)):
        run_contract_audit(path, tmp_path / 'run', runner=reject_algorithm)
