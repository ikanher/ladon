"""Frozen contract suite for rational branch checked receipts (#413-415).

Tests patch only the local Lean replay boundary for fast deterministic cases; the
last test is opt-in and uses no network/model.
"""
from __future__ import annotations

import copy
import hashlib
import os
import time
from pathlib import Path

import pytest

import ladon.proof_contract_rational_check as rational_check
import ladon.proof_contract_rational_probes as route
from ladon.proof_contract_rational_probes import (
    check_rational_branch_probe,
    plan_rational_branch_probe,
)
from ladon.proof_contract_refinement import create_refinement_branch

ROOT = Path(__file__).resolve().parents[3]
LEAN_ROOT = Path('/home/codex/projects/lean/matrix-factorization')
LIMITS = {'timeout_seconds': 10, 'max_output_bytes': 1024 * 1024,
          'max_rss_bytes': 12 * 1024**3}


def _pred(op='ge', right=None):
    return {'op': op, 'left': {'var': 'x'},
            'right': {'rat': '0'} if right is None else right}


def _goal(op='ge'):
    return {'variables': ['x'], 'premises': [], 'conclusion': _pred(op)}


def _branch(op='ge', *, source_root=None):
    finding = {
        'id': 'receipt-red-finding', 'status': 'abstract-countermodel',
        'discrepancy': {'claim': 'x is nonnegative', 'observed': 'x = -1'},
        'witness': {'id': 'receipt-red-witness', 'assignment': {'x': '-1'}},
    }
    constraint = {
        'id': 'receipt-red-domain', 'expression': _pred(op),
        'justification': {'kind': 'proposed-repair', 'rationale': 'bounded test branch'},
    }
    return create_refinement_branch(finding, [constraint], source_root=source_root or str(ROOT))


def _source_branch(root, text='Assume x is nonnegative.\n'):
    path = root / 'paper.txt'
    path.write_text(text, encoding='utf-8')
    finding = {
        'id': 'receipt-red-finding', 'status': 'abstract-countermodel',
        'discrepancy': {'claim': 'x is nonnegative', 'observed': 'x = -1'},
        'witness': {'id': 'receipt-red-witness', 'assignment': {'x': '-1'}},
    }
    constraint = {
        'id': 'receipt-red-domain', 'expression': _pred(),
        'justification': {'kind': 'source-cited-refinement', 'source': {
            'path': 'paper.txt', 'startLine': 1, 'endLine': 1,
            'quote': text.rstrip('\n'),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        }, 'nonclaim': 'Span validation does not certify formula fidelity.'},
    }
    return create_refinement_branch(finding, [constraint], source_root=root)


def request(**changes):
    value = {
        'sourceRoot': str(ROOT), 'workspaceRoot': str(LEAN_ROOT),
        'branch': _branch(), 'baseGoal': _goal(), 'assignment': {'x': '1'},
        'deadlineMonotonic': time.monotonic() + 90,
        'limits': copy.deepcopy(LIMITS),
    }
    value.update(changes)
    return value


def _fast_plan(monkeypatch):
    """Avoid Lean preflight while retaining real branch/goal/plan regeneration."""
    def workspace_identity(root, *_args, **_kwargs):
        return 'sha256:' + hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest()
    monkeypatch.setattr(route, '_preflight_workspace', workspace_identity)


