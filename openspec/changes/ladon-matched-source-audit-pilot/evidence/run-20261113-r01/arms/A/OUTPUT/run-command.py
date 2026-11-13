import subprocess,sys,json,datetime,pathlib,time
root=pathlib.Path(__file__).resolve().parent
e=root/'evidence'
log=e/'commands.jsonl'
cmd=sys.argv[1]
rows=log.read_text().splitlines() if log.exists() else []
n=len(rows)+1
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
t=time.monotonic()
r=subprocess.run(cmd,shell=True,executable='/bin/bash',cwd=root.parent/'INPUT/capsule/lean',capture_output=True,text=True)
record={'id':n,'command':cmd,'cwd':str(root.parent/'INPUT/capsule/lean'),'start':start,'end':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':time.monotonic()-t,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
with log.open('a') as f:f.write(json.dumps(record)+'\n')
(e/f'{n:03d}.txt').write_text('$ '+cmd+'\nEXIT '+str(r.returncode)+'\nSTDOUT\n'+r.stdout+'\nSTDERR\n'+r.stderr)
print(r.stdout,end='');print(r.stderr,end='',file=sys.stderr)
sys.exit(r.returncode)
