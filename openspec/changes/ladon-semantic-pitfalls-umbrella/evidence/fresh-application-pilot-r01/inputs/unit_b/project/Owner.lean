import Mathlib.Order.Lattice.Nat
open Set
namespace AuditUnit
#check Nat.sInf_mem
def Claimed (a : ℕ) : Prop := sInf {n : ℕ | a ≤ n} ∈ {n : ℕ | a ≤ n}
end AuditUnit
