"""Bounded named command within the fixed N.3c development session."""
from pathlib import Path
import dataclasses,datetime,json,os,sys
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon');e=Path(__file__).resolve().parent
session=json.loads((e/'SESSION.json').read_text());remaining=(datetime.datetime.fromisoformat(session['deadlineAtUtc'])-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
if remaining<=0:raise SystemExit('N.3c deadline exceeded')
name,*cmd=sys.argv[1:];assert not (e/(name+'.request.json')).exists(),'Output collision'
request={'argv':cmd,'cwd':session['project'],'startUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timeoutSeconds':min(600,remaining)}
(e/(name+'.request.json')).write_text(json.dumps(request,indent=2)+'\n')
env=dict(os.environ);env['PYTHONPATH']=str(root/'temp/c05-roundtrip-diagnosis-r01/src')
for key in ['LEAN_PATH','LEAN_SRC_PATH','LAKE_PACKAGES_DIR']:env.pop(key,None)
r=run_bounded_target_process(cmd,cwd=Path(session['project']),timeout_seconds=min(600,remaining),max_output_bytes=16*1024**2,max_rss_bytes=12*1024**3,env=env,observe_resources=True)
s=dataclasses.asdict(r)
for k in ['stdout','stderr']:(e/(name+'.'+k)).write_text(s.pop(k))
(e/(name+'.process.json')).write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps({'name':name,'exitCode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'stdoutTail':r.stdout[-2400:],'stderrTail':r.stderr[-1200:]}))
