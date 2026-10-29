"""Production, historical inspection and explicit fresh replay of Real edge chains."""

from copy import deepcopy

from ladon import real_bound_native_production as production_api
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis import _deadline, _remaining
from ladon.real_bound_native_analysis_artifacts import recorded_comparison
from ladon.real_bound_native_analysis_codec import decode_replay
from ladon.real_bound_native_chain import _chain_run, _unresolved, current_sources
from ladon.real_bound_native_chain_artifacts import SCHEMA, chain_edges, recorded_chain
from ladon.real_bound_native_prefix_artifacts import recorded_prefix

FRESH_AUTHORITY = 'fresh-source-predicate-scalar-and-edge-checks'


def _record_edge(pair, rule, run):
    record = recorded_prefix if rule == 'order-prefix-v1' else recorded_comparison
    return record(pair, run)


def _validated(bundle):
    canonical_bytes(bundle, max_bytes=MAX_BATCH_BYTES)
    closed(bundle, {'schema', 'status', 'authority', 'analysisRef', 'artifacts', 'snapshotId'},
           'Real chain bundle')
    if (bundle['schema'] != SCHEMA or bundle['snapshotId'] != snapshot_identity(bundle)
            or bundle['authority'] not in {'none', FRESH_AUTHORITY}):
        raise ValueError('invalid Real chain identity or authority claim')
    validate_envelope_batch(bundle['artifacts'])
    try:
        artifacts = {a['artifactId']: a for a in bundle['artifacts']}
        payload = artifacts[bundle['analysisRef']['artifactRef']]['payload']
        edges = chain_edges(artifacts, payload)
        edge_bundles, productions = _reconstruct_edges(edges, payload['rules'])
        expected = recorded_chain(edge_bundles)
        expected['authority'] = bundle['authority']
        expected['snapshotId'] = snapshot_identity(expected)
        if expected != bundle:
            raise ValueError('Real chain differs from exact edge reconstruction')
        return productions, payload
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError('malformed Real chain bundle') from error


def _reconstruct_edges(edges, rules):
    edge_bundles, productions = [], []
    for edge, rule in zip(edges, rules, strict=True):
        pair, run = decode_replay(edge['payload']['replay'])
        if productions and productions[-1] != pair[0]:
            raise ValueError('chain replay requires one exact middle production')
        productions.extend(pair if not productions else pair[1:])
        edge_bundles.append(_record_edge(pair, rule, run))
    return edge_bundles, productions


def produce_chain_bundle(productions, rules, root, *, timeout_seconds=600):
    deadline = _deadline(timeout_seconds)
    failure, fresh, runs = _chain_run(productions, rules, root, deadline)
    if failure is not None:
        return failure
    try:
        return _publish(fresh, rules, runs, root, deadline)
    except TimeoutError:
        results = [{'ruleCandidate': rule, 'status': 'resolved', 'relationCheckRun': run,
                    'residual': None} for rule, run in zip(rules, runs, strict=True)]
        return _unresolved(None, results, phase='publication')


def _publish(fresh, rules, runs, root, deadline):
    edges = []
    for i, (rule, run) in enumerate(zip(rules, runs, strict=True)):
        _remaining(deadline)
        edges.append(_record_edge(fresh[i:i + 2], rule, run))
    _remaining(deadline)
    bundle = recorded_chain(edges)
    current_sources(fresh, root, deadline)
    bundle['authority'] = FRESH_AUTHORITY
    bundle['snapshotId'] = snapshot_identity(bundle)
    _remaining(deadline)
    return bundle


def inspect_chain_bundle(bundle, root=None):
    productions, payload = _validated(bundle)
    if root is not None:
        for value in productions:
            production_api._current_source(value, root)
    return {'schema': 'ladon-real-bound-chain-inspection-v1', 'status': 'validated-historical',
            'authority': 'none', 'freshCheck': False, 'evidenceAuthentication': 'not-established',
            'sourceFreshness': 'current' if root is not None else 'not-checked',
            'analysisRef': deepcopy(bundle['analysisRef']), 'recordedResult': deepcopy(payload['result']),
            'rules': deepcopy(payload['rules']), 'endpointTheorem': 'not-checked',
            'sourceTheoremProof': 'not-checked', 'paperNormBridge': 'unresolved'}


def replay_chain_bundle(bundle, root, *, timeout_seconds=600):
    deadline = _deadline(timeout_seconds)
    productions, payload = _validated(bundle)
    return produce_chain_bundle(productions, payload['rules'], root, timeout_seconds=_remaining(deadline))
