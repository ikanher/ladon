import importlib.util, sys
from pathlib import Path
p=Path(sys.argv[1])
for short in ('proofir_v3_batch','proofir_v3','proofir_v3_payloads'):
 n='ladon.'+short; s=importlib.util.spec_from_file_location(n,p/(short+'.py')); m=importlib.util.module_from_spec(s); sys.modules[n]=m; s.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('fixture','tests/support/proofir_v3_native.py'); f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
v=sys.modules['ladon.proofir_v3']
class Duplicate(dict):
 def items(self):
  it=list(super().items())
  return it + [it[-1]]
for label, wrap in [('top-level',lambda a: Duplicate(a)),('nested',lambda a: (a.__setitem__('extensions',Duplicate(a['extensions'])) or a))]:
 a=wrap(f.claim_artifact())
 try:
  x=v.validate_envelope(a)
  print(label,'ACCEPT',x.content_id, x.to_dict()==f.claim_artifact())
 except Exception as e:
  print(label,'REJECT',type(e).__name__,str(e),repr(getattr(e,'diagnostic',None)))
