import Lean
-- Parsing and equality controls only: this deliberately is not mathematical Real.
structure Real where
  value : Nat
instance (n : Nat) : OfNat Real n := ⟨⟨n⟩⟩
instance : LE Real := ⟨fun a b => a.value ≤ b.value⟩
instance : Mul Real := ⟨fun a b => ⟨a.value * b.value⟩⟩
instance : Add Real := ⟨fun a b => ⟨a.value + b.value⟩⟩
def Set (α : Type) := α → Prop
abbrev Fn := Nat → Real
def BoundGlobal (_f : Fn) (_n : Nat) (_C : Real) : Prop := True
def BoundSet (_f : Fn) (_S : Set Nat) (_n : Nat) (_C : Real) : Prop := True
def Transform (f : Fn) := f
def bump (n : Nat) := n + 5
def product (K C : Real) := K * C
def wrongProduct (K C : Real) := K * (C + 1)
def nonlinearShift (n : Nat) := 2 * n + 1
