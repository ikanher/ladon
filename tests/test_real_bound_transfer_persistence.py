"""Historical native transfer checks using genuine source/kernel run evidence."""

import copy
import json
from pathlib import Path

import pytest
from real_bound_task32_helpers import (
    assert_mutations_rejected,
    assert_not_chain_edge,
    assert_stored,
)
from test_real_bound_comparison_persistence import analysis

from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_native_analysis import _context
from ladon.real_bound_native_transfer_artifacts import recorded_transfer
from ladon.real_bound_native_transfer_evidence import recorded_transfer_evidence

FIXTURE = Path(__file__).parent / 'fixtures/real_bound_native/recorded-transfer.json'


def data():
    return json.loads(FIXTURE.read_text())


def recorded():
    value = data()
    return recorded_transfer(value['productions'], value['relationRun'])


def test_genuine_transfer_publication_preserves_ordered_context_digest_and_sqlite_goal():
    value = data()
    bundle = recorded_transfer(value['productions'], value['relationRun'])
    result = analysis(bundle)['payload']['result']
    expected = snapshot_identity({'contexts': [_context(p) for p in value['productions']]})
    assert result['contextDigest'] == expected
    assert result['transferPremises'] == 'assumed'
    assert_stored(bundle, 2)
    assert_not_chain_edge(bundle)


def test_rehashed_native_promotions_and_owner_mutations_are_rejected():
    assert_mutations_rejected(recorded())


@pytest.mark.parametrize('kind', ['owner', 'term', 'goal', 'memory', 'checker', 'source', 'missing-helper'])
def test_deep_transfer_receipts_bind_actual_request_and_execution(kind):
    value = data()
    run = value['relationRun']
    if kind in ('owner', 'term'):
        run['result']['request']['leftPlanId' if kind == 'owner' else 'term'] = 'changed'
    elif kind == 'goal':
        run['result']['request']['goal']['proposition'] = 'True'
    elif kind == 'memory':
        run['processReceipt']['memoryLimited'] = True
    elif kind == 'checker':
        run['result']['checkerIdentity'] = 'sha256:' + 'f' * 64
    elif kind == 'source':
        run['result']['check']['capture']['capture']['source']['digest'] = 'sha256:' + 'e' * 64
    else:
        run['result']['compilations'].pop()
    with pytest.raises(ValueError):
        recorded_transfer_evidence(value['productions'], run)


def test_historical_transfer_survives_current_checker_drift_without_workers(monkeypatch):
    from ladon import real_bound_native_transfer as live
    from ladon import real_bound_native_transfer_evidence as evidence
    from ladon.real_bound_native_transfer_bundle import inspect_transfer_bundle

    def forbidden(*_args, **_kwargs):
        pytest.fail('historical inspection attempted fresh checking')

    monkeypatch.setattr(live, '_fresh', forbidden)
    monkeypatch.setattr(evidence, 'native_checker_identity', lambda: 'sha256:' + 'f' * 64)
    result = inspect_transfer_bundle(recorded())
    assert result['authority'] == 'none' and result['freshCheck'] is False
    assert result['evidenceAuthentication'] == 'not-established'
    assert result['transferPremises'] == 'assumed'


def install(monkeypatch, limited):
    from ladon import real_bound_native_transfer as live
    from ladon import real_bound_native_transfer_evidence as evidence

    value, calls = data(), []
    monkeypatch.setattr(live.production_api, '_current_source', lambda *_: None)
    monkeypatch.setattr(evidence, 'native_checker_identity', lambda: value['relationRun']['result']['checkerIdentity'])

    def fresh(production, _root, seconds):
        calls.append(('admission', seconds))
        return copy.deepcopy(production)

    def rule(*_args, timeout_seconds):
        calls.append(('rule', timeout_seconds))
        run = copy.deepcopy(value['relationRun'])
        if limited:
            run['processReceipt']['memoryLimited'] = True
        return run

    monkeypatch.setattr(live, '_fresh', fresh)
    monkeypatch.setattr(live, 'check_transfer_relation', rule)
    return calls


@pytest.mark.parametrize('limited', [False, True])
def test_mocked_replay_rechecks_both_owners_and_cannot_reuse_limited_success(monkeypatch, limited):
    from ladon.real_bound_native_transfer_bundle import replay_transfer_bundle

    calls = install(monkeypatch, limited)
    result = replay_transfer_bundle(recorded(), '/root', timeout_seconds=60)
    assert [row[0] for row in calls] == ['admission', 'admission', 'rule']
    assert 60 >= calls[0][1] >= calls[1][1] >= calls[2][1] > 0
    if limited:
        assert result['status'] == 'unresolved' and result['authority'] == 'none'
        assert 'artifacts' not in result
    else:
        assert result['authority'] == 'fresh-source-predicate-scalar-and-transfer-checks'


def test_publication_expiry_preserves_checked_runs_without_native_success(monkeypatch):
    from ladon import real_bound_native_transfer_bundle as bundles

    install(monkeypatch, False)
    original = bundles.recorded_transfer

    def record_then_expire(*args):
        bundle = original(*args)

        def expired(_deadline):
            raise TimeoutError('expired during publication')
        monkeypatch.setattr(bundles, '_remaining', expired)
        return bundle

    monkeypatch.setattr(bundles, 'recorded_transfer', record_then_expire)
    result = bundles.produce_transfer_bundle(*data()['productions'], '/root')
    assert result['status'] == 'unresolved' and result['authority'] == 'none'
    assert len(result['admissionCheckRuns']) == 2
    assert result['relationCheckRun'] is not None
    assert 'artifacts' not in result
