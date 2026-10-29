import Mathlib.Data.Real.Basic

/- Compile this family in a clean module before loading a target source.
   No derivative, norm, or paper-specific meaning is inferred for `measure`. -/
namespace Ladon.RealBound

universe u v w

def PrefixBound {F : Type u} {P : Type v} {Y : Type w}
    (measure : F → P → Y → Nat → Real)
    (f : F) (S : Set P) (n : Nat) (C : Real) : Prop :=
  ∀ j ≤ n, ∀ p ∈ S, ∀ y, measure f p y j ≤ C

def Equivalent {F : Type u} {P : Type v} {Y : Type w}
    (J : F → Set P → Nat → Real → Prop) (measure : F → P → Y → Nat → Real) : Prop :=
  ∀ f S n C, J f S n C ↔ PrefixBound measure f S n C

def OrderPrefix {F : Type u} {P : Type v}
    (J : F → Set P → Nat → Real → Prop) : Prop :=
  ∀ f S i j C, i ≤ j → J f S j C → J f S i C

def BoundMonotone {F : Type u} {P : Type v}
    (J : F → Set P → Nat → Real → Prop) : Prop :=
  ∀ f S n C D, C ≤ D → J f S n C → J f S n D

def Admission {F : Type u} {P : Type v} {Y : Type w}
    (J : F → Set P → Nat → Real → Prop) (measure : F → P → Y → Nat → Real) : Prop :=
  Equivalent J measure ∧ OrderPrefix J ∧ BoundMonotone J

theorem prefix_order {F : Type u} {P : Type v} {Y : Type w}
    (measure : F → P → Y → Nat → Real) : OrderPrefix (PrefixBound measure) := by
  intro f S i j C hij h k hk p hp y
  exact h k (Nat.le_trans hk hij) p hp y

theorem prefix_bound {F : Type u} {P : Type v} {Y : Type w}
    (measure : F → P → Y → Nat → Real) : BoundMonotone (PrefixBound measure) := by
  intro f S n C D hCD h j hj p hp y
  exact le_trans (h j hj p hp y) hCD

theorem admit_of_equiv {F : Type u} {P : Type v} {Y : Type w}
    {J : F → Set P → Nat → Real → Prop} {measure : F → P → Y → Nat → Real}
    (h : Equivalent J measure) : Admission J measure := by
  refine ⟨h, ?_, ?_⟩
  · intro f S i j C hij hj
    exact (h f S i C).mpr (prefix_order measure f S i j C hij ((h f S j C).mp hj))
  · intro f S n C D hCD hC
    exact (h f S n D).mpr (prefix_bound measure f S n C D hCD ((h f S n C).mp hC))

end Ladon.RealBound
