import Main

-- Countermodel to the disputed inference: the conditional survey rule and tea hold,
-- while coffee is false.
example : ¬ ((True → (True ∨ False)) → True → False) := by
  intro h
  exact h (fun _ => Or.inl trivial) trivial

-- The full supplied formal theorem still establishes coffee using hCoffee.
example (blue tea coffee : Prop) (hBlue : blue)
    (hRule : blue → (tea ∨ coffee)) (hTea : tea) (hCoffee : coffee) : coffee := by
  exact result blue tea coffee hBlue hRule hTea hCoffee
