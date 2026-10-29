import hashlib,json,os,sys
from pathlib import Path
sys.path.insert(0,'/home/codex/projects/ladon/src')
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon')
out=root/'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/informed-derivative-diagnostic-20261025'
repo=root/'.codex/state/navier-stokes-informed-diagnostic/formalization'
ns='NavierStokes.SmoothFamilyTorusInverse'
torus='NavierStokes.TorusInverse'
fourier='NavierStokes.SmoothFourierData'
prefix=f'''open scoped ContDiff in ∀ {{P : Type}} [NormedAddCommGroup P] [NormedSpace ℝ P] (d : {torus}.Direction) {{f : {ns}.Source P}} (hf : ContDiff ℝ ∞ f) (hp : {ns}.Periodic f) (w : List Bool) (p : P) (Y : {torus}.Plane) {{C : ℝ}}, (∀ x ∈ Set.Icc (0 : ℝ) 1, ∀ y ∈ Set.Icc (0 : ℝ) 1, ‖f (p, (x, y))‖ ≤ C) → '''
def goal(loss):
    return prefix+f'''(∀ x ∈ Set.Icc (0 : ℝ) 1, ∀ y ∈ Set.Icc (0 : ℝ) 1, ‖{fourier}.xJet (w.length + {loss}) ({ns}.slice f p) (x, y)‖ ≤ C) → (∀ x ∈ Set.Icc (0 : ℝ) 1, ∀ y ∈ Set.Icc (0 : ℝ) 1, ‖{fourier}.xJet (w.length + {loss}) ({fourier}.swapFunction ({ns}.slice f p)) (x, y)‖ ≤ C) → ‖{torus}.derivativeWord w ({ns}.slice ({ns}.inverse d f) p) Y‖ ≤ NavierStokes.ParametricTorusInverse.mixedLossConstant w.length * C'''
if sys.argv[1]=='prepare':
    manifest={}
    for loss in (5,4):
        text=goal(loss)
        with (out/f'goal-loss-{loss}.txt').open('x') as stream:stream.write(text+'\n')
        manifest[str(loss)]={'path':f'goal-loss-{loss}.txt','sha256':hashlib.sha256((text+'\n').encode()).hexdigest()}
    assert goal(5).replace('w.length + 5','w.length + 4')==goal(4)
    (out/'APPLICATION-PROBES.json').write_text(json.dumps({'schema':'authored-application-probes-v1','author':'root','origin':'Exact source theorem interface, with two input derivative orders replaced in the four-order probe. All type parameters, smoothness, periodicity, scalar bounds and output constant retained.','control':5,'probe':4,'difference':'Only w.length + 5 becomes w.length + 4 in the two pure input-derivative premises.','limitation':'These are authored application probes. They do not define the conventional C^m norm, finite maxima, zero-mean solution property or the full equation (8.19). A residual is an unproved bridge, not a refutation.','goals':manifest},indent=2)+'\n')
    print('Frozen the two exact application goals.')
    raise SystemExit(0)
loss=int(sys.argv[1])
goal_text=(out/f'goal-loss-{loss}.txt').read_text().strip()
command=[str(root/'.venv/bin/python'),'-m','ladon.entrypoint','proof-search','check','candidate','--repo-root',str(repo),'--module',ns,'--goal',goal_text,'--candidate',ns+'.norm_derivativeWord_inverse_le','--timeout-seconds','60','--max-rss-mib','12288','--format','json','--projection','audit','--output',str(out/f'application-loss-{loss}.json')]
r=run_bounded_target_process(command,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src')},timeout_seconds=120,max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
receipt={'command':command,'exitCode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'timedOut':r.timed_out,'memoryLimited':r.memory_limited,'outputLimited':r.output_limited,'stdout':r.stdout,'stderr':r.stderr}
with (out/f'application-loss-{loss}-command.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in {'command','stdout','stderr'}}))
print(r.stdout[-1500:]);print(r.stderr[-1500:])
if r.memory_limited:raise SystemExit('Stop progress and report back to user: the 12 GiB memory limit was not enough.')
