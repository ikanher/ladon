import json,time,tempfile,shutil
from pathlib import Path
import ladon.process_supervisor as supervisor
import ladon.theorem_capsule_replay as replay
from ladon.progress import process_rows, descendant_pids
base=Path(tempfile.mkdtemp(prefix='ladon-capsule-actual-probe-'))
samples=[]
active='validation'

def sample(pid):
    rows=process_rows(Path('/proc'))
    descendants=descendant_pids(pid,rows)
    children=[]
    for p in descendants:
        try: args=Path(f'/proc/{p}/cmdline').read_bytes().decode().split('\0')
        except (OSError,UnicodeError): continue
        if args and Path(args[0]).name=='lean':
            children.append({'pid':p,'rss':rows.get(p,(0,0))[1],'args':args})
    rss=sum(rows[p][1] for p in descendants if p in rows)
    samples.append({'stage':active,'time':time.monotonic(),'rss':rss,'lean':children})
    return rss
supervisor.process_tree_rss_bytes=sample
original=replay._run_stage

def stage(*args,**kwargs):
    global active
    active=kwargs['stage']
    print(json.dumps({'stage':active,'event':'start'}),flush=True)
    result=original(*args,**kwargs)
    print(json.dumps({'stage':active,'event':'end','status':result['status'],'peak':result['row'].get('peakRssBytes')}),flush=True)
    return result
replay._run_stage=stage
print(json.dumps({'evidenceDirectory':str(base)}),flush=True)
started=time.monotonic()
root=base/'repository'
shutil.copytree(Path('/tmp/historical-adam-convergence-r02-capsule'),root)
env=replay._replay_environment('allow')
rows=[]
receipt={'status':'not-started','stages':rows,'diagnosticOnly':True}
for name,command,timeout in (
    ('dependency_resolution',['lake','update'],180),
    ('lean_build',['lake','build','Mf.Optimization.StochasticApproximation.AdamGaussianConvergence'],30),
):
    result=stage(command,root,timeout,6*1024**3,env,stage=name,display_command=tuple(command))
    rows.append(result['row'])
    receipt['status']=result['status'] or 'build-finished-not-verified'
    if result['status'] is not None: break
(base/'receipt.json').write_text(json.dumps(receipt,indent=2))
(base/'samples.json').write_text(json.dumps(samples,indent=2))
summary={}
for name in sorted({s['stage'] for s in samples}):
    selected=[s for s in samples if s['stage']==name]
    peak=max(selected,key=lambda s:s['rss'])
    fanout=max(selected,key=lambda s:len(s['lean']))
    summary[name]={'peakTreeRss':peak['rss'],'maxLeanProcesses':len(fanout['lean']),
        'largestLeanRss':max((p['rss'] for s in selected for p in s['lean']),default=0),
        'atMaxFanout':fanout,'atPeak':peak}
report={'status':receipt['status'],'seconds':time.monotonic()-started,'summary':summary}
(base/'summary.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'status':report['status'],'seconds':report['seconds'],'stages':{k:{a:b for a,b in v.items() if a not in ('atMaxFanout','atPeak')} for k,v in summary.items()},'directory':str(base)}),flush=True)
