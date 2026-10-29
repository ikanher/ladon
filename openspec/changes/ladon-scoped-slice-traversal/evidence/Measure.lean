import NavierStokes.SmoothFamilyTorusInverse
import Lean
open Lean Elab Command Meta
private partial def measureSlice (root : Expr) : MetaM Unit := do
  let seen ← IO.mkRef ({} : ExprSet)
  let nodes ← IO.mkRef (0 : Nat)
  let hits ← IO.mkRef (0 : Nat)
  let rec visit (e : Expr) : MetaM Unit := do
    nodes.modify (· + 1)
    if (← nodes.get) > 200000 then throwError "measurement cap"
    if (← seen.get).contains e then return
    seen.modify (·.insert e)
    if e.isApp && e.getAppFn.constName? == some `NavierStokes.SmoothFourierData.coefficient_seminorm_bound then
      hits.modify (· + 1)
    match e with
    | .app f a => visit f; visit a
    | .lam _ t b _ | .forallE _ t b _ => visit t; visit b
    | .letE _ t v b _ => visit t; visit v; visit b
    | .mdata _ b | .proj _ _ b => visit b
    | _ => pure ()
  visit root
  logInfo m!"unique={(← seen.get).size} visits={(← nodes.get)} hits={(← hits.get)}"
run_meta do
  let i ← getConstInfo `NavierStokes.SmoothFamilyTorusInverse.norm_derivativeWord_inverse_le
  measureSlice (i.value! true)
