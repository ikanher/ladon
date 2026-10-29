import LadonRealBoundComposition
import Mathlib.Tactic.NormNum

open Ladon.RealBound
namespace RuleExamples

universe u v w p

theorem dependent_composition {X : Type u} {Y : Type v} {Z : Type w} {P : Type p}
    (J : X → Set P → Nat → Real → Prop) (Q : Y → Set P → Nat → Real → Prop)
    (R : Z → Set P → Nat → Real → Prop) (A : X → Y) (B : Y → Z)
    (K : X → Real → Real) (L : Y → Real → Real)
    (S : Set P) (a b c : Nat)
    (first : ∀ x C, TransferAt J Q x (A x) S a b C (K x C))
    (second : ∀ y D, TransferAt Q R y (B y) S b c D (L y D)) :
    ∀ x C, TransferAt J R x (B (A x)) S a c C (L (A x) (K x C * C) * K x C) := by
  intro x C
  exact transfer_compose (first x C) (second (A x) (K x C * C))

theorem weaken_input {X Y P : Type} (J : X → Set P → Nat → Real → Prop)
    (Q : Y → Set P → Nat → Real → Prop) (x : X) (y : Y) (S : Set P) (C K : Real)
    (hJ : OrderPrefix J) (h : TransferAt J Q x y S 3 1 C K) :
    TransferAt J Q x y S 7 1 C K :=
  transfer_input_prefix hJ (by decide : 3 ≤ 7) h

theorem weaken_output {X Y P : Type} (J : X → Set P → Nat → Real → Prop)
    (Q : Y → Set P →Nat → Real → Prop) (x : X) (y : Y) (S : Set P) (C K : Real)
    (hQ : OrderPrefix Q) (h : TransferAt J Q x y S 7 3 C K) :
    TransferAt J Q x y S 7 1 C K :=
  transfer_output_prefix hQ (by decide : 1 ≤ 3) h

theorem weaken_coefficient {X Y P : Type} (J : X → Set P → Nat → Real → Prop)
    (Q : Y → Set P → Nat → Real → Prop) (x : X) (y : Y) (S : Set P) (C : Real)
    (hQ : BoundMonotone Q) (h : TransferAt J Q x y S 7 3 C 2) :
    TransferAt J Q x y S 7 3 C 5 :=
  transfer_coefficient_mono hQ (by norm_num : (2 : Real) ≤ 5) h

def scalarMeasure (x : Real) (_p _y : Unit) (_j : Nat) : Real := x
def pairMeasure (x : Real × Real) (_p _y : Unit) (_j : Nat) : Real := x.1 + x.2
def tripleMeasure (x : Real × Real × Real) (_p _y : Unit) (_j : Nat) : Real :=
  x.1 + x.2.1 + x.2.2

def scalarBudget := PrefixBound scalarMeasure
def pairBudget := PrefixBound pairMeasure
def tripleBudget := PrefixBound tripleMeasure

theorem scalar_to_pair (x C : Real) (S : Set Unit) :
    TransferAt scalarBudget pairBudget x (x, x) S 7 3 C 2 := by
  refine ⟨by norm_num, ?_⟩
  intro _ hx j hj p hp y
  have bound := hx j (Nat.le_trans hj (by decide : 3 ≤ 7)) p hp y
  change x + x ≤ 2 * C
  change x ≤ C at bound
  simpa only [two_mul] using add_le_add bound bound

theorem pair_to_triple (x : Real × Real) (C : Real) (S : Set Unit) :
    TransferAt pairBudget tripleBudget x (x.1, x.2, x.1 + x.2) S 3 1 C 2 := by
  refine ⟨by norm_num, ?_⟩
  intro _ hx j hj p hp y
  have bound := hx j (Nat.le_trans hj (by decide : 1 ≤ 3)) p hp y
  change x.1 + x.2 + (x.1 + x.2) ≤ 2 * C
  change x.1 + x.2 ≤ C at bound
  simpa only [two_mul] using add_le_add bound bound

theorem scalar_to_triple (x C : Real) (S : Set Unit) :
    TransferAt scalarBudget tripleBudget x (x, x, x + x) S 7 1 C (2 * 2) :=
  transfer_compose (scalar_to_pair x C S) (pair_to_triple (x, x) (2 * C) S)

def sequenceMeasure (x : Nat → Real) (p : Nat) (_y : Unit) (j : Nat) : Real := x (p + j)
def sequenceBudget := PrefixBound sequenceMeasure

theorem scale_sequence (q : Real) (hq : 0 ≤ q) (x : Nat → Real) (C : Real) (S : Set Nat) :
    TransferAt sequenceBudget sequenceBudget x (fun i => q * x i) S 5 2 C q := by
  refine ⟨hq, ?_⟩
  intro _ hx j hj p hp y
  exact mul_le_mul_of_nonneg_left (hx j (Nat.le_trans hj (by decide : 2 ≤ 5)) p hp y) hq

theorem sequence_context (q : Real) (hq : 0 ≤ q) (x : Nat → Real)
    (C : Real) (S : Set Nat)
    (second : TransferAt sequenceBudget sequenceBudget (fun i => q * x i)
      (fun i => (q + 1) * (q * x i)) S 2 0 (q * C) (q + 1)) :
    TransferAt sequenceBudget sequenceBudget x (fun i => (q + 1) * (q * x i))
      S 5 0 C ((q + 1) * q) :=
  transfer_compose (scale_sequence q hq x C S) second

theorem scale_inequality (K C D : Real) (hK : 0 ≤ K) (hCD : C ≤ D) :
    K * C ≤ K * D := scaled_bound_mono hK hCD

theorem identity_example {X P : Type} (J : X → Set P → Nat → Real → Prop)
    (x : X) (S : Set P) (n : Nat) (C : Real) :
    TransferAt J J x x S n n C 1 := transfer_identity J x S n C

end RuleExamples
