import Lean
namespace PitfallCorpus

def Pointwise : Prop := ∀ n : Nat, ∃ k : Nat, n < k
def Uniform : Prop := ∃ k : Nat, ∀ n : Nat, n < k
def NatIntMismatch : Prop := (2 : Nat) - 3 = 0 ∧ (Int.ofNat 2 - 3 : Int) = -1
def Contradictory (n : Nat) : Prop := n = 0 ∧ n = 1
class HasConclusion (P : Prop) : Prop where
  proof : P
end PitfallCorpus
