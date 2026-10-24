"""Bind an original correspondence to one replayed native route requirement."""
from __future__ import annotations

from pathlib import Path

from ._proof_contract_context_preparation import _digest, _owner, prepare_context
from ._proof_contract_obligation_check_inputs import _selected_identity, _validation_plan
from ._proof_contract_planned_source_binding import _validate_plan_provider
from ._proof_contract_planned_source_trace import _select_verified_plan_requirement
from .proof_contract_bridge import _resource_stop
from .proof_contract_formal import verify_formal_snapshot
from .proof_contract_obligation_worker import _validate_native
from .proof_contract_source_obligations import (
    _fresh_formal_observation,
    _require_fresh_snapshot_match,
    _runner,
)


def prepare_route_context(request):
    """Called only inside the shared-deadline, memory-bounded route worker."""
    from ._proof_contract_route_context_goals import route_goals

    state = _native_route(request)
    context_request = {key: request[key] for key in ('repoRoot', 'context', 'deadlineMonotonic', 'limits')}
    context_request['correspondenceRef'] = request['sourceBindings']['correspondenceRef']
    context = prepare_context(context_request)
    if context.get('status') != 'prepared':
        return {'status': 'incomplete', 'context': context}
    _match_context_provider(context, state['provider'])
    prefix = _guard_endpoint(request, context, state['parent'])
    if _resource_stop(prefix, request['limits']):
        return {'status': 'incomplete', 'prefix': prefix}
    binding = _binding(request, state, context, prefix)
    goals, symbols = route_goals(context, binding, state)
    identity = _digest({'profile': 'route-context-bridge-v1', 'binding': binding,
                        'goals': goals, 'residuals': context['residuals']})
    return {'status': 'prepared', 'planId': identity, 'binding': binding,
        'goals': goals, 'symbols': symbols, 'residuals': context['residuals'],
        'adapter': {**context['adapter'], 'sourcePath': prefix['subject']['path'],
                    'sourceDigest': prefix['subject']['digest']},
        'construction': {'context': context['construction'], 'prefixCheck': prefix},
        'planStatus': state['historical']['status'],
        'routeComparisons': state['historical']['routeComparisons'],
        'planCoverage': state['historical']['coverage']}


def _native_route(request):
    root = Path(request['repoRoot']).resolve(strict=True)
    analysis = _validate_native({'artifact': request['analysisArtifact'], 'context': request['context']})
    plan, historical = _validation_plan({'result': analysis}, request['context'])
    ri, qi = _indices(historical, request['selectedIdentity'])
    selected = _select_verified_plan_requirement(plan, historical, ri, qi, request['selectedIdentity'])
    parent_reading = _parent_reading(request, root, plan)
    bindings = request['sourceBindings']
    parent = verify_formal_snapshot(bindings['parentSnapshot'], root)
    provider = verify_formal_snapshot(bindings['providerSnapshot'], root)
    if parent['contract'] != plan.desired_contract:
        raise ValueError('original parent differs from the native desired contract')
    _validate_plan_provider(selected, plan, provider, parent, root)
    fresh = [_observe(snapshot, root, request) for snapshot in (parent, provider)]
    return {'plan': plan, 'historical': historical, 'selected': selected,
            'parentReading': parent_reading, 'parent': parent, 'provider': provider,
            'parentFresh': fresh[0], 'providerFresh': fresh[1]}


def _indices(historical, identity):
    matches = [(ri, qi) for ri, route in enumerate(historical['routeComparisons'])
        for qi, row in enumerate(route['backwardRequirements'])
        if _selected_identity(route, row) == identity]
    if len(matches) != 1:
        raise ValueError('selected native route requirement is absent or ambiguous')
    return matches[0]


