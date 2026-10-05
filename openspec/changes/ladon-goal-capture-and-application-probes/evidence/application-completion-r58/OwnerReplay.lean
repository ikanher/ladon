import Lean
open Lean Elab Command

theorem completionFeasibilityReplay : ∀ {α : Type} [Inhabited α] (x : α),
  @Eq α x x →
    let y := x;
    @Eq α x x → @Eq α x x :=
  fun {α} [Inhabited α] x h =>
  let y := x;
  fun z => h

run_cmd do
  let axioms ← Lean.collectAxioms `completionFeasibilityReplay
  let names := String.intercalate "," (axioms.toList.map toString)
  logInfo m!"LADON_AXIOMS [{names}]"
  if axioms.contains ``sorryAx then throwError "replay depends on sorryAx"
