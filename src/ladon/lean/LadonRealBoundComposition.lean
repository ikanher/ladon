import LadonRealBound

/- These laws operate at explicit endpoints and input bounds. A caller may
   quantify them in its own original context; no coefficient uniformity follows. -/
namespace Ladon.RealBound

universe u v w p

def TransferAt {X : Type u} {Y : Type v} {P : Type p}
    (J : X → Set P → Nat → Real → Prop) (Q : Y → Set P → Nat → Real → Prop)
    (x : X) (y : Y) (S : Set P) (m n : Nat) (C K : Real) : Prop :=
  0 ≤ K ∧ (0 ≤ C → J x S m C → Q y S n (K * C))

theorem transfer_identity {X : Type u} {P : Type p}
    (J : X → Set P → Nat → Real → Prop) (x : X) (S : Set P) (n : Nat) (C : Real) :
    TransferAt J J x x S n n C 1 := by
  refine ⟨zero_le_one, ?_⟩
  intro _ h
  simpa only [one_mul] using h

theorem transfer_compose {X : Type u} {Y : Type v} {Z : Type w} {P : Type p}
    {J : X → Set P → Nat → Real → Prop} {Q : Y → Set P → Nat → Real → Prop}
    {R : Z → Set P → Nat → Real → Prop}
    {x : X} {y : Y} {z : Z} {S : Set P} {m n r : Nat} {C K L : Real}
    (first : TransferAt J Q x y S m n C K)
    (second : TransferAt Q R y z S n r (K * C) L) :
    TransferAt J R x z S m r C (L * K) := by
  refine ⟨mul_nonneg second.1 first.1, ?_⟩
  intro hC h
  have middle := first.2 hC h
  have final := second.2 (mul_nonneg first.1 hC) middle
  simpa only [mul_assoc] using final

theorem transfer_input_prefix {X : Type u} {Y : Type v} {P : Type p}
    {J : X → Set P → Nat → Real → Prop} {Q : Y → Set P → Nat → Real → Prop}
    {x : X} {y : Y} {S : Set P} {m m' n : Nat} {C K : Real}
    (hprefix : OrderPrefix J) (hmm' : m ≤ m')
    (step : TransferAt J Q x y S m n C K) :
    TransferAt J Q x y S m' n C K := by
  refine ⟨step.1, ?_⟩
  intro hC h
  exact step.2 hC (hprefix x S m m' C hmm' h)

theorem transfer_output_prefix {X : Type u} {Y : Type v} {P : Type p}
    {J : X → Set P → Nat → Real → Prop} {Q : Y → Set P → Nat → Real → Prop}
    {x : X} {y : Y} {S : Set P} {m n n' : Nat} {C K : Real}
    (hprefix : OrderPrefix Q) (hn'n : n' ≤ n)
    (step : TransferAt J Q x y S m n C K) :
    TransferAt J Q x y S m n' C K := by
  refine ⟨step.1, ?_⟩
  intro hC h
  exact hprefix y S n' n (K * C) hn'n (step.2 hC h)

theorem transfer_coefficient_mono {X : Type u} {Y : Type v} {P : Type p}
    {J : X → Set P → Nat → Real → Prop} {Q : Y → Set P → Nat → Real → Prop}
    {x : X} {y : Y} {S : Set P} {m n : Nat} {C K L : Real}
    (monotone : BoundMonotone Q) (hKL : K ≤ L)
    (step : TransferAt J Q x y S m n C K) :
    TransferAt J Q x y S m n C L := by
  refine ⟨le_trans step.1 hKL, ?_⟩
  intro hC h
  exact monotone y S n (K * C) (L * C)
    (mul_le_mul_of_nonneg_right hKL hC) (step.2 hC h)

theorem scaled_bound_mono {K C D : Real} (hK : 0 ≤ K) (hCD : C ≤ D) :
    K * C ≤ K * D :=
  mul_le_mul_of_nonneg_left hCD hK

end Ladon.RealBound
