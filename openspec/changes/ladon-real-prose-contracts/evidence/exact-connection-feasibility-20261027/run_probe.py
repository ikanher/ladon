import json,os,sys,time
from pathlib import Path
from dataclasses import asdict
from ladon.process_supervisor import run_bounded_target_process
b=Path('.codex/state/real-prose-connection').resolve()
budget=b/'probe-budget.json'
if not budget.exists():budget.write_text(json.dumps({'deadlineMonotonic':time.monotonic()+600,'seconds':600,'maxRssBytes':12*1024**3,'maxOutputBytes':8*1024**2})+'\n')
deadline=json.loads(budget.read_text())['deadlineMonotonic'];assert deadline>time.monotonic()
label=sys.argv[1];out=b/(label+'-process.json');assert not out.exists()
command=[sys.executable,str(b/'execute_probe.py'),*sys.argv[2:]]
r=run_bounded_target_process(command,cwd=Path('.').resolve(),env={**os.environ,'PYTHONPATH':str(Path('src').resolve())},timeout_seconds=deadline-time.monotonic(),max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
out.write_text(json.dumps(asdict(r),indent=2)+'\n')
print({'exit':r.returncode,'seconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'stdout':r.stdout[-1500:],'stderr':r.stderr[-1000:]})
assert not any([r.timed_out,r.memory_limited,r.output_limited]),'Stop progress and report resource stop to user.'
