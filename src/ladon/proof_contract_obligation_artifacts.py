"""Native, conditional obligation bundles with exact derivation and input ownership."""
from __future__ import annotations

from .proof_contract_obligation_planner import ContractObligationPlanRequest
from .proof_contract_payloads import closed
from .proof_contract_rules import PROFILE_DIGEST
from .proofir_v3 import make_envelope, validate_envelope

REQUEST_FIELDS = {
    'goal_ref': 'goalRef', 'rule_bindings': 'ruleBindings',
    'endpoint_interfaces': 'endpointInterfaces', 'scope_bindings': 'scopeBindings',
    'desired_contract': 'desiredContract', 'desired_reading_identity': 'desiredReadingIdentity',
    'described_route_step_refs': 'describedRouteStepRefs',
    'per_application_backward_choices': 'perApplicationBackwardChoices',
    'route_priorities': 'routePriorities', 'bounds': 'bounds',
}


def request_payload(request):
    if not isinstance(request, ContractObligationPlanRequest):
        raise TypeError('request must be ContractObligationPlanRequest')
    return {target: getattr(request, source) for source, target in REQUEST_FIELDS.items()}


def request_from_payload(graph, contracts, payload):
    closed(payload, set(REQUEST_FIELDS.values()), 'obligation request')
    return ContractObligationPlanRequest(derivation_artifact=graph, contract_artifacts=contracts,
        **{source: payload[target] for source, target in REQUEST_FIELDS.items()})


def obligations_artifact(request, *, analysis_id):
    from .proof_contract_artifacts import _prepare_propagation_inputs
    from .proof_contract_obligation_planner import plan_contract_obligation_bundles

    payload = request_payload(request)
    inputs = _prepare_propagation_inputs(request.derivation_artifact, request.contract_artifacts,
        analysis_id, request.goal_ref, request.rule_bindings, request.endpoint_interfaces,
        request.scope_bindings, request.bounds)
    # Use the native-owned inputs, preserving every request value and its order.
    owned = request_from_payload(inputs['derivation'], inputs['contracts'], payload)
    result = plan_contract_obligation_bundles(owned)
    return _envelope(owned, analysis_id, payload, result)


def _envelope(request, analysis_id, payload, result):
    graph = validate_envelope(request.derivation_artifact).to_dict()
    refs = [{'artifactRef': row['artifactId'], 'kind': 'contract',
             'localId': row['payload']['contractId']} for row in request.contract_artifacts]
    body = {'analysisId': analysis_id, 'profileDigest': PROFILE_DIGEST, 'stage': 'obligations',
            'derivationGoalRef': {'artifactRef': graph['artifactId'], **request.goal_ref},
            'contractRefs': refs, 'request': payload, 'result': result,
            'checkRunRefs': [], 'residuals': []}
    return make_envelope(artifact_kind='proofir.contract-analysis',
        producer={'name': 'ladon-contract-obligations', 'version': '1'},
        environment_ref=graph['environmentRef'],
        subject_refs=[{'kind': 'contract-analysis', 'localId': analysis_id}],
        coverage={'status': 'complete' if result['status'] == 'complete' else 'partial',
                  'observed': 1}, payload=body,
        limitations=[{'id': 'conditional-contract-profile',
                      'message': 'Backward bundles are conditional sufficient requirements.'},
                     {'id': 'source-contract-binding-unchecked',
                      'message': 'Graph, rule and prose attribution are not certified by this plan.'},
                     {'id': 'deadline-observation-unverified',
                      'message': 'Historical deadline decisions support replay, not clock authentication.'}],
    ).to_dict()
