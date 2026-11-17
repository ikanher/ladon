import Mathlib.Algebra.BigOperators.Group.Finset.Sigma
import Mf.DP.ClassicalEventDPSubsampling

namespace Mf
namespace DP

open scoped BigOperators

noncomputable section

/-!
Subset-replacement counting correspondence for classical subsampling.

This module isolates the finite combinatorial hole in the appendix proof of
`"Gaussian Differential Privacy" (Dong, Roth, Su, 2019)`.

Primary literature anchors:
- replacement step:
  `paper/theory/mu-dp/appendices/property.tex#L288`
- multiplicity explanation:
  `paper/theory/mu-dp/appendices/property.tex#L299`

The paper works with size-`m` subsets `I ⊆ [n]` and a distinguished differing
individual `1`. Here we use a distinguished index `special : Fin n`; the paper's
`1` is alias-only notation.

The theorem surface exposed here is intentionally combinatorial:
- explicit included/excluded size-`m` subset families
- the replacement operation that swaps `special` out for an outside index
- the exact `m`-fold multiplicity of excluded subsets under that replacement
- a counted summation identity and weighted corollary that feed the appendix
  refinement `B >= k * Abar + b`

The downstream theorem-facing consumer remains
`Mf.DP.ClassicalEventDPProfileSubsampling`.
-/

/-- All size-`m` subsets of the ambient `Fin n` universe. -/
def sizeMSubsets (n m : ℕ) : Finset (Finset (Fin n)) :=
  (Finset.univ : Finset (Fin n)).powersetCard m

/-- Size-`m` subsets containing the distinguished index. -/
def includedSubsets {n : ℕ} (special : Fin n) (m : ℕ) : Finset (Finset (Fin n)) :=
  (sizeMSubsets n m).filter (fun s => special ∈ s)

/-- Size-`m` subsets excluding the distinguished index. -/
def excludedSubsets {n : ℕ} (special : Fin n) (m : ℕ) : Finset (Finset (Fin n)) :=
  (sizeMSubsets n m).filter (fun s => special ∉ s)

/-- Admissible replacements for an included subset: outside indices other than `special`. -/
def replacementChoices {n : ℕ} (special : Fin n) (s : Finset (Fin n)) : Finset (Fin n) :=
  ((Finset.univ.erase special).filter fun x => x ∉ s)

/-- Replace the distinguished index by an outside index. -/
def replaceSpecialWith {n : ℕ} (special : Fin n) (s : Finset (Fin n)) (x : Fin n) :
    Finset (Fin n) :=
  insert x (s.erase special)

/-- Left indexing family for the replacement correspondence. -/
def includedReplacementPairs {n : ℕ} (special : Fin n) (m : ℕ) :
    Finset (Sigma fun _s : Finset (Fin n) => Fin n) :=
  (includedSubsets special m).sigma (fun s => replacementChoices special s)

/-- Right indexing family for the replacement correspondence. -/
def excludedMemberPairs {n : ℕ} (special : Fin n) (m : ℕ) :
    Finset (Sigma fun _s : Finset (Fin n) => Fin n) :=
  (excludedSubsets special m).sigma fun s => s

/-- Fiber of replacement pairs landing in a fixed excluded subset. -/
def replacementFiber {n : ℕ} (special : Fin n) (m : ℕ) (t : Finset (Fin n)) :
    Finset (Sigma fun _s : Finset (Fin n) => Fin n) :=
  (includedReplacementPairs special m).filter fun a =>
    replaceSpecialWith special a.1 a.2 = t

@[simp] theorem mem_includedSubsets_iff {n m : ℕ} {special : Fin n} {s : Finset (Fin n)} :
    s ∈ includedSubsets special m ↔ special ∈ s ∧ s.card = m := by
  constructor
  · intro hs
    rcases Finset.mem_filter.mp hs with ⟨hsPow, hsSpecial⟩
    exact ⟨hsSpecial, (Finset.mem_powersetCard_univ.mp hsPow)⟩
  · intro hs
    rcases hs with ⟨hsSpecial, hsCard⟩
    refine Finset.mem_filter.mpr ?_
    exact ⟨Finset.mem_powersetCard_univ.mpr hsCard, hsSpecial⟩

@[simp] theorem mem_excludedSubsets_iff {n m : ℕ} {special : Fin n} {s : Finset (Fin n)} :
    s ∈ excludedSubsets special m ↔ special ∉ s ∧ s.card = m := by
  constructor
  · intro hs
    rcases Finset.mem_filter.mp hs with ⟨hsPow, hsSpecial⟩
    exact ⟨hsSpecial, (Finset.mem_powersetCard_univ.mp hsPow)⟩
  · intro hs
    rcases hs with ⟨hsSpecial, hsCard⟩
    refine Finset.mem_filter.mpr ?_
    exact ⟨Finset.mem_powersetCard_univ.mpr hsCard, hsSpecial⟩

