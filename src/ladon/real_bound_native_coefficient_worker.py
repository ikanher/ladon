"""Check one pointwise coefficient implication in a private Lean context."""

import hashlib
import json
import sys
from dataclasses import asdict

from ladon.correspondence_check import _check_goal
from ladon.proof_contract_io import _decode
from ladon.proof_contract_payloads import closed
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_admission_worker import MAX_BYTES, _accepted, _inventory, _verify_inventory
from ladon.real_bound_binding_check import verify_binding_source
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_coefficient_check import (
    COEFFICIENT_SOURCE,
    coefficient_request,
    source_prefix,
)
from ladon.real_bound_native_plan import validate_real_plan
from ladon.real_bound_native_worker import _compile_all, _compile_helper, _prepare
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message


def _prepare_single(job):
    closed(job, {'version', 'root', 'workspace', 'plan', 'request', 'deadlineMonotonic', 'checkerIdentity'},
           'Real coefficient job')
    if job['version'] != 1 or job['checkerIdentity'] != native_checker_identity():
        raise ValueError('stale Real coefficient checker')
    plan = job['plan']
    validate_real_plan(plan)
    terms = {'predicate-admission': job['request']['admissionTerm'], 'scalar-semantics': job['request']['scalarTerm']}
    request = coefficient_request(plan, terms)
    if request != job['request']:
        raise ValueError('coefficient request differs from source-bound plan')
    root, source, context = verify_binding_source(job['root'], plan['bindingPlan'])
    if any((library / 'LadonRealBoundCoefficient.olean').exists() for library in context.library_roots):
        raise ValueError('reserved Real coefficient helper already exists')
    root, source, workspace, base_job = _prepare(job)
    return root, source, workspace, base_job, request


def _check(job):
    root, source, workspace, base_job, request = _prepare_single(job)
    result = {'schema': 'ladon-real-bound-coefficient-check-v1', 'status': 'unresolved',
              'request': request, 'checkerIdentity': job['checkerIdentity'], 'compilations': [], 'check': None}
    if not _compile_all(job, base_job, workspace, result):
        return _limited(result)
    helper_job = {**job, 'plan': {'coefficientSourceDigest': 'sha256:' + hashlib.sha256(COEFFICIENT_SOURCE.read_bytes()).hexdigest()}}
    compilation = _compile_helper(workspace, helper_job, COEFFICIENT_SOURCE, 'coefficientSourceDigest')
    result['compilations'].append(asdict(compilation))
    if not compilation.succeeded:
        return _limited(result)
    evidence = _check_goal(request['goal']['proposition'], request['term'], workspace,
                           source_prefix(job['plan']) + source, {}, pinned_toolchain(workspace))
    result['check'] = evidence
    if _accepted(evidence):
        _verify_inventory(_inventory(evidence))
        result['status'] = 'checked'
    verify_binding_source(root, job['plan']['bindingPlan'])
    if job['checkerIdentity'] != native_checker_identity():
        raise ValueError('Real coefficient checker changed during execution')
    return result


def _limited(result):
    if result['compilations'][-1]['memory_limited']:
        result['diagnostic'] = memory_limit_message(DEFAULT_MAX_RSS_BYTES,
                                                   result['compilations'][-1]['peak_rss_bytes'])
    return result


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Real coefficient input exceeds 8 MiB')
        result = _check(_decode(raw))
        encoded = json.dumps({'status': 'completed', 'result': result, 'diagnostic': None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError('Real coefficient output exceeds 8 MiB')
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({'status': 'rejected', 'result': None, 'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
