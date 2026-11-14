import dataclasses
import json
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process
from ladon.semantic_lean_execution import prepare_direct_lean_execution

out=Path(__file__).resolve().parent
repo=Path('/home/codex/projects/lean/matrix-factorization')
original=repo/'Mf/Optimization/FiniteMemoryAdam/CumulativeEnergyUsefulUtility.lean'
source=original.read_text()
start=source.index('theorem physical_window_expected_energy_le')
end=source.index(' := by',start)
header=source[start:end].replace('physical_window_expected_energy_le','checked_source_energy_chain')
header=header.replace('≤ 29/10', '≤ 63*(73/10:ℝ)^2/(T:ℝ)+1011*(26/(T:ℝ)+1/999) ∧\n    63*(73/10:ℝ)^2/(T:ℝ)+1011*(26/(T:ℝ)+1/999) ≤ 29/10')
assert '∧' in header
term=(out.parent/'attempt03/term.lean.txt').read_text()
term=term.replace('exact (hEnergy.trans hEnvelope).trans hCap','exact ⟨hEnergy.trans hEnvelope, hCap⟩')
probe=('import Mf.Optimization.FiniteMemoryAdam.CumulativeEnergyNumericalBudget\n'
       'import Mf.Optimization.FiniteMemoryAdam.CumulativeEnergyUtility\n'
       'import Mf.Optimization.FiniteMemoryAdam.CumulativeUsefulUtility\n'
       'namespace Mf.Optimization.FiniteMemoryAdam.Cumulative.Energy\n'
       'open MeasureTheory LocalizedVector\nnoncomputable section\n'
       'set_option maxHeartbeats 800000\n'+header+' := '+term+
       '\n#print axioms checked_source_energy_chain\nend\nend Mf.Optimization.FiniteMemoryAdam.Cumulative.Energy\n')
p=out/'CheckedEnergyChain.lean'
p.write_text(probe)
execution=prepare_direct_lean_execution(repo,None,None,require_compiled_module=False)
cmd=['/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean',str(p)]
r=run_bounded_target_process(cmd,cwd=repo,env=execution.environment,
    timeout_seconds=180,max_output_bytes=8*1024**2,max_rss_bytes=12288*1024**2)
record=dataclasses.asdict(r)
record['libraryRoots']=[str(p) for p in execution.library_roots]
(out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ('returncode','stdout','stderr','elapsed_seconds','timed_out','memory_limited','peak_rss_bytes')},indent=2))
raise SystemExit(0 if r.succeeded else 1)
