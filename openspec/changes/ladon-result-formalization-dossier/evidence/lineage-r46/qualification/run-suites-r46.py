import json,os,subprocess,sys
from pathlib import Path
root=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/full-qualification');candidate=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/candidate');runtime=sys.argv[1];prefix=candidate.parent/runtime;env=dict(os.environ)
for key in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS'):env.pop(key,None)
env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',LADON_REQUIRE_EXECUTION_NONLEAKAGE='1',LADON_CONSOLE=str(prefix/'bin/ladon'))
for family in ('discovery','integration','correctness','authority'):
 argv=[str(prefix/'bin/python'),'-I',str(candidate/'scripts/run_child_acceptance.py'),'--inventory',str(candidate/f'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/{family}-acceptance-inventory.json'),'--context',str(root/'context-r46.json'),'--wheel',str(candidate.parent/'dist/ladon-0.2.0-py3-none-any.whl'),'--runtime',runtime,'--output',str(root/f'{family}-r46-{runtime}.json')]
 env.pop('LADON_ACCEPTANCE_HOST_NETWORK_NAMESPACE',None)
 if family=='discovery':env['LADON_ACCEPTANCE_HOST_NETWORK_NAMESPACE']=os.readlink('/proc/self/ns/net')
 print('START '+family,flush=True)
 with (root/f'{family}-r46-{runtime}.log').open('wb') as log:proc=subprocess.run((['bwrap','--unshare-net','--bind','/','/','--proc','/proc','--dev','/dev']+argv) if family=='discovery' else argv,cwd=candidate,env=env,stdout=log,stderr=subprocess.STDOUT)
 result=json.loads((root/f'{family}-r46-{runtime}.json').read_text());print(json.dumps({'family':family,'exitCode':proc.returncode,'collected':len(result['collected']),'passed':len(result['passed']),'failed':result['failed'],'skipped':result['skipped'],'error':result.get('qualificationError')}),flush=True)
 if proc.returncode:raise SystemExit(proc.returncode)
