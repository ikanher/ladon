import json,time
from pathlib import Path
from ladon.proof_contract_route_context import plan_route_context_bridge,check_route_context_bridge
from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check
p=Path('.codex/state/proof-contract-analysis/route-context');r=json.loads((p/'first-request.json').read_text());start=time.monotonic();r['deadlineMonotonic']=start+90
plan=plan_route_context_bridge(r);assert plan['status']=='planned',plan['diagnostic']
terms={'source-reading':'by intros; simp_all [ThreeSteps.N0, ThreeSteps.N1, ThreeSteps.C]'}
result=check_route_context_bridge(r,plan['planId'],terms)
(p/'compact-probe.json').write_text(json.dumps(result,separators=(',',':'),ensure_ascii=False))
g=next(g for g in result['goals'] if g['id']=='source-reading');raw=load_goal_evidence(Path(r['repoRoot']),g['result']);assert _accepted_check(raw) and _accepted_check(g['result']) and g['status']=='checked-support'
measurement={'status':result['status'],'elapsedSeconds':time.monotonic()-start,'budgetSeconds':90,'resultBytes':(p/'compact-probe.json').stat().st_size,'rawBytes':g['result']['evidenceRef']['bytes'],'compactGoalBytes':len(json.dumps(g['result']).encode()),'rawReceiptAndTrustAccepted':True};(p/'compact-measurement.json').write_text(json.dumps(measurement,indent=2));print(measurement)
