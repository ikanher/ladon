import Main

-- The supplied prose states exactly the premises hp : P and hpq : P → Q,
-- then claims Q. Check that direct inference in the pinned local environment.
theorem proseInference (P Q : Prop) (hp : P) (hpq : P → Q) : Q := by
  exact hpq hp

#check proseInference
#check result
