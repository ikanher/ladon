import hashlib,importlib.util,json,sys
from pathlib import Path
repo=Path('/home/codex/projects/ladon'); cli=repo/'openspec/changes/ladon-pitfall-baselines/scripts/runtime_custody.py'
sys.argv=['artifact-check',str(cli)]
s=importlib.util.spec_from_file_location('red',repo/'.codex/state/pitfall-runtime/red/test_runtime_custody.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
t=m.CustodyCli(); t.setUp()
try:
 source=t.component/'Example.lean'; artifact=t.component/'Example.olean'
 source.write_text('example : True := True.intro\n');artifact.write_bytes(b'representative compiled artifact for integrity-link test\n')
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 pairs=[{'source':'fixture/Example.lean','artifact':'fixture/Example.olean','sourceSha256':sha(source),'artifactSha256':sha(artifact)}]
 pairfile=t.base/'pairs.json';pairfile.write_text(json.dumps(pairs))
 good=t.base/'paired-bundle';dest=t.base/'paired-restored'
 t.call('capture','--repo',t.repo,'--bundle',good,'--component',f'fixture={t.component}','--artifact-pairs',pairfile)
 identity=(good/'manifest.sha256').read_text().strip()
 t.call('restore','--bundle',good,'--identity',identity,'--destination',dest)
 frozen_source=dest/'fixture/Example.lean';frozen_artifact=dest/'fixture/Example.olean';old=sha(frozen_artifact)
 frozen_source.write_text('example : False := by sorry\n')
 t.call('verify','--bundle',good,'--identity',identity,'--root',dest,expected=1)
 assert sha(frozen_artifact)==old
 print('PASS changed source with unchanged compiled artifact is rejected on verification')
 source.write_text('example : False := by sorry\n')
 t.call('capture','--repo',t.repo,'--bundle',t.base/'stale-pair-bundle','--component',f'fixture={t.component}','--artifact-pairs',pairfile,expected=1)
 assert not (t.base/'stale-pair-bundle').exists()
 print('PASS stale source/artifact pair inventory is rejected before a bundle is published')
finally:t.tearDown()
