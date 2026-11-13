import sys, subprocess, pathlib, datetime, json, time, shlex
out=pathlib.Path(__file__).parent.parent
inp=out.parent/'INPUT'
label=sys.argv[1]; cmd=sys.argv[2:]
if pathlib.Path(cmd[0]).name in ['lean','lake']: inp=inp/'capsule'/'lean'
start=datetime.datetime.now(datetime.timezone.utc).isoformat(); t=time.monotonic()
r=subprocess.run(cmd,cwd=inp,text=True,capture_output=True)
p=out/'evidence'/(label+'.txt'); p.write_text('$ '+shlex.join(cmd)+'\nCWD: '+str(inp)+'\n'+r.stdout+r.stderr+'\nEXIT: '+str(r.returncode)+'\n')
row={'time_utc':start,'command':cmd,'cwd':str(inp),'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-t,'output_file':str(p.relative_to(out)),'lean_lake_invocations':int(pathlib.Path(cmd[0]).name in ['lean','lake'])}
with (out/'evidence'/'commands.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
print(p.read_text())
sys.exit(r.returncode)
