"""Root-only serial source acceptance under one unchanged 1,200-second clock."""
import copy
import contextlib
import hashlib
import json
import shutil
import sys
import time
from dataclasses import replace
from pathlib import Path

from ladon._contract_propagation_budget import fingerprint
from ladon._proof_contract_obligation_check_inputs import _selected_identity, _validation_plan
from ladon._proof_contract_bridge_goals import bridge_interpretation
from ladon._proof_contract_source_obligations_formula import _formula_symbols
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_cli import contract_main
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_contract_obligation_supervision import run_obligation_planner
from ladon.proof_contract_provider_expansion import make_provider_slice_request, expand_obligation_provider
from ladon.proof_contract_route_context import plan_route_context_bridge, check_route_context_bridge
from ladon.proof_contract_source_obligations import _runner
from ladon.proofir_correspondence import interpretation_artifacts, bind_native_interpretation, correspondence_artifacts
from support.proof_contract_planned_source import build_plan_request

out=Path(sys.argv[1]);root=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=True);root.mkdir()
for name in ('ThreeSteps.lean','lean-toolchain'):
 shutil.copyfile(Path('tests/fixtures/proof_contract_planned_source')/name,root/name)
source=(root/'ThreeSteps.lean').read_bytes();started=time.monotonic();deadline=started+1200
limits={'timeout_seconds':30,'max_rss_bytes':12*1024**3,'max_output_bytes':8*1024**2}
def save(name,value):
 with (out/name).open('x') as f:json.dump(value,f,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def check_clock():assert time.monotonic()<deadline,'Shared source acceptance budget expired'
def reading(snapshot, name):
    r = bridge_interpretation({'contractRecord': snapshot['contract']}, _formula_symbols(snapshot['observation']['normalizedTypeExpr']), {'path': name + '.txt'})
    r['id'] = name
    quote = 'The original bound is stated on Fin 5.'
    raw = (quote + '\n').encode()
    (root / (name + '.txt')).write_bytes(raw)
    r['source'] = {'path': name + '.txt', 'startLine': 1, 'endLine': 1, 'quote': quote, 'sha256': hashlib.sha256(raw).hexdigest()}
    r['formula']['body']['binder']['domain'] = 'Fin 5'

    def change(node):
        if isinstance(node, dict):
            if node == {'tag': 'var', 'id': 'b1'}:
                return {'tag': 'app', 'symbol': 'value', 'args': [node]}
            return {k: change(v) for k, v in node.items()}
        if isinstance(node, list):
            return [change(v) for v in node]
        return node
    r['formula']['body']['body'] = change(r['formula']['body']['body'])
    r['symbols']['value'] = {'leanName': 'Fin.val', 'leanType': 'Fin 5 → Nat'}
    return r
snapshots={}
for name in ('firstBound','secondBound','thirdBound','alternateBound','endpoint'):
 check_clock();snapshots[name]=produce_formal_snapshot(root,'ThreeSteps.lean','ThreeSteps','ThreeSteps.'+name,timeout_seconds=30,runner=_runner(deadline),max_rss_bytes=12*1024**3)
 assert snapshots[name]['status']=='extracted',snapshots[name]['status'];save(name+'-snapshot.json',snapshots[name])
parent=reading(snapshots['endpoint'],'parent-reading');parent_pair=interpretation_artifacts(parent,snapshots['endpoint']['environment'],source_root=root)
plan=replace(build_plan_request(snapshots),desired_reading_identity={'readingId':parent['id'],'interpretationDigest':parent_pair[1]['artifactId']})
checked=run_obligation_planner(plan,deadline_monotonic=deadline,limits=limits,operation='artifact-v2',analysis_id='analysis:route-context-final')
save('analysis-publication.json',checked);assert checked['status']=='completed',checked
analysis=checked['result'];save('analysis.json',analysis)
context={'artifacts':[plan.derivation_artifact,*[a for s in snapshots.values() for a in s['artifacts']],*parent_pair]}

def native_request(name,statement):
 check_clock()
 route,req=next((r,g) for r in analysis['payload']['result']['routeComparisons'] for g in r['backwardRequirements'] if g['statementRef']['localId']==statement)
 demand=next(d for d in route['obligationBundle']['demands'] if d['witnessRef']==req['parentWitnessRef'] and d['outputContractDigest']=='sha256:'+fingerprint(req['contractRecord']).hex())
 selected=make_provider_slice_request(analysis,context,route,demand,req,deadline,limits)
 observed=expand_obligation_provider({'repoRoot':str(root),'analysisArtifact':analysis,'context':context,'providerSliceRequest':selected,'application':'Eq.trans','occurrence':0,'deadlineMonotonic':deadline,'limits':limits})
 save(name+'-extraction.json',observed);assert observed['status']=='observed',observed['diagnostic']
 leaf=reading(snapshots[name],name+'-reading');pair=interpretation_artifacts(leaf,snapshots[name]['environment'],source_root=root)
 local_context={'artifacts':context['artifacts']+list(pair)}
 prepared=prepare_correspondence(leaf,observed['slice'],{'s':'b0','x':{'symbol':'value','args':['b1']}})
 prepared=bind_native_interpretation(prepared,local_context['artifacts'],source_root=root)
 owner=correspondence_artifacts(prepared);local_context['artifacts'].append(owner)
 return {'repoRoot':str(root),'analysisArtifact':analysis,'context':local_context,'selectedIdentity':_selected_identity(route,req),'sourceBindings':{'parentSnapshot':snapshots['endpoint'],'providerSnapshot':snapshots[name],'parentInterpretationRef':{'artifactRef':parent_pair[1]['artifactId'],'kind':'interpretation','localId':parent['id']},'correspondenceRef':{'artifactRef':owner['artifactId'],'kind':'correspondence','localId':owner['payload']['correspondenceId']}},'deadlineMonotonic':deadline,'limits':limits}

positive=native_request('firstBound','first');save('positive-request.json',positive)
with (out/'positive-plan-cli.log').open('x') as log, contextlib.redirect_stdout(log):
 code=contract_main(['route-context-obligations','--input',str(out/'positive-request.json'),'--output',str(out/'positive-plan.json')])
planned=json.loads((out/'positive-plan.json').read_text());assert code==0 and planned['status']=='planned',planned['diagnostic']
terms={g['id']:'by intros; simp_all [ThreeSteps.N0, ThreeSteps.N1, ThreeSteps.C]' for g in planned['goals'] if g['id']!='source-requirement'}
terms.update({'interpretation':'by intro h; exact h','object-map':'by intros; trivial','domain':'by intro s i; dsimp only; exact ⟨⟨s, rfl⟩, ⟨i.val, rfl⟩⟩','endpoint-transfer':'by intro h s i; exact h s i.val'})
save('positive-terms.json',terms)
with (out/'positive-check-cli.log').open('x') as log, contextlib.redirect_stdout(log):
 code=contract_main(['check-route-context-bridge','--input',str(out/'positive-request.json'),'--plan-id',planned['planId'],'--terms',str(out/'positive-terms.json'),'--output',str(out/'positive-result.json')])
result=json.loads((out/'positive-result.json').read_text());assert code==0
print('positive',result['status'],result['elapsedSeconds'],flush=True);assert result['status']=='checked-support',result['diagnostic']
assert result['demandDischarged'] is True and len(result['goals'])==13

middle=native_request('secondBound','second');save('middle-request.json',middle)
middle_plan=plan_route_context_bridge(middle);save('middle-plan.json',middle_plan);assert middle_plan['status']=='planned',middle_plan['diagnostic']
mt={'source-reading':'by intros; simp_all [ThreeSteps.N1, ThreeSteps.N2, ThreeSteps.C]', 'contract-transfer':'by intro h; exact h'}
save('middle-terms.json',mt);mr=check_route_context_bridge(middle,middle_plan['planId'],mt);save('middle-result.json',mr)
assert mr['status']=='unresolved-bridge' and mr['demandDischarged'] is False,mr['diagnostic']
assert next(g for g in mr['goals'] if g['id']=='source-reading')['status']=='checked-support'
assert next(g for g in mr['goals'] if g['id']=='contract-transfer')['status']=='unresolved'
assert 'result' not in next(g for g in mr['goals'] if g['id']=='source-requirement')
assert mr['routeComparisons']==analysis['payload']['result']['routeComparisons']
print('middle',mr['status'],mr['elapsedSeconds'],flush=True)

for name,proofs in [('missing-assumption',{'premise-5':'by intro s i h; exact hm'}),('excluded-parent',{'source-reading':'by exact ThreeSteps.endpoint'}),('closed-reading',{'source-reading':'by assumption'})]:
 check_clock();save(name+'-terms.json',proofs);r=check_route_context_bridge(positive,planned['planId'],proofs);save(name+'-result.json',r)
 assert r['status']=='unresolved-bridge' and r['demandDischarged'] is False,r['diagnostic']
 assert all(g['status']!='checked-support' for g in r['goals'])
 print(name,r['status'],r['elapsedSeconds'],flush=True)

for name,mutate in [
 ('changed-reading',lambda r:r['sourceBindings']['parentInterpretationRef'].update(localId='other-reading')),
 ('wrong-provider',lambda r:r['sourceBindings'].update(providerSnapshot=snapshots['secondBound'])),
 ('forged-assumption',lambda r:r.update(assumptions=['original desired conclusion'])),
 ('forged-rule',lambda r:r['analysisArtifact']['payload']['request']['ruleBindings'][0].update(ruleId='caller-rule')),
 ('changed-order',lambda r:r['selectedIdentity'].update(premiseOrdinal=999))]:
 check_clock();r=copy.deepcopy(positive);mutate(r);save(name+'-input.json',r);outcome=plan_route_context_bridge(r);save(name+'-result.json',outcome)
 assert outcome['status']=='rejected' and not outcome['demandDischarged'],(name,outcome['diagnostic'])
 print(name,outcome['status'],flush=True)

check_clock();changed=copy.deepcopy(positive);changed['deadlineMonotonic']-=0.5
r=check_route_context_bridge(changed,planned['planId'],{});save('changed-checkpoint-result.json',r);assert r['status']=='rejected' and not r['demandDischarged']
expired=copy.deepcopy(positive);expired['deadlineMonotonic']=time.monotonic()-1
r=plan_route_context_bridge(expired);save('expired-result.json',r);assert r['status']=='incomplete' and 'preparation' not in r
# Native UTC is independently enforced before native worker/source activity.
expired_native=copy.deepcopy(positive);expired_native['analysisArtifact']['payload']['request']['bounds']['deadlineUtc']='2000-01-01T00:00:00Z'
r=plan_route_context_bridge(expired_native);save('expired-native-result.json',r);assert r['status']=='incomplete' and 'preparation' not in r
assert (root/'ThreeSteps.lean').read_bytes()==source
# Intentional insufficient-memory control is last. Never retry or increase it.
check_clock();low=copy.deepcopy(positive);low['limits']['max_rss_bytes']=1024**2;save('memory-stop-input.json',low)
r=plan_route_context_bridge(low);save('memory-stop-result.json',r)
assert r['status']=='incomplete' and r['memoryReportBackRequired'] and not r['demandDischarged']
assert 'Stop progress and report back to user' in r['diagnostic']['message']
save('acceptance.json',{'status':'PASS','elapsedSeconds':time.monotonic()-started,'budgetSeconds':1200,'sourceSha256':hashlib.sha256(source).hexdigest(),'normalStageCaps':limits,'positiveGoals':13,'memoryStop':'last/no-retry','detectionBenefit':'unmeasured','wholeMethodAuthority':'none'})
print('PASS',time.monotonic()-started,flush=True)
