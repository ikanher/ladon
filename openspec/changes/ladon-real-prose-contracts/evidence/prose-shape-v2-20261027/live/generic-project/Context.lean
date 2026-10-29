import Mathlib.Data.Real.Basic
abbrev Fn := Nat → Real
def BoundGlobal (f : Fn) (n : Nat) (C : Real) : Prop := ∀ i ≤ n, |f i| ≤ C
def BoundSet (f : Fn) (S : Set Nat) (n : Nat) (C : Real) : Prop := ∀ i ∈ S, i ≤ n → |f i| ≤ C
def Transform (f : Fn) : Fn := fun i => 2 * f i
def bump (n : Nat) := n + 5
def otherOffset (n : Nat) := n + 7
def product (K C : Real) := K * C
def wrongProduct (K C : Real) := K * (C + 1)
