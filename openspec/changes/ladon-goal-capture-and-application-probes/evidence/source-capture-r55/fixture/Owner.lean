namespace Owner
variable (α : Type) (x : α)
local notation "Point" => α
example (h : x = x) : (x = x) ∧ (x = x) := by
  let y : Point := x
  constructor
  · skip
    exact h
  · skip
    exact h
end Owner
