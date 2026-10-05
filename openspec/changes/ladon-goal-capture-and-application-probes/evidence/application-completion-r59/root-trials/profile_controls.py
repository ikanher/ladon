from pathlib import Path
from dataclasses import asdict
import tempfile,json,sys
sys.path.insert(0,str(Path.cwd()/'tests'))
from test_source_goal_completion_lean import _value_context,_capture,_request
from ladon.source_goal_completion import complete_source_goal
from ladon.process_supervisor import run_bounded_target_process
records=[]
def observer(command,**options):
 result=run_bounded_target_process(command,**options)
 records.append({'process':asdict(result),'input':options.get('input_bytes',b'').decode()})
 return result
results={}
with tempfile.TemporaryDirectory(prefix='ladon-completion-self-') as d:
 root=Path(d);source,ctx,cap=_value_context(root,'_example (x := x) h')
 r=complete_source_goal(_request(root,ctx,cap,'z'),runner=observer);results['selfThroughValue']={'capture':cap,'result':r}
 Path('.codex/state/application-completion-r59/root-trials/self-through-value-results.json').write_text(json.dumps({'results':results,'processes':records},indent=2))
 assert r['status']=='rejected',r
 assert 'implementation-detail' in r['diagnostic']['message'],r
with tempfile.TemporaryDirectory(prefix='ladon-completion-data-') as d:
 root=Path(d);source,ctx,cap=_capture(root,'example (x : Nat) : Nat := by\n  let z := x\n  skip\n',3,6)
 r=complete_source_goal(_request(root,ctx,cap,'z'),runner=observer);results['dataGoal']={'capture':cap,'result':r}
 assert r['status']=='completed',r
 assert r['trust']['observedAxioms']==[],r
out=Path('.codex/state/application-completion-r59/root-trials/profile-controls-results.json')
out.write_text(json.dumps({'results':results,'processes':records},indent=2))
print(json.dumps({k:v['result']['status'] for k,v in results.items()}))
