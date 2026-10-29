import json,time,hashlib
from pathlib import Path
from ladon.correspondence_check import _check_goal
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_admission import plan_prefix_admission

state=Path('.codex/state/real-bound-admission').resolve();root=state/'project'
clock=json.loads((state/'gate-clock.json').read_text())
source=(root/'PrefixExamples.lean').read_bytes(); context=pinned_toolchain(root)
request={'source':{'path':'PrefixExamples.lean','sha256':hashlib.sha256(source).hexdigest()},'environmentRef':context.context_identity,'predicate':'SequenceBounds.envelope','measure':'SequenceBounds.sample','objectType':'SequenceBounds.Object','parameterType':'Nat','pointType':'Unit'}
plan=plan_prefix_admission(request);(state/'plan.json').write_text(json.dumps(plan,indent=2))
terms=['SequenceBounds.adapter.1','SequenceBounds.adapter.2.1','SequenceBounds.adapter.2.2']
summary=[]
for goal,term in zip(plan['goals'],terms):
 assert time.monotonic()<clock['deadlineMonotonic']
 start=time.monotonic(); result=_check_goal(goal['proposition'],term,root,source,{},pinned_toolchain(root))
 (state/(goal['id']+'.json')).write_text(json.dumps(result,indent=2))
 completion=result.get('completion',{});row={'id':goal['id'],'status':result['status'],'seconds':time.monotonic()-start,'completion':completion.get('status'),'trust':completion.get('trust')}
 summary.append(row);print(row,flush=True)
 if result['status']!='supported':break
(state/'gate-summary.json').write_text(json.dumps(summary,indent=2))
