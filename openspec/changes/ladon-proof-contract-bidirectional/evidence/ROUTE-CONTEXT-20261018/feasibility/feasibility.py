import copy, hashlib, json, shutil, time
from dataclasses import replace
from pathlib import Path
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_contract_source_obligations import _runner
from ladon.proof_contract_obligation_supervision import run_obligation_planner
from support.proof_contract_planned_source import build_plan_request
from ladon.proof_contract_provider_expansion import make_provider_slice_request, expand_obligation_provider
from ladon._contract_propagation_budget import fingerprint
from ladon._proof_contract_obligation_check_inputs import _selected_identity
from ladon._proof_contract_bridge_goals import bridge_interpretation
from ladon._proof_contract_source_obligations_formula import _formula_symbols
from ladon.proofir_correspondence import interpretation_artifacts, bind_native_interpretation, correspondence_artifacts
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_context_bridge import plan_context_bridge
p=Path('.codex/state/proof-contract-analysis/route-context');root=(p/'probe-repo').resolve();root.mkdir()
for n in ('ThreeSteps.lean','lean-toolchain'):shutil.copyfile(Path('tests/fixtures/proof_contract_planned_source')/n,root/n)
start=time.monotonic();deadline=start+90
limits={'timeout_seconds':30,'max_rss_bytes':12*1024**3,'max_output_bytes':8*1024**2}
def save(n,v): (p/n).write_text(json.dumps(v,separators=(',',':'),ensure_ascii=False))
def reading(snapshot,name):
 r=bridge_interpretation({'contractRecord':snapshot['contract']},_formula_symbols(snapshot['observation']['normalizedTypeExpr']),{'path':name+'.txt'})
 r['id']=name;quote='The original bound is stated on Fin 5.';raw=(quote+'\n').encode();(root/(name+'.txt')).write_bytes(raw)
 r['source']={'path':name+'.txt','startLine':1,'endLine':1,'quote':quote,'sha256':hashlib.sha256(raw).hexdigest()}
 r['formula']['body']['binder']['domain']='Fin 5'
 def change(node):
  if isinstance(node,dict):
   if node=={'tag':'var','id':'b1'}: return {'tag':'app','symbol':'value','args':[node]}
   return {k:change(v) for k,v in node.items()}
  if isinstance(node,list):return [change(v) for v in node]
  return node
 r['formula']['body']['body']=change(r['formula']['body']['body'])
 r['symbols']['value']={'leanName':'Fin.val','leanType':'Fin 5 → Nat'}
 return r
snapshots={}
for n in ('firstBound','secondBound','thirdBound','alternateBound','endpoint'):
 snapshots[n]=produce_formal_snapshot(root,'ThreeSteps.lean','ThreeSteps','ThreeSteps.'+n,timeout_seconds=30,runner=_runner(deadline),max_rss_bytes=limits['max_rss_bytes'])
 assert snapshots[n]['status']=='extracted',snapshots[n]
save('snapshots.json',snapshots)
parent=reading(snapshots['endpoint'],'parent-reading');parent_pair=interpretation_artifacts(parent,snapshots['endpoint']['environment'],source_root=root)
plan=replace(build_plan_request(snapshots),desired_reading_identity={'readingId':parent['id'],'interpretationDigest':parent_pair[1]['artifactId']})
checked=run_obligation_planner(plan,deadline_monotonic=deadline,limits=limits,operation='artifact-v2',analysis_id='analysis:route-context-probe')
assert checked['status']=='completed',checked
analysis=checked['result'];context={'artifacts':[plan.derivation_artifact,*[a for s in snapshots.values() for a in s['artifacts']],*parent_pair]}
routes=analysis['payload']['result']['routeComparisons']
pick=next((r,g) for r in routes for g in r['backwardRequirements'] if g['statementRef']['localId']=='first')
route,req=pick
demand=next(d for d in route['obligationBundle']['demands'] if d['witnessRef']==req['parentWitnessRef'] and d['outputContractDigest']=='sha256:'+fingerprint(req['contractRecord']).hex())
provider_request=make_provider_slice_request(analysis,context,route,demand,req,deadline,limits)
observed=expand_obligation_provider({'repoRoot':str(root),'analysisArtifact':analysis,'context':context,'providerSliceRequest':provider_request,'application':'Eq.trans','occurrence':0,'deadlineMonotonic':deadline,'limits':limits})
save('provider.json',observed);assert observed['status']=='observed',observed['diagnostic']
leaf=reading(snapshots['firstBound'],'leaf-reading');pair=interpretation_artifacts(leaf,snapshots['firstBound']['environment'],source_root=root)
context['artifacts'].extend(pair)
prepared=prepare_correspondence(leaf,observed['slice'],{'s':'b0','x':{'tag':'app','symbol':'value','args':[{'tag':'var','id':'b1'}]}})
prepared=bind_native_interpretation(prepared,context['artifacts'],source_root=root)
owner=correspondence_artifacts(prepared);context['artifacts'].append(owner)
ref={'artifactRef':owner['artifactId'],'kind':'correspondence','localId':owner['payload']['correspondenceId']}
request={'repoRoot':str(root),'analysisArtifact':analysis,'context':context,'selectedIdentity':_selected_identity(route,req),'sourceBindings':{'parentSnapshot':snapshots['endpoint'],'providerSnapshot':snapshots['firstBound'],'parentInterpretationRef':{'artifactRef':parent_pair[1]['artifactId'],'kind':'interpretation','localId':parent['id']},'correspondenceRef':ref},'deadlineMonotonic':deadline,'limits':limits}
save('request.json',request)
context_request={'repoRoot':str(root),'context':context,'correspondenceRef':ref,'deadlineMonotonic':deadline,'limits':limits}
result=plan_context_bridge(context_request);save('context-plan.json',result)
assert result['status']=='planned',result['diagnostic']
save('measurement.json',{'elapsedSeconds':time.monotonic()-start,'budgetSeconds':90,'contextPreparation':result['preparation'],'goals':[(g['id'],g['goal']) for g in result['goals']]})
print(json.dumps({'elapsedSeconds':time.monotonic()-start,'preparationSeconds':result['preparation']['processReceipt']['elapsedSeconds'],'goals':[g['id'] for g in result['goals']],'residuals':result['residuals']}))
