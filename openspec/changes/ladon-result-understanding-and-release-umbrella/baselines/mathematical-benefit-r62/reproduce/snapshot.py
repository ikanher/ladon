from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile

root = Path('/home/codex/projects/ladon')
run = Path(tempfile.mkdtemp(prefix='ladon-benefit-readers-r62-', dir='/home/codex/.cache/ladon-qualification-r62'))
candidate = run / 'candidate'
candidate.mkdir()
paths = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root).decode().split('\0')
records=[]
for name in sorted(set(paths) - {''}):
    source = root / name
    if not source.is_file():
        continue
    dest = candidate / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    records.append({'path': name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'bytes': source.stat().st_size})
for command in [['git','init','-q'],['git','config','user.email','local-candidate@localhost'],['git','config','user.name','Ladon local candidate'],['git','config','core.hooksPath','/dev/null'],['git','add','-A'],['git','commit','-qm','Local r62 presentation and paragraph projection qualification snapshot']]:
    subprocess.run(command,cwd=candidate,check=True)
identity={'sourceHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
          'sourceIndexSha256':hashlib.sha256((root/'.git/index').read_bytes()).hexdigest(),
          'candidateCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=candidate,text=True).strip(),
          'sourceInventoryDigest':'sha256:'+hashlib.sha256(json.dumps(records,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
(run/'source-inventory.json').write_text(json.dumps(records,indent=2)+'\n')
(run/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
(root/'.codex/state/benefit-readers-r62/qualification-run-path').write_text(str(run)+'\n')
print(json.dumps({'run':str(run),'files':len(records),**identity}))
