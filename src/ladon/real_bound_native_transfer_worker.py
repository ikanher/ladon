"""Privately check the exact conditional transfer goal from two live declarations."""

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
from ladon.real_bound_native_coefficient_worker import _limited
from ladon.real_bound_native_plan import validate_real_plan
from ladon.real_bound_native_relation_history import _same_context
from ladon.real_bound_native_transfer_check import (
    COMPOSITION_SOURCE,
    TRANSFER_SOURCE,
    source_prefix,
    transfer_request,
)
from ladon.real_bound_native_worker import _compile_all, _compile_helper, _prepare


def _verify_helpers(context):
    if any((lib / (name.stem + '.olean')).exists() for lib in context.library_roots
           for name in (COMPOSITION_SOURCE, TRANSFER_SOURCE)):
        raise ValueError('reserved transfer helper already exists')


def _prepare_pair(job):
    closed(job, {'version', 'root', 'workspace', 'leftPlan', 'rightPlan', 'request',
                 'deadlineMonotonic', 'checkerIdentity'}, 'Real transfer job')
    if job['version'] != 1 or job['checkerIdentity'] != native_checker_identity():
        raise ValueError('stale transfer checker')
    a, b = job['leftPlan'], job['rightPlan']
    for plan in (a, b):
        validate_real_plan(plan)
    request = transfer_request(a, b, job['request']['terms'])
    if request != job['request'] or not _same_context(a, b):
        raise ValueError('transfer request or source context differs')
    right_root, right_source, context = verify_binding_source(job['root'], b['bindingPlan'])
    _verify_helpers(context)
    native = {**job, 'plan': a}
    root, source, workspace, base = _prepare(native)
    if root != right_root or source != right_source:
        raise ValueError('transfer owners differ in copied source')
    return root, source, workspace, base, native, request


def _check(job):
    root, source, workspace, base, native, request = _prepare_pair(job)
    result = {'schema': 'ladon-real-bound-transfer-check-v1', 'status': 'unresolved',
              'request': request, 'checkerIdentity': job['checkerIdentity'], 'compilations': [], 'check': None}
    if not _compile_all(native, base, workspace, result):
        return _limited(result)
    for path in (COMPOSITION_SOURCE, TRANSFER_SOURCE):
        helper_job = {**job, 'plan': {'sourceDigest': 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()}}
        run = _compile_helper(workspace, helper_job, path, 'sourceDigest')
        result['compilations'].append(asdict(run))
        if not run.succeeded:
            return _limited(result)
    evidence = _check_goal(request['goal']['proposition'], request['term'], workspace,
                           source_prefix(job['leftPlan']) + source, {}, pinned_toolchain(workspace))
    result['check'] = evidence
    if _accepted(evidence):
        _verify_inventory(_inventory(evidence))
        result['status'] = 'checked'
    for plan in (job['leftPlan'], job['rightPlan']):
        verify_binding_source(root, plan['bindingPlan'])
    if job['checkerIdentity'] != native_checker_identity():
        raise ValueError('transfer checker changed during execution')
    return result


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('transfer input exceeds 8 MiB')
        result = _check(_decode(raw))
        encoded = json.dumps({'status': 'completed', 'result': result, 'diagnostic': None})
        if len(encoded.encode()) > MAX_BYTES:
            raise ValueError('transfer output exceeds 8 MiB')
        print(encoded)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        print(json.dumps({'status': 'rejected', 'result': None, 'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
