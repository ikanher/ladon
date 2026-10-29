"""Fresh pointwise output weakening, with no inferred coefficient uniformity."""

from copy import deepcopy

from ladon import real_bound_native_production as production_api
from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_native_analysis import (
    _bound_inputs,
    _contract_ref,
    _deadline,
    _fresh_check_evidence,
    _remaining,
)
from ladon.real_bound_native_analysis_bundle import _semantic_owner
from ladon.real_bound_native_coefficient_check import check_coefficient_relation
from ladon.real_bound_native_coefficient_evidence import checked_coefficient_evidence

SCHEMA = 'ladon-real-bound-coefficient-analysis-v1'


class _AdmissionIncomplete(Exception):
    def __init__(self, run):
        super().__init__('fresh Real coefficient admission is incomplete')
        self.run = run


def _fresh(production, root, timeout_seconds):
    fresh = production_api.replay_real_bound(production, root, timeout_seconds=timeout_seconds)
    if fresh.get('status') != 'admitted' or fresh.get('authority') != 'fresh-lean-check':
        raise _AdmissionIncomplete(fresh.get('check'))
    # Full evidence reconstruction is mandatory; a status flag is insufficient.
    production_api._verify_production(fresh)
    return fresh


def accepted_coefficient_run(run, production):
    """Validate a newly executed worker response; never substitute saved history."""
    try:
        checked_coefficient_evidence(production, run)
        return True
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError):
        return False


def _admit(production, root, deadline):
    _remaining(deadline)
    production_api._verify_production(production)
    _remaining(deadline)
    production_api._current_source(production, root)
    fresh = _fresh(production, root, _remaining(deadline))
    if _semantic_owner(production) != _semantic_owner(fresh):
        raise ValueError('coefficient replay substituted the exact owner')
    return fresh


def check_coefficient_implication(production, root, *, timeout_seconds=600):
    """Check a conditional law over the original source data and a new bound L."""
    return _coefficient_run(production, root, timeout_seconds=timeout_seconds)[0]


def _coefficient_run(production, root, *, timeout_seconds=600):
    deadline = _deadline(timeout_seconds)
    _bound_inputs([production])
    fresh, run, residual, admission_run = None, None, None, None
    try:
        fresh = _admit(production, root, deadline)
        admission_run = fresh.get('check')
        run = check_coefficient_relation(root, fresh['request']['plan'], fresh['request']['terms'],
                                         timeout_seconds=_remaining(deadline))
        if not accepted_coefficient_run(run, fresh):
            residual = 'real-coefficient-lean-check-unaccepted'
        _remaining(deadline)
        production_api._current_source(fresh, root)
        _remaining(deadline)
    except TimeoutError:
        residual = 'real-coefficient-shared-deadline-expired'
    except _AdmissionIncomplete as error:
        admission_run = error.run
        residual = 'real-coefficient-admission-incomplete'
    result = _result(fresh, run, residual, admission_run)
    try:
        _remaining(deadline)
    except TimeoutError:
        result = _result(fresh, run, 'real-coefficient-shared-deadline-expired', admission_run)
    return result, fresh


def _diagnostic(run):
    if not isinstance(run, dict):
        return None
    inner = run.get('result')
    return run.get('diagnostic') or (inner.get('diagnostic') if isinstance(inner, dict) else None)


def _result(fresh, run, residual, admission_run):
    result = {'schema': SCHEMA, 'status': 'resolved' if residual is None else 'unresolved',
              'relation': 'output-coefficient-implies' if residual is None else None,
              'rule': 'coefficient-mono-v1' if residual is None else None,
              'scope': 'pointwise-fixed-output-context',
              'inputContractRef': _contract_ref(fresh) if fresh is not None else None,
              'freshCheckEvidence': _fresh_check_evidence(fresh) if fresh is not None else [],
              'admissionCheckRun': deepcopy(admission_run),
              'diagnostic': _diagnostic(run) or _diagnostic(admission_run),
              'relationCheckRun': deepcopy(run), 'residuals': [] if residual is None else [{'code': residual}],
              'authority': 'fresh-source-predicate-scalar-and-coefficient-checks' if residual is None else 'none',
              'sourceTheoremProof': 'not-checked', 'coefficientUniformity': 'not-inferred',
              'paperNormBridge': 'unresolved', 'mathematicalFalsity': 'not-established',
              'limitations': ['conditional-output-predicate-implication-only', 'source-theorem-proof-not-checked',
                              'coefficient-uniformity-not-inferred', 'paper-norm-bridge-unresolved',
                              'not-persisted-as-a-native-analysis']}
    result['analysisId'] = snapshot_identity(result)
    return result
