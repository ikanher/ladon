import Lean
namespace FidelityFixture
open Lean
example {α : Type} [Inhabited α] (x : α) (h : x = x) : x = x ∧ x = x := by
  let y := x
  have z : x = x := (_example (α := α) (x := x) h).1
  constructor
