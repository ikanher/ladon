"""Structural and batch semantic acceptance for native obligation bundles."""
from __future__ import annotations

from .proof_contract_payloads import _refs, closed, identifier, residuals, rows
from .proof_contract_rules import PROFILE_DIGEST
from .proofir_v3 import _require_ref


def validate_obligation_payload(payload, value, subjects, env):
    closed(payload, {'analysisId', 'profileDigest', 'stage', 'derivationGoalRef', 'contractRefs',
                    'request', 'result', 'checkRunRefs', 'residuals'}, 'obligations payload')
    identifier(payload['analysisId'], 'analysis ID')
    if ('contract-analysis', payload['analysisId']) not in subjects:
        raise ValueError('obligations must own their exact typed analysis subject')
    if payload['profileDigest'] != PROFILE_DIGEST or payload['stage'] != 'obligations':
        raise ValueError('unsupported obligations profile or stage')
    _require_ref(payload['derivationGoalRef'], '/payload/derivationGoalRef',
                 subjects, env, value, 'statement')
    _refs(payload, 'contractRefs', 'contract', value, subjects, env)
    _refs(payload, 'checkRunRefs', 'check-run', value, subjects, env)
    residuals(payload['residuals'])
    _validate_request_shape(payload['request'])
    _validate_result(payload['result'], value)


def _validate_request_shape(request):
    from .proof_contract_obligation_artifacts import REQUEST_FIELDS
    from .proof_contract_payloads import _require_local_statement_ref

    closed(request, set(REQUEST_FIELDS.values()), 'obligations request')
    _require_local_statement_ref(request['goalRef'], 'obligations goal')
    for field in ('ruleBindings', 'endpointInterfaces', 'scopeBindings',
                  'describedRouteStepRefs', 'perApplicationBackwardChoices', 'routePriorities'):
        rows(request[field], field)
    if request['bounds'] is not None and not isinstance(request['bounds'], dict):
        raise TypeError('obligation bounds must be an object or null')


def _validate_result(result, value):
    if not isinstance(result, dict) or result.get('schema') != 'ladon-contract-obligation-planner-v2':
        raise ValueError('obligations require a versioned v2 result')
    if (result.get('checkerAuthority') != 'none'
            or result.get('mathematicalFalsity') != 'not-established'
            or result.get('authority') != 'conditional-profile'):
        raise ValueError('obligation planning cannot promote checker or falsity authority')
    _validate_status_coverage(result, value)
    limitations = {r['id'] for r in value['limitations']}
    if not {'source-contract-binding-unchecked', 'deadline-observation-unverified'} <= limitations:
        raise ValueError('obligations must retain source and clock limitations')


def _validate_status_coverage(result, value):
    if result.get('status') not in {'complete', 'partial', 'unsupported-cycle'}:
        raise ValueError('unsupported obligations result status')
    expected = 'complete' if result['status'] == 'complete' else 'partial'
    if value['coverage']['status'] != expected:
        raise ValueError('obligations coverage differs from result status')


def recompute_obligation_inputs(artifacts, payload):
    from .proof_contract_obligation_artifacts import request_from_payload
    from .proof_contract_payloads import _prevalidate_native_request, _validate_contract_owners

    graph_ref = payload['derivationGoalRef']
    graph = artifacts[graph_ref['artifactRef']]
    if graph['artifactKind'] != 'proofir.derivation':
        raise ValueError('obligations require the exact native derivation owner')
    contracts = [artifacts[r['artifactRef']] for r in payload['contractRefs']]
    _validate_contract_owners(payload['contractRefs'], contracts)
    request = payload['request']
    if request['goalRef'] != {k: graph_ref[k] for k in ('kind', 'localId')}:
        raise ValueError('obligation goal differs from its derivation owner')
    _prevalidate_native_request(graph, contracts, request)
    owned = request_from_payload(graph, contracts, request)
    _require_exact_replay(owned, payload['result'])


def _require_exact_replay(request, result):
    from .proof_contract_obligation_planner import _plan_contract_obligation_bundles

    trace = result.get('deadlineObservation')
    if trace is None:
        raise ValueError('obligations are missing deadline replay decisions')
    expected = _plan_contract_obligation_bundles(request, _deadline_replay=trace)
    if result != expected:
        raise ValueError('obligation result differs from exact whole-plan replay')
