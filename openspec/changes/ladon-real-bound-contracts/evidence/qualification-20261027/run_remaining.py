from dataclasses import asdict
import json,os,sys
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
state=Path('.codex/state/task41');root=Path.cwd()
for name in ['derivative','binding','import']:
 run=run_bounded_target_process([sys.executable,str(state/('qualify_'+name+'.py'))],cwd=root,
  timeout_seconds=2400,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES,env=os.environ)
 (state/(name+'-process.json')).write_text(json.dumps(asdict(run),indent=2)+'\n')
 (state/(name+'.log')).write_text(run.stdout+'\n'+run.stderr)
 print(name,run.returncode,round(run.elapsed_seconds,2),flush=True)
 assert run.succeeded,run.stdout[-2000:]+run.stderr[-2000:]
