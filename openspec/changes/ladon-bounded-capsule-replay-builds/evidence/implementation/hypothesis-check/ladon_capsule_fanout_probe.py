import json, os, time, tempfile
from pathlib import Path
import ladon.process_supervisor as supervisor
from ladon.progress import process_rows, descendant_pids
from ladon.theorem_capsule_replay import _replay_environment

base = Path(tempfile.mkdtemp(prefix='ladon-capsule-fanout-'))
lake = '/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lake'
env = _replay_environment('deny')
samples=[]
peaks={}

def sample(pid):
    rows=process_rows(Path('/proc'))
    descendants=descendant_pids(pid,rows)
    total=sum(rows[p][1] for p in descendants if p in rows)
    children=[]
    for p in descendants:
        try:
            args=Path(f'/proc/{p}/cmdline').read_bytes().decode().split('\0')
        except (OSError,UnicodeError):
            continue
        if args and Path(args[0]).name == 'lean':
            rss=rows.get(p,(0,0))[1]
            metrics={}
            try:
                for line in Path(f'/proc/{p}/smaps_rollup').read_text().splitlines():
                    fields=line.split()
                    if fields and fields[0] in ('Pss:','Private_Clean:','Private_Dirty:'):
                        metrics[fields[0][:-1]]=int(fields[1])*1024
            except OSError: pass
            children.append({'pid':p,'rss':rss,'args':args,**metrics})
            peaks[p]=max(peaks.get(p,0),rss)
    samples.append({'time':time.monotonic(),'rss':total,'lean':children})
    return total
supervisor.process_tree_rss_bytes=sample

def setup(name):
    root=base/name
    (root/'Probe').mkdir(parents=True)
    (root/'lean-toolchain').write_text('leanprover/lean4:v4.33.0\n')
    (root/'lakefile.toml').write_text('name = "fanout_probe"\n[[lean_lib]]\nname = "Probe"\n')
    for i in range(3):
        (root/'Probe'/f'M{i}.lean').write_text(f'import Lean\nrun_cmd do IO.sleep 3000\ntheorem probe_{i} : True := True.intro\n')
    (root/'Probe.lean').write_text(''.join(f'import Probe.M{i}\n' for i in range(3)))
    return root

results=[]
for policy in ('default','ordered'):
    root=setup(policy)
    samples.clear(); peaks.clear()
    started=time.monotonic()
    modules=['Probe'] if policy=='default' else [*(f'Probe.M{i}' for i in range(3)), 'Probe']
    commands=[]
    for module in modules:
        remaining=60-(time.monotonic()-started)
        if remaining<=0: raise RuntimeError('shared deadline expired')
        r=supervisor.run_bounded_target_process([lake,'build',module],cwd=root,
            timeout_seconds=remaining,max_rss_bytes=6*1024**3,max_output_bytes=1024**2,env=env)
        commands.append({'module':module,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,
            'memoryLimited':r.memory_limited,'timedOut':r.timed_out})
        if not r.succeeded: break
    peak=max(samples,key=lambda s:s['rss']) if samples else {}
    report={'policy':policy,'seconds':time.monotonic()-started,'maxLeanProcesses':max((len(s['lean']) for s in samples),default=0),
        'peakTreeRss':peak.get('rss'), 'leanAtPeak':peak.get('lean'), 'largestLeanRss':max(peaks.values(),default=0),
        'leanPssAtPeak':sum(p.get('Pss',0) for p in peak.get('lean',[])), 'commands':commands,'samples':samples}
    (base/f'{policy}.json').write_text(json.dumps(report,indent=2))
    results.append({k:v for k,v in report.items() if k not in ('samples','commands','leanAtPeak')})
    print(json.dumps({'result':results[-1],'success':all(c['returncode']==0 for c in commands),'evidence':str(base/f'{policy}.json')}),flush=True)
print(json.dumps({'directory':str(base)}),flush=True)
