import Lean
namespace FidelityFixture
open Lean
example {α : Type} [Inhabited α] (x : α) (y : α := x) (h : y = y) : y = y ∧ y = y := by
  constructor
