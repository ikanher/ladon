import Mf.DP.VectorClipping

namespace Mf
namespace DP
namespace Training

/-- A user-level dataset is a finite set of user records. -/
abbrev UserDataset (Record : Type*) [DecidableEq Record] := Finset Record

/-- Symmetric user add/remove adjacency used by the mathematical training mechanisms. -/
def UserAddRemoveAdj
    {Record : Type*} [DecidableEq Record] :
    UserDataset Record → UserDataset Record → Prop :=
  FinsetAddRemoveAdjacent

theorem userAddRemoveAdj_symm
    {Record : Type*} [DecidableEq Record]
    {left right : UserDataset Record}
    (h : UserAddRemoveAdj left right) :
    UserAddRemoveAdj right left :=
  finsetAddRemoveAdjacent_symm h

/-- User replace-one adjacency through a shared dataset.  Distinct absent
records are removed and added, so this relation excludes the diagonal. -/
def UserReplaceOneAdj
    {Record : Type*} [DecidableEq Record]
    (left right : UserDataset Record) : Prop :=
  ∃ common removed added,
    removed ∉ common ∧
    added ∉ common ∧
    removed ≠ added ∧
    left = insert removed common ∧
    right = insert added common

theorem userReplaceOneAdj_symm
    {Record : Type*} [DecidableEq Record]
    {left right : UserDataset Record}
    (h : UserReplaceOneAdj left right) :
    UserReplaceOneAdj right left := by
  rcases h with ⟨common, removed, added, hremoved, hadded, hne, hleft, hright⟩
  exact ⟨common, added, removed, hadded, hremoved, hne.symm, hright, hleft⟩

theorem userReplaceOneAdj_card_eq
    {Record : Type*} [DecidableEq Record]
    {left right : UserDataset Record}
    (h : UserReplaceOneAdj left right) :
    left.card = right.card := by
  rcases h with ⟨common, removed, added, hremoved, hadded, _, rfl, rfl⟩
  simp [hremoved, hadded]

theorem userReplaceOneAdj_ne
    {Record : Type*} [DecidableEq Record]
    {left right : UserDataset Record}
    (h : UserReplaceOneAdj left right) :
    left ≠ right := by
  rcases h with ⟨common, removed, added, hremoved, hadded, hne, rfl, rfl⟩
  intro heq
  have hmem : removed ∈ insert added common := by
    rw [← heq]
    simp
  rcases Finset.mem_insert.mp hmem with heq' | hmem'
  · exact hne heq'
  · exact hremoved hmem'

/-- Every replacement is an ordered removal followed by an insertion through
the common dataset supplied by the replacement witness. -/
theorem userReplaceOneAdj_addRemove_hops
    {Record : Type*} [DecidableEq Record]
    {left right : UserDataset Record}
    (h : UserReplaceOneAdj left right) :
    ∃ middle,
      UserAddRemoveAdj left middle ∧
      UserAddRemoveAdj middle right := by
  rcases h with ⟨common, removed, added, hremoved, hadded, _, hleft, hright⟩
  refine ⟨common, ?_, ?_⟩
  · exact Or.inr ⟨removed, hremoved, hleft⟩
  · exact Or.inl ⟨added, hadded, hright⟩

end Training
end DP
end Mf
