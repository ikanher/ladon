from pathlib import Path
from dataclasses import asdict
import json,os,sys
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd();state=root/'.codex/state/application-handoff-r60';run=Path((state/'run-path').read_text().strip());candidate=Path((root/'.codex/state/application-completion-r59/run-path').read_text().strip());capture=json.loads((run/'capture-b.stdout').read_text());selection=json.loads((run/'selection.json').read_text());localnames=[l['userName'] for l in capture['capture']['goal']['localContext'] if not l['implementationDetail']];term=selection['selected']['candidateName']+' '+' '.join(localnames)+' ?_';(run/'partial-proposal.json').write_text(json.dumps({'selectedFrom':str(run/'selection.json'),'captureId':capture['capture']['captureId'],'orderedCapturedLocalsUsed':localnames,'explicitMissingArgument':'?_','term':term},indent=2)+'\n')
lean=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean');env=dict(os.environ)
for k in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV'):env.pop(k,None)
mode=sys.argv[1] if len(sys.argv)>1 else 'json';name='completion-b-'+mode
argv=[str(candidate/'py312/bin/ladon'),'proof-search','goal','complete','--repo-root',str(run/'fixture'),'--capture-file',str(run/'capture-b.stdout'),'--term',term,'--lean-path',str(lean),'--lake-path',str(lean.with_name('lake')),'--timeout-seconds','30','--format',mode]
r=run_bounded_target_process(argv,cwd=Path('/tmp'),env=env,timeout_seconds=55,max_output_bytes=8388608,max_rss_bytes=34359738368);(run/(name+'.stdout')).write_text(r.stdout);(run/(name+'.stderr')).write_text(r.stderr);row=asdict(r);row.pop('stdout');row.pop('stderr');(run/(name+'.command.json')).write_text(json.dumps(row,indent=2)+'\n');assert r.returncode==0,(r.stdout[-1000:],r.stderr[-1000:])
expected='0 ≤ Mf.DP.fixedEpochCenterGap point h boundary'
if mode=='json':
 result=json.loads(r.stdout);assert result['status']=='incomplete' and result['replay']['status']=='not-run' and not result['trust']['accepted'],result
 residual=result['application']['residualGoals'];assert len(residual)==1 and residual[0]['typeDisplay']==expected,residual
 assert result['application']['originalGoal']['typeStructural']==capture['capture']['goal']['typeStructural']
 (run/'completion-b-summary.json').write_text(json.dumps({'status':result['status'],'residual':residual[0],'resources':result['resourceAccounting'],'replay':result['replay']['status']},indent=2)+'\n')
else:
 assert 'application outcome: incomplete' in r.stdout and 'remaining obligation: '+expected in r.stdout
 assert r.stdout.index('remaining obligation:')<r.stdout.index('transitive trust'),r.stdout
print(json.dumps({'status':'passed','format':mode,'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes,'residual':expected}))
