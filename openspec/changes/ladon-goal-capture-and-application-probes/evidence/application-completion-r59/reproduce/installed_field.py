"""Root-operated ordinary installed CLI checks; no API/test fixture imports."""
from pathlib import Path
from dataclasses import asdict
import hashlib,json,os
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd(); state=root/'.codex/state/application-completion-r59';run=Path((state/'run-path').read_text().strip());out=run/'field-retest';out.mkdir();repo=out/'value-project';repo.mkdir()
lean=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean');cli=run/'py312/bin/ladon'
(repo/'lean-toolchain').write_text('leanprover/lean4:v4.32.1\n')
source='namespace Owner\nvariable {α : Type} [Inhabited α]\nexample (x : α) (h : x = x) : x = x := by\n  have z : x = x := h\n  skip\nend Owner\n'
(repo/'Owner.lean').write_text(source)
env=dict(os.environ)
for k in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV'):env.pop(k,None)
rows=[]
def hashes(project):return {str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file()}
def command(name,argv):
 r=run_bounded_target_process(argv,cwd=Path('/tmp'),env=env,timeout_seconds=35,max_output_bytes=8388608,max_rss_bytes=34359738368)
 (out/(name+'.stdout')).write_text(r.stdout);(out/(name+'.stderr')).write_text(r.stderr)
 row=asdict(r);row.pop('stdout');row.pop('stderr');row['name']=name;rows.append(row)
 (out/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert r.returncode==0 and not any((r.timed_out,r.memory_limited,r.output_limited)),(name,r.stdout,r.stderr)
 return r.stdout
base=[str(cli),'proof-search','goal']; options=['--repo-root',str(repo),'--lean-path',str(lean),'--lake-path',str(lean.with_name('lake')),'--timeout-seconds','30']
before=hashes(repo);cap_path=out/'capture.json'
command('capture',base+['capture']+options+['--source','Owner.lean','--module','Owner','--line','5','--column','6','--format','json','--output',str(cap_path)])
cap=json.loads(cap_path.read_text());assert cap['status']=='captured',cap
complete=base+['complete']+options+['--capture-file',str(cap_path)]
full=json.loads(command('completion',complete+['--term','z','--format','json']))
assert full['status']=='completed' and full['replay']['status']=='accepted' and full['trust']['accepted'] and full['trust']['observedAxioms']==[],full
assert full['captureId']==cap['capture']['captureId'] and full['application']['originalGoal']['typeStructural']==cap['capture']['goal']['typeStructural']
partial=json.loads(command('partial',complete+['--term','?_','--format','json']))
assert partial['status']=='incomplete' and partial['replay']['status']=='not-run',partial
assert partial['application']['residualGoals'][0]['localContext']==cap['capture']['goal']['localContext']
text=command('partial-text',complete+['--term','?_','--format','text','--progress'])
assert 'x = x' in text and text.index('remaining obligation')<text.index('trust'),text
after=hashes(repo);assert before==after
summary={'status':'passed','candidate':json.loads((run/'identity.json').read_text()),'scope':'root-operated installed CLI capture and original-goal complete/residual/text, not discovery, fixed-epoch, reader benefit or prose correspondence','commands':len(rows),'wallSeconds':sum(r['elapsed_seconds'] for r in rows),'peakRssBytes':max(r['peak_rss_bytes'] or 0 for r in rows),'sourceBefore':before,'sourceAfter':after,'statuses':{'capture':cap['status'],'completion':full['status'],'partial':partial['status']},'captureId':cap['capture']['captureId']}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
