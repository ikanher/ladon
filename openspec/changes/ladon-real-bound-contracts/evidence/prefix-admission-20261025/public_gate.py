import json,sys,time
from pathlib import Path
from dataclasses import asdict
from ladon.process_supervisor import run_bounded_target_process
state=Path('.codex/state/real-bound-admission').resolve();root=state/'consumer-project'
clock=json.loads((state/'gate-clock.json').read_text())
remaining=clock['deadlineMonotonic']-time.monotonic();assert remaining>0
command=[sys.executable,'-m','ladon.entrypoint','investigation','contract','check-prefix-laws','--root',str(root),'--input',str(state/'consumer-plan.json'),'--terms',str(state/'consumer-terms.json'),'--timeout-seconds',str(remaining),'--output',str(state/'public-result.json')]
r=run_bounded_target_process(command,cwd=Path.cwd(),timeout_seconds=remaining,max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
receipt=asdict(r)
# CLI writes the full evidence to its immutable output file.
receipt['stdout']=r.stdout[:500];(state/'public-command.json').write_text(json.dumps(receipt,indent=2))
print('public exit',r.returncode, 'stderr',r.stderr[:500],flush=True)
if (state/'public-result.json').exists(): print(json.loads((state/'public-result.json').read_text())['status'],flush=True)
