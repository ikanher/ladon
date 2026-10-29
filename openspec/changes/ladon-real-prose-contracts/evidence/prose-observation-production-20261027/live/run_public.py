import dataclasses,json,os,sys,time
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
b=Path('.codex/state/prose-observation-production/live').resolve();root=b/'project'
p=b/'budget.json'
if p.exists():deadline=json.loads(p.read_text())['deadlineMonotonic']
else:
 deadline=time.monotonic()+600;p.write_text(json.dumps({'deadlineMonotonic':deadline,'seconds':600}))
assert deadline>time.monotonic()
label=sys.argv[1];output=b/(label+'.json');assert not output.exists()
arguments=sys.argv[2:]
if arguments[0] in ('observe-prose-bound','replay-prose-bound'):
 arguments += ['--timeout-seconds',str(min(600,deadline-time.monotonic()))]
command=[sys.executable,'-m','ladon.entrypoint','investigation','contract',*arguments, '--output',str(output)]
env={**os.environ,'PYTHONPATH':str(Path('src').resolve())}
r=run_bounded_target_process(command,cwd=Path('.').resolve(),env=env,timeout_seconds=deadline-time.monotonic(),max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
(b/(label+'-process.json')).write_text(json.dumps({'command':command,**dataclasses.asdict(r)},indent=2)+'\n')
assert not any((r.timed_out,r.memory_limited,r.output_limited)), 'Stop progress and report resource stop to user.'
print({'exit':r.returncode,'seconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes})
if output.exists():
 j=json.loads(output.read_text());print({k:j.get(k) for k in ['schema','status','authority','admission','fidelity']})
else: print(r.stdout[-2000:]);print(r.stderr[-1000:])
