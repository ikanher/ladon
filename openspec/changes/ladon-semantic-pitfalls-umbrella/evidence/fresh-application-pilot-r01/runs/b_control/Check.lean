import Mathlib.Order.Lattice.Nat
open Set
namespace AuditUnitControl

def Claimed (a : ℕ) : Prop := sInf {n : ℕ | a ≤ n} ∈ {n : ℕ | a ≤ n}

example (a : ℕ) : Claimed a := by
  unfold Claimed
  exact Nat.sInf_mem ⟨a, by simp⟩

end AuditUnitControl
