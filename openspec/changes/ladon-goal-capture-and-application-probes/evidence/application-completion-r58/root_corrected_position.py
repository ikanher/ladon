from pathlib import Path
from dataclasses import asdict
import hashlib,json
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon');base=root/'.codex/state/application-completion-r58/feasibility'
source=base/'Owner.lean';data=source.read_bytes()
req={'protocolVersion':'ladon-lean-source-goal-v1/capture','contextRef':'root-position-control','module':'FidelityFixture.Owner','filename':'Owner.lean','sourceDigest':'sha256:'+hashlib.sha256(data).hexdigest(),'snapshotPath':str(source),'line':5,'column':13,'requestId':'root-position-control'}
cmd=['/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean','--run',str(base/'ladon_source_goal_helper.lean')]
r=run_bounded_target_process(cmd,cwd=root,timeout_seconds=30,max_output_bytes=8*1024**2,max_rss_bytes=32*1024**3,input_bytes=('LADON_GOAL_REQUEST '+json.dumps(req)+'\n').encode())
out=root/'.codex/state/application-completion-r58/root-corrected-position.json';out.write_text(json.dumps({'request':req,'limits':{'timeoutSeconds':30,'maxRssBytes':32*1024**3,'maxOutputBytes':8*1024**2},'process':asdict(r),'sourceUnchanged':source.read_bytes()==data},indent=2)+'\n')
print({'exit':r.returncode,'seconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'stderr':r.stderr,'stdoutStart':r.stdout[:300]})
