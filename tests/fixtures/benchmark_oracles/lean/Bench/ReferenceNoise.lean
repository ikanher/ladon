namespace Bench

def referenceNoise (count : Nat) (xs : List Nat) : Nat :=
  count + xs.length

theorem missingTheoremShape (n : Nat) : n = n := by
  rfl

end Bench
