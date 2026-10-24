"""Planning-only native application probes, replayed from exact typed owners."""
from ._proof_contract_probe_pair import derive_probe_result, probe_reference
from .proof_contract_payloads import _refs, closed, identifier, residuals
from .proof_contract_rules import PROFILE_DIGEST


def validate_probe_payload(p, value, subjects, env):
    from ._proof_contract_probe_templates import validate_template

    closed(p, {'analysisId', 'profileDigest', 'stage', 'contractRefs', 'correspondenceRefs',
               'template', 'result', 'checkRunRefs', 'residuals'}, 'probe analysis payload')
    identifier(p['analysisId'], 'analysis ID')
    if ('contract-analysis', p['analysisId']) not in subjects:
        raise ValueError('probe analysis must own its exact typed subject')
    if p['profileDigest'] != PROFILE_DIGEST or p['stage'] != 'probes':
        raise ValueError('unsupported probe profile or stage')
    _probe_refs(p, value, subjects, env)
    validate_template(p['template'])
    if p['checkRunRefs'] != []:
        raise ValueError('planned probes cannot carry checker authority')
    residuals(p['residuals'])
    if not isinstance(p['result'], dict) or p['result'].get('checkerAuthority') != 'none':
        raise ValueError('planned probes require explicitly absent checker authority')
    _probe_result_shape(p['result'])
    if 'source-contract-binding-unchecked' not in {r['id'] for r in value['limitations']}:
        raise ValueError('probe plan must retain its interpretation fidelity limitation')


def _probe_refs(p, value, subjects, env):
    for field, kind in (('contractRefs', 'contract'), ('correspondenceRefs', 'correspondence')):
        _refs(p, field, kind, value, subjects, env, minimum=2)
        if len(p[field]) != 2:
            raise ValueError('probes require exactly two ' + kind + ' references')
        for ref in p[field]:
            probe_reference(ref, kind)


def _probe_result_shape(result):
    from .proof_contract_payloads import rows

    closed(result, {'schema', 'status', 'template', 'scope', 'goals', 'residuals',
                   'checkerAuthority', 'wholeMethodAuthority', 'sourceFidelity',
                   'mathematicalFalsity'}, 'planned probe result')
    if (result['schema'] != 'ladon-application-probe-plan-v1'
            or result['status'] not in {'planned', 'unsupported'}
            or result['wholeMethodAuthority'] != 'none'
            or result['sourceFidelity'] != 'attributed-unreviewed'
            or result['mathematicalFalsity'] != 'not-established'):
        raise ValueError('invalid planned probe result authority or schema')
    rows(result['goals'], 'probe goals')
    for goal in result['goals']:
        closed(goal, {'goalId', 'kind', 'goal', 'goalDigest', 'status'}, 'planned probe goal')
        if goal['status'] != 'open':
            raise ValueError('native probe plan goals must remain open')
    residuals(result['residuals'])


def recompute_probe_inputs(artifacts, p):
    sides = [{'contractRef': c, 'correspondenceRef': r}
             for c, r in zip(p['contractRefs'], p['correspondenceRefs'], strict=True)]
    expected = derive_probe_result(artifacts, *sides, p['template'])
    if p['result'] != expected or p['residuals'] != expected['residuals']:
        raise ValueError('probe plan differs from exact source-bound input recomputation')
