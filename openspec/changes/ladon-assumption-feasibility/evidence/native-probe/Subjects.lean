import Lean
import FeasibilityProbe.Native

namespace FeasibilityProbe.Subjects

theorem inhabited (n : Nat) (_h : n = 0) : True := True.intro
theorem impossible (n : Nat) (h0 : n = 0) (h1 : n = 1) : n = 37 := by omega
theorem fixed (_h : (1 : Nat) = 0) : True := True.intro

end FeasibilityProbe.Subjects

open Lean Elab Term Meta

-- Resolve a declaration, then return its native generated premise proposition.
-- The string is a declaration locator, never a printed expression to reparse.
elab "premise_context% " target:str : term => do
  let info ← getConstInfo target.getString.toName
  match ← FeasibilityProbe.Native.buildPremiseGoal info.type with
  | .supported goal =>
      if goal.hasFVar || goal.hasMVar then throwError "premise context is open"
      pure goal
  | .unsupported _ => throwError "unsupported premise context"
