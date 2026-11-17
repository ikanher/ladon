import Mf.DP.ClassicalEventDPSubsetReplacementCounting

namespace SamplingOrdering

-- At-most-one coordinate difference; equality is permitted.
def AgreeOff {n : ℕ} {X : Type} (a b : Fin n → X) (j : Fin n) : Prop :=
  ∀ i, i ≠ j → a i = b i

def selected {n m : ℕ} {X : Type} (D : Fin n → X) (e : Fin m → Fin n) := D ∘ e

-- Same-subset comparison: the original changed slot has one preimage at most.
theorem selected_agree_off {n m : ℕ} {X : Type}
    (D D' : Fin n → X) (special : Fin n) (hD : AgreeOff D D' special)
    (e : Fin m → Fin n) (he : Function.Injective e)
    (j : Fin m) (hj : e j = special) :
    AgreeOff (selected D e) (selected D' e) j := by
  intro i hij
  apply hD
  intro h
  apply hij
  apply he
  exact h.trans hj.symm

-- Excluded branch has identical selected inputs.
theorem selected_eq_of_excluded {n m : ℕ} {X : Type}
    (D D' : Fin n → X) (special : Fin n) (hD : AgreeOff D D' special)
    (e : Fin m → Fin n) (excluded : ∀ i, e i ≠ special) :
    selected D e = selected D' e := by
  funext i
  exact hD (e i) (excluded i)

def replaceInPlace {n m : ℕ} (e : Fin m → Fin n) (j : Fin m) (outside : Fin n) :
    Fin m → Fin n := fun i => if i = j then outside else e i

theorem replacement_injective {n m : ℕ}
    (e : Fin m → Fin n) (he : Function.Injective e)
    (j : Fin m) (outside : Fin n) (houtside : ∀ i, e i ≠ outside) :
    Function.Injective (replaceInPlace e j outside) := by
  intro a b hab
  by_cases ha : a = j
  · subst a
    by_cases hb : b = j
    · exact hb.symm
    · simp [replaceInPlace, hb] at hab
      exact False.elim (houtside b hab.symm)
  · by_cases hb : b = j
    · subst b
      simp [replaceInPlace, ha] at hab
      exact False.elim (houtside a hab)
    · apply he
      simpa [replaceInPlace, ha, hb] using hab

-- Replacement comparison: keep the selected coordinates in their original positions.
theorem replacement_agree_off {n m : ℕ} {X : Type}
    (D D' : Fin n → X) (special : Fin n) (hD : AgreeOff D D' special)
    (e : Fin m → Fin n) (he : Function.Injective e)
    (j : Fin m) (hj : e j = special) (outside : Fin n) :
    AgreeOff (selected D e) (selected D' (replaceInPlace e j outside)) j := by
  intro i hij
  change D (e i) = D' (if i = j then outside else e i)
  rw [if_neg hij]
  apply hD
  intro h
  exact hij (he (h.trans hj.symm))

-- Ordered selections for subsets {0,1} and {1,2}, with distinct slot values.
def before : Fin 2 → Fin 3 := ![0, 1]
def after : Fin 2 → Fin 3 := ![1, 2]

theorem sorted_replacement_changes_both :
    before 0 ≠ after 0 ∧ before 1 ≠ after 1 := by decide

theorem sorted_replacement_not_agree_off :
    ¬ ∃ j, AgreeOff before after j := by
  unfold AgreeOff
  decide

-- Finite uniform output-law calculation for M(tuple) = first slot value,
-- with distinct slot values D=(0,1,2). Only M's result is observed.
def increasingSelections : Finset (Fin 3 × Fin 3) :=
  Finset.univ.filter (fun a => a.1 < a.2)
def orderedSelections : Finset (Fin 3 × Fin 3) :=
  Finset.univ.filter (fun a => a.1 ≠ a.2)

def firstZeroProbability (choices : Finset (Fin 3 × Fin 3)) : ℚ :=
  ((choices.filter (fun a => a.1 = 0)).card : ℚ) / (choices.card : ℚ)

theorem ordering_changes_output_law :
    firstZeroProbability increasingSelections = 2/3 ∧
    firstZeroProbability orderedSelections = 1/3 ∧
    firstZeroProbability increasingSelections ≠ firstZeroProbability orderedSelections := by
  have hi : increasingSelections.card = 3 := by decide
  have ho : orderedSelections.card = 6 := by decide
  have hi0 : (increasingSelections.filter (fun a => a.1 = 0)).card = 2 := by decide
  have ho0 : (orderedSelections.filter (fun a => a.1 = 0)).card = 2 := by decide
  norm_num [firstZeroProbability, hi, ho, hi0, ho0]

#print selected_agree_off
#print selected_eq_of_excluded
#print replacement_injective
#print replacement_agree_off
#print sorted_replacement_not_agree_off
#print axioms selected_agree_off
#print axioms selected_eq_of_excluded
#print axioms replacement_injective
#print axioms replacement_agree_off
#print axioms sorted_replacement_not_agree_off
#print axioms ordering_changes_output_law
end SamplingOrdering
