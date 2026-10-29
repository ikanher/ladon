from pathlib import Path
import copy,json,shutil
from ladon.real_prose_inputs import generated_source
from ladon.real_bound_binding import _alpha_expression
b=Path('.codex/state/real-prose-connection');p=b/'probe-project';p.mkdir(exist_ok=True)
old=Path('.codex/state/prose-observation-production/live/project')
(p/'lean-toolchain').write_bytes((old/'lean-toolchain').read_bytes())
if not (p/'.lake').exists():(p/'.lake').symlink_to((old/'.lake').resolve(),target_is_directory=True)
a=json.loads(Path('.codex/state/real-prose-native/live/navier-produced.json').read_text())
from ladon.real_prose_native_payload import recognition_history
r=recognition_history(a['check']['result']['artifacts'][-1]['payload'])
formal=json.loads(Path('openspec/changes/ladon-real-bound-contracts/evidence/qualification-20261027/native/inverse_finiteJets-production.json').read_text())
formal_snapshot=formal['request']['plan']['bindingPlan']['observation']['statementSnapshot']
formal_expr=_alpha_expression(formal_snapshot['observation']['normalizedTypeExpr'])
source=(old/'ProseCases.lean').read_bytes()
assert source.startswith(formal['sourceText'].encode())
reading5=copy.deepcopy(r['request']['interpretation']);reading5['id']='probe:five-order-control'
reading5['symbols']['shift']['leanName']='LadonSourcePair.shiftFive'
request5={'interpretation':reading5,'context':r['request']['context']}
src5,owner5=generated_source(request5,source)
src4,owner4=generated_source(r['request'],src5)
helper=Path('src/ladon/lean/LadonRealBoundBinding.lean').read_text()
renderer=helper[helper.index('private def binderInfoName'):helper.index('\n\nprivate def predicate')]
macro='''

namespace LadonExactConnectionProbe
open Lean Meta Elab Term
RENDERER

elab "ladon_exact_connection% " formal:str expected:str authored:str : term => do
  let formalName := formal.getString.toName
  let authoredName := authored.getString.toName
  let f ← getConstInfo formalName
  let ftype ← zetaReduce (← instantiateMVars f.type)
  let wanted ← match Json.parse expected.getString with
    | .ok v => pure v
    | .error msg => throwError "{msg}"
  unless exprJson ftype == wanted do throwError "formal proposition owner mismatch"
  let a ← getConstInfo authoredName
  let value ← match a with
    | .defnInfo info => pure info.value
    | _ => throwError "authored owner is not a proposition definition"
  unless a.type == mkSort Level.zero do throwError "authored owner is not declared Prop"
  unless (← inferType value) == mkSort Level.zero do throwError "authored value is not Prop"
  return mkForall (Name.mkSimple "formal") BinderInfo.default ftype value

end LadonExactConnectionProbe
'''.replace('RENDERER',renderer)
base=src4.decode()+macro
(p/'Context.lean').write_text(base)
f_name=formal_snapshot['selection']['declaration']
for label,owner in [('five',owner5),('four',owner4)]:
 goal='ladon_exact_connection% '+json.dumps(f_name)+' '+json.dumps(json.dumps(formal_expr,ensure_ascii=False,separators=(',',':')))+' '+json.dumps(owner['declaration'])
 # The proof uses the supplied formal premise, not the already-proved specialization.
 term='''by
  intro original n
  obtain ⟨K, hK, h⟩ := @original LadonSourcePair.NoParameter inferInstance inferInstance inferInstance .temporal n
  refine ⟨K, hK, ?_⟩
  intro F C hf hp hm hC hb
  have hs : ContDiff ℝ ∞ (LadonSourcePair.liftSource F) :=
    hf.comp LadonSourcePair.eraseParameter.toContinuousLinearEquiv.contDiff
  have hper : NavierStokes.SmoothFamilyTorusInverse.Periodic (LadonSourcePair.liftSource F) :=
    fun _ => hp
  have hinput := (LadonSourcePair.bound_equiv F _ C).mpr hb
  have houtput := h (LadonSourcePair.liftSource F) Set.univ C hs hper hC hinput
  rw [LadonSourcePair.lift_inverse] at houtput
  exact (LadonSourcePair.bound_equiv (LadonSourcePair.planeInverse .temporal F) n (K * C)).mp houtput
'''
 (b/('probe-'+label+'.json')).write_text(json.dumps({'goal':goal,'term':term,'source':'Context.lean'},ensure_ascii=False,indent=2)+'\n')
(b/'PROBE-OWNERS.json').write_text(json.dumps({'formalDeclaration':f_name,'formalSourceDigest':formal_snapshot['source']['sha256'],'prefixExtensionExact':True,'authoredOwners':{'five':owner5,'four':owner4},'scope':'Feasibility only. Type-owner checked in Lean; authored exact expected-expression binding still requires producer integration. No nativeconnection.'},indent=2)+'\n')
