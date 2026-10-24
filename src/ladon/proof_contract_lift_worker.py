"""Fresh native checks for the source-owned Nat/rational lift operation."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

from .proof_contract_io import _decode
from .proof_contract_payloads import closed

MAX_BYTES = 8 * 1024**2


def _compute(job):
    from .proof_contract_lift_check import _owned_plan

    closed(job, {'version', 'operation', 'request', 'expectedPlanId', 'term',
                 'attemptId', 'checkerIdentity'}, 'lift worker job')
    if job['version'] != 1 or job['operation'] != 'check-nat-rational-lift':
        raise ValueError('unknown lift worker operation')
    if type(job['attemptId']) is not str or not re.fullmatch('[0-9a-f]{32}', job['attemptId']):
        raise ValueError('invalid lift attempt identity')
    _, _, _, request, plan, bounds = _owned_plan(job['request'], job['expectedPlanId'], job['term'])
    source = _source(Path(request['repoRoot']).resolve(strict=True), plan['interpretation']['source'])
    if plan['status'] != 'planned':
        return _failure(job, plan, source, 'unsupported', 'unsupported-profile', plan['reason'])
    try:
        return _check_native(job, request, plan, source, bounds)
    except (ValueError, TypeError, KeyError, OSError) as error:
        return _checking_failure(job, plan, source, error)


def _checking_failure(job, plan, source, error):
    message = str(error)
    if 'changed' in message or 'stale' in message:
        return _failure(job, plan, source, 'stale-input', 'stale-input', message)
    for code in ('semantic-goal-mismatch', 'proof-rejected', 'trust-rejected'):
        if code in message:
            return _failure(job, plan, source, 'rejected', code, message)
    return _failure(job, plan, source, 'unresolved', 'native-check-unresolved', message)


def _check_native(job, request, plan, source, bounds):
    from .correspondence_check import _check_goal
    from .proof_contract_lift_check import _validate_native_evidence
    from .proof_slice import pinned_toolchain

    root = Path(request['repoRoot']).resolve(strict=True)
    context = pinned_toolchain(root)
    if _checker_identity() != job['checkerIdentity']:
        raise ValueError('checker identity changed before native stage')
    from ._proof_contract_goal_scratch import ENV_WORKSPACE
    lease = os.environ.get(ENV_WORKSPACE)
    actual = _check_goal(plan['goal'], job['term'], root, source, {}, context)
    failure = _actual_failure(actual, bounds)
    if failure is not None:
        return _failure(job, plan, source, *failure)
    capture = actual['capture']['capture']
    inventory = capture['environment']['compiledInventory']
    if not _canonical_imports_covered(inventory):
        return _failure(job, plan, source, 'unsupported', 'canonical-environment-coverage',
                        'Canonical imports are outside the verified actual import closure.')
    if lease is not None:
        os.environ[ENV_WORKSPACE] = lease
    canonical, error = _observe_canonical(plan, root, context, bounds)
    if error is not None:
        return _failure(job, plan, source, *error)
    native = _native_result(job, plan, source, actual, canonical, context)
    _validate_native_evidence(native, job)
    _verify_inventory(inventory)
    _reverify_inputs(root, request, source, context, job['checkerIdentity'])
    return native


def _actual_failure(actual, bounds):
    from .proof_contract_bridge import _resource_stop

    stopped = _resource_stop(actual, bounds)
    if stopped:
        return 'incomplete', stopped['code'], stopped['message']
    completion = actual.get('completion') or {}
    if completion.get('status') == 'trust-rejected':
        return 'rejected', 'trust-rejected', 'Independent proof replay found disallowed axioms.'
    if completion.get('status') == 'rejected':
        return 'rejected', 'proof-rejected', 'The supplied proof did not complete the generated goal.'
    if actual.get('status') != 'supported':
        return 'unresolved', 'native-check-unresolved', 'Native capture or completion did not finish.'
    return None


def _canonical_imports_covered(inventory):
    names = {row['module'] for row in inventory['modules']}
    return {'Lean', 'Init.Data.Rat.Lemmas'} <= names


def _observe_canonical(plan, root, context, bounds):
    from .correspondence_check import (
        _actual_typed_subject,
        _generated_prelude,
        _goal_temporary_directory,
        _write_goal_source,
    )
    from .process_supervisor import run_bounded_target_process
    from .semantic_lean_execution import prepare_direct_lean_execution

    remaining = min(60, bounds['deadlineMonotonic'] - time.monotonic())
    if remaining <= 0:
        return None, ('incomplete', 'timeout', 'Shared lift-check deadline expired.')
    with _goal_temporary_directory(root / '.ladon/correspondence') as (temporary, owner):
        path = temporary / 'LadonCorrespondence.lean'
        text = _generated_prelude(None, _canonical_prelude(plan['interpretation']), {}, plan['goal'])
        _write_goal_source(path, text, owner)
        execution = prepare_direct_lean_execution(root, None, context, require_compiled_module=False)
        process = run_bounded_target_process([*execution.command, str(path)], cwd=root,
            env=execution.environment, timeout_seconds=remaining,
            max_output_bytes=bounds['max_output_bytes'], max_rss_bytes=bounds['max_rss_bytes'])
        failure = _canonical_failure(process, bounds)
        if failure:
            return None, failure
        try:
            return _actual_typed_subject(process)['subject']['structural'], None
        except (ValueError, TypeError, KeyError):
            return None, ('unsupported', 'unsupported-canonical-goal', 'Missing canonical typed observation.')


def _canonical_failure(process, bounds):
    from dataclasses import asdict

    from .proof_contract_bridge import _resource_stop
    stopped = _resource_stop(asdict(process), bounds)
    if stopped:
        return 'incomplete', stopped['code'], stopped['message']
    if not process.succeeded:
        return 'unsupported', 'unsupported-canonical-goal', 'Canonical clean Rat goal could not be elaborated.'
    return None


def _canonical_prelude(interpretation):
    # Opaque names are only for type observation. The caller term is checked in
    # the actual source; these dummy definitions never reach that proof stage.
    claim, predicate = interpretation['formalClaim'], interpretation['formalPredicate']
    return ('import Init.Data.Rat.Lemmas\n'
            f'opaque {claim} : Prop := True\n'
            f'opaque {predicate} : Nat -> Prop := fun _ => True\n').encode()


def _native_result(job, plan, source, actual, canonical, context):
    capture = actual['capture']['capture']
    evidence = {'capture': capture, 'completion': actual['completion'],
                'canonicalTypedSubject': canonical,
                'actualTypedSubject': actual['typedSubject']['subject']['structural'],
                'compiledInventory': capture['environment']['compiledInventory'],
                'environmentRef': context.context_identity, 'executableIdentity': context.lean_identity}
    return {'status': 'completed', 'planId': plan['planId'], 'witness': plan['witness'],
            'binding': _binding(job, plan, source), 'nativeEvidence': evidence}


def _verify_inventory(inventory):
    from ._source_goal_inventory import verify_inventory
    rows = inventory['modules']
    files = {row['module']: Path(row['path']) for row in rows}
    environment = {'payload': {'compiledModules': [
        {'module': row['module'], 'digest': row['digest']} for row in rows]}}
    verify_inventory(files, environment, inventory)


def _reverify_inputs(root, request, source, context, checker):
    from .lean_toolchain import verify_toolchain_identities
    from .proof_slice import pinned_toolchain
    verify_toolchain_identities(context)
    if pinned_toolchain(root).context_identity != context.context_identity:
        raise ValueError('pinned context changed during native check')
    if _source(root, request['interpretation']['source']) != source:
        raise ValueError('source bytes changed during native check')
    if _checker_identity() != checker:
        raise ValueError('checker implementation changed during native check')


def _binding(job, plan, source):
    request = job['request']
    return {'attemptId': job['attemptId'], 'checkerIdentity': job['checkerIdentity'],
            'planId': plan['planId'], 'goal': request['goal'], 'witness': plan['witness'],
            'interpretation': request['interpretation'], 'mode': request['mode'],
            'termDigest': _sha((job['term'] or '').encode()),
            'root': str(Path(request['repoRoot']).resolve(strict=True)),
            'source': request['interpretation']['source'], 'sourceDigest': _sha(source)}


def _source(root, reference):
    from .source_association_io import _read_regular, _safe_repo_file
    data = _read_regular(_safe_repo_file(root, reference['path']), MAX_BYTES)
    if hashlib.sha256(data).hexdigest() != reference['sha256']:
        raise ValueError('source digest changed')
    data.decode('utf-8')
    return data


def _failure(job, plan, source, status, code, message):
    return {'status': status, 'planId': plan['planId'], 'witness': plan['witness'],
            'binding': _binding(job, plan, source), 'nativeEvidence': None,
            'diagnosticCode': code, 'diagnostic': message}


def _checker_identity():
    from .correspondence_implementation import implementation_digest
    base = Path(__file__).parent
    names = ('proof_contract_lift_check.py', 'proof_contract_lift_worker.py',
             'proof_contract_lift_goals.py', '_proof_contract_lift_evidence.py',
             'proof_contract_obligation_supervision.py',
             'proof_contract_refinement.py', 'rational_witness.py', 'resource_limits.py',
             'proof_contract_source_obligations.py', 'proof_contract_io.py', 'proof_contract_payloads.py')
    rows = {name: _sha((base / name).read_bytes()) for name in names}
    rows['correspondence'] = implementation_digest()
    return _sha(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode())


def _sha(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def _response(result):
    body = {'status': 'completed', 'result': result, 'diagnostic': None}
    encoded = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    if len(encoded.encode()) > MAX_BYTES:
        result = {**result, 'status': 'incomplete', 'nativeEvidence': None,
                  'diagnosticCode': 'output-limit', 'diagnostic': 'Native lift evidence exceeds 8 MiB.'}
        body['result'] = result
        encoded = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return encoded


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('worker input exceeds 8 MiB')
        sys.stdout.write(_response(_compute(_decode(raw))))
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, OverflowError,
            RecursionError, UnicodeError) as error:
        sys.stdout.write(json.dumps({'status': 'rejected', 'result': None,
                                     'diagnostic': str(error)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
