import json,time,sys,os
from dataclasses import asdict
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
state=Path('.codex/state/real-bound-admission');clock=json.loads((state/'gate-clock.json').read_text());remaining=clock['deadlineMonotonic']-time.monotonic();assert remaining>0
r=run_bounded_target_process([sys.executable,str(state/'check_gate.py')],cwd=Path.cwd(),env=dict(os.environ),timeout_seconds=remaining,max_rss_bytes=12*1024**3,max_output_bytes=1024**2)
(state/'gate-supervision.json').write_text(json.dumps(asdict(r),indent=2));print(r.stdout,r.stderr,flush=True)
