from pathlib import Path
from dataclasses import asdict
import json,os
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd();state=root/'.codex/state/application-handoff-r60';run=Path((state/'run-path').read_text().strip());candidate=Path((root/'.codex/state/application-completion-r59/run-path').read_text().strip())/'candidate';env=dict(os.environ)
for k in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV'):env.pop(k,None)
env['PATH']='/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin:'+env['PATH'];env['TMPDIR']='/home/codex/.cache'
checks=[('installed-distribution',['scripts/installed_distribution_smoke.py','--candidate',str(candidate),'--package-resource','ladon:lean/ladon_source_goal_completion_helper.lean','--package-resource','ladon:lean/ladon_source_goal_helper.lean']),('required-lean-integration',['scripts/lean_integration_gate.py','--candidate',str(candidate),'--required']),('required-portable-benchmarks',['scripts/ladon_benchmarks.py','--candidate',str(candidate),'--required','--output',str(run/'required-portable-benchmark-results.json')])]
rows=[]
for name,args in checks:
 r=run_bounded_target_process(['uv','run','--locked','python']+args,cwd=root,env=env,timeout_seconds=180,max_output_bytes=8388608,max_rss_bytes=34359738368);(run/(name+'.stdout')).write_text(r.stdout);(run/(name+'.stderr')).write_text(r.stderr);row=asdict(r);row.pop('stdout');row.pop('stderr');row['name']=name;rows.append(row);(run/'required-qualification-commands.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({'name':name,'exitCode':r.returncode,'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes}),flush=True);assert r.returncode==0,(name,r.stdout[-2000:],r.stderr[-1000:])
