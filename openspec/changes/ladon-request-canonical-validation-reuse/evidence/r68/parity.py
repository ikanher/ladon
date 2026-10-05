import subprocess,json,hashlib,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
state=Path(__file__).resolve().parent;out=state/'parity';out.mkdir(exist_ok=True)
before=state.parent/'preparation-r65/py311/bin/ladon';after=state/'py311/bin/ladon'
real=Path('/home/codex/.cache/ladon-reader-loop-r49/shared/result.zip');small=state/'small-complete/result.zip'
relocated=out/'relocated.zip';shutil.copy2(small,relocated)
records=[]
def execute(side,exe,name,command,args):
 proc=subprocess.run([str(exe),'result',command,*args],capture_output=True)
 for suffix,data in [('stdout',proc.stdout),('stderr',proc.stderr)]:
  (out/f'{name}-{side}.{suffix}').write_bytes(data)
 return {'name':name,'side':side,'argv':[str(exe),'result',command,*args], 'exit':proc.returncode,'stdout_sha256':hashlib.sha256(proc.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(proc.stderr).hexdigest(),'output':proc.stdout}
def pair(name,command,args):
 with ThreadPoolExecutor(max_workers=2) as pool:
  rows=list(pool.map(lambda x:execute(*x,name,command,args),[('before',before),('after',after)]))
 assert rows[0]['exit']==rows[1]['exit']
 assert rows[0]['output']==rows[1]['output']
 assert rows[0]['stderr_sha256']==rows[1]['stderr_sha256']
 records.extend({k:v for k,v in row.items() if k!='output'} for row in rows)
 return rows[0]
for cmd,section in [('inspect','targets'),('guide','steps')]:
 args=[str(real),'--section',section,'--limit','1','--format','json']
 first=pair('real-'+cmd+'-first',cmd,args)
 data=json.loads(first['output']);cursor=data.get('nextCursor') or data.get('pagination',{}).get('nextCursor')
 if cursor:pair('real-'+cmd+'-next',cmd,args+['--cursor',cursor])
 pair('real-'+cmd+'-text',cmd,[str(real),'--section',section,'--limit','1','--format','text'])
 pair('real-'+cmd+'-invalid',cmd,[str(real),'--claim','not-a-claim'])
for cmd in ['inspect','guide']:
 for fmt in ['text','json']:
  for source,label in [(small,'original'),(relocated,'relocated')]:
   pair('small-'+cmd+'-'+fmt+'-'+label,cmd,[str(source),'--section','checking','--format',fmt])
 for flag,value in [('--limit','0'),('--cursor','not-a-cursor'),('--claim','missing')]:
  pair('small-'+cmd+'-invalid-'+flag[2:],cmd,[str(small),flag,value])
(out/'records.json').write_text(json.dumps(records,indent=2)+'\n');print(len(records),'commands byte-identical across candidates')
