import LadonRealBound

namespace SequenceBounds

def Object := Nat → Real

def sample (f : Object) (p : Nat) (_y : Unit) (j : Nat) : Real := f (p + j)

def envelope (f : Object) (S : Set Nat) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, f (p + j) ≤ C

theorem adapter : Ladon.RealBound.Admission envelope sample := by
  apply Ladon.RealBound.admit_of_equiv
  intro f S n C
  constructor
  · intro h j hj p hp y
    exact h j hj p hp
  · intro h j hj p hp
    exact h j hj p hp ()

end SequenceBounds
