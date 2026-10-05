import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'src')
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon')
base=root/'.codex/state/application-completion-r58/feasibility'
source=base/'OwnerHave.lean'; helper=base/'helper_self.lean'
b=source.read_bytes()
req={'protocolVersion':'ladon-lean-source-goal-v1/capture','contextRef':'nondep-fixture','module':'FidelityFixture.OwnerHave','filename':'OwnerHave.lean','sourceDigest':'sha256:'+hashlib.sha256(b).hexdigest(),'snapshotPath':str(source),'line':7,'column':13,'requestId':'nondep-fixture'}
cmd=['/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean','--run',str(helper)]
r=run_bounded_target_process(cmd,cwd=root,timeout_seconds=30,max_output_bytes=8*1024*1024,max_rss_bytes=32*1024**3,input_bytes=('LADON_GOAL_REQUEST '+json.dumps(req)+'\n').encode())
receipt={'command':cmd,'cwd':str(root),'request':req,'limits':{'timeoutSeconds':30,'maxOutputBytes':8*1024*1024,'maxRssBytes':32*1024**3},'returncode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'timedOut':r.timed_out,'outputLimited':r.output_limited,'memoryLimited':r.memory_limited,'stdout':r.stdout,'stderr':r.stderr}
(base/'self-rejection-receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'returncode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'timedOut':r.timed_out,'outputLimited':r.output_limited,'memoryLimited':r.memory_limited,'stdoutHead':r.stdout[:3000],'stderr':r.stderr[-1500:]}))
