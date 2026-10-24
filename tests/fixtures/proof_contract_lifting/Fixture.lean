import Init.Data.Rat.Lemmas

namespace LiftFixture

def Predicate (n : Nat) : Prop := n < 2 → n = 0
def Claim : Prop := ∀ n : Nat, Predicate n

def StrictPredicate (n : Nat) : Prop := n = 0 → n < 2 → n = 0
def StrictClaim : Prop := ∀ n : Nat, StrictPredicate n

end LiftFixture
