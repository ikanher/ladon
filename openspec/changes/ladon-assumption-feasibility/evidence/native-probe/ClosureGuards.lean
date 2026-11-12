import Lean
import FeasibilityProbe.Native

open Lean Elab Command Meta

theorem letContext : ∀ (h : False),
    let leaked : Nat := False.elim h
    ∀ (n : Nat), n = leaked → True := by
  intros
  trivial

def dataResult (n : Nat) : Nat := n

elab "#require_unsupported " target:ident : command => do
  let name ← liftCoreM <| realizeGlobalConstNoOverloadWithInfo target
  let info ← getConstInfo name
  liftTermElabM do
    match ← FeasibilityProbe.Native.buildPremiseGoal info.type with
    | .unsupported _ => pure ()
    | .supported _ => throwError "{target} silently projected an unsupported context"

#require_unsupported letContext
#require_unsupported dataResult
