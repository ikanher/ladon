"""Supervised exact source-bound prefix implications with replayable law terms."""

import hashlib
import tempfile
from pathlib import Path

from ladon.real_bound_native_analysis import _deadline, _remaining
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_plan import validate_real_plan
from ladon.real_bound_native_relation_worker import _relation_goal
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

PREFIX_SOURCE = Path(__file__).parent / 'lean/LadonRealBoundPrefix.lean'


def prefix_request(stronger, weaker, admission_term):
    from ladon.proof_contract_source import snapshot_identity

    if not isinstance(admission_term, str) or not admission_term.strip() or len(admission_term.encode()) > 65536:
        raise ValueError('prefix admission requires a bounded proof term')
    a = stronger['bindingPlan']['observation']['candidate']
    b = weaker['bindingPlan']['observation']['candidate']
    index = [row['binderId'] for row in a['telescope']].index(a['roles']['order'])
    arguments = _relation_goal(stronger, weaker).removeprefix('ladon_real_bound_relation% ')
    arguments += f" {index} {a['loss']} {b['loss']}"
    goal = 'ladon_real_bound_prefix% ' + arguments
    obligation = weaker['goals'][0]['proposition']
    term = (f'by\n  have admitted : ({obligation}) := ({admission_term})\n'
            f'  exact ladon_real_bound_prefix_proof% {arguments} admitted')
    request = {'strongerPlanId': stronger['planId'], 'weakerPlanId': weaker['planId'],
               'goal': {'proposition': goal, 'sha256': 'sha256:' + hashlib.sha256(goal.encode()).hexdigest()},
               'term': term, 'admissionTerm': admission_term}
    request['requestId'] = snapshot_identity(request)
    return request


def check_prefix_relation(root, stronger, weaker, admission_term, *, timeout_seconds=600):
    from ladon.proof_contract_obligation_supervision import _execute_job

    deadline = _deadline(timeout_seconds)
    validate_real_plan(stronger)
    validate_real_plan(weaker)
    request = prefix_request(stronger, weaker, admission_term)
    identity = native_checker_identity()
    bounds = {'timeout_seconds': _remaining(deadline), 'deadlineMonotonic': deadline,
              'max_output_bytes': 8 * 1024**2, 'max_rss_bytes': DEFAULT_MAX_RSS_BYTES}
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    with tempfile.TemporaryDirectory(prefix='ladon-real-prefix-') as workspace:
        job = {'version': 1, 'root': str(Path(root).resolve(strict=True)), 'workspace': workspace,
               'strongerPlan': stronger, 'weakerPlan': weaker, 'request': request,
               'deadlineMonotonic': deadline, 'checkerIdentity': identity}
        run = _execute_job(job, bounds, state, None, worker_module='ladon.real_bound_native_prefix_worker')
    if identity != native_checker_identity():
        raise ValueError('Real prefix checker changed during execution')
    return run


def source_prefix(plan):
    helper = 'LadonRealBoundDerivative' if 'derivativeProfile' in plan['bindingPlan'] else 'LadonRealBoundBinding'
    return f'import {helper}\nimport LadonRealBoundScalars\nimport LadonRealBoundPrefix\n'.encode()
