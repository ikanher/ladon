"""Check one source-derived input-prefix implication in a private Lean context."""

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
from ladon.real_bound_native_plan import validate_real_plan
from ladon.real_bound_native_prefix_check import PREFIX_SOURCE, prefix_request, source_prefix
from ladon.real_bound_native_relation_worker import _same_source
from ladon.real_bound_native_worker import _compile_all, _compile_helper, _prepare
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES, memory_limit_message


def _prepare_pair(job):
    closed(job, {'version', 'root', 'workspace', 'strongerPlan', 'weakerPlan', 'request',
                 'deadlineMonotonic', 'checkerIdentity'}, 'Real prefix job')
    if job['version'] != 1 or job['checkerIdentity'] != native_checker_identity():
        raise ValueError('stale Real prefix checker')
    stronger, weaker = job['strongerPlan'], job['weakerPlan']
    for plan in (stronger, weaker):
        validate_real_plan(plan)
    request = prefix_request(stronger, weaker, job['request']['admissionTerm'])
    if request != job['request'] or not _same_source(stronger, weaker):
        raise ValueError('prefix request or exact source context differs')
    strong_root, strong_source, strong_context = verify_binding_source(job['root'], stronger['bindingPlan'])
    native_job = {**job, 'plan': weaker}
    root, source, workspace, base_job = _prepare(native_job)
    if root != strong_root or source != strong_source:
        raise ValueError('prefix owners have different source bytes')
    if any((library / 'LadonRealBoundPrefix.olean').exists() for library in strong_context.library_roots):
        raise ValueError('reserved Real prefix helper already exists')
    return root, source, workspace, base_job, native_job, request


def _check(job):
    root, source, workspace, base_job, native_job, request = _prepare_pair(job)
    stronger, weaker = job['strongerPlan'], job['weakerPlan']
    result = {'schema': 'ladon-real-bound-prefix-check-v1', 'status': 'unresolved',
              'request': request, 'checkerIdentity': job['checkerIdentity'],
              'compilations': [], 'check': None}
    if not _compile_all(native_job, base_job, workspace, result):
        return _limited(result)
    helper_job = {**job, 'plan': {'prefixSourceDigest': 'sha256:' + hashlib.sha256(PREFIX_SOURCE.read_bytes()).hexdigest()}}
    compilation = _compile_helper(workspace, helper_job, PREFIX_SOURCE, 'prefixSourceDigest')
    result['compilations'].append(asdict(compilation))
    if not compilation.succeeded:
        return _limited(result)
    evidence = _check_goal(request['goal']['proposition'], request['term'], workspace,
                           source_prefix(weaker) + source, {}, pinned_toolchain(workspace))
    result['check'] = evidence
    if _accepted(evidence):
        _verify_inventory(_inventory(evidence))
        result['status'] = 'checked'
    for plan in (stronger, weaker):
        verify_binding_source(root, plan['bindingPlan'])
    if job['checkerIdentity'] != native_checker_identity():
        raise ValueError('Real prefix checker changed during execution')
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
            raise ValueError('Real prefix input exceeds 8 MiB')
        result = _check(_decode(raw))
        encoded = json.dumps({'status': 'completed', 'result': result, 'diagnostic': None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError('Real prefix output exceeds 8 MiB')
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({'status': 'rejected', 'result': None, 'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
