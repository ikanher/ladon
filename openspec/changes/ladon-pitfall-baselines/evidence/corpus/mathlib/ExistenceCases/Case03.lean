import LeastElement
namespace ExistenceCases.Case03
open Audit.LeastElement
def subject : Prop := ∀ S : Set ℕ, S.Nonempty → sInf S ∈ S ∧ ∀ n ∈ S, sInf S ≤ n
#print axioms ExistenceCases.Case03.subject
end ExistenceCases.Case03
