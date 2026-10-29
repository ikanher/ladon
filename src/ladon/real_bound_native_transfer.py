"""Fresh conditional composition; the source-shaped transfer premises remain assumed."""

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
from ladon.real_bound_native_coefficient import _AdmissionIncomplete, _diagnostic, _fresh
from ladon.real_bound_native_transfer_check import check_transfer_relation, transfer_candidate
from ladon.real_bound_native_transfer_evidence import accepted_transfer_run

SCHEMA = 'ladon-real-bound-transfer-analysis-v1'


def _admit(value, root, deadline):
    _remaining(deadline)
    production_api._verify_production(value)
    _remaining(deadline)
    production_api._current_source(value, root)
    fresh = _fresh(value, root, _remaining(deadline))
    if _semantic_owner(value) != _semantic_owner(fresh):
        raise ValueError('transfer replay substituted an exact owner')
    return fresh


def _transfer_run(left, right, root, *, timeout_seconds=600):
    deadline = _deadline(timeout_seconds)
    _bound_inputs([left, right])
    fresh, admissions, run, residual = [], [], None, None
    try:
        for value in (left, right):
            actual = _admit(value, root, deadline)
            fresh.append(actual)
            admissions.append(actual['check'])
        residual = transfer_candidate(*fresh)
        if residual is None:
            run = check_transfer_relation(root, *[p['request']['plan'] for p in fresh],
                [p['request']['terms'] for p in fresh], timeout_seconds=_remaining(deadline))
            if not accepted_transfer_run(run, fresh):
                residual = 'real-transfer-lean-check-unaccepted'
        for value in fresh:
            _remaining(deadline)
            production_api._current_source(value, root)
        _remaining(deadline)
    except TimeoutError:
        residual = 'real-transfer-shared-deadline-expired'
    except _AdmissionIncomplete as error:
        admissions.append(error.run)
        residual = 'real-transfer-admission-incomplete'
    result = _result(fresh, admissions, run, residual)
    try:
        _remaining(deadline)
    except TimeoutError:
        result = _result(fresh, admissions, run, 'real-transfer-shared-deadline-expired')
    return result, fresh


def check_transfer_composition(left, right, root, *, timeout_seconds=600):
    return _transfer_run(left, right, root, timeout_seconds=timeout_seconds)[0]


def _run_diagnostic(run, admissions):
    return _diagnostic(run) or next((_diagnostic(a) for a in reversed(admissions) if _diagnostic(a)), None)


def _result(fresh, admissions, run, residual):
    result = {'schema': SCHEMA, 'status': 'resolved' if residual is None else 'unresolved',
              'relation': 'conditional-transfer-composition' if residual is None else None,
              'rule': 'transfer-compose-v1' if residual is None else None,
              'scope': 'conditional-source-shaped-transfer-composition', 'transferPremises': 'assumed',
              'sourceTheoremProof': 'not-checked', 'coefficientUniformity': 'not-inferred',
              'paperNormBridge': 'unresolved', 'mathematicalFalsity': 'not-established',
              'contractRefs': [_contract_ref(p) for p in fresh],
              'freshCheckEvidence': [e for p in fresh for e in _fresh_check_evidence(p)],
              'admissionCheckRuns': deepcopy(admissions), 'relationCheckRun': deepcopy(run),
              'diagnostic': _run_diagnostic(run, admissions),
              'authority': 'fresh-source-predicate-scalar-and-transfer-checks' if residual is None else 'none',
              'residuals': [] if residual is None else [{'code': residual}],
              'limitations': ['transfer-premises-assumed', 'source-theorem-proof-not-checked',
                              'coefficient-uniformity-not-inferred', 'paper-norm-bridge-unresolved',
                              'not-persisted-as-a-native-analysis']}
    result['analysisId'] = snapshot_identity(result)
    return result
