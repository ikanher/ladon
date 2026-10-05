namespace Owner
section Inside
variable (α : Type)
open Nat
set_option pp.universes true
example (x : α) (h : x = x) : (x = x) ∧ (x = x) := by
  let x : α := x
  constructor
  · skip
    exact h
  · skip
    exact h
end Inside
end Owner
