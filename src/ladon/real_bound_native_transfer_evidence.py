"""Exact historical consistency for conditional transfer proofs, not authentication."""

import hashlib

from ladon.correspondence_check import _generated_prelude
from ladon.proof_contract_payloads import closed
from ladon.proofir_v3 import _digest
from ladon.real_bound_admission_worker import _accepted
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_evidence import _deep_evidence, _receipts
from ladon.real_bound_native_relation_history import _run_envelope
from ladon.real_bound_native_transfer_check import (
    source_prefix,
    transfer_candidate,
    transfer_request,
)


def recorded_transfer_evidence(productions, run):
    if not isinstance(productions, list) or len(productions) != 2:
        raise ValueError('transfer evidence requires two exact ordered owners')
    if transfer_candidate(*productions) is not None:
        raise ValueError('incompatible transfer source contexts or layouts')
    _run_envelope(run)
    result = run['result']
    closed(result, {'schema', 'status', 'request', 'checkerIdentity', 'compilations', 'check'}, 'transfer result')
    plans = [p['request']['plan'] for p in productions]
    expected = transfer_request(*plans, [p['request']['terms'] for p in productions])
    _check_result(result, expected, productions)
    _native_evidence(result, plans[0], productions[0]['sourceText'], expected)
    return result


def _check_result(result, expected, productions):
    identity = result['checkerIdentity']
    if (result['schema'] != 'ladon-real-bound-transfer-check-v1' or result['status'] != 'checked'
            or result['request'] != expected or not _digest(identity)
            or any(p['check']['result']['checkerIdentity'] != identity for p in productions)
            or not _accepted(result['check'])):
        raise ValueError('transfer proof differs from exact owners or recorded checker')


def _native_evidence(result, plan, text, expected):
    count = 6 if 'derivativeProfile' in plan['bindingPlan'] else 5
    if not isinstance(result['compilations'], list) or len(result['compilations']) != count:
        raise ValueError('transfer proof requires all helper compilations')
    _receipts(result['compilations'])
    _deep_evidence({'term': expected['term'], 'evidence': result['check']})
    goal = expected['goal']['proposition']
    prelude = _generated_prelude(None, source_prefix(plan) + text.encode(), {}, goal)
    generated = (prelude + f'\nexample : {goal} := by\n  skip\n').encode()
    source = result['check']['capture']['capture']['source']
    if (source['digest'] != 'sha256:' + hashlib.sha256(generated).hexdigest()
            or source['byteLength'] != len(generated)):
        raise ValueError('transfer capture differs from exact copied source and goal')


def accepted_transfer_run(run, productions):
    try:
        return recorded_transfer_evidence(productions, run)['checkerIdentity'] == native_checker_identity()
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError):
        return False
