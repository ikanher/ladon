"""Pure binding checks over retained actual statement-owner fixtures."""
import json
from pathlib import Path
from time import monotonic

import pytest

from ladon import proof_contract_provider_expansion as expansion
from ladon._proof_contract_obligation_check_inputs import _requirements_for_demand


def _request():
    fixture = Path(__file__).parent/'fixtures/proof_contract_provider_expansion/native.json'
    data = json.loads(fixture.read_text())
    analysis, context = data['analysisArtifact'], data['context']
    route = next(r for r in analysis['payload']['result']['routeComparisons'] if r['describedRoute'])
    requirement = next(r for r in route['backwardRequirements'] if r['interfaceId']=='first')
    demand = next(d for d in route['obligationBundle']['demands']
        if any(r==requirement for _,r in _requirements_for_demand([requirement],d)))
    deadline = monotonic()+30
    limits = {'timeout_seconds':30,'max_rss_bytes':12*1024**3,'max_output_bytes':8*1024**2}
    selected = expansion.make_provider_slice_request(analysis,context,route,demand,
                                                    requirement,deadline,limits)
    return {'repoRoot':'.','analysisArtifact':analysis,'context':context,
        'providerSliceRequest':selected,'application':'Eq.trans','occurrence':0,
        'deadlineMonotonic':deadline,'limits':limits}


def test_actual_owner_fixture_targets_exact_original_declaration_and_owns_copy():
    request = _request(); selected = request['providerSliceRequest']
    target = selected['sourceSelection']
    assert target['availability']=='available'
    assert target['declaration']=='ThreeSteps.firstBound'
    assert target['sourcePath']=='ThreeSteps.lean'
    assert target['anchor']['contentDigest']==target['contentDigest']
    target['anchor']['contentDigest']='changed'
    assert all(a.get('payload',{}).get('anchors',[{}])[0].get('contentDigest')!='changed'
               for a in request['context']['artifacts'])


@pytest.mark.parametrize('field', ['routeId','obligation','sourceRef','reading','contract',
                                  'anchor','generated-origin'])
def test_forged_request_is_rejected_before_original_source_worker(field, monkeypatch):
    request = _request(); selected = request['providerSliceRequest']
    _forge(selected,field)
    monkeypatch.setattr(expansion,'run_provider_job',
        lambda *args, **_kwargs: pytest.fail('forged binding reached original source worker'))
    result = expansion.expand_obligation_provider(request)
    assert result['status']=='rejected'
    assert result['providerSnapshot'] is None
    assert result['slice'] is None


def _forge(selected, field):
    if field=='reading':
        selected['binding']['desiredReadingIdentity']['readingId']='forged'
    elif field=='contract':
        selected['contractRef']['localId']='forged'
    elif field=='anchor':
        selected['sourceSelection']['contentDigest']='sha256:'+'0'*64
        selected['sourceSelection']['anchor']['contentDigest']='sha256:'+'0'*64
    elif field=='generated-origin':
        selected['goalOrigin']='generated-contract-obligation'
    else:
        selected[field]='sha256:'+'0'*64
