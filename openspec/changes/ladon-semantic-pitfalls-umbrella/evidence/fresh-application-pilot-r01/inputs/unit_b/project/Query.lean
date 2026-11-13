import Mathlib.Order.Lattice.Nat
open Set
namespace AuditUnit
def Claimed (a : ℕ) : Prop := sInf {n : ℕ | a ≤ n} ∈ {n : ℕ | a ≤ n}
example (a : ℕ) : Claimed a := by
  skip
end AuditUnit