private theorem replaceSpecialWith_card {n m : ℕ} {special x : Fin n} {s : Finset (Fin n)}
    (hs : s.card = m) (hsSpecial : special ∈ s) (hx : x ∉ s) :
    (replaceSpecialWith special s x).card = m := by
  have hxErase : x ∉ s.erase special := by
    intro hxErase
    exact hx (Finset.mem_of_mem_erase hxErase)
  rw [replaceSpecialWith, Finset.card_insert_of_notMem hxErase]
  have hEraseAdd : (s.erase special).card + 1 = m := by
    simpa [hs] using Finset.card_erase_add_one hsSpecial
  omega

private theorem replaceSpecialWith_mem_excludedSubsets
    {n m : ℕ} {special x : Fin n} {s : Finset (Fin n)}
    (hs : s ∈ includedSubsets special m) (hx : x ∈ replacementChoices special s) :
    replaceSpecialWith special s x ∈ excludedSubsets special m := by
  have hsSpecial : special ∈ s := (mem_includedSubsets_iff.mp hs).1
  have hsCard : s.card = m := (mem_includedSubsets_iff.mp hs).2
  have hxNotMem : x ∉ s := (Finset.mem_filter.mp hx).2
  refine mem_excludedSubsets_iff.mpr ?_
  refine ⟨?_, replaceSpecialWith_card hsCard hsSpecial hxNotMem⟩
  have hxNe : x ≠ special := by
    intro hEq
    exact hxNotMem (hEq ▸ hsSpecial)
  intro hmem
  rw [replaceSpecialWith, Finset.mem_insert] at hmem
  rcases hmem with hEq | hErase
  · exact hxNe hEq.symm
  · exact Finset.notMem_erase special s hErase

private theorem replaceSpecialWith_eq_self_of_inverse {n : ℕ} {special x : Fin n}
    {s : Finset (Fin n)} (hsSpecial : special ∈ s) (hx : x ∉ s) :
    insert special ((replaceSpecialWith special s x).erase x) = s := by
  have hxErase : x ∉ s.erase special := by
    intro hxErase
    exact hx (Finset.mem_of_mem_erase hxErase)
  rw [replaceSpecialWith, Finset.erase_insert hxErase, Finset.insert_erase hsSpecial]

private theorem inverse_included_mem {n m : ℕ} {special : Fin n} {t : Finset (Fin n)} {y : Fin n}
    (ht : t ∈ excludedSubsets special m) (hy : y ∈ t) :
    insert special (t.erase y) ∈ includedSubsets special m := by
  have htSpecial : special ∉ t := (mem_excludedSubsets_iff.mp ht).1
  have htCard : t.card = m := (mem_excludedSubsets_iff.mp ht).2
  refine mem_includedSubsets_iff.mpr ?_
  refine ⟨by simp, ?_⟩
  have hspecialErase : special ∉ t.erase y := by
    intro h
    exact htSpecial (Finset.mem_of_mem_erase h)
  rw [Finset.card_insert_of_notMem hspecialErase]
  have hEraseAdd : (t.erase y).card + 1 = m := by
    simpa [htCard] using Finset.card_erase_add_one hy
  omega

private theorem inverse_choice_mem {n : ℕ} {special : Fin n} {t : Finset (Fin n)} {y : Fin n}
    (ht : special ∉ t) (hy : y ∈ t) :
    y ∈ replacementChoices special (insert special (t.erase y)) := by
  have hyNe : y ≠ special := by
    intro hEq
    exact ht (hEq ▸ hy)
  have hyNotMem : y ∉ insert special (t.erase y) := by
    simp [hyNe]
  exact Finset.mem_filter.mpr ⟨by simp [hyNe], hyNotMem⟩

private theorem replace_inverse_eq {n : ℕ} {special : Fin n} {t : Finset (Fin n)} {y : Fin n}
    (ht : special ∉ t) (hy : y ∈ t) :
    replaceSpecialWith special (insert special (t.erase y)) y = t := by
  have hspecialErase : special ∉ t.erase y := by
    intro h
    exact ht (Finset.mem_of_mem_erase h)
  rw [replaceSpecialWith, Finset.erase_insert hspecialErase, Finset.insert_erase hy]

