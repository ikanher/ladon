import json,os,subprocess
from pathlib import Path
root=Path('/home/codex/.cache/ladon-qualification-r48/ladon-bundles-r48-ouvuyuvz/full-qualification');candidate=Path('/home/codex/.cache/ladon-qualification-r48/ladon-bundles-r48-ouvuyuvz/candidate');records=[]
for runtime in ('py311','py312'):
 prefix=candidate.parent/runtime;env=dict(os.environ)
 for key in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS'):env.pop(key,None)
 env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',LADON_CONSOLE=str(prefix/'bin/ladon'))
 argv=[str(prefix/'bin/python'),'-I','-m','pytest','-q',str(candidate/'tests/test_result_manifest.py'),str(candidate/'tests/test_result_cli.py'),str(candidate/'tests/test_result_resolution.py')]
 log=root/f'result-installed-r48-{runtime}.log'
 with log.open('wb') as stream: proc=subprocess.run(argv,cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT)
 records.append({'runtime':runtime,'argv':argv,'workingDirectory':str(root),'exitCode':proc.returncode,'logPath':str(log)})
 assert proc.returncode==0,log
 argv=[str(prefix/'bin/python'),'-I',str(root/'compare-frozen-baseline-r48.py'),'--output-dir',str(root/f'baseline-comparison-r48-{runtime}'),'--ladon',str(prefix/'bin/ladon'),'--runtime',runtime]
 proc=subprocess.run(argv,cwd=root,env=env,capture_output=True)
 log=root/f'baseline-current-r48-{runtime}.log';log.write_bytes(proc.stdout+proc.stderr)
 records.append({'runtime':runtime,'argv':argv,'workingDirectory':str(root),'exitCode':proc.returncode,'logPath':str(log)})
 assert proc.returncode==0,log
(root/'result-focused-commands-r48.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records))
