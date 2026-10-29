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


noncomputable def _root_.LadonProseReading_b9ca7587fe232ab2a9a8894d263c1028e884e06e7ea5e78ce5e340f4e65337a5 : Prop := (∀ (v0 : Nat), (∃ (v1 : Real), ((0 ≤ v1) ∧ (∀ (v2 : Fn), (∀ (v3 : Real), ((0 ≤ v3) → (((_root_.BoundGlobal : Fn → Nat → Real → Prop) v2 ((_root_.bump : Nat → Nat) v0) v3) → ((_root_.BoundGlobal : Fn → Nat → Real → Prop) ((_root_.Transform : Fn → Fn) v2) v0 ((_root_.product : Real → Real → Real) v1 v3)))))))))
