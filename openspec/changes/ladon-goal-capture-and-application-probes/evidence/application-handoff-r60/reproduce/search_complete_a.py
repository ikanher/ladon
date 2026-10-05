from pathlib import Path
from dataclasses import asdict
import json,os
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd();state=root/'.codex/state/application-handoff-r60';run=Path((state/'run-path').read_text().strip());candidate=Path((root/'.codex/state/application-completion-r59/run-path').read_text().strip());cli=candidate/'py312/bin/ladon';matrix=(root/'../lean/matrix-factorization').resolve();repo=run/'fixture';lean=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean');capture=json.loads((run/'capture-a.stdout').read_text());env=dict(os.environ)
for k in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV'):env.pop(k,None)
def command(name,argv):
 r=run_bounded_target_process(argv,cwd=Path('/tmp'),env=env,timeout_seconds=55,max_output_bytes=8388608,max_rss_bytes=34359738368);(run/(name+'.stdout')).write_text(r.stdout);(run/(name+'.stderr')).write_text(r.stderr);row=asdict(r);row.pop('stdout');row.pop('stderr');(run/(name+'.command.json')).write_text(json.dumps(row,indent=2)+'\n');print(json.dumps({'name':name,'returnCode':r.returncode,'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes}),flush=True);assert r.returncode==0,(name,r.stdout[-1000:],r.stderr[-1000:]);return json.loads(r.stdout)
command('index-build',[str(cli),'proof-search','index','build','--repo-root',str(run/'selected-source-search'),'--index',str(run/'selected-source.sqlite'),'--format','json'])
result=command('search-fresh',[str(cli),'proof-search','search','type-text','--repo-root',str(run/'selected-source-search'),'--index',str(run/'selected-source.sqlite'),'--pattern','fixedEpochCenterGap','--scope','module','--root','Mf.DP.PoissonFixedEpochCenterGapPropagation','--limit','8','--freshness','verify','--format','json'])
assert result['freshness']=='verified-fresh' and not result['truncated'],result
normalize=lambda s:s.replace('Mf.DP.','').strip()
goal=normalize(capture['capture']['goal']['typeDisplay']);rows=[r for r in result['results'] if normalize(r['renderedType'].rsplit(' : ',1)[-1])==goal];assert len(rows)==1,rows
selected=rows[0];locals_=[l['userName'] for l in capture['capture']['goal']['localContext'] if not l['implementationDetail']];term=selected['candidateName']+' '+' '.join(locals_)
(run/'selection.json').write_text(json.dumps({'basis':'unique lexical conclusion-text match after documented namespace normalization; advisory selection, not formal matching','suppliedTheoremName':False,'operator':'root already familiar with expected mathematical task; not a blind reader','pattern':'goal function token fixedEpochCenterGap','selected':selected,'orderedCapturedLocalsUsed':locals_,'proposedTerm':term},indent=2)+'\n')
result=command('completion-a',[str(cli),'proof-search','goal','complete','--repo-root',str(repo),'--capture-file',str(run/'capture-a.stdout'),'--term',term,'--lean-path',str(lean),'--lake-path',str(lean.with_name('lake')),'--timeout-seconds','30','--format','json'])
(run/'completion-a-summary.json').write_text(json.dumps({'status':result['status'],'replayStatus':result['replay']['status'],'trust':result['trust'],'diagnostic':result['diagnostic'],'resources':result['resourceAccounting']},indent=2)+'\n')
assert result['status']=='completed',result
assert result['application']['originalGoal']['typeStructural']==capture['capture']['goal']['typeStructural']
print(json.dumps({'status':result['status'],'axioms':result['trust']['observedAxioms']}))
