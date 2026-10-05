from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,re
root=Path('/home/codex/projects/ladon');state=root/'.codex/state/benefit-readers-r62';run=Path((state/'run-path').read_text().strip());qual=Path((state/'qualification-run-path').read_text().strip());out=root/'openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/mathematical-benefit-r62';out.mkdir(exist_ok=True)
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
records=[]
for name in ['application-ordinary','application-augmented','exposition-ordinary','exposition-augmented']:
 source=run/'sessions'/name
 for p in source.rglob('*'):
  if p.is_file():copy(p,out/'sessions'/name/p.relative_to(source))
 summary=json.loads((source/'summary.json').read_text());before=json.loads((source/'before.json').read_text());after=json.loads((source/'after.json').read_text());commands=json.loads((source/'commands.json').read_text());assert not summary['parseErrors']
 unchanged=all(before['source'][file]==after['source'][file] for file in ['TaskOne.lean','TaskTwo.lean','lean-toolchain']);assert unchanged
 ladon_calls=[c['id'] for c in commands if re.search(r'\bladon\s+(?:result|proof-search|--help)',c['command'])];assert not ladon_calls
 file_events=[d['item'] for d in map(json.loads,(source/'events.jsonl').read_text().splitlines()) if d.get('type')=='item.completed' and d.get('item',{}).get('type')=='file_change']
 records.append({**summary,'originalTaskSourcesUnchanged':unchanged,'ladonCommandCount':len(ladon_calls),'fileChangeEvents':file_events})
for name in ['contract.md','reader-protocol.json','task-inventory.json','budget.json','qualified-candidate.json','frozen-verification.json','preflight-adjudication.json','shell-path-preflight.json','prepared-identity.json']:
 copy(state/name,out/name)
for name in ['identity.json','unchanged-core-parity.json','clean-baseline.command.json','required-qualification-commands.json','required-portable-benchmark-results.json','py311-summary.json','py312-summary.json','py311-contracts.command.json','py312-contracts.command.json']:
 copy(qual/name,out/'qualification'/name)
for name in ['baseline-final-outer-receipt.json','install-final-outer-receipt.json','failed-baseline-outer-receipt.json']:
 copy(state/name,out/'qualification'/name)
for py in ['py311','py312']:
 save(out/'qualification'/(py+'-origins.json'),json.loads((qual/(py+'-origin.log')).read_text()))
 copy(qual/(py+'-contracts.log'),out/'qualification'/(py+'-contracts.txt'))
for folder in ['recorder-preflight','recorder-preflight-v2','lean-preflight','preparation','preparation-v2','preparation-v3','preparation-v4']:
 for p in (run/folder).rglob('*'):
  if p.is_file() and p.suffix!='.zip':copy(p,out/'preparation'/folder/p.relative_to(run/folder))
for name in ['passages.json','evaluation-guide.json','selection.json','source-inventory.json']:
 copy(run/'shared'/name,out/'fixture'/name)
for name in ['TaskOne.lean','TaskTwo.lean']:copy(run/'application-ordinary'/name,out/'fixture'/name)
# Retain the original failing proposals and every assertion-preserving replacement.
for name in ['frozen-original-test.py','frozen-refactored-test.py','maintained-red.txt','proposed-red-run.txt']:
 copy(state/name,out/'failed-attempts'/name)
for folder in ['red','green']:
 for p in (state/folder).rglob('*'):
  if p.is_file() and p.suffix in {'.md','.py','.patch','.json','.txt'}:copy(p,out/'portfolio'/folder/p.relative_to(state/folder))
for name in ['snapshot.py','qualify.py','required.py','qualification.py','session_exec.py','read_one.py','collect.py','prepare_readers.py','prepare_guide.py','prepare_public.py','prepare_public_v2.py','prepare_public_v3.py','prepare_public_v4.py','preflight_recorder.py','preflight_recorder_v2.py','preflight_lean.py']:
 copy(state/name,out/'reproduce'/name)
# Root semantic adjudication; these are attributed evaluations, not Lean proofs of prose.
expected=json.loads((run/'shared/passages.json').read_text())['passages'];judgments=[]
for arm in ['ordinary','augmented']:
 path=run/'reader-output'/('exposition-'+arm)/'revisions.json';revisions=json.loads(path.read_text())['revisions'];assert {r['id'] for r in revisions}=={r['id'] for r in expected}
 by_id={r['id']:r for r in revisions};assert all(by_id[r['id']]['original_text']==r['paragraph'] for r in expected)
 assert by_id['passage-42']['revised_text']==by_id['passage-42']['original_text']
 assert 'boundary' in by_id['passage-68']['revised_text'] and 'narrows' in by_id['passage-68']['reason']
 judgments.append({'arm':arm,'control42Unchanged':True,'coverage17':'Correctly separates supplied transcript bindings from conventional average-only claim; absence not falsehood','premise68':'Adds boundary nonnegativity and explicitly narrows original statement; no original stronger-goal completion claimed','proseAndProofStrategy':'Separate attributed fidelity/method judgment retained','freshLeanStep':arm=='ordinary','evaluator':'root agent, source/type/evidence inspection; not independent human labels','revisionsPath':'sessions/exposition-'+arm+'/work/reports/revisions.json'})
accept={'schema':'ladon-mathematical-benefit-r62-v1','recordedAt':datetime.now(timezone.utc).isoformat(),'candidate':json.loads((qual/'identity.json').read_text()),'engineering':json.loads((state/'qualified-candidate.json').read_text()),'sessions':records,'application':{'ordinaryA':'Compiler-accepted original-goal-equivalent scratch theorem; transitive axioms propext/Classical.choice/Quot.sound observed','ordinaryB':'Original-context partial application checked, exact boundary-gap residual observed; no impossibility claim','augmentedA':'Compiler-accepted original-goal-equivalent scratch theorem; same permitted axioms observed','augmentedB':'Exact premise diagnosed from type and checked narrowed conditional theorem; no fresh original-B partial checking; original goal remains unresolved','ladonUsed':False,'comparativeApplicationBenefit':'unestablished'},'exposition':judgments,'readerBenefit':'Ladon-specific benefit unestablished; same-guide ordinary tools suffice for these first attempts','interventions':[],'readerRetries':0,'rootPreparationFailuresRetained':True,'recordingLimit':'Native event bytes and known generated outputs preserved; no universal filesystem capture. Ordinary exposition /tmp proof was copied after session and remains verbatim in recorded creation command. No native reported output truncation observed; this is not unlimited-output guarantee.','task9.1':'open','umbrella':{'done':33,'total':50},'nextGate':'Pro decision on narrowing/freeze versus a materially different task; do not add infrastructure or repeat favorable prompts by default'}
save(out/'acceptance.json',accept)
resources=['session,seconds,peak_tree_rss_bytes,lean_executed,ladon_commands']
for row in records:resources.append(f"{row['name']},{row['seconds']:.6f},{row['peakTreeRssBytes']},{row['name']!='exposition-augmented'},0")
(out/'resources.csv').write_text('\n'.join(resources)+'\n')
print(json.dumps({'output':str(out),'readerSessions':len(records),'readerSeconds':sum(r['seconds'] for r in records),'peakReaderGiB':max(r['peakTreeRssBytes'] for r in records)/2**30,'readerBenefit':accept['readerBenefit']}))
