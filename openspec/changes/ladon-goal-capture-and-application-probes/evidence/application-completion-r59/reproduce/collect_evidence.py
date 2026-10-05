from pathlib import Path
import shutil,json,hashlib,sqlite3
root=Path.cwd();state=root/'.codex/state/application-completion-r59'; run=Path((state/'run-path').read_text().strip());failed=Path((state/'failed-run-path').read_text().strip());out=root/'openspec/changes/ladon-goal-capture-and-application-probes/evidence/application-completion-r59';out.mkdir(exist_ok=True)
def copy(src,dst):
 target=out/dst;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
for path in (state/'root-trials').rglob('*'):
 if path.is_file() and path.suffix in ('.json','.py'):
  copy(path,Path('root-trials')/path.relative_to(state/'root-trials'))
for name in ['contract.md','protocol-notes.md','protocol-split-ast-parity.json','protocol-before-quality-split.py','snapshot.py','qualify.py','installed_field.py','installed_real.py','baseline-outer-receipt.json','baseline-second-outer-receipt.json','install-outer-receipt.json','frozen-tests.json']:
 copy(state/name,Path('reproduce' if name.endswith('.py') else 'records')/name)
for source,subdir in [(run,'qualified-candidate'),(failed,'failed-candidate')]:
 for path in source.iterdir():
  if path.is_file() and path.suffix in ('.json','.log'):
   copy(path,Path(subdir)/path.name)
for subdir in ('field','field-retest'):
 for path in (run/subdir).rglob('*'):
  if path.is_file(): copy(path,Path(subdir)/path.relative_to(run/subdir))
db=sqlite3.connect(root/'.codex/state/ultra-result-evidence.sqlite3');db.row_factory=sqlite3.Row
rows=[dict(r) for r in db.execute('SELECT * FROM posts WHERE post_id BETWEEN 785 AND 821 ORDER BY post_id')]
(out/'portfolio.json').write_text(json.dumps(rows,indent=2)+'\n')
identity=json.loads((run/'identity.json').read_text());origins=[];hashes={}
for runtime in ('py311','py312'):
 origin=json.loads((run/(runtime+'-origin.log')).read_text());origins.append(origin)
 for row in origin['files']:
  relative=row['path'].split('/site-packages/ladon/',1)[1]
  expected=hashlib.sha256((root/'src/ladon'/relative).read_bytes()).hexdigest();assert expected==row['sha256'];hashes[relative]=expected
source_root=run/'candidate'
for relative,digest in hashes.items():assert hashlib.sha256((source_root/'src/ladon'/relative).read_bytes()).hexdigest()==digest
summary={'installedRealContracts':json.loads((run/'py311-real-completion-summary.json').read_text()),'schema':'ladon-source-goal-completion-slice-acceptance-v1','scope':'OpenSpec1.3/2.3; explicit captured-original-goal completion with independent compiler and trust; no fixed-epoch discovery, enclosing-declaration completion, prose correspondence or comparative usefulness','identity':identity,'wheelSha256':hashlib.sha256(next((run/'dist').glob('*.whl')).read_bytes()).hexdigest(),'sourceOwnerHashes':hashes,'originsAndParity':origins,'customIntegrationBudget':json.loads((state/'root-trials/budget.json').read_text()),'installedField':json.loads((run/'field-retest/summary.json').read_text()),'installedPortableContracts':{runtime:json.loads((run/(runtime+'-summary.json')).read_text()) for runtime in ('py311','py312')},'qualificationReceipts':{n:json.loads((state/n).read_text()) for n in ('baseline-second-outer-receipt.json','install-outer-receipt.json')}}
assert summary['qualificationReceipts']['baseline-second-outer-receipt.json']['returncode']==0
assert summary['qualificationReceipts']['install-outer-receipt.json']['returncode']==0
assert hashlib.sha256((root/'.git/index').read_bytes()).hexdigest()==identity['sourceIndexSha256']
(out/'acceptance.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'directory':str(out),'ownerParity':len(hashes),'scope':summary['scope']}))
