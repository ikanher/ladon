import hashlib,json,sys
from pathlib import Path
from ladon._proof_contract_context_preparation import prepare_context
from ladon.proof_contract_obligation_worker import _validate_native
from ladon._proof_contract_obligation_check_inputs import _validation_plan
from ladon._proof_contract_planned_source_trace import _select_verified_plan_requirement
from ladon.proof_contract_formal import verify_formal_snapshot
from ladon._proof_contract_planned_source_binding import _validate_plan_provider
from ladon.proof_contract_source_obligations import _fresh_formal_observation,_require_fresh_snapshot_match,_runner
from ladon._proof_contract_source_obligations_staging import _stage_prefix_check
from ladon._proof_contract_source_obligations_prefix import check_generated_prefix
r=json.loads(sys.stdin.read());root=Path(r['repoRoot']);b=r['sourceBindings'];limits=r['limits'];deadline=r['deadlineMonotonic']
a=_validate_native({'artifact':r['analysisArtifact'],'context':r['context']});plan,historical=_validation_plan({'result':a},r['context'])
ri,qi=next((ri,qi) for ri,route in enumerate(historical['routeComparisons']) for qi,g in enumerate(route['backwardRequirements']) if {'routeId':route['routeId'],**{k:g[k] for k in r['selectedIdentity'] if k!='routeId'}}==r['selectedIdentity'])
selected=_select_verified_plan_requirement(plan,historical,ri,qi,r['selectedIdentity'])
parent=verify_formal_snapshot(b['parentSnapshot'],root);provider=verify_formal_snapshot(b['providerSnapshot'],root);_validate_plan_provider(selected,plan,provider,parent,root)
for s in (parent,provider):
 fresh=_fresh_formal_observation(s,root,_runner(deadline),limits);_require_fresh_snapshot_match(s,fresh)
context=prepare_context({'repoRoot':r['repoRoot'],'context':r['context'],'correspondenceRef':b['correspondenceRef'],'deadlineMonotonic':deadline,'limits':limits});assert context['status']=='prepared',context
raw=(root/context['adapter']['sourcePath']).read_bytes();key=hashlib.sha256(raw+b'route-endpoint-exclusion').hexdigest()
subject=_stage_prefix_check(root,Path('.ladon/contract-obligations')/key/'Route.lean',raw,parent,key,deadline,[])
checked=check_generated_prefix(root,subject,parent['environment'],limits,_runner(deadline));print(json.dumps({'status':'prepared','goals':len(context['goals']),'prefix':checked}))