@[simp] theorem replacementChoices_card {n m : ℕ} {special : Fin n} {s : Finset (Fin n)}
    (hs : s ∈ includedSubsets special m) :
    (replacementChoices special s).card = n - m := by
  have hsSpecial : special ∈ s := (mem_includedSubsets_iff.mp hs).1
  have hsCard : s.card = m := (mem_includedSubsets_iff.mp hs).2
  have hchoices : replacementChoices special s = (Finset.univ.filter fun x : Fin n => x ∉ s) := by
    ext x
    constructor
    · intro hx
      exact Finset.mem_filter.mpr ⟨by simp, (Finset.mem_filter.mp hx).2⟩
    · intro hx
      have hxNot : x ∉ s := (Finset.mem_filter.mp hx).2
      have hxNe : x ≠ special := by
        intro h
        exact hxNot (h ▸ hsSpecial)
      exact Finset.mem_filter.mpr ⟨by simp [hxNe], hxNot⟩
  have hinside : (Finset.univ.filter fun x : Fin n => x ∈ s) = s := by
    ext x
    simp
  have hsplit := Finset.card_filter_add_card_filter_not (s := (Finset.univ : Finset (Fin n)))
      (p := fun x : Fin n => x ∈ s)
  have hsplit' : s.card + (replacementChoices special s).card = n := by
    rw [hchoices, ← hinside]
    simpa using hsplit
  omega

private def toExcludedPair {n : ℕ} {special : Fin n} :
    Sigma (fun _s : Finset (Fin n) => Fin n) → Sigma (fun _s : Finset (Fin n) => Fin n)
  | ⟨s, x⟩ => ⟨replaceSpecialWith special s x, x⟩

private def fromExcludedPair {n : ℕ} {special : Fin n} :
    Sigma (fun _s : Finset (Fin n) => Fin n) → Sigma (fun _s : Finset (Fin n) => Fin n)
  | ⟨t, y⟩ => ⟨insert special (t.erase y), y⟩

private theorem toExcludedPair_mem {n m : ℕ} {special : Fin n}
    (a : Sigma fun _s : Finset (Fin n) => Fin n)
    (ha : a ∈ includedReplacementPairs special m) :
    toExcludedPair (special := special) a ∈ excludedMemberPairs special m := by
  rcases Finset.mem_sigma.mp ha with ⟨hs, hx⟩
  refine Finset.mem_sigma.mpr ?_
  refine ⟨replaceSpecialWith_mem_excludedSubsets hs hx, ?_⟩
  simp [toExcludedPair, replaceSpecialWith]

private theorem fromExcludedPair_mem {n m : ℕ} {special : Fin n}
    (b : Sigma fun _s : Finset (Fin n) => Fin n)
    (hb : b ∈ excludedMemberPairs special m) :
    fromExcludedPair (special := special) b ∈ includedReplacementPairs special m := by
  rcases Finset.mem_sigma.mp hb with ⟨ht, hy⟩
  refine Finset.mem_sigma.mpr ?_
  refine ⟨inverse_included_mem ht hy, ?_⟩
  exact inverse_choice_mem (mem_excludedSubsets_iff.mp ht).1 hy

private theorem to_from_left_inv {n m : ℕ} {special : Fin n}
    (a : Sigma fun _s : Finset (Fin n) => Fin n)
    (ha : a ∈ includedReplacementPairs special m) :
    fromExcludedPair (special := special) (toExcludedPair (special := special) a) = a := by
  rcases Finset.mem_sigma.mp ha with ⟨hs, hx⟩
  rcases a with ⟨s, x⟩
  apply Sigma.ext
  · dsimp [toExcludedPair, fromExcludedPair]
    have hsSpecial : special ∈ s := (mem_includedSubsets_iff.mp hs).1
    have hxNotMem : x ∉ s := (Finset.mem_filter.mp hx).2
    simpa using replaceSpecialWith_eq_self_of_inverse hsSpecial hxNotMem
  · rfl

private theorem to_from_right_inv {n m : ℕ} {special : Fin n}
    (b : Sigma fun _s : Finset (Fin n) => Fin n)
    (hb : b ∈ excludedMemberPairs special m) :
    toExcludedPair (special := special) (fromExcludedPair (special := special) b) = b := by
  rcases Finset.mem_sigma.mp hb with ⟨ht, hy⟩
  rcases b with ⟨t, y⟩
  apply Sigma.ext
  · dsimp [toExcludedPair, fromExcludedPair]
    simpa using replace_inverse_eq (mem_excludedSubsets_iff.mp ht).1 hy
  · rfl

