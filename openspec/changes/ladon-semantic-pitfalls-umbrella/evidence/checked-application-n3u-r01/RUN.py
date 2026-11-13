"""One bounded operation in the fixed N.3u session; retain raw evidence."""
from pathlib import Path
import dataclasses,datetime,json,os,sys
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon');e=Path(__file__).resolve().parent
session=json.loads((e/'SESSION.json').read_text());deadline=datetime.datetime.fromisoformat(session['deadlineAtUtc'])
remaining=(deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
if remaining<=0:raise SystemExit('Session deadline exceeded')
operation,name=sys.argv[1:];inputs=json.loads((e/'INPUTS.json').read_text())[name]
args=[str(root/'.venv/bin/python'),'-m','ladon.entrypoint','proof-search','goal',operation,'--repo-root',session['project'],'--toolchain-mode','explicit','--lean-path','/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean','--lake-path','/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lake','--timeout-seconds',str(max(1,int(min(600,remaining)))),'--max-rss-mib','12288','--max-output-mib','16','--format','json','--output',str(e/(name+'-'+operation+'.json'))]
if operation=='capture':args+=['--source',inputs['source'],'--module',inputs['module'],'--line',str(inputs['line']),'--column',str(inputs['column']),'--expected-source-digest','sha256:'+inputs['sha256']]
else:args+=['--capture-file',str(e/(name+'-capture.json')),'--term',(e/(name+'.term')).read_text()]
label=name+'-'+operation
assert not (e/(label+'.request.json')).exists(),'Refuse operation collision'
start=datetime.datetime.now(datetime.timezone.utc);(e/(label+'.request.json')).write_text(json.dumps({'startedAtUtc':start.isoformat(),'argv':args,'cwd':str(root)},indent=2)+'\n')
env=dict(os.environ);env['PYTHONPATH']=str(root/'src')
for k in ['LEAN_PATH','LEAN_SRC_PATH','LAKE_PACKAGES_DIR']:env.pop(k,None)
r=run_bounded_target_process(args,cwd=root,timeout_seconds=min(600,remaining),max_output_bytes=16*1024**2,max_rss_bytes=12*1024**3,env=env,observe_resources=True)
record=dataclasses.asdict(r)
for k in ['stdout','stderr']:(e/(label+'.'+k)).write_text(record.pop(k))
(e/(label+'.process.json')).write_text(json.dumps(record,indent=2)+'\n')
report=json.loads((e/(label+'.json')).read_text()) if (e/(label+'.json')).exists() else {}
print(json.dumps({'operation':label,'exitCode':r.returncode,'status':report.get('status'),'elapsedSeconds':r.elapsed_seconds,'keys':list(report)}))
