"""Bounded source-derived coefficient law requests and supervised execution."""

import hashlib
import tempfile
from pathlib import Path

from ladon.real_bound_admission_check import _validate_terms
from ladon.real_bound_native_analysis import _deadline, _remaining
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_plan import validate_real_plan
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

COEFFICIENT_SOURCE = Path(__file__).parent / 'lean/LadonRealBoundCoefficient.lean'


def coefficient_request(plan, terms):
    from ladon.proof_contract_source import snapshot_identity

    _validate_terms(plan, terms)
    arguments = plan['goals'][1]['proposition'].removeprefix('ladon_scalar_admission% ')
    goal = 'ladon_real_bound_coefficient% ' + arguments
    predicate_term, scalar_term = terms['predicate-admission'], terms['scalar-semantics']
    term = (f"by\n  have admitted : ({plan['goals'][0]['proposition']}) := ({predicate_term})\n"
            f"  have scalars : ({plan['goals'][1]['proposition']}) := ({scalar_term})\n"
            f'  exact ladon_real_bound_coefficient_proof% {arguments} admitted scalars')
    request = {'planId': plan['planId'],
               'goal': {'proposition': goal, 'sha256': 'sha256:' + hashlib.sha256(goal.encode()).hexdigest()},
               'term': term, 'admissionTerm': predicate_term, 'scalarTerm': scalar_term}
    request['requestId'] = snapshot_identity(request)
    return request


def check_coefficient_relation(root, plan, terms, *, timeout_seconds=600):
    from ladon.proof_contract_obligation_supervision import _execute_job

    deadline = _deadline(timeout_seconds)
    validate_real_plan(plan)
    request = coefficient_request(plan, terms)
    identity = native_checker_identity()
    bounds = {'timeout_seconds': _remaining(deadline), 'deadlineMonotonic': deadline,
              'max_output_bytes': 8 * 1024**2, 'max_rss_bytes': DEFAULT_MAX_RSS_BYTES}
    state = {'receipt': None, 'inputDigest': None, 'bounds': None}
    with tempfile.TemporaryDirectory(prefix='ladon-real-coefficient-') as workspace:
        job = {'version': 1, 'root': str(Path(root).resolve(strict=True)), 'workspace': workspace,
               'plan': plan, 'request': request, 'deadlineMonotonic': deadline, 'checkerIdentity': identity}
        run = _execute_job(job, bounds, state, None, worker_module='ladon.real_bound_native_coefficient_worker')
    if identity != native_checker_identity():
        raise ValueError('Real coefficient checker changed during execution')
    return run


def source_prefix(plan):
    helper = 'LadonRealBoundDerivative' if 'derivativeProfile' in plan['bindingPlan'] else 'LadonRealBoundBinding'
    return f'import {helper}\nimport LadonRealBoundScalars\nimport LadonRealBoundCoefficient\n'.encode()
