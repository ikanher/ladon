"""Bounded follow-up: verify the full displayed chain in the existing context."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

out = Path(__file__).resolve().parent
prior = out.parent / 'internal-0.4.2-adam-energy-r01'
repo = Path('/home/codex/projects/lean/matrix-factorization')
term = '''by
  have hq0 : 0 < q := by exact_mod_cast (show (0:ℝ) < q by linarith [hqr.1])
  have hV0 := releaseVariance_nonneg 50000 100000 q.coe_nonneg hqr.2 σ θ ρ (1001/1000)
  have hV := releaseVariance_safe (G := 1001/1000) hqr hθ hρ (by norm_num)
    (physical_noise_window_scaled hσ)
  have checkedChain :
      (expectedUpdateEnergy (T := T) F data η (1/100000000) x0 q hq σ ≤
        63*(73/10:ℝ)^2/(T:ℝ)+1011*(26/(T:ℝ)+1/999)) ∧
      (63*(73/10:ℝ)^2/(T:ℝ)+1011*(26/(T:ℝ)+1/999) ≤ 29/10) := by
    constructor
    · exact (model_expected_update_energy_le (T := T) F data (by norm_num) (by norm_num)
        hθ hρ (by norm_num) η (1/100000000) x0 hη (by norm_num) q hq hq0 σ
        (r := 64) (by norm_num)).trans (logEnergyBound_envelope (by omega) hV0 hV)
    · have hTR : (16384:ℝ) ≤ T := by exact_mod_cast hT
      have h1 : 63*(73/10:ℝ)^2/(T:ℝ) ≤ 63*(73/10:ℝ)^2/16384 := by gcongr
      have h2 : (26:ℝ)/(T:ℝ) ≤ 26/16384 := by gcongr
      norm_num at h1 h2 ⊢
      linarith
  exact checkedChain.1.trans checkedChain.2
'''
(out / 'term.lean.txt').write_text(term)
cmd = [sys.executable, '-m', 'ladon.entrypoint', 'proof-search', 'goal', 'complete',
       '--repo-root', str(repo), '--capture-file', str(prior/'energy-goal-capture.json'),
       '--term', term, '--toolchain-mode', 'explicit',
       '--lean-path', '/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean',
       '--lake-path', '/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lake',
       '--timeout-seconds', '180', '--max-output-mib', '8', '--max-rss-mib', '12288',
       '--format', 'json', '--output', str(out/'completion.json')]
source=repo/'latex/natural-language/finite_initialized_clipped_adam_rate.tex'
initial=hashlib.sha256(source.read_bytes()).hexdigest()
started=time.monotonic()
with (out/'stdout.txt').open('w') as stdout, (out/'stderr.txt').open('w') as stderr:
    result=subprocess.run(cmd,cwd=repo,stdout=stdout,stderr=stderr,check=False)
record={'command':cmd,'cwd':str(repo),'exitCode':result.returncode,
        'elapsedSeconds':time.monotonic()-started,'sourceSha256Before':initial,
        'sourceSha256After':hashlib.sha256(source.read_bytes()).hexdigest(),
        'captureSha256':hashlib.sha256((prior/'energy-goal-capture.json').read_bytes()).hexdigest()}
(out/'command.json').write_text(json.dumps(record,indent=2)+'\n')
if (out/'completion.json').exists():
    payload=json.loads((out/'completion.json').read_text())
    print(json.dumps({key:payload.get(key) for key in ('status','diagnostic','resourceAccounting')},indent=2))
else:
    print('No completion artifact; inspect stderr.txt')
raise SystemExit(result.returncode)
