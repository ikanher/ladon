import ast,hashlib,json,time
from pathlib import Path
from ladon.proofir_correspondence import interpretation_artifacts,bind_native_interpretation,correspondence_artifacts
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_context_bridge import plan_context_bridge
from ladon._proof_contract_obligation_check_inputs import _selected_identity
from ladon._proof_contract_bridge_goals import bridge_interpretation
from ladon._proof_contract_source_obligations_formula import _formula_symbols
p=Path('.codex/state/proof-contract-analysis/route-context');root=(p/'probe-repo').resolve()
code=ast.parse((p/'feasibility.py').read_text());exec(compile(ast.Module(body=[n for n in code.body if isinstance(n,ast.FunctionDef) and n.name=='reading'],type_ignores=[]),'<reading-helper>','exec'))
snapshots=json.loads((p/'snapshots.json').read_text());observed=json.loads((p/'provider.json').read_text());old=observed['request'];context=old['context'];analysis=old['analysisArtifact']
spent=sum(s.get('elapsedSeconds',0) for s in snapshots.values())+observed['elapsedSeconds'];start=time.monotonic();deadline=start+max(0,90-spent);limits=old['limits']
leaf=reading(snapshots['firstBound'],'leaf-reading');pair=interpretation_artifacts(leaf,snapshots['firstBound']['environment'],source_root=root);context['artifacts'].extend(pair)
prepared=prepare_correspondence(leaf,observed['slice'],{'s':'b0','x':{'symbol':'value','args':['b1']}});prepared=bind_native_interpretation(prepared,context['artifacts'],source_root=root)
owner=correspondence_artifacts(prepared);context['artifacts'].append(owner);ref={'artifactRef':owner['artifactId'],'kind':'correspondence','localId':owner['payload']['correspondenceId']}
route,req=next((r,g) for r in analysis['payload']['result']['routeComparisons'] for g in r['backwardRequirements'] if g['statementRef']['localId']=='first')
parent_pair=next(a for a in context['artifacts'] if a['artifactKind']=='proofir.interpretation' and a['payload']['interpretationId']=='parent-reading')
request={'repoRoot':str(root),'analysisArtifact':analysis,'context':context,'selectedIdentity':_selected_identity(route,req),'sourceBindings':{'parentSnapshot':snapshots['endpoint'],'providerSnapshot':snapshots['firstBound'],'parentInterpretationRef':{'artifactRef':parent_pair['artifactId'],'kind':'interpretation','localId':'parent-reading'},'correspondenceRef':ref},'deadlineMonotonic':deadline,'limits':limits}
(p/'request.json').write_text(json.dumps(request,separators=(',',':')))
result=plan_context_bridge({'repoRoot':str(root),'context':context,'correspondenceRef':ref,'deadlineMonotonic':deadline,'limits':limits});(p/'context-plan.json').write_text(json.dumps(result,separators=(',',':')))
measurement={'priorMeasuredSeconds':spent,'resumeSeconds':time.monotonic()-start,'totalMeasuredSeconds':spent+time.monotonic()-start,'budgetSeconds':90,'status':result['status'],'diagnostic':result['diagnostic'],'preparation':result.get('preparation')};(p/'measurement.json').write_text(json.dumps(measurement,indent=2));print(json.dumps(measurement));assert result['status']=='planned',result['diagnostic']
print([(g['id'],g['goal']) for g in result['goals']])
