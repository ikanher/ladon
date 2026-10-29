"""Order-prefix candidates must preserve contexts and require fresh exact proof."""

import copy
import json

import pytest
from test_real_bound_native_analysis import production

from ladon.proof_contract_cli import contract_main


def pair():
    low = production()
    high = copy.deepcopy(low)
    record = high['artifacts'][-1]['payload']['record']
    record['loss'] = 4
    # A context-only synthetic control, not admitted or live evidence.
    ref = record['application']['input']['orderRef']
    descriptor = next(row for row in high['artifacts'][-1]['subjectRefs']
                      if row['localId'] == ref['localId'])
    changed = copy.deepcopy(descriptor)
    changed['localId'] = 'expr:' + 'd' * 64
    changed['fingerprint']['digest'] = 'sha256:' + 'd' * 64
    high['artifacts'][-1]['subjectRefs'].append(changed)
    record['application']['input']['orderRef'] = {'kind': 'expression', 'localId': changed['localId']}
    return high, low


def test_only_loss_and_its_input_order_are_candidate_differences():
    from ladon.real_bound_native_prefix import prefix_candidate

    high, low = pair()
    assert prefix_candidate(high, low) is None
    assert prefix_candidate(low, high) == 'real-prefix-direction-unproved'


@pytest.mark.parametrize('field,value', [
    ('endpointId', 'different-endpoint'),
    ('interpretation', {'kind': 'different-interpretation'}),
    ('constant', {'binderId': 'b1', 'permittedBinderIds': []}),
])
def test_candidate_does_not_ignore_endpoint_interpretation_or_scope(field, value):
    from ladon.real_bound_native_prefix import prefix_candidate

    high, low = pair()
    high['artifacts'][-1]['payload']['record'][field] = value
    assert prefix_candidate(high, low) == 'real-prefix-context-mismatch'


def test_unchecked_relation_does_not_establish_a_rule():
    from ladon.real_bound_native_prefix import accepted_prefix_run

    assert accepted_prefix_run({'status': 'completed', 'result': {'status': 'checked'}}, {}, {}) is False


def test_prefix_cli_has_explicit_direction_and_unresolved_exit(tmp_path, capsys, monkeypatch):
    from ladon import real_bound_native_prefix as prefix

    path = tmp_path / 'production.json'
    path.write_text('{}')
    calls = []

    def run(stronger, weaker, root, *, timeout_seconds):
        calls.append((stronger, weaker, root, timeout_seconds))
        return {'schema': 'ladon-real-bound-prefix-analysis-v1', 'status': 'unresolved'}

    monkeypatch.setattr(prefix, 'check_prefix_implication', run)
    assert contract_main(['check-real-bound-prefix', '--stronger', str(path), '--weaker', str(path),
                          '--root', str(tmp_path), '--timeout-seconds', '21']) == 2
    assert calls == [({}, {}, tmp_path, 21.0)]
    assert json.loads(capsys.readouterr().out)['status'] == 'unresolved'
