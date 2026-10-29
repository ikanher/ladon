"""Public actual-Mathlib connection checks; mocks do not satisfy this gate."""

import pytest
from real_prose_connection_live_helpers import authored_input, formal_input, project

from ladon.real_prose_connection import connect_real_prose_bound, inspect_real_prose_connection
from ladon.real_prose_connection_inputs import REQUEST_SCHEMA


@pytest.fixture(scope='module')
def live_inputs(tmp_path_factory):
    root = project(tmp_path_factory)
    return root, formal_input(root), authored_input(root, global_scope=False)


def test_unrelated_set_estimate_gets_fresh_conditional_connection(live_inputs):
    root, formal, authored = live_inputs
    request = {'schema':REQUEST_SCHEMA,'term':'by intro original; exact original','premises':[]}
    result = connect_real_prose_bound(formal, authored, root, root, request,timeout_seconds=300)
    assert result['status'] == 'connected', result
    assert result['admission'] == 'unresolved'
    assert result['sourceTheoremProof'] == 'not-checked'
    assert result['mathematicalFalsity'] == 'not-established'
    evidence = result['check']['result']['goal']['completion']
    assert evidence['status'] == 'completed' and evidence['replay']['status'] == 'accepted'
    assert evidence['trust']['accepted'] is True and evidence['trust']['coverage'] == 'complete'
    report = inspect_real_prose_connection(result)
    assert report['authority'] == 'none' and report['freshCheck'] is False
    assert report['evidenceAuthentication'] == 'not-established'
