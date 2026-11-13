import Mathlib.Order.Lattice.Nat
open Set
namespace AuditUnit
#check Nat.sInf_mem
def Claimed (S : Set ℕ) : Prop := sInf S ∈ S
end AuditUnit
