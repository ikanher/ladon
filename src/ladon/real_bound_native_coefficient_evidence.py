"""Validate complete coefficient receipts; saved consistency is not fresh checking."""

import hashlib

from ladon.correspondence_check import _generated_prelude
from ladon.proof_contract_payloads import closed
from ladon.proofir_v3 import _digest
from ladon.real_bound_admission_worker import _accepted
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_coefficient_check import coefficient_request, source_prefix
from ladon.real_bound_native_evidence import _deep_evidence, _receipts
from ladon.real_bound_native_relation_history import _run_envelope


def checked_coefficient_evidence(production, run):
    """Require the current exact owner, proof terms, goal, capture and receipts."""
    result = recorded_coefficient_evidence(production, run)
    if result['checkerIdentity'] != native_checker_identity():
        raise ValueError('coefficient evidence uses a different current checker')
    return result


def recorded_coefficient_evidence(production, run):
    """Reconstruct recorded evidence without authenticating its origin or freshness."""
    _run_envelope(run)
    result = run['result']
    closed(result, {'schema', 'status', 'request', 'checkerIdentity', 'compilations', 'check'},
           'Real coefficient result')
    plan = production['request']['plan']
    expected = coefficient_request(plan, production['request']['terms'])
    identity = result['checkerIdentity']
    if (result['schema'] != 'ladon-real-bound-coefficient-check-v1' or result['status'] != 'checked'
            or result['request'] != expected or not _digest(identity)
            or production['check']['result']['checkerIdentity'] != identity
            or not _accepted(result['check'])):
        raise ValueError('coefficient proof differs from admitted owner or current checker')
    count = 5 if 'derivativeProfile' in plan['bindingPlan'] else 4
    if not isinstance(result['compilations'], list) or len(result['compilations']) != count:
        raise ValueError('coefficient proof requires every helper compilation')
    _receipts(result['compilations'])
    _deep_evidence({'term': expected['term'], 'evidence': result['check']})
    _source_capture(result['check'], plan, production['sourceText'], expected['goal']['proposition'])
    return result


def _source_capture(check, plan, text, goal):
    prelude = _generated_prelude(None, source_prefix(plan) + text.encode(), {}, goal)
    generated = (prelude + f'\nexample : {goal} := by\n  skip\n').encode()
    source = check['capture']['capture']['source']
    if (source['digest'] != 'sha256:' + hashlib.sha256(generated).hexdigest()
            or source['byteLength'] != len(generated)):
        raise ValueError('coefficient capture differs from exact copied source and goal')
