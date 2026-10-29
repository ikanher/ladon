import json,sys,time
from pathlib import Path
from dataclasses import asdict
from ladon.process_supervisor import run_bounded_target_process
s=Path('.codex/state/real-bound-admission');c=json.loads((s/'gate-clock.json').read_text());remaining=c['deadlineMonotonic']-time.monotonic();assert remaining>0
r=run_bounded_target_process([sys.executable,str(s/'negative_gate.py')],cwd=Path.cwd(),timeout_seconds=remaining,max_rss_bytes=12*1024**3,max_output_bytes=1024**2)
(s/'negative-supervision.json').write_text(json.dumps(asdict(r),indent=2));print(r.stdout,r.stderr,'timeout',r.timed_out)
