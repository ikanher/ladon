from pathlib import Path
import json,os
from dataclasses import asdict
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon');state=root/'.codex/state/benefit-readers-r62';run=Path((state/'run-path').read_text().strip());cli='/home/codex/.cache/ladon-qualification-r61/ladon-exposition-scope-r61-z3sf9fbx/py312/bin/ladon';shared=run/'shared';out=run/'preparation-v4';out.mkdir();rows=[]
commands=[('result-export',[cli,'result','export',str(shared/'manifest.json'),'--selection',str(shared/'selection.json'),'--output',str(shared/'result.zip')])]
for name,argv in commands:
 r=run_bounded_target_process(argv,cwd=Path('/tmp'),timeout_seconds=120,max_output_bytes=8388608,max_rss_bytes=34359738368);(out/(name+'.stdout')).write_text(r.stdout);(out/(name+'.stderr')).write_text(r.stderr);x=asdict(r);x.pop('stdout');x.pop('stderr');rows.append(x);(out/'commands.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({'operation':name,'exitCode':r.returncode,'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes,'stdout':r.stdout[-700:],'stderr':r.stderr[-700:]}),flush=True);assert r.returncode==0 and not any(x[k] for k in ['timed_out','memory_limited','output_limited'])
