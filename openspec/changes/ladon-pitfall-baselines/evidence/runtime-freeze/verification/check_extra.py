import importlib.util,json,sys,hashlib,subprocess
from pathlib import Path
repo=Path('/home/codex/projects/ladon'); cli=repo/'openspec/changes/ladon-pitfall-baselines/scripts/runtime_custody.py'
sys.argv=['extra',str(cli)]
s=importlib.util.spec_from_file_location('red',repo/'.codex/state/pitfall-runtime/red/test_runtime_custody.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
t=m.CustodyCli();t.setUp()
try:
 identity=(t.bundle/'manifest.sha256').read_text().strip()
 # Destroy donor availability; reconstruction and import must survive.
 t.repo.rename(t.base/'hidden-donor')
 dest=t.base/'second-restoration'
 t.call('restore','--bundle',t.bundle,'--identity',identity,'--destination',dest)
 t.call('verify','--bundle',t.bundle,'--identity',identity,'--root',dest)
 origin=t.call('run','--bundle',t.bundle,'--identity',identity,'--root',dest,'--','--probe').stdout.splitlines()[0]
 assert Path(origin).is_relative_to(dest)
 print('PASS donor-independent reconstruction and preserved import origin')
 # Launcher corruption must not execute, even though application source is untouched.
 launch=dest/'runtime_custody.py'; original=launch.read_bytes();launch.write_bytes(original+b'\n# drift\n')
 t.call('run','--bundle',t.bundle,'--identity',identity,'--root',dest,'--','--probe',expected=1);launch.write_bytes(original)
 print('PASS launcher drift rejection')
 data=json.loads((t.bundle/'manifest.json').read_text()); payload=t.bundle/data['payload']; raw=payload.read_bytes();payload.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
 t.call('verify','--bundle',t.bundle,'--identity',identity,'--root',dest,expected=1)
 t.call('restore','--bundle',t.bundle,'--identity',identity,'--destination',t.base/'corrupt',expected=1)
 payload.write_bytes(raw);print('PASS archive corruption rejection on verify and reconstruction')
 manifest=t.bundle/'manifest.json'; original=manifest.read_bytes();manifest.write_bytes(original+b' ')
 (t.bundle/'manifest.sha256').write_text(hashlib.sha256(manifest.read_bytes()).hexdigest()+'\n')
 t.call('verify','--bundle',t.bundle,'--identity',identity,'--root',dest,expected=1)
 print('PASS externally pinned identity rejects manifest/sidecar replacement')
finally:t.tearDown()
