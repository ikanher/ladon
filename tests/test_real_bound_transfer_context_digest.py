"""Transfer context identity must hash an ordered object, not a bare list.

This is a payload-builder unit control, not evidence of a checked transfer.
"""

import json

from test_real_bound_coefficient_persistence import FIXTURE

from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_native_transfer_artifacts import _payload


def test_transfer_payload_context_digest_retains_both_ordered_contexts(monkeypatch):
    from ladon import real_bound_native_transfer_artifacts as artifacts

    data = json.loads(FIXTURE.read_text())
    production = data['production']
    contexts = iter([{'marker': 'first'}, {'marker': 'second'}])
    monkeypatch.setattr(artifacts, '_context', lambda _p: next(contexts))
    relation = {'artifactId': 'sha256:' + 'a' * 64, 'payload': {'checkRunId': 'check:rule'}}
    payload = _payload({}, [production, production], relation, 'sha256:' + 'b' * 64,
                       data['relationRun']['result'])
    expected = snapshot_identity({'contexts': [{'marker': 'first'}, {'marker': 'second'}]})
    assert payload['result']['contextDigest'] == expected
    assert expected != snapshot_identity({'contexts': [{'marker': 'second'}, {'marker': 'first'}]})
