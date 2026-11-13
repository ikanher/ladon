import Mathlib.Order.Lattice.Nat
open Set
namespace AuditUnit
def Claimed (S : Set ℕ) : Prop := sInf S ∈ S
example (S : Set ℕ) : Claimed S := by
  skip
end AuditUnit
