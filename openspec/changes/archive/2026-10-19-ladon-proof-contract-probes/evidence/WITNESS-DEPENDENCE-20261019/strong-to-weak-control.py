import json, time
from pathlib import Path
from ladon.proof_contract_probes import plan_application_probe, check_application_probe
from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check

base=Path('.codex/state/proof-contract-analysis/witness-feasibility')
p=base/'attempt-06'; p.mkdir()
prior=json.loads((base/'START.json').read_text())
source=base/'attempt-04'
repo=(source/'repo').resolve()
batch=json.loads((source/'context.json').read_text())['artifacts']
sides=json.loads((source/'actual-sides.json').read_text())
deadline=prior['deadlineMonotonic']; limits={'timeout_seconds':30,'max_rss_bytes':12*1024**3,'max_output_bytes':8*1024**2}
request={'repoRoot':str(repo),'context':{'artifacts':batch},'left':sides[0],'right':sides[1],
 'template':{'familyId':'witness-dependence','version':'witness-dependence-v2','direction':'left-to-right','kind':'implication'},
 'deadlineMonotonic':deadline,'limits':limits}
(p/'request.json').write_text(json.dumps(request,sort_keys=True,indent=2))
planned=plan_application_probe(request); (p/'planned.json').write_text(json.dumps(planned,sort_keys=True,indent=2))
assert planned['status']=='planned', planned
terms={'formal-reading':'Iff.rfl','probe':'''by
  intro h
  obtain ⟨w, hw⟩ := h
  intro x
  exact ⟨w, hw x⟩'''}
(p/'terms.json').write_text(json.dumps(terms,sort_keys=True,indent=2))
t0=time.monotonic(); checked=check_application_probe(request,planned['planId'],terms)
(p/'checked.json').write_text(json.dumps(checked,sort_keys=True,indent=2))
accepted=[]
for goal in checked['goals']:
 raw=load_goal_evidence(repo,goal['result']); ok=_accepted_check(raw)
 assert ok and goal['status']=='checked-support',(goal['goalId'],goal['status'])
 accepted.append(goal['goalId'])
assert len(accepted)==2 and checked['status']=='checked-local-implication'
assert checked['artifact']['payload']['checkRunRefs']==[]
(p/'RESULT.json').write_text(json.dumps({'status':'PASS','scope':'strong-to-weak cross-order implication control under the shared original witness qualification deadline','acceptedGoals':len(accepted),'goalIds':accepted,'elapsedSeconds':time.monotonic()-t0},sort_keys=True,indent=2))
print('PASS',accepted,'elapsed',time.monotonic()-t0)