/-- Each excluded size-`m` subset appears exactly `m` times under replacement. -/
theorem replacementFiber_card_eq_m {n m : ℕ} {special : Fin n}
    {t : Finset (Fin n)} (ht : t ∈ excludedSubsets special m) :
    (replacementFiber special m t).card = m := by
  classical
  let rightFiber : Finset (Sigma fun _s : Finset (Fin n) => Fin n) :=
    (excludedMemberPairs special m).filter fun b => b.1 = t
  have hRightCard : rightFiber.card = m := by
    have hCardEq : t.card = rightFiber.card := by
      exact Finset.card_nbij'
        (i := fun y : Fin n => ⟨t, y⟩)
        (j := fun b : Sigma fun _s : Finset (Fin n) => Fin n => b.2)
        (s := t)
        (t := rightFiber)
        (by
          intro y hy
          refine Finset.mem_filter.mpr ?_
          exact ⟨Finset.mem_sigma.mpr ⟨ht, hy⟩, rfl⟩)
        (by
          intro b hb
          rcases b with ⟨u, y⟩
          rcases Finset.mem_filter.mp hb with ⟨hbMem, hEqFirst⟩
          rcases Finset.mem_sigma.mp hbMem with ⟨_hu, hy⟩
          cases hEqFirst
          simpa using hy)
        (by
          intro y hy
          rfl)
        (by
          intro b hb
          rcases b with ⟨u, y⟩
          rcases Finset.mem_filter.mp hb with ⟨_hbMem, hEqFirst⟩
          cases hEqFirst
          rfl)
    rw [← hCardEq]
    simp [mem_excludedSubsets_iff.mp ht]
  have hEquivCard : (replacementFiber special m t).card = rightFiber.card := by
    exact Finset.card_nbij'
      (i := fun a : Sigma fun _s : Finset (Fin n) => Fin n => toExcludedPair (special := special) a)
      (j := fun b : Sigma fun _s : Finset (Fin n) => Fin n =>
        fromExcludedPair (special := special) ⟨t, b.2⟩)
      (s := replacementFiber special m t)
      (t := rightFiber)
      (by
        intro a ha
        refine Finset.mem_filter.mpr ?_
        exact ⟨toExcludedPair_mem (special := special) a ((Finset.mem_filter.mp ha).1),
          (Finset.mem_filter.mp ha).2⟩)
        (by
          intro b hb
          refine Finset.mem_filter.mpr ?_
          refine ⟨fromExcludedPair_mem (special := special) ⟨t, b.2⟩ ?_, ?_⟩
          · rcases Finset.mem_filter.mp hb with ⟨hbMem, hEqFirst⟩
            rcases b with ⟨u, y⟩
            rcases Finset.mem_sigma.mp hbMem with ⟨hu, hy⟩
            cases hEqFirst
            exact Finset.mem_sigma.mpr ⟨hu, hy⟩
          · rcases Finset.mem_filter.mp hb with ⟨hbMem, hEqFirst⟩
            rcases b with ⟨u, y⟩
            rcases Finset.mem_sigma.mp hbMem with ⟨_hu, hy⟩
            cases hEqFirst
            change replaceSpecialWith special (insert special (u.erase y)) y = u
            exact replace_inverse_eq (special := special)
              ((mem_excludedSubsets_iff.mp ht).1) hy)
      (by
        intro a ha
        have haMem : a ∈ includedReplacementPairs special m := (Finset.mem_filter.mp ha).1
        have haEq : (toExcludedPair (special := special) a).1 = t := (Finset.mem_filter.mp ha).2
        calc
          fromExcludedPair (special := special) ⟨t, (toExcludedPair (special := special) a).2⟩
            = fromExcludedPair (special := special) (toExcludedPair (special := special) a) := by
                rcases a with ⟨s, x⟩
                dsimp [toExcludedPair, fromExcludedPair] at haEq ⊢
                simpa using
                  congrArg (fun u : Finset (Fin n) => insert special (u.erase x))
                    haEq.symm
          _ = a := to_from_left_inv (special := special) a haMem)
      (by
        intro b hb
        rcases b with ⟨u, y⟩
        rcases Finset.mem_filter.mp hb with ⟨hbMem, hEqFirst⟩
        rcases Finset.mem_sigma.mp hbMem with ⟨hu, hy⟩
        have hRight := to_from_right_inv (special := special) ⟨u, y⟩
          (Finset.mem_sigma.mpr ⟨hu, hy⟩)
        cases hEqFirst
        simpa using hRight)
  rw [hEquivCard, hRightCard]