def _replay_hook(monkeypatch, *, status='completed', raw_status='accepted',
                 support='supported', code='completed', compiled_inventory=None):
    """Mock the dedicated bounded generated-goal replay boundary.

    The checker implementation should call this boundary once per generated goal,
    with the exact proposition, proof term, and receipt binding. Returning a bounded
    supervisor envelope models completion, replay, and trust independently.
    """
    calls = []

    def replay(job, bounds, state, runner=None, **kwargs):
        calls.append((copy.deepcopy(job), copy.deepcopy(bounds)))
        inventory = compiled_inventory(len(calls)) if callable(compiled_inventory) else compiled_inventory
        inventory = [] if inventory is None else copy.deepcopy(inventory)
        goal = job.get('goal') or job.get('request', {}).get('goal')
        term = job.get('term') or job.get('request', {}).get('term')
        binding = job.get('binding') or job.get('request', {}).get('binding')
        raw = {
            'status': raw_status,
            'completion': {'status': 'completed', 'termDigest': _sha(term or '')},
            'replay': {'status': 'replayed'}, 'trust': {'status': 'trusted'},
            'generatedProposition': goal, 'binding': binding,
            'evidence': {
                'capture': {'capture': {
                    'captureId': 'test-capture',
                    'source': {'digest': _sha(goal or '')},
                    'goal': {'typeStructural': 'test-structural-goal'},
                    'environment': {'executionContextRef': 'test-context',
                                    'compiledInventory': inventory},
                }},
                'completion': {
                    'status': 'completed', 'termDigest': _sha(term or ''),
                    'replay': {'status': 'accepted', 'sourceDigest': _sha(goal or '')},
                    'trust': {'status': 'trusted', 'accepted': True,
                              'coverage': 'complete', 'policy': 'test-policy',
                              'observedAxioms': ['propext']},
                },
                'processReceipts': [{
                    'stdoutDigest': _sha('stdout'), 'stderrDigest': _sha('stderr'),
                    'elapsedSeconds': 0.01, 'returnCode': 0,
                    'peakRssBytes': 1024, 'timedOut': False,
                    'memoryLimited': False, 'outputLimited': False,
                }],
                'leanExecutableDigest': _sha('lean'),
                'executionContextIdentity': 'test-context',
                'sourceDigest': _sha(goal or ''),
            },
        }
        return {
            'status': status, 'diagnostic': {'code': code, 'message': code},
            'result': raw if status == 'completed' else None,
            'processReceipt': {'status': status}, 'bounds': bounds,
        }

    monkeypatch.setattr(route, '_execute_job', replay, raising=False)
    return calls


def _sha(value):
    return 'sha256:' + hashlib.sha256(value.encode()).hexdigest()


def _terms(plan, term='by norm_num'):
    return {row['goalId']: term for row in plan['goals']}


def _plan(monkeypatch, req=None):
    _fast_plan(monkeypatch)
    return plan_rational_branch_probe(request() if req is None else req)


def _assert_no_support(result):
    assert result.get('checkedSupport') is None
    assert result.get('receipt') is None
    assert not any(row.get('status') == 'checked-support'
                   for row in result.get('goals', []))


