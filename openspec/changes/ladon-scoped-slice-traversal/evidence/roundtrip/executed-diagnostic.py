import json
from pathlib import Path
import ladon.proof_slice as ps
original=ps.helper_source

def diagnostic_source(path):
    code=original(path)
    code=code.replace(b'let sort \xe2\x86\x90 inferType target', b'logInfo m!"DEBUG ROUNDTRIP TARGET:\\n{targetText}"\n        logInfo m!"DEBUG ROUNDTRIP PROOF:\\n{proofText}"\n        let sort \xe2\x86\x90 inferType target')
    return code

ps.helper_source=diagnostic_source
root=Path('.codex/state/navier-stokes-informed-diagnostic/formalization').resolve()
v=ps.extract_proof_slice(root,'NavierStokes/SmoothFamilyTorusInverse.lean','NavierStokes.SmoothFamilyTorusInverse','NavierStokes.SmoothFamilyTorusInverse.norm_derivativeWord_inverse_le','NavierStokes.SmoothFourierData.coefficient_seminorm_bound',scoped=True)
Path('.codex/state/scoped-roundtrip/diagnostic.json').write_text(json.dumps(v,indent=2))
for r in v['processReceipts']:
 if r.get('stdout'):
  Path('.codex/state/scoped-roundtrip/printed.txt').write_text(r['stdout'])
  print(r['stdout'][:2200])
