"""Historical prefix proof consistency; stored evidence has no fresh authority."""

import hashlib

from ladon.correspondence_check import _generated_prelude
from ladon.proof_contract_payloads import closed
from ladon.proofir_v3 import _digest
from ladon.real_bound_admission_worker import _accepted
from ladon.real_bound_native_evidence import _deep_evidence, _receipts
from ladon.real_bound_native_prefix_check import prefix_request, source_prefix
from ladon.real_bound_native_relation_history import _run_envelope, _same_context


def checked_prefix_evidence(productions, run):
    """Reconstruct the saved ordered claim, never authenticate its recorded origin."""
    from ladon.real_bound_native_prefix import prefix_candidate

    if not isinstance(productions, list) or len(productions) != 2:
        raise ValueError('prefix evidence requires two ordered productions')
    try:
        stronger, weaker = productions
        plans = [row['request']['plan'] for row in productions]
        if (prefix_candidate(stronger, weaker) is not None or not _same_context(*plans)
                or stronger['sourceText'] != weaker['sourceText']):
            raise ValueError('recorded prefix has incompatible ordered owners')
        _run_envelope(run)
        _check_result(run['result'], stronger, weaker)
    except (TypeError, KeyError, IndexError, AttributeError, RecursionError) as error:
        raise ValueError('malformed recorded prefix evidence') from error
    return run['result']


def _check_result(result, stronger, weaker):
    closed(result, {'schema', 'status', 'request', 'checkerIdentity', 'compilations', 'check'},
           'Real prefix result')
    plan = weaker['request']['plan']
    expected = prefix_request(stronger['request']['plan'], plan,
                              weaker['request']['terms']['predicate-admission'])
    identity = result['checkerIdentity']
    if (result['schema'] != 'ladon-real-bound-prefix-check-v1' or result['status'] != 'checked'
            or result['request'] != expected or not _digest(identity)
            or any(row['check']['result']['checkerIdentity'] != identity for row in (stronger, weaker))
            or not _accepted(result['check'])):
        raise ValueError('recorded prefix proof differs from admitted owners or checker')
    _native_evidence(result, plan, expected, weaker['sourceText'])


def _native_evidence(result, plan, expected, source_text):
    count = 5 if 'derivativeProfile' in plan['bindingPlan'] else 4
    if not isinstance(result['compilations'], list) or len(result['compilations']) != count:
        raise ValueError('recorded prefix requires every helper compilation')
    _receipts(result['compilations'])
    _deep_evidence({'term': expected['term'], 'evidence': result['check']})
    prelude = _generated_prelude(None, source_prefix(plan) + source_text.encode(), {},
                                 expected['goal']['proposition'])
    generated = (prelude + f"\nexample : {expected['goal']['proposition']} := by\n  skip\n").encode()
    source = result['check']['capture']['capture']['source']
    if (source['digest'] != 'sha256:' + hashlib.sha256(generated).hexdigest()
            or source['byteLength'] != len(generated)):
        raise ValueError('recorded prefix capture differs from copied source and goal')
