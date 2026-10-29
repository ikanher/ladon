"""Sequential fresh admission and per-edge checks under one shared deadline."""

from ladon import real_bound_native_production as production_api
from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_native_analysis import _bound_inputs, _context, _fresh, _remaining
from ladon.real_bound_native_analysis_bundle import _semantic_owner
from ladon.real_bound_native_chain_artifacts import RULES
from ladon.real_bound_native_check import check_real_bound_relation, native_checker_identity
from ladon.real_bound_native_prefix import prefix_candidate
from ladon.real_bound_native_prefix_check import check_prefix_relation
from ladon.real_bound_native_prefix_history import checked_prefix_evidence
from ladon.real_bound_native_relation_history import checked_relation_evidence
from ladon.real_bound_native_relation_worker import _same_source


def _inputs(productions, rules):
    if not isinstance(productions, list) or not 2 <= len(productions) <= 128:
        raise ValueError('Real chain requires 2 to 128 ordered productions')
    if (not isinstance(rules, list) or len(rules) != len(productions) - 1
            or any(not isinstance(r, str) or r not in RULES for r in rules)):
        raise ValueError('Real chain requires one supported rule per adjacent pair')
    _bound_inputs([productions, rules])


def _admit(productions, root, deadline):
    for value in productions:
        _remaining(deadline)
        production_api._verify_production(value)
        _remaining(deadline)
        production_api._current_source(value, root)
    fresh = []
    for saved in productions:
        current = _fresh(saved, root, _remaining(deadline))
        if _semantic_owner(saved) != _semantic_owner(current):
            raise ValueError('Real chain replay substituted an exact semantic owner')
        fresh.append(current)
    return fresh


def current_sources(productions, root, deadline):
    for value in productions:
        _remaining(deadline)
        production_api._current_source(value, root)
    _remaining(deadline)


def _candidate(pair, rule):
    if not _same_source(*(p['request']['plan'] for p in pair)):
        return 'real-chain-source-context-mismatch'
    if rule == 'order-prefix-v1':
        return prefix_candidate(*pair)
    return None if _context(pair[0]) == _context(pair[1]) else 'real-bound-context-mismatch'


def _check_edge(pair, rule, root, deadline):
    residual = _candidate(pair, rule)
    if residual is not None:
        return residual, None
    plans = [p['request']['plan'] for p in pair]
    if rule == 'order-prefix-v1':
        run = check_prefix_relation(root, *plans, pair[1]['request']['terms']['predicate-admission'],
                                    timeout_seconds=_remaining(deadline))
        validator = checked_prefix_evidence
    else:
        run = check_real_bound_relation(root, *plans, timeout_seconds=_remaining(deadline))
        validator = checked_relation_evidence
    try:
        evidence = validator(pair, run)
        identity = native_checker_identity()
        if (evidence['checkerIdentity'] != identity
                or any(p['check']['result']['checkerIdentity'] != identity for p in pair)):
            raise ValueError('fresh chain edge checker differs from its owners')
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return 'real-chain-edge-check-unaccepted', run
    return None, run


def _chain_run(productions, rules, root, deadline):
    _inputs(productions, rules)
    try:
        fresh = _admit(productions, root, deadline)
    except TimeoutError:
        return _unresolved(None, [], phase='admission'), [], []
    runs, results = [], []
    failure = None
    for index, rule in enumerate(rules):
        try:
            residual, run = _check_edge(fresh[index:index + 2], rule, root, deadline)
        except TimeoutError:
            residual, run = 'real-chain-deadline-expired', None
        results.append({'ruleCandidate': rule, 'status': 'unresolved' if residual else 'resolved',
                        'relationCheckRun': run, 'residual': residual})
        if residual:
            failure = _unresolved(index, results)
            break
        runs.append(run)
    if failure is None:
        try:
            current_sources(fresh, root, deadline)
        except TimeoutError:
            failure = _unresolved(None, results, phase='freshness')
    return failure, fresh, runs


def _unresolved(index, results, *, phase='edge'):
    result = {'schema': 'ladon-real-bound-chain-analysis-v1', 'status': 'unresolved',
              'complete': False, 'failedEdge': index, 'failedPhase': phase,
              'checkedEdgeCount': sum(r['status'] == 'resolved' for r in results),
              'edgeResults': results, 'authority': 'none', 'endpointTheorem': 'not-checked',
              'sourceTheoremProof': 'not-checked', 'paperNormBridge': 'unresolved',
              'mathematicalFalsity': 'not-established'}
    result['analysisId'] = snapshot_identity(result)
    return result
