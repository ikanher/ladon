from pathlib import Path
import json,hashlib,shutil,tempfile
root=Path('/home/codex/projects/ladon');state=root/'.codex/state/offset-bridge-r63';state.mkdir(exist_ok=True)
run=Path(tempfile.mkdtemp(prefix='ladon-offset-r63-',dir='/home/codex/.cache'));(state/'run-path').write_text(str(run)+'\n')
old=Path((root/'.codex/state/benefit-readers-r62/run-path').read_text().strip());matrix=(root/'../lean/matrix-factorization').resolve()
shared=run/'shared';shutil.copytree(old/'shared',shared,symlinks=True)
# Unrelated synthetic passages are not needed for this known correspondence gap.
for n in ['passages.json','evaluation-guide.json']:(shared/n).unlink()
target='''import Mf.DP.PoissonFixedEpochAsymptotics

open Filter
open scoped Topology
namespace OffsetBridge
noncomputable section
set_option autoImplicit false

/-- Intended offset component only. A placeholder here is not completion. -/
theorem fixedEpochOffsetBridge
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    Tendsto
      (fun extra : Nat =>
        sensitivity /
          (Mf.DP.poissonFixedEpochCalibratedStddev
            (Mf.DP.PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
            sensitivity epsilon delta : Real) -
          Real.sqrt (2 * Real.log ((epoch + extra : Nat) : Real)))
      atTop
      (nhds (Mf.DP.standardNormalQuantile
        (-Real.log (1 - delta) / (epoch : Real)))) := by
  sorry

#print axioms fixedEpochOffsetBridge
end OffsetBridge
'''
(shared/'IntendedTarget.lean').write_text(target)
# Preserve the exact original paragraph and component assessment independently.
m=json.loads((shared/'manifest.json').read_text());a=json.loads((shared/'assessments.json').read_text())
claim=next(v for v in m['claims'] if v['id']=='thm:smallbatch');(shared/'original-claim.txt').write_text(claim['statement']+'\n')
rows=a.get('assessments',a.get('components',[]));print('assessment keys',list(a))
for arm in ['ordinary','augmented']:
 cwd=run/arm;cwd.mkdir();(cwd/'Bridge.lean').write_text(target);(cwd/'lean-toolchain').write_bytes((matrix/'lean-toolchain').read_bytes())
 (cwd/'.lake/build/lib').mkdir(parents=True);(cwd/'.lake/build/lib/lean').symlink_to(matrix/'.lake/build/lib/lean',target_is_directory=True);(cwd/'.lake/packages').symlink_to(matrix/'.lake/packages',target_is_directory=True)
 (cwd/'mathematics').symlink_to(shared,target_is_directory=True);(run/'reader-output'/arm).mkdir(parents=True)
 base=f'''Resolve the known fixed-epoch offset correspondence gap using the ready Lean project. Work in {cwd}; save review deliverables in {run/'reader-output'/arm}. You have a finite 1800-second work allowance. Do the mathematics; recording happens outside your task.

Bridge.lean contains the exact intended theorem with an UNPROVED sorry placeholder. Preserve its signature and original target (also immutable mathematics/IntendedTarget.lean). Establish that theorem from the existing formal results, compile with ordinary Lean, and inspect transitive axioms; sorryAx or added assumptions do not complete it. If incomplete, retain actual attempts and describe the exact remaining obligation without claiming falsehood. A narrowed or conditional theorem must be separate and labelled.

Both configurations have ordinary Lean 4.33.0, rg, tactics, compiler and #print axioms. Inspect mathematics/source/Mf/DP, mathematics/exposition.tex, manifest.json, guide.json and assessments.json. This is a named correspondence gap, not blind search. Relevant general theorem: Mf.DP.tendsto_fixedParticipationCalibratedStddev_offset, and fixed-epoch owners in PoissonFixedEpochAsymptotics.lean, Rate and Variance. The target uses T=E+extra, covering all admissible integer horizons; it includes the explicit sqrt/log scale and quantile constant. Check calibration definition equality, not just matching sampling rates. No complete bridge proof is supplied.

Then save revisions.json containing original offset paragraph, minimally revised paragraph, exact proof/attempt reference, proposed offset coverage assessment, unchanged leading-component status, and rationale distinguishing formal proof from attributed correspondence. Do not upgrade leading or the whole theorem. Do not edit supplied shared materials or compiled imports. Report the actual outcome and any statement narrowing. Normal ordinary-tool exploration is welcome.
'''
 if arm=='augmented':base+='''\nExisting Ladon is optional. Qualified candidate 3806c436fe68e4d5700646b649b6a6525ec14ba0 is on PATH. See ladon proof-search --help and ladon result guide/inspect --help; source-goal completion is available via ladon proof-search complete --help. Use only if it helps preserve original-goal/proof/coverage handoff; command invocation alone is no benefit. The existing portable manifest assets are in mathematics/evidence.\n'''
 else:base+='\nUse ordinary Lean/source/file tools for this baseline; do not invoke Ladon.\n'
 (state/(arm+'-prompt.txt')).write_text(base)
protocol={'schema':'ladon-offset-bridge-r63-v1','model':'gpt-6-luna','reasoning':'medium','taskOrder':['ordinary','augmented'],'secondsPerSession':1800,'memoryCapBytes':34359738368,'savedReportsCapped':False,'retries':0,'interventions':[],'qualifiedOptionalCandidate':'3806c436fe68e4d5700646b649b6a6525ec14ba0','sourceSnapshot':'same frozen r62 shared Mf/DP sources and evidence; compiled imports read-only from pinned neighbor','task':'thm:smallbatch offset only','targetSha256':hashlib.sha256(target.encode()).hexdigest(),'interpretation':'Attributed formal rendering: extra ranges over Nat, T=E+extra covers every admissible integer horizon; early horizons omitted by atTop. Exact sigma, explicit scale and limiting quantile preserved. No leading coverage promotion.','success':'Unchanged intended declaration compiler checked with allowed transitive axioms, or exact residual; product contribution evaluated separately; no forcing uptake or retrying prompts','stoppingRule':'If optional existing commands add no concrete contribution, consolidate standalone interfaces; no third uptake challenge','promptHashes':{arm:hashlib.sha256((state/(arm+'-prompt.txt')).read_bytes()).hexdigest() for arm in ['ordinary','augmented']}}
(state/'reader-protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');(state/'qualification-run-path').write_text((root/'.codex/state/benefit-readers-r62/qualification-run-path').read_text())
shutil.copy2(root/'.codex/state/benefit-readers-r62/session_exec.py',state/'session_exec.py')
t=(root/'.codex/state/benefit-readers-r62/read_one.py').read_text().replace("'.codex/state/benefit-readers-r62'","'.codex/state/offset-bridge-r63'").replace("name.endswith('augmented')","name == 'augmented'").replace('timeout_seconds=600','timeout_seconds=1800').replace("assert (state/'qualified-candidate.json').exists()","assert (state/'qualification-run-path').exists()")
(state/'read_one.py').write_text(t)
print(run)
