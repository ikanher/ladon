import json,re,statistics
from dataclasses import asdict
from pathlib import Path
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd()
repo=root/'.codex/state/navier-stokes-informed-diagnostic/formalization'
out=root/'openspec/changes/ladon-scoped-slice-traversal/evidence/cache-comparison'
out.mkdir(exist_ok=False)
execution=prepare_direct_lean_execution(repo,None,pinned_toolchain(repo),require_compiled_module=False)
for mode,path in [('uncached',root/'src/ladon/lean/ladon_scoped_slice_helper.lean'),('cached',root/'.codex/state/scoped-traversal/scoped-green/ladon_scoped_slice_helper.lean')]:
    code=path.read_text().split('private def resolveName',1)[0]
    code=code.replace('-- LADON_TARGET_IMPORT','import NavierStokes.SmoothFamilyTorusInverse').replace('(maxNodes := 8192)','(maxNodes := 131072)')
    code=code.replace('  walk root 0 #[] true #[]','  let start ← IO.monoNanosNow\n  let result ← walk root 0 #[] true #[]\n  let elapsed := (← IO.monoNanosNow) - start\n  logInfo m!"visited={(← visited.get)} occurrences={result.size} nanos={elapsed}"\n  return result')
    code+='\nrun_meta do\n  let info ← getConstInfo `NavierStokes.SmoothFamilyTorusInverse.norm_derivativeWord_inverse_le\n  let _ ← scopedOccurrences (info.value! true) `NavierStokes.SmoothFourierData.coefficient_seminorm_bound\n'
    (out/f'{mode}.lean').write_text(code)
rows=[]
for i in range(3):
    for mode in (['uncached','cached'] if i%2==0 else ['cached','uncached']):
        r=run_bounded_target_process([*execution.command,str(out/f'{mode}.lean')],cwd=repo,env=execution.environment,timeout_seconds=60,max_output_bytes=8388608,max_rss_bytes=12*1024**3)
        row=asdict(r);row.update(mode=mode,repetition=i)
        with (out/f'{mode}-{i}.json').open('x') as f:json.dump(row,f,indent=2)
        if not r.succeeded:raise SystemExit(r.stdout+r.stderr)
        match=re.search(r'visited=(\d+) occurrences=(\d+) nanos=(\d+)',r.stdout)
        row.update(visits=int(match[1]),occurrences=int(match[2]),traversalSeconds=int(match[3])/1e9)
        rows.append(row)
summary={mode:{'visits':next(r['visits'] for r in rows if r['mode']==mode),'medianTraversalSeconds':statistics.median(r['traversalSeconds'] for r in rows if r['mode']==mode),'medianProcessSeconds':statistics.median(r['elapsed_seconds'] for r in rows if r['mode']==mode),'maxRssBytes':max(r['peak_rss_bytes'] for r in rows if r['mode']==mode)} for mode in ['uncached','cached']}
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
