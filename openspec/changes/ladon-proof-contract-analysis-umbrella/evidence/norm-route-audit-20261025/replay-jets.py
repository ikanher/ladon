import json,hashlib
from pathlib import Path
from ladon.proof_slice import pinned_toolchain
from ladon.source_goal_capture import SourceGoalCaptureRequest,capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest,complete_source_goal
base=Path('/home/codex/projects/ladon/openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/norm-route-audit-20261025')
root=Path('/home/codex/projects/ladon/.codex/state/navier-stokes-informed-diagnostic/formalization')
original=root/'NavierStokes/SmoothFamilyTorusInverse.lean'
goal=(base/'jet-goal-5.txt').read_text().strip()
term='@NavierStokes.SmoothFamilyTorusInverse.inverse_finiteJets'
source=original.read_text()+'\nexample : '+goal+' := by\n  skip\n'
path=root/'.ladon/norm-route-audit/JetRouteReplay.lean'
path.parent.mkdir(parents=True,exist_ok=True)
with path.open('x') as f:f.write(source)
(base/'JetRouteReplay.lean').write_text(source)
(base/'jet-term.txt').write_text(term+'\n')
ctx=pinned_toolchain(root)
c=capture_source_goal(SourceGoalCaptureRequest(root,str(path.relative_to(root)),'JetRouteReplay',len(source.splitlines()),4,ctx))
(base/'jet-capture.json').write_text(json.dumps(c,indent=2)+'\n')
print('capture:',c['status'],flush=True)
assert c['status']=='captured',c.get('diagnostic')
r=complete_source_goal(SourceGoalCompletionRequest(root,c['capture'],term,ctx))
(base/'jet-completion.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'status':r['status'],'diagnostic':r['diagnostic'],'trust':r['trust'],'resources':r['resourceAccounting']}),flush=True)
assert r['status']=='completed'