def _parent_reading(request, root, plan):
    from .proofir_correspondence import interpretation_artifacts

    ref = request['sourceBindings']['parentInterpretationRef']
    owner = _owner(request['context']['artifacts'], ref, 'proofir.interpretation')
    expected = {'readingId': owner['payload']['interpretationId'],
                'interpretationDigest': owner['artifactId']}
    if plan.desired_reading_identity != expected:
        raise ValueError('native parent interpretation differs from the original desired reading')
    pair = interpretation_artifacts(owner['payload']['record'], owner['environmentRef'], source_root=root)
    if pair[1] != owner or owner['environmentRef'] != request['analysisArtifact']['environmentRef']:
        raise ValueError('parent interpretation ownership, source or environment changed')
    if not any(row == pair[0] for row in request['context']['artifacts']):
        raise ValueError('parent interpretation has no exact original source-map owner')
    return owner


def _observe(snapshot, root, request):
    fresh = _fresh_formal_observation(snapshot, root, _runner(request['deadlineMonotonic']), request['limits'])
    _require_fresh_snapshot_match(snapshot, fresh)
    return fresh


def _match_context_provider(context, provider):
    binding = context['binding']
    selection = binding['selection']
    expected = {'path': provider['source']['path'], 'sha256': provider['source']['sha256']}
    actual = {key: binding['originalSource'][key] for key in expected}
    if (actual != expected or binding['environment'] != provider['environment']
            or selection['declaration'] != provider['selection']['declaration']
            or selection['module'] != provider['selection']['module']
            or selection['sourceFile'] != provider['source']['path']):
        raise ValueError('original correspondence is not the selected native provider')


def _guard_endpoint(request, context, parent):
    from ._proof_contract_source_obligations_prefix import check_generated_prefix
    from ._proof_contract_source_obligations_staging import _stage_prefix_check
    from .proof_contract_bridge_worker import _verified_source

    root = Path(request['repoRoot']).resolve(strict=True)
    raw = _verified_source(root, context['adapter'])
    key = _digest({'contextPlanId': context['planId'],
                   'endpoint': parent['selection']}).removeprefix('sha256:')
    subject = _stage_prefix_check(root, Path('.ladon/contract-obligations') / key / 'Route.lean',
                                  raw, parent, key, request['deadlineMonotonic'], [])
    return check_generated_prefix(root, subject, parent['environment'], request['limits'],
                                  _runner(request['deadlineMonotonic']))


def _binding(request, state, context, prefix):
    from ._proof_contract_bridge_preparation import _selected_demand
    from .proof_contract_rules import PROFILE, PROFILE_DIGEST

    selected, historical = state['selected'], state['historical']
    demand = _selected_demand({'routeComparisons': historical['routeComparisons'],
        'selectedRouteId': request['selectedIdentity']['routeId'], 'selectedRequirement': selected})
    analysis = request['analysisArtifact']
    return {'analysisRef': {'artifactRef': analysis['artifactId'], 'kind': 'contract-analysis',
                'localId': analysis['payload']['analysisId']},
        'desiredReadingIdentity': state['plan'].desired_reading_identity,
        'readingDigestPolicy': 'nativeartifactId-v1',
        'parentInterpretationRef': request['sourceBindings']['parentInterpretationRef'],
        'parentInterpretation': state['parentReading']['payload']['record'],
        'desiredContract': state['plan'].desired_contract,
        'selectedIdentity': request['selectedIdentity'], 'selectedRequirement': selected,
        'selectedDemand': demand, 'selectedDemandDigest': _digest(demand),
        'ruleBindings': state['plan'].rule_bindings,
        'profileDigest': PROFILE_DIGEST, 'profile': PROFILE,
        'parentSnapshotId': state['parent']['snapshotId'],
        'providerSnapshotId': state['provider']['snapshotId'],
        'parentSource': state['parent']['source'], 'parentSelection': state['parent']['selection'],
        'correspondenceRef': request['sourceBindings']['correspondenceRef'],
        'contextPlanId': context['planId'], 'contextBinding': context['binding'],
        'strictPrefixDigest': prefix['subject']['digest'],
        'outerDeadlineMonotonic': request['originalDeadlineMonotonic'],
        'plannerDeadlineUtc': (state['plan'].bounds or {}).get('deadlineUtc'),
        'limits': request['limits']}