def test_closed_check_input_rejects_extra_or_caller_authored_goal_fields(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    terms = _terms(plan)
    for key, value in [('goal', 'True'), ('leanGoal', 'True'),
                       ('proof', 'by trivial'), ('unchecked', True)]:
        malformed = copy.deepcopy(req)
        malformed[key] = value
        with pytest.raises((TypeError, ValueError)):
            check_rational_branch_probe(malformed, plan['planId'], terms)


def test_exact_regeneration_and_stale_plan_id(monkeypatch):
    req = request()
    original = _plan(monkeypatch, req)
    _replay_hook(monkeypatch)
    stale = check_rational_branch_probe(req, 'sha256:' + '0' * 64,
                                        _terms(original))
    assert stale['status'] in {'rejected', 'stale-input'}
    _assert_no_support(stale)

    changed = request(assignment={'x': '2'})
    result = check_rational_branch_probe(changed, original['planId'],
                                         _terms(original))
    assert result['status'] in {'rejected', 'stale-input'}
    _assert_no_support(result)


def test_terms_must_cover_exact_generated_goal_ids_and_be_nonempty(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    _replay_hook(monkeypatch)
    for terms in ({}, {plan['goals'][0]['goalId']: 'by norm_num'},
                  {plan['goals'][0]['goalId']: ''},
                  {plan['goals'][0]['goalId']: 'by norm_num', 'extra': 'by trivial'}):
        result = check_rational_branch_probe(req, plan['planId'], terms)
        _assert_no_support(result)
        assert result['status'] in {'rejected', 'unresolved', 'incomplete'}


def test_acceptance_requires_completed_worker_replay_and_trust(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    terms = _terms(plan)
    for supervisor, replay, trust in [
        ('incomplete', 'replayed', 'trusted'),
        ('completed', 'rejected', 'trusted'),
        ('completed', 'replayed', 'untrusted'),
    ]:
        def worker(job, bounds, state, runner=None, *, supervisor=supervisor,
                   replay=replay, trust=trust, **kwargs):
            term = job.get('term') or job.get('request', {}).get('term') or ''
            raw = {'status': 'accepted',
                   'completion': {'status': 'completed', 'termDigest': _sha(term)},
                   'replay': {'status': replay}, 'trust': {'status': trust}}
            return {'status': supervisor, 'result': raw if supervisor == 'completed' else None,
                    'diagnostic': {'code': 'mock'}, 'processReceipt': {'status': supervisor},
                    'bounds': bounds}
        monkeypatch.setattr(route, '_execute_job', worker, raising=False)
        result = check_rational_branch_probe(req, plan['planId'], terms)
        _assert_no_support(result)


def test_receipt_binds_each_semantic_identity_and_exact_term(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    calls = _replay_hook(monkeypatch)
    result = check_rational_branch_probe(req, plan['planId'], _terms(plan))
    assert result['status'] == 'checked-rational-branch', result
    receipt = result['receipt']
    assert receipt['planId'] == plan['planId']
    _assert_semantic_bindings(receipt, plan)
    assert receipt['termDigests'] == {gid: _sha(term) for gid, term in _terms(plan).items()}
    assert receipt['compiledInventoryDigest'] == rational_check._digest_text([])
    assert len(set(receipt['compiledInventoryDigestsByGoal'].values())) == 1
    assert all(call[0] for call in calls)
    assert result['sourceFormulaFidelity'] == 'unverified'
    assert result['originalClaimRefuted'] is False


def _assert_semantic_bindings(receipt, plan):
    for key in ('branchId', 'branchKind', 'sourceSpanIdentities',
                'baseGoalSha256', 'derivedGoalSha256', 'assignment',
                'goalDigests', 'checkerIdentity', 'workspaceIdentity'):
        assert receipt[key] == plan[key]


def test_cache_is_never_accepted_without_fresh_lean_replay(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    terms = _terms(plan)
    _replay_hook(monkeypatch)
    first = check_rational_branch_probe(req, plan['planId'], terms)
    cache = first['cache']
    replay_calls = _replay_hook(monkeypatch)
    hit = check_rational_branch_probe(req, plan['planId'], terms, cached_result=cache)
    assert hit['status'] == 'checked-rational-branch'
    assert replay_calls
    assert not any(goal['reused'] for goal in hit['goals'])
    assert hit['cache']['reusePolicy'] == 'fresh-lean-replay-required'

    changed_term = dict(terms)
    changed_term[next(iter(changed_term))] = 'by decide'
    miss_calls = _replay_hook(monkeypatch)
    miss = check_rational_branch_probe(req, plan['planId'], changed_term,
                                       cached_result=cache)
    assert miss['status'] != 'checked-rational-branch' or not all(g['reused'] for g in miss['goals'])
    assert miss_calls


def test_forged_cache_cannot_bypass_worker_acceptance(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    terms = _terms(plan)
    forged = {
        'schema': 'ladon-rational-branch-check-cache-v1', 'planId': plan['planId'],
        'goals': [],
    }
    for goal in plan['goals']:
        term = terms[goal['goalId']]
        binding = rational_check._goal_binding(
            plan, goal, term, rational_check._proof_checker_identity())
        forged['goals'].append({
            'goalId': goal['goalId'], 'goalDigest': _sha(goal['leanProposition']),
            'proposition': goal['leanProposition'], 'term': term,
            'termDigest': _sha(term), 'status': 'checked-support', 'binding': binding,
            'result': {
                'status': 'accepted', 'generatedProposition': goal['leanProposition'],
                'binding': binding,
                'completion': {'status': 'completed', 'termDigest': _sha(term)},
                'replay': {'status': 'replayed'}, 'trust': {'status': 'trusted'},
            },
        })
    calls = _replay_hook(monkeypatch, status='incomplete', code='timeout')
    result = check_rational_branch_probe(req, plan['planId'], terms, cached_result=forged)
    assert calls
    assert result['status'] == 'incomplete'
    _assert_no_support(result)


@pytest.mark.parametrize('mutation', [
    'branch', 'source-span', 'base-goal', 'derived-goal', 'assignment',
    'generated-proposition', 'checker', 'workspace',
])
def test_cache_invalidates_for_each_semantic_input(monkeypatch, mutation, tmp_path):
    if mutation == 'source-span':
        req = request(sourceRoot=str(tmp_path), branch=_source_branch(tmp_path))
    else:
        req = request()
    plan = _plan(monkeypatch, req)
    _replay_hook(monkeypatch)
    prior = check_rational_branch_probe(req, plan['planId'], _terms(plan))['cache']
    changed = _mutate_cache_input(monkeypatch, mutation, tmp_path, req)
    regenerated = _plan(monkeypatch, changed)
    assert regenerated['planId'] != plan['planId']
    calls = _replay_hook(monkeypatch)
    result = check_rational_branch_probe(changed, regenerated['planId'],
                                        _terms(regenerated), cached_result=prior)
    assert calls, f'{mutation} change incorrectly reused prior receipt'
    if mutation in {'generated-proposition', 'checker'}:
        assert result['status'] in {'rejected', 'checked-rational-branch'}
    else:
        assert result['status'] == 'checked-rational-branch'


def _mutate_cache_input(monkeypatch, mutation, tmp_path, req):
    changed = copy.deepcopy(req)
    if mutation == 'branch':
        changed['branch'] = _branch('gt')
    elif mutation == 'source-span':
        changed['branch'] = _source_branch(tmp_path, 'Assume x is strictly positive.\n')
    elif mutation == 'base-goal':
        changed['baseGoal'] = _goal('gt')
    elif mutation == 'derived-goal':
        changed['branch'] = _branch('gt')
    elif mutation == 'assignment':
        changed['assignment'] = {'x': '2'}
    elif mutation == 'generated-proposition':
        monkeypatch.setattr(route, '_proofir_artifact', lambda _plan: {})
        actual_encoder = route.encode_rational_goal

        def changed_proposition(*args, **kwargs):
            encoded = actual_encoder(*args, **kwargs)
            encoded = copy.deepcopy(encoded)
            encoded['obligations'][0]['leanProposition'] += ' '  # invalid if trusted as caller input
            return encoded

        monkeypatch.setattr(route, 'encode_rational_goal', changed_proposition)
    elif mutation == 'checker':
        monkeypatch.setattr(route, '_proofir_artifact', lambda _plan: {})
        actual_encoder = route.encode_rational_goal

        def changed_checker(*args, **kwargs):
            encoded = copy.deepcopy(actual_encoder(*args, **kwargs))
            encoded['checkerIdentity'] = 'sha256:' + 'f' * 64
            return encoded

        monkeypatch.setattr(route, 'encode_rational_goal', changed_checker)
    elif mutation == 'workspace':
        changed['workspaceRoot'] = str(ROOT)
    return changed


def test_malformed_and_mismatched_cache_fails_closed(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    terms = _terms(plan)
    _replay_hook(monkeypatch)
    good = check_rational_branch_probe(req, plan['planId'], terms)['cache']
    for cache in (None, [], {}, {'schema': 'bad', 'planId': plan['planId'], 'goals': []},
                  {**good, 'planId': 'sha256:' + '0' * 64},
                  {**good, 'goals': [None]},
                  {**good, 'goals': [{**good['goals'][0], 'termDigest': 'sha256:' + '0' * 64}]},
                  {**good, 'goals': [{**good['goals'][0], 'result': {'status': 'rejected'}}]}):
        calls = _replay_hook(monkeypatch)
        result = check_rational_branch_probe(req, plan['planId'], terms, cached_result=cache)
        assert calls, 'invalid cache was treated as accepted evidence'
        assert result['status'] == 'checked-rational-branch'


@pytest.mark.parametrize('stop', ['timeout', 'memory-limit', 'output-limit'])
def test_worker_stops_never_publish_checked_support(monkeypatch, stop):
    req = request()
    plan = _plan(monkeypatch, req)
    _replay_hook(monkeypatch, status='incomplete', code=stop)
    result = check_rational_branch_probe(req, plan['planId'], _terms(plan))
    assert result['status'] == 'incomplete'
    assert result.get('reason') == stop
    _assert_no_support(result)


def test_unsupported_regeneration_never_publishes_checked_support(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    monkeypatch.setattr(route, '_preflight_workspace',
        lambda *_args, **_kwargs: {'schema': 'ladon-rational-branch-plan-v1',
            'status': 'unsupported', 'reason': 'mathlib-unavailable', 'goals': [],
            'generatedGoalIdentities': [], 'checkedSupport': None, 'receipt': None})
    result = check_rational_branch_probe(req, plan['planId'], _terms(plan))
    assert result['status'] == 'unsupported'
    _assert_no_support(result)


@pytest.mark.parametrize('worker_status,raw_status', [
    ('rejected', 'accepted'), ('completed', 'rejected'), ('incomplete', 'accepted'),
])
def test_rejected_or_incomplete_checks_publish_no_support(monkeypatch, worker_status, raw_status):
    req = request()
    plan = _plan(monkeypatch, req)
    _replay_hook(monkeypatch, status=worker_status, raw_status=raw_status)
    result = check_rational_branch_probe(req, plan['planId'], _terms(plan))
    assert result['status'] in {'rejected', 'incomplete', 'unresolved'}
    _assert_no_support(result)


def test_accepted_worker_without_evidence_cannot_publish_support(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    _replay_hook(monkeypatch)
    replay = route._execute_job

    def strip_evidence(*args, **kwargs):
        checked = replay(*args, **kwargs)
        checked['result']['evidence']['processReceipts'] = []
        return checked

    monkeypatch.setattr(route, '_execute_job', strip_evidence)
    result = check_rational_branch_probe(req, plan['planId'], _terms(plan))
    assert result['status'] == 'rejected'
    assert result['reason'] == 'missing-check-run-evidence'
    _assert_no_support(result)


def test_changed_compiled_inventory_between_goals_is_stale(monkeypatch):
    req = request()
    plan = _plan(monkeypatch, req)
    _replay_hook(monkeypatch, compiled_inventory=lambda index: (
        [] if index == 1 else [{'module': 'Mathlib', 'digest': _sha('changed')}]))
    result = check_rational_branch_probe(req, plan['planId'], _terms(plan))
    assert result['status'] == 'stale-input'
    assert result['reason'] == 'compiled-inventory-changed-during-check'
    _assert_no_support(result)


@pytest.mark.skipif(not os.environ.get('LADON_RUN_SLOW_TESTS'),
                    reason='set LADON_RUN_SLOW_TESTS=1 to run local Mathlib integration')
def test_local_mathlib_generated_propositions_replay_without_network(monkeypatch):
    if not (LEAN_ROOT / '.lake').is_dir() or not (LEAN_ROOT / 'lean-toolchain').is_file():
        pytest.skip('pinned local Mathlib workspace unavailable')
    req = request()
    req['deadlineMonotonic'] = time.monotonic() + 300
    req['limits'] = {'timeout_seconds': 120, 'max_output_bytes': 8 * 1024 * 1024,
                     'max_rss_bytes': 12 * 1024**3}
    plan = plan_rational_branch_probe(req)
    if plan['status'] != 'planned':
        pytest.skip(f'local plan preflight unavailable: {plan.get("status")}')
    result = check_rational_branch_probe(req, plan['planId'], _terms(plan))
    assert result['status'] == 'checked-rational-branch', result
    assert result['receipt']['workspaceIdentity'] == plan['workspaceIdentity']
    assert all(goal['status'] == 'checked-support' for goal in result['goals'])
    assert len(result['artifacts']) == len(plan['goals'])
    assert len(result['receipt']['checkRunRefs']) == len(plan['goals'])
