import FeasibilityFixture
import FeasibilityWorker

open Lean Elab Command Term Meta Ladon.Feasibility

elab "#expect_premises " target:ident " : " expected:term : command => do
  liftTermElabM do
    let info ← getConstInfo target.getId
    let expected ← elabType expected
    let .ok actual ← (closePremises info.type 64).run |
      throwError "fixture unexpectedly unsupported"
    unless ← isDefEq actual.proposition expected do
      throwError "unexpected closure {actual.proposition}"

#expect_premises silly_theorem : (∃ n : Nat, n = 0 ∧ n = 1)
#expect_premises trivialConclusion : (∃ n : Nat, n = 0 ∧ n = 1)
#expect_premises inhabitedNat : (∃ n : Nat, n = 0)
#expect_premises prove_anything : (∃ _ : Prop, BadStructure)
#expect_premises propParameter : (∃ P : Prop, P)
#expect_premises legitimateContradiction : Decoy
#expect_premises negFalse : True
#expect_premises explicitArrow : False
#expect_premises verifiedClaim : False
#expect_premises aliasedNegation : True
#expect_premises certifiedClaim : (∃ h : False, ∃ _ : Receipt h, True)
#expect_premises feasibleDependent : (∃ h : True, ∃ _ : TrueReceipt h, True)

#expect_premises boolParam : (∃ _ : Bool, False)
#expect_premises dependentParam : (∃ α : Type, ∃ _ : α, False)
#expect_premises projectedContradiction : (∃ n : Nat, IncompatibleBounds n)

run_cmd do
  let nameForReplay := freshCertificateName (← getEnv)
  if nameForReplay == certificateName then
    throwError "fixture must exercise the certificate name collision"
  for name in [`wrongRefutation, `circularRefutation, `uncheckedRefutation] do
    let info ← getConstInfo name
    let proof : TheoremVal := {
      name := nameForReplay
      levelParams := []
      type := info.type
      value := mkConst name
    }
    liftIO <| saveCertificate s!"{name}.olean" #[.thmInfo proof]

  let expected ← getConstInfo `circularRefutation
  let mistyped : TheoremVal := {
    name := nameForReplay
    levelParams := []
    type := expected.type
    value := mkConst `wrongRefutation
  }
  liftIO <| saveCertificate "mistyped.olean" #[.thmInfo mistyped]

  let independent ← getConstInfo `independentRefutation
  let colliding : TheoremVal := {
    name := certificateName
    levelParams := []
    type := independent.type
    value := mkConst independent.name
  }
  liftIO <| saveCertificate "collidingCertificate.olean" #[.thmInfo colliding]

  let auxiliary : TheoremVal := {
    name := `LadonFeasibility.fixtureAuxiliary
    levelParams := []
    type := independent.type
    value := mkConst independent.name
  }
  let certificate := { auxiliary with name := nameForReplay, value := mkConst auxiliary.name }
  liftIO <| saveCertificate "withAuxiliary.olean" #[.thmInfo auxiliary, .thmInfo certificate]
