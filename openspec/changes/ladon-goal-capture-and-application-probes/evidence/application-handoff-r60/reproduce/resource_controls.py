from pathlib import Path
from dataclasses import asdict
import json,os
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd();state=root/'.codex/state/application-handoff-r60';run=Path((state/'run-path').read_text().strip());candidate=Path((root/'.codex/state/application-completion-r59/run-path').read_text().strip());term=json.loads((run/'selection.json').read_text())['proposedTerm'];lean=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean');env=dict(os.environ)
for k in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV'):env.pop(k,None)
base=[str(candidate/'py312/bin/ladon'),'proof-search','goal','complete','--repo-root',str(run/'fixture'),'--capture-file',str(run/'capture-a.stdout'),'--term',term,'--lean-path',str(lean),'--lake-path',str(lean.with_name('lake')),'--format','json']
results={}
for name,options,expected in [('timeout',['--timeout-seconds','0.1'],'timeout'),('memory',['--max-rss-mib','32'],'memory-limit'),('output',['--max-output-mib','1'],'output-limit')]:
 r=run_bounded_target_process(base+options,cwd=Path('/tmp'),env=env,timeout_seconds=20,max_output_bytes=8388608,max_rss_bytes=34359738368);(run/('resource-'+name+'.stdout')).write_text(r.stdout);(run/('resource-'+name+'.stderr')).write_text(r.stderr);row=asdict(r);row.pop('stdout');row.pop('stderr');(run/('resource-'+name+'.command.json')).write_text(json.dumps(row,indent=2)+'\n');assert r.returncode==1,(name,r.stdout[-800:],r.stderr[-800:]);v=json.loads(r.stdout);assert v['status']==expected and not v['trust']['accepted'] and v['replay']['status']=='not-run',v
 results[name]={'status':v['status'],'resourceAccounting':v['resourceAccounting'],'processReceipts':v['processReceipts']};(run/'resource-controls-summary.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'control':name,'status':v['status'],'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes}),flush=True)
