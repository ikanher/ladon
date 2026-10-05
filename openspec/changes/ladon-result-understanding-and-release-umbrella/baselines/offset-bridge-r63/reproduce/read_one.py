"""Run one frozen fresh reader and save source changes outside its task."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib,json,os,shutil,sys
from ladon.process_supervisor import run_bounded_target_process
from ladon.lean_toolchain import compiled_library_roots
root=Path('/home/codex/projects/ladon');state=root/'.codex/state/offset-bridge-r63';run=Path((state/'run-path').read_text().strip());qual=Path((state/'qualification-run-path').read_text().strip());name=sys.argv[1];cwd=run/name;reports=run/'reader-output'/name;out=run/'sessions'/name
assert name in json.loads((state/'reader-protocol.json').read_text())['taskOrder'];assert not out.exists(),'Preserve initial attempts; no silent retry.'
assert (state/'qualification-run-path').exists(),'Qualification required before reader sessions.'
protocol=json.loads((state/'reader-protocol.json').read_text());prompt=(state/(name+'-prompt.txt')).read_text();assert hashlib.sha256(prompt.encode()).hexdigest()==protocol['promptHashes'][name]
out.mkdir(parents=True)
def inventory(directory):
 rows={}
 for base,dirs,files in os.walk(directory,followlinks=False):
  dirs[:]=[v for v in dirs if v!='.lake' and not (Path(base)/v).is_symlink()]
  for file in files:
   p=Path(base)/file
   if p.is_symlink():continue
   rows[str(p.relative_to(directory))]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 return rows
before={'source':inventory(cwd),'reports':inventory(reports)};(out/'before.json').write_text(json.dumps(before,indent=2)+'\n');(out/'prompt.txt').write_text(prompt)
argv=['/home/codex/node_modules/.bin/codex','exec','--json','--ephemeral','--ignore-user-config','--skip-git-repo-check','-m','gpt-6-luna','-c','model_reasoning_effort="medium"','-c','approval_policy="never"','-s','workspace-write','--add-dir',str(reports),'-C',str(cwd),'-o',str(out/'final.txt'),prompt]
(out/'reader-argv.json').write_text(json.dumps(argv,indent=2)+'\n')
env=dict(os.environ)
for key in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV'):env.pop(key,None)
leanbin='/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin';env['PATH']=leanbin+':'+env['PATH'];env['LEAN_PATH']=os.pathsep.join(str(p) for p in compiled_library_roots(cwd))
if name == 'augmented':env['PATH']=str(qual/'py312/bin')+':'+env['PATH']
(out/'environment-selection.json').write_text(json.dumps({'leanBinaryDirectory':leanbin,'LEAN_PATH':env['LEAN_PATH'],'ladonAugmentation':str(qual/'py312/bin') if name == 'augmented' else 'excluded by task instruction; ambient executable not OS removed','candidateCommit':json.loads((qual/'identity.json').read_text())['candidateCommit'],'recordedAt':datetime.now(timezone.utc).isoformat()},indent=2)+'\n')
r=run_bounded_target_process([str(root/'.venv/bin/python'),str(state/'session_exec.py'),str(out),str(out/'reader-argv.json')],cwd=cwd,env=env,timeout_seconds=1800,max_output_bytes=8388608,max_rss_bytes=34359738368)
(out/'supervisor.json').write_text(json.dumps(asdict(r),indent=2)+'\n')
after={'source':inventory(cwd),'reports':inventory(reports)};(out/'after.json').write_text(json.dumps(after,indent=2)+'\n')
for area,directory in [('source',cwd),('reports',reports)]:
 for path in after[area]:
  p=out/'work'/area/path;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(directory/path,p)
events=[];parse_errors=[]
for i,line in enumerate((out/'events.jsonl').read_text().splitlines(),1):
 try:events.append(json.loads(line))
 except json.JSONDecodeError as exc:parse_errors.append({'line':i,'error':str(exc)})
commands=[x['item'] for x in events if x.get('type')=='item.completed' and x.get('item',{}).get('type')=='command_execution'];truncations=[x['id'] for x in commands if any(marker in x.get('aggregated_output','') for marker in ('Warning: truncated output','tokens truncated','Output truncated','Output is truncated'))]
(out/'commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
summary={'name':name,'processExitCode':r.returncode,'seconds':r.elapsed_seconds,'peakTreeRssBytes':r.peak_rss_bytes,'timedOut':r.timed_out,'memoryLimited':r.memory_limited,'outputLimited':r.output_limited,'commandCount':len(commands),'commandExitCodes':[x.get('exit_code') for x in commands],'eventBytes':(out/'events.jsonl').stat().st_size,'nativeReportedTruncations':truncations,'parseErrors':parse_errors,'usage':[x['usage'] for x in events if x.get('type')=='turn.completed'],'unassistedInitialAttempt':True,'interventions':[],'completionIsMathematicalOutcomeNotProcessExit':True}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
