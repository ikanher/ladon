import json,os,sys
from dataclasses import asdict
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd()
original=root/'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/informed-derivative-diagnostic-20261025'
out=root/'openspec/changes/ladon-scoped-slice-traversal/evidence'
for loss in (5,4):
    command=json.loads((original/f'application-loss-{loss}-command.json').read_text())['command']
    command[command.index('--output')+1]=str(out/f'application-loss-{loss}.json')
    with (out/f'application-loss-{loss}-command.json').open('x') as f:
        json.dump({'command':command,'state':'started'},f);f.flush()
        r=run_bounded_target_process(command,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src')},timeout_seconds=120,max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
        f.seek(0);f.truncate();json.dump(asdict(r),f,indent=2);f.write('\n')
    print(loss,r.returncode,r.elapsed_seconds,r.peak_rss_bytes,flush=True)
    if r.memory_limited:sys.exit('Stop progress and report back to user: the 12 GiB memory limit was not enough.')
    if r.timed_out or r.output_limited:sys.exit('Bounded control replay interrupted.')
