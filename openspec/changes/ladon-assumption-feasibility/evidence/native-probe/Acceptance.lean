import Lean
import FeasibilityProbe.Native

open Lean Elab Command Term Meta

namespace FeasibilityProbe.RedAcceptance

theorem inhabited_input (n : Nat) (h : n = 0) : True := True.intro
theorem impossible_input (n : Nat) (h0 : n = 0) (h1 : n = 1) : n = 37 := by omega
theorem conditional_input (n : Nat) (h : n = 0) : n + 1 = 1 := by omega
theorem fixed_input (h : (1 : Nat) = 0) : True := True.intro

theorem alias_dependent_input (h : False)
    (x : (let leaked : Nat := False.elim h; Nat)) : True := True.intro

syntax (name := expectPremiseGoal) "#expect_premise_goal " ident " : " term : command
@[command_elab expectPremiseGoal] def elabExpectPremiseGoal : CommandElab
  | `(#expect_premise_goal $decl:ident : $expected:term) => do
      let declName ← liftCoreM <| realizeGlobalConstNoOverloadWithInfo decl
      let info ← getConstInfo declName
      liftTermElabM do
        let expectedExpr ← elabType expected
        match ← FeasibilityProbe.Native.buildPremiseGoal info.type with
        | .supported actual =>
            if actual.hasFVar || actual.hasMVar then
              throwError "{decl} produced an open premise goal"
            unless ← isDefEq actual expectedExpr do
              throwError "{decl} produced a goal with the wrong type"
        | .unsupported _ => throwError "{decl} unexpectedly unsupported"
  | _ => throwUnsupportedSyntax

syntax (name := expectDeclarationType) "#expect_declaration_type " ident " : " term : command
@[command_elab expectDeclarationType] def elabExpectDeclarationType : CommandElab
  | `(#expect_declaration_type $decl:ident : $expected:term) => do
      let declName ← liftCoreM <| realizeGlobalConstNoOverloadWithInfo decl
      let info ← getConstInfo declName
      liftTermElabM do
        let expectedExpr ← elabType expected
        unless ← isDefEq info.type expectedExpr do
          throwError "{decl} no longer has its conditional theorem type"
  | _ => throwUnsupportedSyntax

syntax (name := expectUnsupported) "#expect_premise_unsupported " ident : command
@[command_elab expectUnsupported] def elabExpectUnsupported : CommandElab
  | `(#expect_premise_unsupported $decl:ident) => do
      let declName ← liftCoreM <| realizeGlobalConstNoOverloadWithInfo decl
      let info ← getConstInfo declName
      liftTermElabM do
        match ← FeasibilityProbe.Native.buildPremiseGoal info.type with
        | .unsupported _ => pure ()
        | .supported _ => throwError "{decl} must remain explicitly unsupported"
  | _ => throwUnsupportedSyntax

#expect_declaration_type impossible_input : (∀ n : Nat, n = 0 → n = 1 → n = 37)
#expect_declaration_type conditional_input : (∀ n : Nat, n = 0 → n + 1 = 1)
#expect_premise_goal inhabited_input : (∃ n : Nat, n = 0)
#expect_premise_goal impossible_input : (∃ n : Nat, n = 0 ∧ n = 1)
#expect_premise_goal conditional_input : (∃ n : Nat, n = 0)
#expect_premise_goal fixed_input : ((1 : Nat) = 0)
#expect_premise_unsupported alias_dependent_input

-- `impossible_input` itself proves an arbitrary target from contradictory assumptions;
-- that valid conditional declaration is not a source error.

-- Independent closed proofs: no declaration hypotheses are in scope.
example : (∃ n : Nat, n = 0) := ⟨0, rfl⟩
example : ¬ (∃ n : Nat, n = 0 ∧ n = 1) := by
  rintro ⟨n, h0, h1⟩
  omega
example : (∀ n : Nat, n = 0 → n + 1 = 1) := by
  intro n h
  omega
example : ¬ ((1 : Nat) = 0) := by decide

end FeasibilityProbe.RedAcceptance
