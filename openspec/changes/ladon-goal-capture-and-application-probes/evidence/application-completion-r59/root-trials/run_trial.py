import json
import sys
from dataclasses import asdict
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd(); directory=root/'.codex/state/application-completion-r59/root-trials'
budget_path=directory/'budget.json';budget=json.loads(budget_path.read_text())
remaining=budget['budgetSeconds']-budget['chargedUpperBoundSeconds']
if remaining < 1: raise SystemExit('cumulative integration budget exhausted')
label=sys.argv[1];path=directory/(label+'.json')
if path.exists(): raise SystemExit('trial path already exists; preserve historical bytes')
r=run_bounded_target_process(sys.argv[2:],cwd=root,timeout_seconds=min(60,remaining),max_output_bytes=8388608,max_rss_bytes=34359738368)
path.write_text(json.dumps(asdict(r),indent=2))
budget['chargedUpperBoundSeconds']+=r.elapsed_seconds
budget['trials'].append({'path':str(path.relative_to(root)),'chargedSeconds':r.elapsed_seconds})
budget_path.write_text(json.dumps(budget,indent=2))
print(json.dumps({'returnCode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'budgetRemainingSeconds':budget['budgetSeconds']-budget['chargedUpperBoundSeconds'],'output':r.stdout[-9000:],'stderr':r.stderr[-1000:]}))
