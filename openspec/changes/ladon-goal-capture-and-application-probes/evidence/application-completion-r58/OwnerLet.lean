import Lean
namespace FidelityFixture
open Lean
example {α : Type} [Inhabited α] (x : α) (h : x = x) : x = x ∧ x = x := by
  let y := x
  constructor
