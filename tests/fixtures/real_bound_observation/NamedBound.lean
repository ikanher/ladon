-- Deliberately NOT the mathematical reals. Names and syntax cannot admit laws.
structure Real where
  value : Nat

instance : OfNat Real 0 := ⟨⟨0⟩⟩
instance : LE Real := ⟨fun _ _ => True⟩
instance : Mul Real := ⟨fun a _ => a⟩

def ArbitraryBound (_f : Nat → Real) (_S : Nat → Prop) (_n : Nat) (_C : Real) : Prop :=
  True

def Transform (f : Nat → Real) := f

theorem namedEstimate (n : Nat) :
    ∃ K : Real, 0 ≤ K ∧ ∀ (f : Nat → Real) (S : Nat → Prop) (C : Real),
      0 ≤ C → ArbitraryBound f S (n + 7) C →
      ArbitraryBound (Transform f) S n (K * C) := by
  refine ⟨0, trivial, ?_⟩
  intros
  trivial
