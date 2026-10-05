from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path.cwd();state=root/'.codex/state/compaction-r63';q=Path((state/'qualification-run-path').read_text().strip());out=root/'openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/compaction-maintenance-r63';out.mkdir(exist_ok=True)
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
identity=json.loads((q/'identity.json').read_text());prior=Path('/home/codex/.cache/ladon-qualification-r62/ladon-benefit-readers-r62-i1tsbx5u/candidate');changed=[];same=[]
for v in json.loads((q/'source-inventory.json').read_text()):
 if not v['path'].startswith('src/ladon/'):continue
 p=q/'candidate'/v['path']
 if p.is_file():
  rel=p.relative_to(q/'candidate');old=prior/rel
  if old.exists() and old.read_bytes()==p.read_bytes():same.append(str(rel))
  else:changed.append(str(rel))
assert changed==['src/ladon/result_inspection_page.py'],changed
for folder in ['src','tests']:
 for v in json.loads((q/'source-inventory.json').read_text()):
  if v['path'].startswith(folder+'/'):
   p=root/v['path'];assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],p
assert hashlib.sha256((root/'.git/index').read_bytes()).hexdigest()==identity['sourceIndexSha256']
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==identity['sourceHead']
for n in ['identity.json','clean-baseline.command.json','py311-contracts.command.json','py312-contracts.command.json','py311-summary.json','py312-summary.json','required-qualification-commands.json','required-portable-benchmark-results.json']:
 copy(q/n,out/'qualification'/n)
for py in ['py311','py312']:
 copy(q/(py+'-contracts.log'),out/'qualification'/(py+'-contracts.txt'));save(out/'qualification'/(py+'-origins.json'),json.loads((q/(py+'-origin.log')).read_text()))
for version,pathfile in [('v1','failed-qualification-run-path'),('v2','failed-qualification-run-path-v2')]:
 failed=Path((state/pathfile).read_text().strip());copy(failed/'identity.json',out/'failed-attempts'/version/'identity.json');copy(failed/'clean-baseline.command.json',out/'failed-attempts'/version/'command.json');(out/'failed-attempts'/version/'quality-failure.txt').write_text((failed/'clean-baseline.log').read_text()[-2500:])
copy(state/'maintained-red.txt',out/'failed-attempts'/'maintained-red.txt');copy(state/'frozen-original-test.py',out/'failed-attempts'/'frozen-original-test.py')
for n in ['snapshot.py','qualify.py','required.py','collect.py']:copy(state/n,out/'reproduce'/n)
frozen=json.loads(subprocess.check_output(['python','.codex/skills/ultra-code/scripts/ultra_code_bb.py','verify-tests','--db','.codex/state/ultra-result-evidence.sqlite3'],text=True));assert frozen['status']=='verified';save(out/'frozen-verification.json',frozen)
board=[json.loads(v) for v in subprocess.check_output(['python','.codex/skills/ultra-code/scripts/ultra_code_bb.py','read','--db','.codex/state/ultra-result-evidence.sqlite3','--since','915','--limit','100','--format','jsonl'],text=True).splitlines()];save(out/'portfolio.json',{'posts':[v for v in board if v.get('topic')=='compaction-r63'],'roles':'Real distinct Luna-medium red, green and integrated-audit workers; root integrates and qualifies.'})
commands=json.loads((q/'required-qualification-commands.json').read_text());assert len(commands)==3 and all(v['returncode']==0 for v in commands)
save(out/'acceptance.json',{'candidate':identity,'strictBaseline':json.loads((q/'clean-baseline.command.json').read_text()),'runtimeUnchanged':len(same),'runtimeChanged':changed,'requiredCommands':commands,'codeAndTestsMatchSnapshot':True,'rootHeadIndexPreserved':True,'frozenRegistryVerified':len(frozen['frozenTests']),'installedTestsPerRuntime':289,'maintainedTests':3167,'readerCandidate':'r62 3806c436fe68e4d5700646b649b6a6525ec14ba0, not this later maintenance build','validationScope':'Bounded presentation correctness/compatibility/packaging, not mathematical benefit','independentAuditPost':927})
print(json.dumps({'output':str(out),'candidate':identity['candidateCommit'],'runtimeUnchanged':len(same)}))
