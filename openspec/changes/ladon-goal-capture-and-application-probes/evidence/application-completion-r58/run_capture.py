import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'src')
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon')
base=root/'.codex/state/application-completion-r58/feasibility'
source=base/'Owner.lean'
b=source.read_bytes()
req={'protocolVersion':'ladon-lean-source-goal-v1/capture','contextRef':'test-context','module':'FidelityFixture.Owner','filename':'Owner.lean','sourceDigest':'sha256:'+hashlib.sha256(b).hexdigest(),'snapshotPath':str(source),'line':4,'column':13,'requestId':'feasibility','contextRef':'test-context'}
cmd=['/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean','--run',str(base/'ladon_source_goal_helper.lean')]
r=run_bounded_target_process(cmd,cwd=root,env=None,timeout_seconds=30,max_output_bytes=8*1024*1024,max_rss_bytes=8*1024**3,input_bytes=('LADON_GOAL_REQUEST '+json.dumps(req)+'\n').encode())
print(json.dumps({'command':cmd,'returncode':r.returncode,'elapsed':r.elapsed_seconds,'rss':r.peak_rss_bytes,'timedOut':r.timed_out,'stdoutTail':r.stdout[-1000:],'stderr':r.stderr[-1000:]},indent=2))
