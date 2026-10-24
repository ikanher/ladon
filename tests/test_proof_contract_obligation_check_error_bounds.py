"""Rejected requests cannot copy unvalidated fields into diagnostic receipts."""
import json

import pytest
from test_proof_contract_obligation_check_boundaries import _request

from ladon.proof_contract_obligation_checks import check_obligation_sources


@pytest.mark.parametrize('kind', ['string', 'cycle', 'boolean'])
def test_invalid_attempt_limit_never_escapes_into_error_report(tmp_path, kind):
    request = _request(tmp_path)
    cycle = {}
    cycle['self'] = cycle
    request['maxCheckAttempts'] = {'string': 'private-canary' * 100000,
                                 'cycle': cycle, 'boolean': True}[kind]
    report = check_obligation_sources(request)
    encoded = json.dumps(report, allow_nan=False)
    assert report['status'] == 'rejected'
    assert report['resourceAccounting']['maxCheckAttempts'] is None
    assert 'private-canary' not in encoded
    assert len(encoded) < 2048
    assert not (tmp_path / 'run').exists()