/--
The replacement correspondence is a bijection between:
- included subsets together with a legal replacement choice, and
- excluded subsets together with a chosen member.
-/
theorem replacementPairSum_eq_excludedMemberPairSum {n m : ℕ} {special : Fin n}
    {α : Type*} [AddCommMonoid α] (f : Finset (Fin n) → α) :
    ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s,
      f (replaceSpecialWith special s x)
      =
    ∑ t ∈ excludedSubsets special m, ∑ _y ∈ t, f t := by
  classical
  rw [Finset.sum_sigma', Finset.sum_sigma']
  refine Finset.sum_bij' (fun a _ => toExcludedPair (special := special) a)
    (fun b _ => fromExcludedPair (special := special) b)
    (fun a ha => toExcludedPair_mem a ha)
    (fun b hb => fromExcludedPair_mem b hb)
    (fun a ha => to_from_left_inv a ha)
    (fun b hb => to_from_right_inv b hb)
    ?_
  intro a ha
  rcases a with ⟨s, x⟩
  rfl

/--
Raw counted identity: the double replacement sum equals `m` times the sum over
excluded size-`m` subsets.
-/
theorem replacementPairSum_eq_m_nsmul_sum_excluded {n m : ℕ} {special : Fin n}
    {α : Type*} [AddCommMonoid α] (f : Finset (Fin n) → α) :
    ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s,
      f (replaceSpecialWith special s x)
      =
    m • ∑ t ∈ excludedSubsets special m, f t := by
  classical
  calc
    ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s,
        f (replaceSpecialWith special s x)
      = ∑ t ∈ excludedSubsets special m, ∑ y ∈ t, f t :=
          replacementPairSum_eq_excludedMemberPairSum (special := special) (m := m) f
    _ = ∑ t ∈ excludedSubsets special m, t.card • f t := by
          refine Finset.sum_congr rfl ?_
          intro t ht
          simp
    _ = ∑ t ∈ excludedSubsets special m, m • f t := by
          refine Finset.sum_congr rfl ?_
          intro t ht
          simp [mem_excludedSubsets_iff.mp ht]
    _ = m • ∑ t ∈ excludedSubsets special m, f t := by
          rw [Finset.sum_nsmul]

/--
Weighted real-valued corollary in the appendix inequality shape.
-/
theorem countedRefinement_of_replacementPointwiseBound {n m : ℕ} {special : Fin n}
    (beta alpha : Finset (Fin n) → ℝ) (k b : ℝ)
    (hpointwise :
      ∀ s ∈ includedSubsets special m,
        ∀ x ∈ replacementChoices special s,
          k * alpha (replaceSpecialWith special s x) + b ≤ beta s) :
    (m : ℝ) * ∑ t ∈ excludedSubsets special m, (k * alpha t + b)
      ≤
    ((n - m : ℕ) : ℝ) * ∑ s ∈ includedSubsets special m, beta s := by
  classical
  have hleft :
      ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s,
        beta s
        =
      ((n - m : ℕ) : ℝ) * ∑ s ∈ includedSubsets special m, beta s := by
    calc
      ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s, beta s
        = ∑ s ∈ includedSubsets special m, ((replacementChoices special s).card : ℝ) * beta s := by
            refine Finset.sum_congr rfl ?_
            intro s hs
            simp [nsmul_eq_mul]
      _ = ∑ s ∈ includedSubsets special m, ((n - m : ℕ) : ℝ) * beta s := by
            refine Finset.sum_congr rfl ?_
            intro s hs
            rw [replacementChoices_card hs]
      _ = ((n - m : ℕ) : ℝ) * ∑ s ∈ includedSubsets special m, beta s := by
            rw [Finset.mul_sum]
  have hpointwiseSum :
      ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s,
        (k * alpha (replaceSpecialWith special s x) + b)
      ≤
      ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s,
        beta s := by
    refine Finset.sum_le_sum ?_
    intro s hs
    refine Finset.sum_le_sum ?_
    intro x hx
    exact hpointwise s hs x hx
  have hright :
      ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s,
        (k * alpha (replaceSpecialWith special s x) + b)
        =
      (m : ℝ) * ∑ t ∈ excludedSubsets special m, (k * alpha t + b) := by
    simpa using
      replacementPairSum_eq_m_nsmul_sum_excluded (special := special) (m := m)
        (f := fun t => (k * alpha t + b))
  calc
    (m : ℝ) * ∑ t ∈ excludedSubsets special m, (k * alpha t + b)
      =
    ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s,
      (k * alpha (replaceSpecialWith special s x) + b) := by
        symm
        exact hright
    _ ≤ ∑ s ∈ includedSubsets special m, ∑ x ∈ replacementChoices special s, beta s :=
        hpointwiseSum
    _ = ((n - m : ℕ) : ℝ) * ∑ s ∈ includedSubsets special m, beta s := hleft

end
end DP
end Mf
