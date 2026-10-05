from pathlib import Path
import json,os
from dataclasses import asdict
from ladon.process_supervisor import run_bounded_target_process
from ladon.lean_toolchain import compiled_library_roots
root=Path('/home/codex/projects/ladon');state=root/'.codex/state/benefit-readers-r62';run=Path((state/'run-path').read_text().strip());repo=run/'application-ordinary';out=run/'lean-preflight';out.mkdir();lean=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean');env=dict(os.environ);env['LEAN_PATH']=os.pathsep.join(str(p) for p in compiled_library_roots(repo));env['PATH']=str(lean.parent)+':'+env['PATH']
records=[]
for task,name,tactic in [('TaskOne','preflightOne','exact?'),('TaskTwo','preflightTwo','apply?')]:
 code=(repo/(task+'.lean')).read_text().replace('example (','theorem '+name+' (',1).replace('  skip\n','  '+tactic+'\n')+'\n#print axioms '+name+'\n'
 p=repo/(name+'.lean');p.write_text(code)
 r=run_bounded_target_process([str(lean),str(p)],cwd=repo,env=env,timeout_seconds=60,max_output_bytes=8388608,max_rss_bytes=34359738368)
 (out/(task+'.stdout')).write_text(r.stdout);(out/(task+'.stderr')).write_text(r.stderr);x=asdict(r);x.pop('stdout');x.pop('stderr');x['source']=code;records.append(x)
 print(json.dumps({'name':name,'exitCode':r.returncode,'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes,'outputTail':r.stdout[-1500:],'stderr':r.stderr[-400:]}),flush=True)
(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
# Keep solved preflight work outside the subsequent reader task.
for name in ['preflightOne','preflightTwo']:(repo/(name+'.lean')).rename(out/(name+'.lean'))
assert records[0]['returncode']==0
assert records[1]['returncode']!=0 and 'fixedEpochCenterGap point h boundary' in (out/'TaskTwo.stdout').read_text()
