"""Closed native records for ordered, individually checked Real predicate edges."""

from copy import deepcopy

from ladon.proof_contract_payloads import _refs, closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proofir_v3 import MAX_BATCH_BYTES, canonical_bytes, validate_envelope_batch
from ladon.real_bound_native_analysis_artifacts import _unique
from ladon.real_bound_native_analysis_codec import decode_replay
from ladon.real_bound_native_artifacts import _envelope, external
from ladon.real_bound_native_payload import LIMITATIONS
from ladon.real_bound_native_profile import PROFILE_DIGEST

SCHEMA = 'ladon-real-bound-chain-bundle-v1'
ANALYSIS_KIND = 'real-bound-chain-v1'
RULES = frozenset({'identity-v1', 'order-prefix-v1'})


def is_chain(payload):
    return (payload.get('profileDigest') == PROFILE_DIGEST and payload.get('stage') == 'propagation'
            and payload.get('analysisKind') == ANALYSIS_KIND)


def _payload(contracts, edges, checks, rules):
    body = {'profileDigest': PROFILE_DIGEST, 'stage': 'propagation', 'analysisKind': ANALYSIS_KIND,
            'contractRefs': deepcopy(contracts), 'edgeAnalysisRefs': deepcopy(edges),
            'checkRunRefs': deepcopy(checks), 'rules': list(rules),
            'result': {'status': 'recorded-checked', 'authority': 'none', 'edgeCount': len(edges),
                       'scope': 'individually-checked-input-predicate-edges',
                       'endpointTheorem': 'not-checked', 'sourceTheoremProof': 'not-checked',
                       'paperNormBridge': 'unresolved', 'mathematicalFalsity': 'not-established'},
            'residuals': []}
    return {'analysisId': 'analysis:' + snapshot_identity(body)[7:], **body}


def _edge_rule(artifact):
    p = artifact['payload']
    if artifact['artifactKind'] != 'proofir.contract-analysis' or p['profileDigest'] != PROFILE_DIGEST:
        raise ValueError('chain requires Real analysis edges')
    if p['stage'] != 'comparison':
        raise ValueError('chain edges must be individual comparisons, not nested chains')
    if p.get('analysisKind') == 'real-bound-prefix-v1':
        return 'order-prefix-v1'
    if 'analysisKind' not in p:
        return 'identity-v1'
    raise ValueError('unsupported Real chain edge kind')


def _from_edges(edges):
    if not isinstance(edges, list) or not 1 <= len(edges) <= 127:
        raise ValueError('Real chain requires 1 to 127 checked edges')
    contracts, refs, checks, rules = [], [], [], []
    env = edges[0]['environmentRef']
    for edge in edges:
        rules.append(_edge_rule(edge))
        p = edge['payload']
        left, right = p['contractRefs']
        if (edge['environmentRef'] != env or (contracts and contracts[-1] != left)):
            raise ValueError('chain adjacent edges must share the exact middle owner and environment')
        if not contracts:
            contracts.append(left)
        contracts.append(right)
        refs.append(external(edge, 'contract-analysis', p['analysisId']))
        checks.extend(p['checkRunRefs'])
    return _payload(contracts, refs, checks, rules), env


def validate_chain_payload(p, value, subjects, env):
    closed(p, {'analysisId', 'profileDigest', 'stage', 'analysisKind', 'contractRefs',
               'edgeAnalysisRefs', 'checkRunRefs', 'rules', 'result', 'residuals'}, 'Real chain payload')
    for key, kind in [('contractRefs', 'contract'), ('edgeAnalysisRefs', 'contract-analysis'),
                      ('checkRunRefs', 'check-run')]:
        _refs(p, key, kind, value, subjects, env)
    n = len(p['contractRefs'])
    if not (2 <= n <= 128 and len(p['edgeAnalysisRefs']) == len(p['checkRunRefs']) == n - 1):
        raise ValueError('Real chain must preserve all contract positions and edges')
    _validate_rules(p['rules'], n)
    if p != _payload(p['contractRefs'], p['edgeAnalysisRefs'], p['checkRunRefs'], p['rules']):
        raise ValueError('Real chain differs from its closed historical result')
    if ('contract-analysis', p['analysisId']) not in subjects:
        raise ValueError('Real chain must own its analysis subject')
    _limitations(value)


def _validate_rules(rules, positions):
    if (not isinstance(rules, list) or len(rules) != positions - 1
            or any(not isinstance(r, str) or r not in RULES for r in rules)):
        raise ValueError('invalid Real chain rules')


def _limitations(value):
    if (value['coverage']['status'] != 'partial'
            or not set(LIMITATIONS) <= {row['id'] for row in value['limitations']}):
        raise ValueError('Real chain requires partial coverage and historical limitations')


def chain_edges(artifacts, payload):
    edges = []
    for ref in payload['edgeAnalysisRefs']:
        edge = artifacts.get(ref['artifactRef'])
        if edge is None or external(edge, 'contract-analysis', edge['payload']['analysisId']) != ref:
            raise ValueError('Real chain requires each exact edge analysis owner')
        edges.append(edge)
    return edges


def validate_chain_owners(artifacts, payload):
    edges = chain_edges(artifacts, payload)
    expected, _env = _from_edges(edges)
    if expected != payload:
        raise ValueError('Real chain differs from its ordered edge owners')
    prior = None
    for edge in edges:
        pair, _run = decode_replay(edge['payload']['replay'])
        if prior is not None and prior != pair[0]:
            raise ValueError('native chain requires one exact middle replay owner')
        prior = pair[1]


def _validated_edge(bundle):
    from ladon.real_bound_native_analysis_bundle import _validated as comparison
    from ladon.real_bound_native_prefix_bundle import _validated as prefix

    validator = {'ladon-real-bound-comparison-bundle-v1': comparison,
                 'ladon-real-bound-prefix-bundle-v1': prefix}.get(bundle.get('schema'))
    if validator is None:
        raise ValueError('Real chain requires a supported single-edge bundle')
    productions, _payload_value = validator(bundle)
    artifact = next(a for a in bundle['artifacts'] if a['artifactId'] == bundle['analysisRef']['artifactRef'])
    return artifact, productions


def _validated_edges(bundles):
    edges, prior = [], None
    for bundle in bundles:
        artifact, pair = _validated_edge(bundle)
        if prior is not None and prior != pair[0]:
            raise ValueError('chain requires one exact adjacent middle production')
        edges.append(artifact)
        prior = pair[1]
    return edges


def recorded_chain(edge_bundles):
    """Join exact historical owners, without authenticating saved execution."""
    canonical_bytes(edge_bundles, max_bytes=MAX_BATCH_BYTES)
    if not isinstance(edge_bundles, list) or not 1 <= len(edge_bundles) <= 127:
        raise ValueError('Real chain requires 1 to 127 checked edge bundles')
    payload, env = _from_edges(_validated_edges(edge_bundles))
    artifact = _envelope('contract-analysis', env,
                         [{'kind': 'contract-analysis', 'localId': payload['analysisId']}], payload)
    artifacts = _unique([a for b in edge_bundles for a in b['artifacts']] + [artifact])
    validate_envelope_batch(artifacts)
    bundle = {'schema': SCHEMA, 'status': 'recorded-checked', 'authority': 'none',
              'analysisRef': external(artifact, 'contract-analysis', payload['analysisId']),
              'artifacts': artifacts}
    bundle['snapshotId'] = snapshot_identity(bundle)
    canonical_bytes(bundle, max_bytes=MAX_BATCH_BYTES)
    return bundle
