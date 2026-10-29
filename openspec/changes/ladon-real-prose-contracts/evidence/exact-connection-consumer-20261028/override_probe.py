"""Falsify target binding under a conditional source elaboration extension."""
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path('tests').resolve()))
from real_prose_connection_live_helpers import interpretation
from ladon.proof_slice import pinned_toolchain
from ladon.real_prose_connection import connect_real_prose_bound
from ladon.real_prose_native_production import produce_real_prose_bound

base = Path(__file__).resolve().parent
q = base/'qualified-set'
original_root = Path((q/'ROOT.txt').read_text().strip())
root = base/'source-override-probe'
root.mkdir()
(root/'lean-toolchain').write_bytes((original_root/'lean-toolchain').read_bytes())
(root/'.lake/build/lib/lean').mkdir(parents=True)
for i,library in enumerate(pinned_toolchain(original_root).library_roots):
    target = root/f'.lake/packages/import{i}/.lake/build/lib/lean'
    target.parent.mkdir(parents=True)
    target.symlink_to(library,target_is_directory=True)
rule = 'elab_rules : term | `(ladon_prose_exact_goal% $_request:str) => pure (Lean.mkConst ``True)'
probe = 'ladon_prose_exact_goal% "{}"'
extension = '''

def ConnectionBadOperator (f : Real) := f+1
open Lean Elab Command
run_cmd do
  match Lean.Parser.runParserCategory (← getEnv) `term PROBE with
  | .error _ => pure ()
  | .ok _ =>
    match Lean.Parser.runParserCategory (← getEnv) `command RULE with
    | .error message => throwError "{message}"
    | .ok command => elabCommand command
'''.replace('PROBE',json.dumps(probe)).replace('RULE',json.dumps(rule))
(root/'Context.lean').write_text((original_root/'Context.lean').read_text()+extension)
(root/'claim.txt').write_bytes((original_root/'claim.txt').read_bytes())
reading = interpretation(root,global_scope=False)
reading['id'] = 'generic:overridden-goal-falsifier'
reading['symbols']['A'] = {'leanName':'ConnectionBadOperator','leanType':'Real → Real'}
context = {'schema':'ladon-prose-bound-context-v1','file':'Context.lean','module':'Context','scope':'file-end'}
authored = produce_real_prose_bound(root,reading,context,alternative_id='generic:overridden-goal',
                                    author='falsification',timeout_seconds=120)
(base/'OVERRIDE-AUTHORED.json').write_text(json.dumps(authored)+'\n')
assert authored['status'] == 'authored',authored['check'].get('diagnostic')
formal = json.loads((q/'FORMAL.json').read_text())
request = {'schema':'ladon-real-prose-connection-request-v1','term':'by exact True.intro','premises':[]}
result = connect_real_prose_bound(formal,authored,original_root,root,request,timeout_seconds=300)
(base/'OVERRIDE-RESULT.json').write_text(json.dumps(result)+'\n')
inner = result['check']['result'] or {}
goal = inner.get('goal') or {}
capture = (goal.get('capture') or {}).get('capture') or {}
print({'status':result['status'],'diagnostic':result['check']['diagnostic'],
       'capturedType':capture.get('goal',{}).get('typeDisplay'),
       'axioms':(goal.get('completion') or {}).get('trust',{}).get('observedAxioms')})
assert result['status'] != 'connected','source elaborator replaced the exact requested goal'
