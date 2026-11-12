from pathlib import Path
import json,time
from ladon.proof_slice import extract_proof_slice
p=Path(__file__).resolve().parent
t=time.monotonic()
r=extract_proof_slice('/home/codex/projects/lean/matrix-factorization','Mf/Optimization/PoissonClippedSGD/GaussianStep.lean','Mf.Optimization.PoissonClippedSGD.GaussianStep','Mf.Optimization.PoissonClippedSGD.gaussian_actual_one_step','Mf.Optimization.PoissonClippedSGD.expected_aligned_step_bound',scoped=True)
(p/'slice-attempt-05.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'status':r['status'],'complete':r['complete'],'elapsedSeconds':time.monotonic()-t,'frontiers':r['frontiers']}))
