"""Fresh input-prefix weakening, separate from equivalence or theorem validity."""

from copy import deepcopy

from ladon import real_bound_native_production as production_api
from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_native_analysis import (
    _bound_inputs,
    _context,
    _contract_ref,
    _deadline,
    _fresh,
    _remaining,
)
from ladon.real_bound_native_analysis_bundle import _semantic_owner
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_prefix_check import check_prefix_relation
from ladon.real_bound_native_relation_worker import _same_source

SCHEMA = 'ladon-real-bound-prefix-analysis-v1'


def _prefix_context(production):
    context = _context(production)
    record = production['artifacts'][-1]['payload']['record']
    # Admission reconstruction binds this precise terminal premise to the source.
    if record['origins']['input'] != record['telescope'][-1]['originPath'] + '/forallE/type':
        raise ValueError('prefix rule requires the exact terminal input premise')
    context.pop('loss')
    context['application']['input'].pop('orderRef')
    context['telescope'][-1]['type'] = {'role': 'related-input-premise'}
    return context


def prefix_candidate(stronger, weaker):
    """Return a missing prerequisite; matching here is never a checked rule."""
    if _prefix_context(stronger) != _prefix_context(weaker):
        return 'real-prefix-context-mismatch'
    a = stronger['artifacts'][-1]['payload']['record']['loss']
    b = weaker['artifacts'][-1]['payload']['record']['loss']
    if b > a:
        return 'real-prefix-direction-unproved'
    return None


def accepted_prefix_run(run, stronger, weaker):
    """Check a fresh worker response; never use current identity to erase history."""
    from ladon.real_bound_native_prefix_history import checked_prefix_evidence

    try:
        evidence = checked_prefix_evidence([stronger, weaker], run)
        return evidence['checkerIdentity'] == native_checker_identity()
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False


def _fresh_inputs(stronger, weaker, root, deadline):
    values = [stronger, weaker]
    _bound_inputs(values)
    for value in values:
        production_api._verify_production(value)
        production_api._current_source(value, root)
    fresh = [_fresh(value, root, _remaining(deadline)) for value in values]
    for old, new in zip(values, fresh, strict=True):
        if _semantic_owner(old) != _semantic_owner(new):
            raise ValueError('prefix replay substituted an exact owner')
    return fresh


def _prefix_run(stronger, weaker, root, *, timeout_seconds=600):
    """Replay both owners and prove only the requested stronger-input implication."""
    deadline = _deadline(timeout_seconds)
    stronger, weaker = _fresh_inputs(stronger, weaker, root, deadline)
    residual = prefix_candidate(stronger, weaker)
    plans = [value['request']['plan'] for value in (stronger, weaker)]
    if not _same_source(*plans):
        residual = 'real-prefix-source-context-mismatch'
    run = None
    if residual is None:
        run = check_prefix_relation(root, *plans, weaker['request']['terms']['predicate-admission'],
                                    timeout_seconds=_remaining(deadline))
        if not accepted_prefix_run(run, stronger, weaker):
            residual = 'real-prefix-lean-check-unaccepted'
    for value in (stronger, weaker):
        production_api._current_source(value, root)
    return _result(stronger, weaker, residual, run), [stronger, weaker]


def check_prefix_implication(stronger, weaker, root, *, timeout_seconds=600):
    """Replay both admissions and check the ordered input-predicate implication."""
    result, _fresh_owners = _prefix_run(stronger, weaker, root, timeout_seconds=timeout_seconds)
    return result


def _result(stronger, weaker, residual, run):
    result = {'schema': SCHEMA, 'status': 'resolved' if residual is None else 'unresolved',
              'relation': 'input-prefix-implies' if residual is None else None,
              'rule': 'order-prefix-v1' if residual is None else None,
              'strongerInputContractRef': _contract_ref(stronger), 'weakerInputContractRef': _contract_ref(weaker),
              'relationCheckRun': deepcopy(run), 'residuals': [] if residual is None else [{'code': residual}],
              'authority': ('fresh-source-predicate-scalar-and-prefix-checks' if residual is None
                            else 'fresh-source-predicate-and-scalar-checks'),
              'sourceTheoremProof': 'not-checked', 'paperNormBridge': 'unresolved',
              'mathematicalFalsity': 'not-established',
              'limitations': ['input-predicate-implication-only', 'source-theorem-proof-not-checked',
                              'paper-norm-bridge-unresolved', 'not-persisted-as-a-native-analysis']}
    result['analysisId'] = snapshot_identity(result)
    return result
