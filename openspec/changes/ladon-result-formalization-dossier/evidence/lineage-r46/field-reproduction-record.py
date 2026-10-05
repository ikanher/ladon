from pathlib import Path
import hashlib,json,os,subprocess,time
root=Path('/home/codex/projects/ladon')
state=root/'.codex/state/dossier-r46'
run=Path((state/'run-path').read_text().strip())
out=run/'field-installed';out.mkdir(exist_ok=True)
base=Path('/home/codex/projects/lean/matrix-factorization/latex/lean/poisson_fixed_epoch_exposition_evidence_r02/target-capture-r44/assembled')
companion=json.loads((state/'real-lineage-inputs.json').read_text());(out/'lineage-inputs.json').write_text(json.dumps(companion,indent=2)+'\n')
db=Path(companion['entries'][0]['database'])
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
initial=digest(db)
manifest=json.loads((base/'note.canonical.result.json').read_text());target_id=companion['entries'][0]['targetId']
common=[str(run/'py311/bin/ladon'),'result','inspect',str(base/'note.canonical.result.json'),'--lineage-inputs',str(out/'lineage-inputs.json'),'--target',target_id,'--limit','100']
for p in sorted((base/'artifacts').glob('*.json')):common.extend(['--artifact',str(p)])
env=os.environ.copy();env.pop('PYTHONPATH',None)
measurements=[]
for label,section in [('lineage','lineage'),('assumptions-0','assumptions'),('assumptions-1','assumptions'),('evidence','evidence')]:
 cmd=common+['--section',section]
 if label=='assumptions-1':
  previous=json.loads((out/'assumptions-0.stdout.json').read_text());cmd+=['--cursor',previous['pagination']['nextCursor']]
 start=time.monotonic()
 p=subprocess.run(['/usr/bin/time','-f','%M','-o',str(out/(label+'.rss.txt')),*cmd],cwd='/tmp',env=env,capture_output=True)
 (out/(label+'.stdout.json')).write_bytes(p.stdout);(out/(label+'.stderr.txt')).write_bytes(p.stderr)
 record={'argv':cmd,'cwd':'/tmp','exitCode':p.returncode,'elapsedSeconds':time.monotonic()-start,'stdoutBytes':len(p.stdout),'peakRssKiB':int((out/(label+'.rss.txt')).read_text())}
 (out/(label+'.command.json')).write_text(json.dumps(record,indent=2)+'\n');measurements.append(record)
 assert p.returncode==0,p.stderr.decode()
 data=json.loads(p.stdout);assert data['rows']
 print(json.dumps({'label':label,**{k:v for k,v in record.items() if k!='argv'},'total':data['pagination']['total'],'returned':data['pagination']['returned'],'status':data['rows'][0]['status']}),flush=True)
final=digest(db);assert final==initial,'input store changed'
(out/'input-store.json').write_text(json.dumps({'path':str(db),'bytes':db.stat().st_size,'sha256Before':initial,'sha256After':final,'unchanged':True},indent=2)+'\n')
(out/'measurements.json').write_text(json.dumps(measurements,indent=2)+'\n')
