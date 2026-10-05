import json,os,subprocess
from pathlib import Path
root=Path('/home/codex/.cache/ladon-qualification-r48/ladon-bundles-r48-ouvuyuvz/full-qualification');candidate=Path('/home/codex/.cache/ladon-qualification-r48/ladon-bundles-r48-ouvuyuvz/candidate');inv=json.loads((candidate/'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/authority-acceptance-inventory.json').read_text());rows=[];env=dict(os.environ)
for key in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS'):env.pop(key,None)
for i,tail in enumerate(inv['sourceQualityArgvTails']):
 argv=[str(candidate.parent/'py311/bin/python'),*tail];log=root/f'source-quality-r48-{i}.log'
 with log.open('wb') as stream:p=subprocess.run(argv,cwd=candidate,env=env,stdout=stream,stderr=subprocess.STDOUT)
 rows.append({'argv':argv,'workingDirectory':str(candidate),'exitCode':p.returncode,'status':'passed' if p.returncode==0 else 'failed','logPath':str(log)})
 assert p.returncode==0
(root/'source-quality-r48.json').write_text(json.dumps(rows,indent=2)+'\n');print('source owner checks passed')
