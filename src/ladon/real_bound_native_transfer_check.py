"""Source-derived requests for conditional composition of two guarded transfers."""

import hashlib
import tempfile
from pathlib import Path

from ladon.real_bound_admission_check import _validate_terms
from ladon.real_bound_native_analysis import _deadline, _remaining
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_plan import validate_real_plan
from ladon.real_bound_native_relation_history import _same_context
from ladon.real_bound_native_relation_worker import _relation_goal
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

DIRECTORY = Path(__file__).parent / 'lean'
COMPOSITION_SOURCE = DIRECTORY / 'LadonRealBoundComposition.lean'
TRANSFER_SOURCE = DIRECTORY / 'LadonRealBoundTransfer.lean'


def _layout(plan):
    candidate = plan['bindingPlan']['observation']['candidate']
    binders = [row['binderId'] for row in candidate['telescope']]
    roles = [binders.index(candidate['roles'][name]) for name in ('order', 'function', 'set', 'bound', 'constant')]
    roles.append(binders.index(candidate['guards']['boundNonnegative']))
    kinds = [(row['quantifier'], row['binderInfo']) for row in candidate['telescope']]
    return roles, kinds


def transfer_candidate(left, right):
    a, b = [p['request']['plan'] for p in (left, right)]
    if not _same_context(a, b) or left['sourceText'] != right['sourceText']:
        return 'real-transfer-source-context-mismatch'
    if _layout(a) != _layout(b):
        return 'real-transfer-context-layout-mismatch'
    return None


def transfer_request(left, right, terms):
    from ladon.proof_contract_source import snapshot_identity

    if not isinstance(terms, list) or len(terms) != 2:
        raise ValueError('transfer requires two ordered admission proof dictionaries')
    for plan, proof in zip((left, right), terms, strict=True):
        _validate_terms(plan, proof)
    if _layout(left) != _layout(right):
        raise ValueError('transfer role and binder layouts differ')
    roles, _kinds = _layout(left)
    arguments = _relation_goal(left, right).removeprefix('ladon_real_bound_relation% ')
    losses = [p['bindingPlan']['observation']['candidate']['loss'] for p in (left, right)]
    arguments += f" [{','.join(map(str, roles))}] {losses[0]} {losses[1]}"
    goal = 'ladon_real_bound_compose% ' + arguments
    lines = ['by']
    for index, (plan, proof) in enumerate(zip((left, right), terms, strict=True)):
        for name, key, goal_index in [('admission', 'predicate-admission', 0), ('scalar', 'scalar-semantics', 1)]:
            lines.append(f"  have {name}{index} : ({plan['goals'][goal_index]['proposition']}) := ({proof[key]})")
    lines.append(f'  exact ladon_real_bound_compose_proof% {arguments} scalar0 scalar1')
    request = {'leftPlanId': left['planId'], 'rightPlanId': right['planId'], 'terms': terms,
               'goal': {'proposition': goal, 'sha256': 'sha256:' + hashlib.sha256(goal.encode()).hexdigest()},
               'term': '\n'.join(lines)}
    request['requestId'] = snapshot_identity(request)
    return request


def source_prefix(plan):
    helper = 'LadonRealBoundDerivative' if 'derivativeProfile' in plan['bindingPlan'] else 'LadonRealBoundBinding'
    return f'import {helper}\nimport LadonRealBoundScalars\nimport LadonRealBoundTransfer\n'.encode()


def check_transfer_relation(root, left, right, terms, *, timeout_seconds=600):
    from ladon.proof_contract_obligation_supervision import _execute_job

    deadline = _deadline(timeout_seconds)
    for plan in (left, right):
        validate_real_plan(plan)
    request = transfer_request(left, right, terms)
    identity = native_checker_identity()
    bounds = {'timeout_seconds': _remaining(deadline), 'deadlineMonotonic': deadline,
              'max_output_bytes': 8 * 1024**2, 'max_rss_bytes': DEFAULT_MAX_RSS_BYTES}
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    with tempfile.TemporaryDirectory(prefix='ladon-real-transfer-') as workspace:
        job = {'version': 1, 'root': str(Path(root).resolve(strict=True)), 'workspace': workspace,
               'leftPlan': left, 'rightPlan': right, 'request': request,
               'deadlineMonotonic': deadline, 'checkerIdentity': identity}
        run = _execute_job(job, bounds, state, None, worker_module='ladon.real_bound_native_transfer_worker')
    if identity != native_checker_identity():
        raise ValueError('Real transfer checker changed during execution')
    return run
