import dataclasses,json,os,sys
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon')
base=root/'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/norm-route-audit-20261025'
repo=root/'.codex/state/navier-stokes-informed-diagnostic/formalization'
ns='NavierStokes.SmoothFamilyTorusInverse'
def goal(loss):
 return f'open scoped ContDiff in ∀ {{P : Type}} [NormedAddCommGroup P] [NormedSpace ℝ P] [FiniteDimensional ℝ P] (d : NavierStokes.TorusInverse.Direction) (n : ℕ), ∃ K : ℝ, 0 ≤ K ∧ ∀ (f : {ns}.Source P) (S : Set P) (C : ℝ), ContDiff ℝ ∞ f → {ns}.Periodic f → 0 ≤ C → {ns}.JetBound f S (n + {loss}) C → {ns}.JetBound ({ns}.inverse d f) S n (K * C)'
assert goal(5).replace('n + 5','n + 4')==goal(4)
for loss in [5,4]:
 with (base/f'jet-goal-{loss}.txt').open('x') as f:f.write(goal(loss)+'\n')
metadata={'origin':'Root-authored transcription of original inverse_finiteJets, preserving generic finite-dimensional P, all original input predicates and quantifier order. Four-order probe changes only input JetBound n+5 to n+4.','limitation':'Application check only, not the paper norm interpretation or mathematical refutation. No new proof or norm definition introduced.'}
with (base/'JET-PROBES.json').open('x') as f:json.dump(metadata,f,indent=2);f.write('\n')
for loss in [5,4]:
 command=[str(root/'.venv/bin/python'),'-m','ladon.entrypoint','proof-search','check','candidate','--repo-root',str(repo),'--module',ns,'--goal',goal(loss),'--candidate',ns+'.inverse_finiteJets','--timeout-seconds','60','--max-rss-mib','12288','--format','json','--projection','audit','--output',str(base/f'jet-check-{loss}.json')]
 r=run_bounded_target_process(command,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src')},timeout_seconds=120,max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
 with (base/f'jet-check-{loss}-command.json').open('x') as f:json.dump({'command':command,**dataclasses.asdict(r)},f,indent=2);f.write('\n')
 print(json.dumps({'loss':loss,'returncode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'stdout':r.stdout[-600:],'stderr':r.stderr[-600:]}),flush=True)
 if r.memory_limited:sys.exit('Stop progress and report back to user: the 12 GiB memory limit was not enough.')
 if r.timed_out or r.output_limited:sys.exit(2)
