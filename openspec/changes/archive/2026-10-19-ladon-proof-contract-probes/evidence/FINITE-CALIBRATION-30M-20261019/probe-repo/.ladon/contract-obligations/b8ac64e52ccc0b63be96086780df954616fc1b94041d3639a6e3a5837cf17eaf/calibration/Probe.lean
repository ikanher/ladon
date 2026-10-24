import Lean
import Std

namespace LadonProbeCalibration

def fullFamily : List (Fin 5) := [0, 1, 2, 3, 4]
def incompleteFamily : List (Fin 5) := [0, 1, 2, 3]

theorem coverage : ∀ i : Fin 5, i ∈ fullFamily := by decide

theorem full_separates (f g : Fin 5 → Bool)
    (agreement : ∀ i ∈ fullFamily, f i = g i) : f = g :=
  funext (fun i => agreement i (coverage i))

def zero : Fin 5 → Bool := fun _ => false
def last : Fin 5 → Bool := fun i => if i.val = 4 then true else false

theorem incomplete_agreement : ∀ i ∈ incompleteFamily, zero i = last i := by decide

theorem incomplete_not_equal : zero ≠ last := by
  intro h
  have h4 := congrFun h (4 : Fin 5)
  change false = true at h4
  cases h4

theorem incomplete_counterexample :
    (∀ i ∈ incompleteFamily, zero i = last i) ∧ zero ≠ last :=
  ⟨incomplete_agreement, incomplete_not_equal⟩

end LadonProbeCalibration
