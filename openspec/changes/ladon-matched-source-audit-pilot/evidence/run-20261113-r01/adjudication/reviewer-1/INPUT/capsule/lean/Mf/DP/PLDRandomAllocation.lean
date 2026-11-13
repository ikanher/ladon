import Mathlib

namespace Mf
namespace DP

open scoped BigOperators

noncomputable section

/-!
Random-allocation PLD semantics.

Literature anchors:
- Look first: `paper/bnb-accounting-wo-bnb/PLD_components/body.tex` `thm:PLDrandAlloc`
- Look first: `paper/bnb-accounting-wo-bnb/PLD_components/appendix.tex` proof of `thm:PLDrandAlloc`

Design note:
- This file uses a measure-pushforward formulation for PLD laws.
- The public object is a forward/reverse pair of laws on `ℝ`, rather than a
  mechanism-specific random variable type.
- This matches the PRV/PLD literature better than embedding the theorem inside
  a particular mechanism definition, and keeps BNB as a consumer of the layer.
-/

/--
Forward/reverse privacy-loss laws carried together as a reusable semantic unit.

`forward` is intended to model the law of `L_{P||Q}` and `reverse` the law of
`L_{Q||P}` for some underlying pair `(P,Q)`, but the structure itself is
agnostic about where those laws came from.

Look first:
- `paper/theory/numerical-composition/PRV.tex` `thm:PRV_LLRV`
- `paper/bnb-accounting-wo-bnb/PLD_components/body.tex` `thm:PLDrandAlloc`
-/
structure PLDPair where
  forward : MeasureTheory.Measure ℝ
  reverse : MeasureTheory.Measure ℝ

/-- PLD dual swaps the forward and reverse laws. -/
def PLDPair.dual (L : PLDPair) : PLDPair :=
  ⟨L.reverse, L.forward⟩

lemma fin_eq_zero_iff_val_eq_zero {n : ℕ} (i : Fin (n + 1)) :
    i = 0 ↔ i.1 = 0 := by
  constructor
  · intro h
    simp [h]
  · intro h
    exact Fin.ext h

lemma ite_fin_eq_zero_to_val_eq_zero
    {α : Sort _} {n : ℕ} (i : Fin (n + 1)) (a b : α) :
    (if i = 0 then a else b) = (if i.1 = 0 then a else b) := by
  by_cases h : i = 0
  · have h' : i.1 = 0 := (fin_eq_zero_iff_val_eq_zero i).1 h
    simp [h]
  · have h' : i.1 ≠ 0 := by
      intro h0
      exact h ((fin_eq_zero_iff_val_eq_zero i).2 h0)
    simp [h, h']

lemma ite_val_eq_zero_to_fin_eq_zero
    {α : Sort _} {n : ℕ} (i : Fin (n + 1)) (a b : α) :
    (if i.1 = 0 then a else b) = (if i = 0 then a else b) := by
  symm
  exact ite_fin_eq_zero_to_val_eq_zero i a b

@[simp] theorem PLDPair.dual_forward (L : PLDPair) :
    (L.dual).forward = L.reverse := rfl

@[simp] theorem PLDPair.dual_reverse (L : PLDPair) :
    (L.dual).reverse = L.forward := rfl

@[simp] theorem PLDPair.dual_dual (L : PLDPair) :
    L.dual.dual = L := by
  cases L
  rfl

/--
Neutral PLD pair for zero-fold independent composition.

Both directions are the Dirac law at `0`, matching the fact that a zero-step
privacy loss is identically zero.
-/
def PLDPair.id : PLDPair :=
  ⟨MeasureTheory.Measure.dirac 0, MeasureTheory.Measure.dirac 0⟩

/--
Independent composition of PLD pairs by addition of privacy-loss realizations.

This is the PLD-level counterpart of composing two independent mechanisms: the
privacy losses add, so the forward and reverse laws are both pushed forward
through addition on `ℝ × ℝ`.

Current honest boundary:
- the semantic forward/reverse law composition is defined here,
- but the repository does not yet expose a generic theorem on the profile side
  of `PLDPair.comp`,
- so downstream accountant packets still need a lower binary profile-
  composition theorem before recursive consumers such as `PLDPair.compFamily`
  can be closed honestly.
-/
def PLDPair.comp (L₁ L₂ : PLDPair) : PLDPair :=
  ⟨MeasureTheory.Measure.map (fun x : ℝ × ℝ => x.1 + x.2) (L₁.forward.prod L₂.forward),
    MeasureTheory.Measure.map (fun x : ℝ × ℝ => x.1 + x.2) (L₁.reverse.prod L₂.reverse)⟩

/--
`k`-fold independent composition of a PLD pair.

The recursion is right-associated on purpose; for the theorem surface in this
file only the existence of a canonical iterated composition matters.
-/
def PLDPair.compPow (L : PLDPair) : ℕ → PLDPair
  | 0 => PLDPair.id
  | n + 1 => (PLDPair.compPow L n).comp L

@[simp] theorem PLDPair.id_forward :
    PLDPair.id.forward = MeasureTheory.Measure.dirac 0 := rfl

@[simp] theorem PLDPair.id_reverse :
    PLDPair.id.reverse = MeasureTheory.Measure.dirac 0 := rfl

@[simp] theorem PLDPair.comp_forward (L₁ L₂ : PLDPair) :
    (L₁.comp L₂).forward
      = MeasureTheory.Measure.map (fun x : ℝ × ℝ => x.1 + x.2) (L₁.forward.prod L₂.forward) := rfl

@[simp] theorem PLDPair.comp_reverse (L₁ L₂ : PLDPair) :
    (L₁.comp L₂).reverse
      = MeasureTheory.Measure.map (fun x : ℝ × ℝ => x.1 + x.2) (L₁.reverse.prod L₂.reverse) := rfl

@[simp] theorem PLDPair.compPow_zero (L : PLDPair) :
    L.compPow 0 = PLDPair.id := rfl

@[simp] theorem PLDPair.compPow_succ (L : PLDPair) (n : ℕ) :
    L.compPow (n + 1) = (L.compPow n).comp L := rfl

@[simp] theorem PLDPair.compPow_one (L : PLDPair) :
    L.compPow 1 = PLDPair.id.comp L := rfl

private def finConsMap (n : ℕ) : (Fin n → ℝ) × ℝ → Fin (n + 1) → ℝ :=
  fun z => @Fin.cons n (fun _ => ℝ) z.2 z.1

private theorem map_finCons_prod_pi_eq_pi
    (μ : MeasureTheory.Measure ℝ) [MeasureTheory.SigmaFinite μ] (n : ℕ) :
    MeasureTheory.Measure.map (finConsMap n)
      ((MeasureTheory.Measure.pi (fun _ : Fin n => μ)).prod μ)
      =
    MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => μ) := by
  have hfun :
      finConsMap n
        =
      ((MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm ∘ Prod.swap) := by
    funext z
    simp [finConsMap, MeasurableEquiv.piFinSuccAbove_symm_apply, Fin.insertNthEquiv]
  calc
    MeasureTheory.Measure.map (finConsMap n)
        ((MeasureTheory.Measure.pi (fun _ : Fin n => μ)).prod μ)
      =
        MeasureTheory.Measure.map
          (((MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm) ∘ Prod.swap)
          ((MeasureTheory.Measure.pi (fun _ : Fin n => μ)).prod μ) := by
            simp [hfun]
    _ =
        MeasureTheory.Measure.map
          ((MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm)
          (MeasureTheory.Measure.map Prod.swap
            ((MeasureTheory.Measure.pi (fun _ : Fin n => μ)).prod μ)) := by
              rw [← MeasureTheory.Measure.map_map
                ((MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm).measurable
                measurable_swap]
    _ =
        MeasureTheory.Measure.map
          ((MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm)
          (μ.prod (MeasureTheory.Measure.pi (fun _ : Fin n => μ))) := by
            rw [MeasureTheory.Measure.prod_swap]
    _ = MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => μ) := by
      simpa using
        ((MeasureTheory.measurePreserving_piFinSuccAbove
          (μ := fun _ : Fin (n + 1) => μ) (i := (0 : Fin (n + 1)))).symm.map_eq)

private theorem measurable_finCons (n : ℕ) :
    Measurable (finConsMap n) := by
  have hfun :
      finConsMap n
        =
      ((MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm ∘ Prod.swap) := by
    funext z
    simp [finConsMap, MeasurableEquiv.piFinSuccAbove_symm_apply, Fin.insertNthEquiv]
  rw [hfun]
  exact ((MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm).measurable.comp
    measurable_swap

private def headTailMap (n : ℕ) : ℝ × (Fin n → ℝ) → Fin (n + 1) → ℝ :=
  fun z => @Fin.cons n (fun _ => ℝ) z.1 z.2

private theorem map_headTail_prod_pi_eq_pi
    (μ ν : MeasureTheory.Measure ℝ)
    [MeasureTheory.SigmaFinite μ] [MeasureTheory.SigmaFinite ν] (n : ℕ) :
    MeasureTheory.Measure.map (headTailMap n)
      (μ.prod (MeasureTheory.Measure.pi (fun _ : Fin n => ν)))
      =
    MeasureTheory.Measure.pi (fun i : Fin (n + 1) => if i = 0 then μ else ν) := by
  have hfun :
      headTailMap n
        =
      (MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm := by
    funext z
    simp [headTailMap, MeasurableEquiv.piFinSuccAbove_symm_apply, Fin.insertNthEquiv]
  haveI : ∀ i : Fin (n + 1),
      MeasureTheory.SigmaFinite ((fun i : Fin (n + 1) => if i = 0 then μ else ν) i) := by
    intro i
    by_cases hi : i = 0
    · simpa [hi] using (inferInstance : MeasureTheory.SigmaFinite μ)
    · simpa [hi] using (inferInstance : MeasureTheory.SigmaFinite ν)
  rw [hfun]
  simpa using
    ((MeasureTheory.measurePreserving_piFinSuccAbove
      (μ := fun i : Fin (n + 1) => if i = 0 then μ else ν)
      (i := (0 : Fin (n + 1)))).symm.map_eq)

private theorem measurable_headTail (n : ℕ) :
    Measurable (headTailMap n) := by
  have hfun :
      headTailMap n
        =
      (MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm := by
    funext z
    simp [headTailMap, MeasurableEquiv.piFinSuccAbove_symm_apply, Fin.insertNthEquiv]
  rw [hfun]
  exact ((MeasurableEquiv.piFinSuccAbove (fun _ : Fin (n + 1) => ℝ) 0).symm).measurable

@[simp] theorem PLDPair.compPow_forward_eq_pi_map_sum (L : PLDPair)
    [MeasureTheory.SigmaFinite L.forward] (k : ℕ) :
    (L.compPow k).forward
      =
    MeasureTheory.Measure.map (fun x : Fin k → ℝ => ∑ i, x i)
      (MeasureTheory.Measure.pi (fun _ : Fin k => L.forward)) := by
  induction k with
  | zero =>
      calc
        (L.compPow 0).forward = MeasureTheory.Measure.dirac 0 := by simp [PLDPair.id]
        _ =
            MeasureTheory.Measure.map (fun _ : Fin 0 → ℝ => (0 : ℝ))
              (MeasureTheory.Measure.pi (fun _ : Fin 0 => L.forward)) := by
                rw [MeasureTheory.Measure.map_const]
                simp
        _ =
            MeasureTheory.Measure.map (fun x : Fin 0 → ℝ => ∑ i, x i)
              (MeasureTheory.Measure.pi (fun _ : Fin 0 => L.forward)) := by
                simp
  | succ n ih =>
      let sumN : (Fin n → ℝ) → ℝ := fun x => ∑ i, x i
      let sumSucc : (Fin (n + 1) → ℝ) → ℝ := fun x => ∑ i, x i
      have hsumN : Measurable sumN := by
        dsimp [sumN]
        fun_prop
      have hsumSucc : Measurable sumSucc := by
        dsimp [sumSucc]
        fun_prop
      have hcompose :
          ((fun w : ℝ × ℝ => w.1 + w.2) ∘ Prod.map sumN (fun x : ℝ => x))
            =
          sumSucc ∘ finConsMap n := by
        funext z
        simp [sumN, sumSucc, finConsMap, Fin.sum_univ_succ, add_comm]
      have hprod :
          ((MeasureTheory.Measure.map sumN
              (MeasureTheory.Measure.pi (fun _ : Fin n => L.forward))).prod L.forward)
            =
          MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
                ((MeasureTheory.Measure.pi (fun _ : Fin n => L.forward)).prod L.forward) := by
              calc
                ((MeasureTheory.Measure.map sumN
                    (MeasureTheory.Measure.pi (fun _ : Fin n => L.forward))).prod L.forward)
                  =
                    ((MeasureTheory.Measure.map sumN
                      (MeasureTheory.Measure.pi (fun _ : Fin n => L.forward))).prod
                      (MeasureTheory.Measure.map (fun x : ℝ => x) L.forward)) := by simp
                _ =
                    MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
                      ((MeasureTheory.Measure.pi (fun _ : Fin n => L.forward)).prod L.forward) := by
                        simpa [Function.id_def] using
                          (MeasureTheory.Measure.map_prod_map
                            (MeasureTheory.Measure.pi (fun _ : Fin n => L.forward)) L.forward
                            hsumN measurable_id)
      calc
        (L.compPow (n + 1)).forward
          =
            MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)
              ((MeasureTheory.Measure.map sumN
                  (MeasureTheory.Measure.pi (fun _ : Fin n => L.forward))).prod L.forward) := by
                    rw [PLDPair.compPow_succ, PLDPair.comp_forward, ih]
        _ =
            MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)
              (MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
                ((MeasureTheory.Measure.pi (fun _ : Fin n => L.forward)).prod L.forward)) := by
                  exact congrArg (MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)) hprod
        _ =
            MeasureTheory.Measure.map
              (((fun w : ℝ × ℝ => w.1 + w.2) ∘ Prod.map sumN (fun x : ℝ => x)))
              ((MeasureTheory.Measure.pi (fun _ : Fin n => L.forward)).prod L.forward) := by
                rw [← MeasureTheory.Measure.map_map (by fun_prop) (by fun_prop)]
        _ =
            MeasureTheory.Measure.map
              (sumSucc ∘ finConsMap n)
              ((MeasureTheory.Measure.pi (fun _ : Fin n => L.forward)).prod L.forward) := by
                rw [hcompose]
        _ =
            MeasureTheory.Measure.map sumSucc
              (MeasureTheory.Measure.map (finConsMap n)
                ((MeasureTheory.Measure.pi (fun _ : Fin n => L.forward)).prod L.forward)) := by
                  rw [← MeasureTheory.Measure.map_map hsumSucc (measurable_finCons n)]
        _ =
            MeasureTheory.Measure.map sumSucc
              (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => L.forward)) := by
                rw [map_finCons_prod_pi_eq_pi (μ := L.forward)]

@[simp] theorem PLDPair.compPow_reverse_eq_pi_map_sum (L : PLDPair)
    [MeasureTheory.SigmaFinite L.reverse] (k : ℕ) :
    (L.compPow k).reverse
      =
    MeasureTheory.Measure.map (fun x : Fin k → ℝ => ∑ i, x i)
      (MeasureTheory.Measure.pi (fun _ : Fin k => L.reverse)) := by
  induction k with
  | zero =>
      calc
        (L.compPow 0).reverse = MeasureTheory.Measure.dirac 0 := by simp [PLDPair.id]
        _ =
            MeasureTheory.Measure.map (fun _ : Fin 0 → ℝ => (0 : ℝ))
              (MeasureTheory.Measure.pi (fun _ : Fin 0 => L.reverse)) := by
                rw [MeasureTheory.Measure.map_const]
                simp
        _ =
            MeasureTheory.Measure.map (fun x : Fin 0 → ℝ => ∑ i, x i)
              (MeasureTheory.Measure.pi (fun _ : Fin 0 => L.reverse)) := by
                simp
  | succ n ih =>
      let sumN : (Fin n → ℝ) → ℝ := fun x => ∑ i, x i
      let sumSucc : (Fin (n + 1) → ℝ) → ℝ := fun x => ∑ i, x i
      have hsumN : Measurable sumN := by
        dsimp [sumN]
        fun_prop
      have hsumSucc : Measurable sumSucc := by
        dsimp [sumSucc]
        fun_prop
      have hcompose :
          ((fun w : ℝ × ℝ => w.1 + w.2) ∘ Prod.map sumN (fun x : ℝ => x))
            =
          sumSucc ∘ finConsMap n := by
        funext z
        simp [sumN, sumSucc, finConsMap, Fin.sum_univ_succ, add_comm]
      have hprod :
          ((MeasureTheory.Measure.map sumN
              (MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse))).prod L.reverse)
            =
          MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
            ((MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse)).prod L.reverse) := by
              calc
                ((MeasureTheory.Measure.map sumN
                    (MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse))).prod L.reverse)
                  =
                    ((MeasureTheory.Measure.map sumN
                      (MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse))).prod
                      (MeasureTheory.Measure.map (fun x : ℝ => x) L.reverse)) := by simp
                _ =
                    MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
                      ((MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse)).prod L.reverse) := by
                        simpa [Function.id_def] using
                          (MeasureTheory.Measure.map_prod_map
                            (MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse)) L.reverse
                            hsumN measurable_id)
      calc
        (L.compPow (n + 1)).reverse
          =
            MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)
              ((MeasureTheory.Measure.map sumN
                  (MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse))).prod L.reverse) := by
                    rw [PLDPair.compPow_succ, PLDPair.comp_reverse, ih]
        _ =
            MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)
              (MeasureTheory.Measure.map (Prod.map sumN (fun x : ℝ => x))
                ((MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse)).prod L.reverse)) := by
                  exact congrArg (MeasureTheory.Measure.map (fun w : ℝ × ℝ => w.1 + w.2)) hprod
        _ =
            MeasureTheory.Measure.map
              (((fun w : ℝ × ℝ => w.1 + w.2) ∘ Prod.map sumN (fun x : ℝ => x)))
              ((MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse)).prod L.reverse) := by
                rw [← MeasureTheory.Measure.map_map (by fun_prop) (by fun_prop)]
        _ =
            MeasureTheory.Measure.map
              (sumSucc ∘ finConsMap n)
              ((MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse)).prod L.reverse) := by
                rw [hcompose]
        _ =
            MeasureTheory.Measure.map sumSucc
              (MeasureTheory.Measure.map (finConsMap n)
                ((MeasureTheory.Measure.pi (fun _ : Fin n => L.reverse)).prod L.reverse)) := by
                  rw [← MeasureTheory.Measure.map_map hsumSucc (measurable_finCons n)]
        _ =
            MeasureTheory.Measure.map sumSucc
              (MeasureTheory.Measure.pi (fun _ : Fin (n + 1) => L.reverse)) := by
                rw [map_finCons_prod_pi_eq_pi (μ := L.reverse)]

@[simp] theorem PLDPair.compPow_eq_pi_map_sum (L : PLDPair)
    [MeasureTheory.SigmaFinite L.forward] [MeasureTheory.SigmaFinite L.reverse] (k : ℕ) :
    L.compPow k
      =
    { forward := MeasureTheory.Measure.map (fun x : Fin k → ℝ => ∑ i, x i)
          (MeasureTheory.Measure.pi (fun _ : Fin k => L.forward))
      , reverse := MeasureTheory.Measure.map (fun x : Fin k → ℝ => ∑ i, x i)
          (MeasureTheory.Measure.pi (fun _ : Fin k => L.reverse)) } := by
  cases h : L.compPow k with
  | mk forward reverse =>
      have hf :
          forward =
            MeasureTheory.Measure.map (fun x : Fin k → ℝ => ∑ i, x i)
              (MeasureTheory.Measure.pi (fun _ : Fin k => L.forward)) := by
                simpa [h] using
                  (PLDPair.compPow_forward_eq_pi_map_sum (L := L) (k := k))
      have hr :
          reverse =
            MeasureTheory.Measure.map (fun x : Fin k → ℝ => ∑ i, x i)
              (MeasureTheory.Measure.pi (fun _ : Fin k => L.reverse)) := by
                simpa [h] using
                  (PLDPair.compPow_reverse_eq_pi_map_sum (L := L) (k := k))
      cases hL : L.compPow k with
      | mk =>
          simp [hf, hr]

/--
Coordinate law used by the remove-direction random-allocation transform:
coordinate `0` is drawn from the forward law and all later coordinates are
drawn from the reverse law.
-/
def removeCoordLaw (L : PLDPair) {t : ℕ} (i : Fin t) : MeasureTheory.Measure ℝ :=
  if i.1 = 0 then L.forward else L.reverse

/--
Pointwise remove-direction transform from `thm:PLDrandAlloc`.

This is the law-level counterpart of
`log ((1 / t) (exp L + Σ exp (-dual(L_i))))`.
-/
def removeTransformValue {t : ℕ} (x : Fin (t + 1) → ℝ) : ℝ :=
  Real.log (((∑ i : Fin (t + 1), if i.1 = 0 then Real.exp (x i) else Real.exp (-x i))
    / (t + 1 : ℝ)))

/--
Pointwise add-direction transform from `thm:PLDrandAlloc`.

This is the law-level counterpart of
`- log ((1 / t) Σ exp (-L_i))`.
-/
def addTransformValue {t : ℕ} (x : Fin (t + 1) → ℝ) : ℝ :=
  -Real.log (((∑ i : Fin (t + 1), Real.exp (-x i)) / (t + 1 : ℝ)))

/--
One remove-direction recursion step on already-aggregated coordinates.

This is the pointwise law-level update corresponding to adding one forward
coordinate to an already-aggregated add-direction tail block of size `t + 1`.
-/
def removeTransformStepValue (t : ℕ) (z : ℝ × ℝ) : ℝ :=
  Real.log (Real.exp z.1 + Real.exp (-z.2 + Real.log (t + 1 : ℝ))) -
    Real.log (t + 2 : ℝ)

/--
One add-direction recursion step on already-aggregated coordinates.

This is the pointwise law-level update corresponding to adding one forward
coordinate to an already-aggregated add-direction block of size `t + 1`.
-/
def addTransformStepValue (t : ℕ) (z : ℝ × ℝ) : ℝ :=
  -Real.log (Real.exp (-z.1) + Real.exp (-z.2 + Real.log (t + 1 : ℝ))) +
    Real.log (t + 2 : ℝ)

lemma measurable_removeTransformValue {t : ℕ} :
    Measurable (@removeTransformValue t) := by
  classical
  unfold removeTransformValue
  refine Measurable.log ?_
  refine Measurable.div_const ?_ _
  let g : Fin (t + 1) → (Fin (t + 1) → ℝ) → ℝ :=
    fun i x => if i.1 = 0 then Real.exp (x i) else Real.exp (-x i)
  have hg : ∀ i, Measurable (g i) := by
    intro i
    dsimp [g]
    by_cases h : i.1 = 0
    · simp only [h, ↓reduceIte]
      fun_prop
    · simp only [h, ↓reduceIte]
      fun_prop
  have hsum : Measurable (fun x => ∑ i : Fin (t + 1), g i x) := by
    classical
    induction (Finset.univ : Finset (Fin (t + 1))) using Finset.induction_on with
    | empty =>
        simp
    | insert a s ha ih =>
        convert (hg a).add ih using 1
        funext x
        simp [Finset.sum_insert ha, Pi.add_apply]
  simpa [g] using hsum

lemma measurable_addTransformValue {t : ℕ} :
    Measurable (@addTransformValue t) := by
  unfold addTransformValue
  refine Measurable.neg ?_
  refine Measurable.log ?_
  refine Measurable.div_const ?_ _
  let g : Fin (t + 1) → (Fin (t + 1) → ℝ) → ℝ := fun i x => Real.exp (-x i)
  have hg : ∀ i, Measurable (g i) := by
    intro i
    dsimp [g]
    fun_prop
  have hsum : Measurable (fun x => ∑ i : Fin (t + 1), g i x) := by
    classical
    induction (Finset.univ : Finset (Fin (t + 1))) using Finset.induction_on with
    | empty =>
        simp
    | insert a s ha ih =>
        convert (hg a).add ih using 1
        funext x
        simp [Finset.sum_insert ha, Pi.add_apply]
  simpa [g] using hsum

lemma measurable_removeTransformStepValue (t : ℕ) :
    Measurable (removeTransformStepValue t) := by
  unfold removeTransformStepValue
  fun_prop

lemma measurable_addTransformStepValue (t : ℕ) :
    Measurable (addTransformStepValue t) := by
  unfold addTransformStepValue
  fun_prop

private theorem exp_neg_addTransformValue_add_log
    {t : ℕ} (x : Fin (t + 1) → ℝ) :
    Real.exp (-addTransformValue x + Real.log (t + 1 : ℝ)) =
      ∑ i : Fin (t + 1), Real.exp (-x i) := by
  have ht_pos : 0 < (t + 1 : ℝ) := by positivity
  calc
    Real.exp (-addTransformValue x + Real.log (t + 1 : ℝ))
        = Real.exp
            (Real.log (((∑ i : Fin (t + 1), Real.exp (-x i)) / (t + 1 : ℝ))) +
              Real.log (t + 1 : ℝ)) := by
              simp [addTransformValue]
    _ = ((∑ i : Fin (t + 1), Real.exp (-x i)) / (t + 1 : ℝ)) * (t + 1 : ℝ) := by
          rw [Real.exp_add, Real.exp_log (by positivity), Real.exp_log ht_pos]
    _ = ∑ i : Fin (t + 1), Real.exp (-x i) := by
          field_simp [ht_pos.ne']

private theorem removeTransformValue_headTail
    {t : ℕ} (x₀ : ℝ) (xs : Fin (t + 1) → ℝ) :
    removeTransformValue (headTailMap (t + 1) (x₀, xs)) =
      removeTransformStepValue t (x₀, addTransformValue xs) := by
  have htail := exp_neg_addTransformValue_add_log xs
  have hsum :
      (∑ i : Fin (t + 2),
          (if i.1 = 0 then Real.exp (headTailMap (t + 1) (x₀, xs) i)
            else Real.exp (-headTailMap (t + 1) (x₀, xs) i)))
        = Real.exp x₀ + ∑ i : Fin (t + 1), Real.exp (-xs i) := by
    simp [headTailMap, Fin.sum_univ_succ]
  have hsum_pos : 0 < Real.exp x₀ + ∑ i : Fin (t + 1), Real.exp (-xs i) := by
    positivity
  have hden : ((↑(t + 1) : ℝ) + 1) = (t + 2 : ℝ) := by
    norm_num [Nat.cast_add]
    ring
  rw [removeTransformStepValue, removeTransformValue, hsum, hden,
    Real.log_div hsum_pos.ne' (by positivity : (t + 2 : ℝ) ≠ 0), htail]

private theorem addTransformValue_headTail
    {t : ℕ} (x₀ : ℝ) (xs : Fin (t + 1) → ℝ) :
    addTransformValue (headTailMap (t + 1) (x₀, xs)) =
      addTransformStepValue t (x₀, addTransformValue xs) := by
  have htail := exp_neg_addTransformValue_add_log xs
  have hsum :
      ∑ i : Fin (t + 2), Real.exp (-headTailMap (t + 1) (x₀, xs) i)
        = Real.exp (-x₀) + ∑ i : Fin (t + 1), Real.exp (-xs i) := by
    simp [headTailMap, Fin.sum_univ_succ]
  have hsum_pos : 0 < Real.exp (-x₀) + ∑ i : Fin (t + 1), Real.exp (-xs i) := by
    positivity
  have hden : ((↑(t + 1) : ℝ) + 1) = (t + 2 : ℝ) := by
    norm_num [Nat.cast_add]
    ring
  rw [addTransformStepValue, addTransformValue, hsum, hden,
    Real.log_div hsum_pos.ne' (by positivity : (t + 2 : ℝ) ≠ 0), htail]
  ring

/--
Law-level remove-direction random-allocation transform on PLD pairs.

Coordinate `0` is a copy of the forward PLD law and the remaining coordinates
are copies of the reverse PLD law, matching the appendix proof's symmetry
reduction.
-/
def removeTransform (L : PLDPair) (t : ℕ) : MeasureTheory.Measure ℝ :=
  MeasureTheory.Measure.map
    (@removeTransformValue t)
    (MeasureTheory.Measure.pi (fun i : Fin (t + 1) => removeCoordLaw L i))

/--
Law-level add-direction random-allocation transform on PLD pairs.

All coordinates are copies of the forward PLD law, matching the
`L_{Q^t || \bar P_t}` direction in `thm:PLDrandAlloc`.
-/
def addTransform (L : PLDPair) (t : ℕ) : MeasureTheory.Measure ℝ :=
  MeasureTheory.Measure.map
    (@addTransformValue t)
    (MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => L.forward))

/--
The theorem-facing random-allocation semantic package.

This is a thin wrapper around the remove/add transform laws so downstream
modules can refer to one object instead of two unrelated measures.
-/
def randomAllocationTransforms (L : PLDPair) (t : ℕ) : PLDPair :=
  ⟨removeTransform L t, addTransform L.dual t⟩

@[simp] theorem randomAllocationTransforms_forward (L : PLDPair) (t : ℕ) :
    (randomAllocationTransforms L t).forward = removeTransform L t := rfl

@[simp] theorem randomAllocationTransforms_reverse (L : PLDPair) (t : ℕ) :
    (randomAllocationTransforms L t).reverse = addTransform L.dual t := rfl

/--
Exact add-side exp-space lift used by the paper recurrence.

This is the additive add transform moved into the exp-convolution space by the
final `-x + log(t+1)` re-log inverse.
-/
def addTransformLift (L : PLDPair) (t : ℕ) : MeasureTheory.Measure ℝ :=
  MeasureTheory.Measure.map (fun x : ℝ => -x + Real.log (t + 1 : ℝ)) (addTransform L t)

theorem removeTransform_succ_eq_step
    (L : PLDPair) [MeasureTheory.SigmaFinite L.forward]
    [MeasureTheory.SigmaFinite L.reverse] (t : ℕ) :
    removeTransform L (t + 1) =
      MeasureTheory.Measure.map (removeTransformStepValue t)
        (L.forward.prod (addTransform L.dual t)) := by
  unfold removeTransform addTransform
  rw [show MeasureTheory.Measure.pi (fun i : Fin (t + 2) => removeCoordLaw L i) =
      MeasureTheory.Measure.map (headTailMap (t + 1))
        (L.forward.prod (MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => L.reverse))) by
      simpa [removeCoordLaw] using
        (map_headTail_prod_pi_eq_pi (μ := L.forward) (ν := L.reverse) (n := t + 1)).symm]
  rw [MeasureTheory.Measure.map_map
    (measurable_removeTransformValue (t := t + 1)) (measurable_headTail (t + 1))]
  rw [show (@removeTransformValue (t + 1)) ∘ headTailMap (t + 1) =
      removeTransformStepValue t ∘ Prod.map id (@addTransformValue t) by
      funext z
      cases z with
      | mk x₀ xs =>
          simpa using removeTransformValue_headTail (t := t) x₀ xs]
  rw [← MeasureTheory.Measure.map_map
    (measurable_removeTransformStepValue t)
    (measurable_id.prodMap (measurable_addTransformValue (t := t)))]
  rw [← MeasureTheory.Measure.map_prod_map
    (μa := L.forward)
    (μc := MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => L.reverse))
    (f := id) (g := @addTransformValue t)
    (hf := by simpa using measurable_id)
    (hg := measurable_addTransformValue (t := t))]
  simp

theorem addTransform_succ_eq_step
    (L : PLDPair) [MeasureTheory.SigmaFinite L.forward] (t : ℕ) :
    addTransform L (t + 1) =
      MeasureTheory.Measure.map (addTransformStepValue t)
        (L.forward.prod (addTransform L t)) := by
  unfold addTransform
  rw [show MeasureTheory.Measure.pi (fun _ : Fin (t + 2) => L.forward) =
      MeasureTheory.Measure.map (headTailMap (t + 1))
        (L.forward.prod (MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => L.forward))) by
      simpa using
        (map_headTail_prod_pi_eq_pi (μ := L.forward) (ν := L.forward) (n := t + 1)).symm]
  rw [MeasureTheory.Measure.map_map
    (measurable_addTransformValue (t := t + 1)) (measurable_headTail (t + 1))]
  rw [show (@addTransformValue (t + 1)) ∘ headTailMap (t + 1) =
      addTransformStepValue t ∘ Prod.map id (@addTransformValue t) by
      funext z
      cases z with
      | mk x₀ xs =>
          simpa using addTransformValue_headTail (t := t) x₀ xs]
  rw [← MeasureTheory.Measure.map_map
    (measurable_addTransformStepValue t)
    (measurable_id.prodMap (measurable_addTransformValue (t := t)))]
  rw [← MeasureTheory.Measure.map_prod_map
    (μa := L.forward)
    (μc := MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => L.forward))
    (f := id) (g := @addTransformValue t)
    (hf := by simpa using measurable_id)
    (hg := measurable_addTransformValue (t := t))]
  simp

theorem addTransformLift_succ_eq_rawLogExp
    (L : PLDPair) [MeasureTheory.SigmaFinite L.forward] (t : ℕ) :
    addTransformLift L (t + 1) =
      MeasureTheory.Measure.map
        (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2))
        ((MeasureTheory.Measure.map (fun x : ℝ => -x) L.forward).prod (addTransformLift L t)) := by
  haveI : MeasureTheory.SFinite (MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => L.forward)) := by
    infer_instance
  haveI : MeasureTheory.SFinite (addTransform L t) := by
    change MeasureTheory.SFinite
      (MeasureTheory.Measure.map (@addTransformValue t)
        (MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => L.forward)))
    infer_instance
  unfold addTransformLift
  rw [addTransform_succ_eq_step]
  rw [MeasureTheory.Measure.map_map (by fun_prop) (measurable_addTransformStepValue t)]
  have hcomp :
      (fun x : ℝ => -x + Real.log ((t + 1 : ℕ) + 1 : ℝ)) ∘ addTransformStepValue t =
        (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2)) ∘
          Prod.map (fun x : ℝ => -x) (fun x : ℝ => -x + Real.log (t + 1 : ℝ)) := by
    funext z
    rcases z with ⟨x, y⟩
    have harg : (↑t : ℝ) + 1 + 1 = (↑t : ℝ) + 2 := by ring
    have hlog : Real.log ((↑t : ℝ) + 1 + 1) = Real.log ((↑t : ℝ) + 2) := congrArg Real.log harg
    simp [addTransformStepValue, Nat.cast_add, hlog]
  have hraw :
      MeasureTheory.Measure.map
        (((fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2)) ∘
          Prod.map (fun x : ℝ => -x) (fun x : ℝ => -x + Real.log (t + 1 : ℝ))))
        (L.forward.prod (addTransform L t)) =
      MeasureTheory.Measure.map
        (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2))
        ((MeasureTheory.Measure.map (fun x : ℝ => -x) L.forward).prod (addTransformLift L t)) := by
    rw [← MeasureTheory.Measure.map_map
      (by
        fun_prop)
      (by
        fun_prop)]
    rw [← MeasureTheory.Measure.map_prod_map
      (μa := L.forward)
      (μc := addTransform L t)
      (f := fun x : ℝ => -x)
      (g := fun x : ℝ => -x + Real.log (t + 1 : ℝ))
      (hf := by fun_prop)
      (hg := by fun_prop)]
    simp [addTransformLift]
  calc
    MeasureTheory.Measure.map
        (((fun x : ℝ => -x + Real.log ((t + 1 : ℕ) + 1 : ℝ)) ∘ addTransformStepValue t))
        (L.forward.prod (addTransform L t))
      =
        MeasureTheory.Measure.map
          (((fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2)) ∘
            Prod.map (fun x : ℝ => -x) (fun x : ℝ => -x + Real.log (t + 1 : ℝ))))
          (L.forward.prod (addTransform L t)) := by
            exact congrArg
              (fun f => MeasureTheory.Measure.map f (L.forward.prod (addTransform L t)))
              hcomp
    _ =
        MeasureTheory.Measure.map
          (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2))
          ((MeasureTheory.Measure.map (fun x : ℝ => -x) L.forward).prod
            (addTransformLift L t)) := hraw

theorem removeTransform_succ_eq_rawLogExp
    (L : PLDPair) [MeasureTheory.SigmaFinite L.forward]
    [MeasureTheory.SigmaFinite L.reverse] (t : ℕ) :
    removeTransform L (t + 1) =
      MeasureTheory.Measure.map (fun x : ℝ => x - Real.log (t + 2 : ℝ))
        (MeasureTheory.Measure.map
          (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2))
          (L.forward.prod (addTransformLift L.dual t))) := by
  haveI : MeasureTheory.SFinite (MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => L.reverse)) := by
    infer_instance
  haveI : MeasureTheory.SFinite (addTransform L.dual t) := by
    change MeasureTheory.SFinite
      (MeasureTheory.Measure.map (@addTransformValue t)
        (MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => L.reverse)))
    infer_instance
  unfold addTransformLift
  rw [removeTransform_succ_eq_step]
  have hcomp :
      removeTransformStepValue t =
        (fun x : ℝ => x - Real.log (t + 2 : ℝ)) ∘
          (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2)) ∘
            Prod.map id (fun x : ℝ => -x + Real.log (t + 1 : ℝ)) := by
    funext z
    rcases z with ⟨x, y⟩
    simp [removeTransformStepValue]
  have hraw :
      MeasureTheory.Measure.map
        ((fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2)) ∘
          Prod.map id (fun x : ℝ => -x + Real.log (t + 1 : ℝ)))
        (L.forward.prod (addTransform L.dual t)) =
      MeasureTheory.Measure.map
        (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2))
        (L.forward.prod
          (MeasureTheory.Measure.map (fun x : ℝ => -x + Real.log (t + 1 : ℝ))
            (addTransform L.dual t))) := by
    rw [← MeasureTheory.Measure.map_map
      (by
        fun_prop)
      (by
        fun_prop)]
    rw [← MeasureTheory.Measure.map_prod_map
      (μa := L.forward)
      (μc := addTransform L.dual t)
      (f := id)
      (g := fun x : ℝ => -x + Real.log (t + 1 : ℝ))
      (hf := by simpa using measurable_id)
      (hg := by fun_prop)]
    simp
  calc
    MeasureTheory.Measure.map (removeTransformStepValue t)
        (L.forward.prod (addTransform L.dual t))
      =
        MeasureTheory.Measure.map
          (((fun x : ℝ => x - Real.log (t + 2 : ℝ)) ∘
            (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2)) ∘
            Prod.map id (fun x : ℝ => -x + Real.log (t + 1 : ℝ))))
          (L.forward.prod (addTransform L.dual t)) := by
            exact congrArg
              (fun f => MeasureTheory.Measure.map f (L.forward.prod (addTransform L.dual t)))
              hcomp
    _ =
        MeasureTheory.Measure.map (fun x : ℝ => x - Real.log (t + 2 : ℝ))
          (MeasureTheory.Measure.map
            ((fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2)) ∘
              Prod.map id (fun x : ℝ => -x + Real.log (t + 1 : ℝ)))
            (L.forward.prod (addTransform L.dual t))) := by
              rw [← MeasureTheory.Measure.map_map
                (by
                  fun_prop)
                (by
                  fun_prop)]
    _ =
        MeasureTheory.Measure.map (fun x : ℝ => x - Real.log (t + 2 : ℝ))
          (MeasureTheory.Measure.map
            (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2))
            (L.forward.prod
              (MeasureTheory.Measure.map (fun x : ℝ => -x + Real.log (t + 1 : ℝ))
                (addTransform L.dual t)))) := by
                  exact congrArg
                    (MeasureTheory.Measure.map (fun x : ℝ => x - Real.log (t + 2 : ℝ)))
                    hraw
    _ =
        MeasureTheory.Measure.map (fun x : ℝ => x - Real.log (t + 2 : ℝ))
          (MeasureTheory.Measure.map
            (fun w : ℝ × ℝ => Real.log (Real.exp w.1 + Real.exp w.2))
            (L.forward.prod (addTransformLift L.dual t))) := by
              simp [addTransformLift]

/--
Block width used in the fixed-size-sampling reduction.

This packages the `⌊ t / k ⌋` quantity from
`paper/bnb-accounting-wo-bnb/PLD_components/body.tex` lines 100-103,
Lemma `lem:multAlloc`, using Lean's natural-number division.

The intended paper-side regime is `1 ≤ k` and `k ≤ t`; this definition only
packages the arithmetic right-hand-side width `⌊ t / k ⌋ = t / k`.
-/
def kOutOfTReductionWidth (t k : ℕ) : ℕ :=
  t / k

/--
Corrected one-allocation width for the public `k`-out-of-`t` theorem surface
under the current Lean `Fin (t + 1)` horizon convention.

If the actual horizon cardinality is `t + 1`, the paper-facing block width is
`floor((t + 1) / k)`. The corresponding Lean `randomAllocationTransforms`
parameter is therefore one less.
-/
def correctedKOutOfTReductionWidth (t k : ℕ) : ℕ :=
  Nat.pred ((t + 1) / k)

/--
Single-allocation PLD pair appearing on the right-hand side of the
`k`-out-of-`t` reduction.

This reuses the existing `1`-out-of-`t` random-allocation layer under the same
parameter convention as `randomAllocationTransforms`.
-/
def kOutOfTSingleAllocationPair (L : PLDPair) (t k : ℕ) : PLDPair :=
  randomAllocationTransforms L (kOutOfTReductionWidth t k)

/--
Analytical upper PLD pair for the `k`-out-of-`t` scheme.

The literature states the reduction as a privacy-profile inequality into the
`k`-fold composition of the `1`-out-of-`⌊ t / k ⌋` scheme. This definition
packages that right-hand side as a reusable PLD-pair object.
-/
def kOutOfTReductionUpperPair (L : PLDPair) (t k : ℕ) : PLDPair :=
  (kOutOfTSingleAllocationPair L t k).compPow k

/--
Corrected analytical upper PLD pair for the public `k`-out-of-`t` theorem
surface.
-/
def correctedKOutOfTReductionUpperPair (L : PLDPair) (t k : ℕ) : PLDPair :=
  (randomAllocationTransforms L (correctedKOutOfTReductionWidth t k)).compPow k

@[simp] theorem kOutOfTSingleAllocationPair_eq_randomAllocationTransforms
    (L : PLDPair) (t k : ℕ) :
    kOutOfTSingleAllocationPair L t k
      = randomAllocationTransforms L (kOutOfTReductionWidth t k) := rfl

@[simp] theorem kOutOfTReductionUpperPair_eq_compPow
    (L : PLDPair) (t k : ℕ) :
    kOutOfTReductionUpperPair L t k
      = (randomAllocationTransforms L (kOutOfTReductionWidth t k)).compPow k := rfl

@[simp] theorem correctedKOutOfTReductionUpperPair_eq_compPow
    (L : PLDPair) (t k : ℕ) :
    correctedKOutOfTReductionUpperPair L t k
      = (randomAllocationTransforms L (correctedKOutOfTReductionWidth t k)).compPow k := rfl

@[simp] theorem kOutOfTReductionWidth_one (t : ℕ) :
    kOutOfTReductionWidth t 1 = t := by
  simp [kOutOfTReductionWidth]

@[simp] theorem kOutOfTReductionWidth_shifted_divisible
    (k m : ℕ) (hk1 : 1 ≤ k) (hm1 : 1 ≤ m) :
    kOutOfTReductionWidth (k * m - 1) k = m - 1 := by
  have hk0 : 0 < k := hk1
  have hlt : k - 1 < k := Nat.sub_lt hk0 (by decide)
  unfold kOutOfTReductionWidth
  have hmul : k * m = k * (m - 1) + k := by
    calc
      k * m = k * ((m - 1) + 1) := by rw [Nat.sub_add_cancel hm1]
      _ = k * (m - 1) + k := by rw [Nat.mul_add, Nat.mul_one]
  have hdecomp : k * m - 1 = k * (m - 1) + (k - 1) := by
    calc
      k * m - 1 = (k * (m - 1) + k) - 1 := by rw [hmul]
      _ = (k * (m - 1) + ((k - 1) + 1)) - 1 := by
        rw [Nat.sub_add_cancel hk1]
      _ = k * (m - 1) + (k - 1) := by
        simp
  rw [hdecomp]
  rw [Nat.add_comm]
  have hdvd : k ∣ k * (m - 1) := dvd_mul_right k (m - 1)
  rw [Nat.add_div_of_dvd_left hdvd]
  rw [Nat.div_eq_of_lt hlt]
  simp [Nat.mul_div_right _ hk0]

@[simp] theorem correctedKOutOfTReductionWidth_shifted_divisible
    (k m : ℕ) (hk1 : 1 ≤ k) (hm1 : 1 ≤ m) :
    correctedKOutOfTReductionWidth (k * m - 1) k = m - 1 := by
  have hkm : 0 < k * m := Nat.mul_pos hk1 hm1
  unfold correctedKOutOfTReductionWidth
  rw [Nat.sub_add_cancel hkm]
  rw [Nat.mul_div_right _ (show 0 < k from hk1)]
  simp [Nat.pred_eq_sub_one]

theorem correctedKOutOfTReductionWidth_shiftedFloorRepair
    {t k : ℕ} (hk1 : 1 ≤ k) :
    correctedKOutOfTReductionWidth (k * (t / k + 1) - 1) k = kOutOfTReductionWidth t k := by
  simpa [kOutOfTReductionWidth] using
    (correctedKOutOfTReductionWidth_shifted_divisible
      k (t / k + 1) hk1 (Nat.succ_le_succ (Nat.zero_le _)))

theorem correctedKOutOfTReductionWidth_floorRepair
    {t k : ℕ} (hk1 : 1 ≤ k) (hkt1 : k ≤ t + 1) :
    correctedKOutOfTReductionWidth (k * ((t + 1) / k) - 1) k
      = correctedKOutOfTReductionWidth t k := by
  let m := (t + 1) / k
  have hm1 : 1 ≤ m := Nat.succ_le_of_lt (Nat.div_pos hkt1 hk1)
  rw [correctedKOutOfTReductionWidth_shifted_divisible k m hk1 hm1]
  dsimp [m]
  unfold correctedKOutOfTReductionWidth
  simp [Nat.pred_eq_sub_one]

@[simp] theorem kOutOfTReductionUpperPair_one (L : PLDPair) (t : ℕ) :
    kOutOfTReductionUpperPair L t 1 = (PLDPair.id.comp (randomAllocationTransforms L t)) := by
  simp [kOutOfTReductionUpperPair, kOutOfTSingleAllocationPair]

@[simp] theorem correctedKOutOfTReductionUpperPair_eq_kOutOfTReductionUpperPair_shifted_divisible
    (L : PLDPair) (k m : ℕ) (hk1 : 1 ≤ k) (hm1 : 1 ≤ m) :
    correctedKOutOfTReductionUpperPair L (k * m - 1) k
      = kOutOfTReductionUpperPair L (k * m - 1) k := by
  unfold correctedKOutOfTReductionUpperPair kOutOfTReductionUpperPair kOutOfTSingleAllocationPair
  simp [correctedKOutOfTReductionWidth_shifted_divisible,
    kOutOfTReductionWidth_shifted_divisible, hk1, hm1]

/--
Exact remove-direction random-allocation PLD identity in law form.

This is the measure-pushforward analogue of the paper statement
`L_{\bar P_t || Q^t} = ψ_t^rem(L_{P||Q})`.

Look first:
- `paper/bnb-accounting-wo-bnb/PLD_components/body.tex` `thm:PLDrandAlloc`
- `paper/bnb-accounting-wo-bnb/PLD_components/appendix.tex` lines 162-178
-/
theorem pld_randomAllocation_remove_eq_transform
    (L : PLDPair) (t : ℕ) :
    (randomAllocationTransforms L t).forward = removeTransform L t := by
  rfl

/--
Exact add-direction random-allocation PLD identity in law form.

This is the measure-pushforward analogue of the paper statement
`L_{Q^t || \bar P_t} = ψ_t^add(L_{Q||P})`.

Look first:
- `paper/bnb-accounting-wo-bnb/PLD_components/body.tex` `thm:PLDrandAlloc`
- `paper/bnb-accounting-wo-bnb/PLD_components/appendix.tex` lines 180-184
-/
theorem pld_randomAllocation_add_eq_transform
    (L : PLDPair) (t : ℕ) :
    (randomAllocationTransforms L t).reverse = addTransform L.dual t := by
  rfl

/--
Right-tail probability used by the privacy-loss-to-`δ(ε)` formula.

Look first:
- `paper/theory/amplification/arxiv.tex` `thm:profileL`
- `paper/theory/dominating-pair/preliminary.tex` `lem:equivalent_defs`
-/
def pldTailRight (μ : MeasureTheory.Measure ℝ) (ε : ℝ) : ℝ :=
  μ.real (Set.Ioi ε)

/--
Left-tail probability used by the reverse-direction term in the
privacy-loss-to-`δ(ε)` formula.
-/
def pldTailLeft (μ : MeasureTheory.Measure ℝ) (ε : ℝ) : ℝ :=
  μ.real (Set.Iio ε)

@[measurability]
theorem measurable_pldTailRight (μ : MeasureTheory.Measure ℝ) :
    Measurable (pldTailRight μ) := by
  unfold pldTailRight
  refine Measurable.ennreal_toReal ?_
  exact Antitone.measurable fun x y hxy =>
    MeasureTheory.measure_mono (Set.Ioi_subset_Ioi hxy)

/--
First-order stochastic domination on PLD laws, expressed via right tails / CCDFs.

This is the realization-level order used by the random-allocation paper before
passing to hockey-stick or privacy-profile consequences.

Look first:
- `paper/bnb-accounting-wo-bnb/PLD_components/body.tex` lines 179-188
- `paper/bnb-accounting-wo-bnb/PLD_components/body.tex` lines 226-243
-/
def StochDominates (upper lower : MeasureTheory.Measure ℝ) : Prop :=
  ∀ x : ℝ, pldTailRight lower x ≤ pldTailRight upper x

/--
`(α, β)`-approximate stochastic domination on PLD laws.

This is the paper's main tightness notion for transformed PLD realizations:
the lower law's right tail at `x` is bounded by the upper law's right tail at
`x - α` plus additive slack `β`.

Look first:
- `paper/bnb-accounting-wo-bnb/PLD_components/body.tex` Definition `def:stochDom`
- `paper/bnb-accounting-wo-bnb/PLD_components/body.tex` lines 179-195
-/
def ApproxStochDominates (α β : ℝ) (upper lower : MeasureTheory.Measure ℝ) : Prop :=
  ∀ x : ℝ, pldTailRight lower x ≤ pldTailRight upper (x - α) + β

@[simp] theorem ApproxStochDominates.zero_zero_iff
    (upper lower : MeasureTheory.Measure ℝ) :
    ApproxStochDominates 0 0 upper lower ↔ StochDominates upper lower := by
  constructor
  · intro h x
    specialize h x
    simpa [ApproxStochDominates, StochDominates] using h
  · intro h x
    specialize h x
    simpa [ApproxStochDominates, StochDominates] using h

/--
Realization-level domination on PLD pairs.

This keeps the forward and reverse directions separate, matching the paper's
add/remove accounting setup. The older `PLDPair.Dominates` definition below is
kept as a privacy-profile-facing consequence layer.
-/
def PLDPair.RealizationDominates (U L : PLDPair) : Prop :=
  StochDominates U.forward L.forward ∧ StochDominates U.reverse L.reverse

/--
Approximate realization-level domination on PLD pairs, keeping the forward and
reverse directions separate.
-/
def PLDPair.ApproxRealizationDominates (α β : ℝ) (U L : PLDPair) : Prop :=
  ApproxStochDominates α β U.forward L.forward ∧
    ApproxStochDominates α β U.reverse L.reverse

@[simp] theorem StochDominates.refl (μ : MeasureTheory.Measure ℝ) :
    StochDominates μ μ := by
  intro x
  exact le_rfl

@[simp] theorem ApproxStochDominates.refl (μ : MeasureTheory.Measure ℝ) :
    ApproxStochDominates 0 0 μ μ := by
  rw [ApproxStochDominates.zero_zero_iff]
  exact StochDominates.refl μ

/-- Approximate stochastic domination composes by adding shifts and tail slack. -/
theorem ApproxStochDominates.trans
    {α₁ α₂ β₁ β₂ : ℝ}
    {upper middle lower : MeasureTheory.Measure ℝ}
    (hupper : ApproxStochDominates α₁ β₁ upper middle)
    (hlower : ApproxStochDominates α₂ β₂ middle lower) :
    ApproxStochDominates (α₁ + α₂) (β₁ + β₂) upper lower := by
  intro x
  have h1 := hlower x
  have h2 := hupper (x - α₂)
  have hshift : x - α₂ - α₁ = x - (α₁ + α₂) := by ring
  rw [hshift] at h2
  linarith

theorem StochDominates.toApprox {upper lower : MeasureTheory.Measure ℝ}
    (h : StochDominates upper lower) :
    ApproxStochDominates 0 0 upper lower := by
  rw [ApproxStochDominates.zero_zero_iff]
  exact h

@[simp] theorem StochDominates.toApprox_iff {upper lower : MeasureTheory.Measure ℝ} :
    ApproxStochDominates 0 0 upper lower ↔ StochDominates upper lower :=
  ApproxStochDominates.zero_zero_iff upper lower

@[simp] theorem PLDPair.realizationDominates_refl (L : PLDPair) :
    L.RealizationDominates L := by
  exact ⟨StochDominates.refl _, StochDominates.refl _⟩

@[simp] theorem PLDPair.approxRealizationDominates_refl (L : PLDPair) :
    L.ApproxRealizationDominates 0 0 L := by
  exact ⟨ApproxStochDominates.refl _, ApproxStochDominates.refl _⟩

theorem PLDPair.realizationDominates_toApprox {U L : PLDPair}
    (h : U.RealizationDominates L) :
    U.ApproxRealizationDominates 0 0 L := by
  exact ⟨h.1.toApprox, h.2.toApprox⟩

@[simp] theorem PLDPair.realizationDominates_iff_approx_zero_zero {U L : PLDPair} :
    U.ApproxRealizationDominates 0 0 L ↔ U.RealizationDominates L := by
  constructor
  · intro h
    exact ⟨(ApproxStochDominates.zero_zero_iff _ _).1 h.1,
      (ApproxStochDominates.zero_zero_iff _ _).1 h.2⟩
  · intro h
    exact PLDPair.realizationDominates_toApprox h

/--
Privacy-profile style evaluation of a PLD pair at `ε`.

This packages the tail formula
`Pr[L_{P||Q} > ε] - exp ε * Pr[L_{Q||P} < -ε]`
from the literature into a reusable Lean definition on `PLDPair`.
-/
def hockeyStickLaw (κ : ℝ) (μ : MeasureTheory.Measure ℝ) : ℝ :=
  ∫ x, max (1 - κ * Real.exp (-x)) 0 ∂μ

/--
Single-law hockey-stick functional at privacy parameter `ε`.

This is the law-level object corresponding to the paper's
`E[(1 - exp(ε - X))_+]`.
-/
def expHockeyStickLaw (ε : ℝ) (μ : MeasureTheory.Measure ℝ) : ℝ :=
  hockeyStickLaw (Real.exp ε) μ

theorem measurable_hockeyStickIntegrand (κ : ℝ) :
    Measurable (fun x : ℝ => max (1 - κ * Real.exp (-x)) 0) := by
  fun_prop

theorem hockeyStickIntegrand_nonneg (κ x : ℝ) :
    0 ≤ max (1 - κ * Real.exp (-x)) 0 := by
  exact le_max_right _ _

theorem hockeyStickIntegrand_le_one {κ x : ℝ} (hκ : 0 ≤ κ) :
    max (1 - κ * Real.exp (-x)) 0 ≤ 1 := by
  have hexp_nonneg : 0 ≤ Real.exp (-x) := le_of_lt (Real.exp_pos _)
  have hmul_nonneg : 0 ≤ κ * Real.exp (-x) := mul_nonneg hκ hexp_nonneg
  have hleft : 1 - κ * Real.exp (-x) ≤ 1 := by linarith
  exact max_le hleft (by norm_num)

theorem integrable_hockeyStickIntegrand
    (κ : ℝ) (μ : MeasureTheory.Measure ℝ) [MeasureTheory.IsFiniteMeasure μ]
    (hκ : 0 ≤ κ) :
    MeasureTheory.Integrable (fun x : ℝ => max (1 - κ * Real.exp (-x)) 0) μ := by
  refine MeasureTheory.Integrable.mono' (MeasureTheory.integrable_const 1) ?_ ?_
  · exact (measurable_hockeyStickIntegrand κ).aestronglyMeasurable
  · refine Filter.Eventually.of_forall ?_
    intro x
    have hnonneg := hockeyStickIntegrand_nonneg κ x
    have hle := hockeyStickIntegrand_le_one (x := x) hκ
    rw [Real.norm_eq_abs, abs_of_nonneg hnonneg]
    exact hle

theorem hockeyStickLaw_antitoneOn
    (μ : MeasureTheory.Measure ℝ) [MeasureTheory.IsProbabilityMeasure μ] :
    AntitoneOn (fun κ : ℝ => hockeyStickLaw κ μ) (Set.Ici (0 : ℝ)) := by
  intro κ hκ κ' hκ' hle
  have hpoint :
      ∀ x : ℝ, max (1 - κ' * Real.exp (-x)) 0 ≤ max (1 - κ * Real.exp (-x)) 0 := by
    intro x
    have hexp_nonneg : 0 ≤ Real.exp (-x) := le_of_lt (Real.exp_pos _)
    have hmul : κ * Real.exp (-x) ≤ κ' * Real.exp (-x) :=
      mul_le_mul_of_nonneg_right hle hexp_nonneg
    have hsub : 1 - κ' * Real.exp (-x) ≤ 1 - κ * Real.exp (-x) := by linarith
    exact max_le_max hsub le_rfl
  letI : MeasureTheory.IsFiniteMeasure μ := by infer_instance
  have hκ_int := integrable_hockeyStickIntegrand κ μ hκ
  have hκ'_int := integrable_hockeyStickIntegrand κ' μ hκ'
  exact MeasureTheory.integral_mono_ae hκ'_int hκ_int
    (Filter.Eventually.of_forall hpoint)

theorem expHockeyStickLaw_antitone
    (μ : MeasureTheory.Measure ℝ) [MeasureTheory.IsProbabilityMeasure μ]
    {ε ε' : ℝ} (hε : ε ≤ ε') :
    expHockeyStickLaw ε' μ ≤ expHockeyStickLaw ε μ := by
  unfold expHockeyStickLaw
  exact hockeyStickLaw_antitoneOn μ
    (by exact le_of_lt (Real.exp_pos ε))
    (by exact le_of_lt (Real.exp_pos ε'))
    (Real.exp_le_exp.mpr hε)

/-!
The basic hockey-stick nonnegativity facts are intentionally kept near the
definitions.  They are small, but downstream certificate bridges use them to
compare zero-slack pointwise routes against profile-valued budgets without
adding ad-hoc nonnegativity assumptions at every consumer.
-/

theorem hockeyStickLaw_nonneg (κ : ℝ) (μ : MeasureTheory.Measure ℝ) :
    0 ≤ hockeyStickLaw κ μ := by
  unfold hockeyStickLaw
  exact MeasureTheory.integral_nonneg fun x => le_max_right _ _

theorem expHockeyStickLaw_nonneg (ε : ℝ) (μ : MeasureTheory.Measure ℝ) :
    0 ≤ expHockeyStickLaw ε μ := by
  simpa [expHockeyStickLaw] using
    hockeyStickLaw_nonneg (Real.exp ε) μ

/--
Forward-law hockey-stick profile induced by a PLD pair.

This is a law-level profile view and is intended to become the primary bridge
from realization-level domination to privacy guarantees. The older `pldDelta`
definition below is kept as a secondary compatibility layer for now.
-/
def PLDPair.profile (L : PLDPair) (ε : ℝ) : ℝ :=
  expHockeyStickLaw ε L.forward

theorem PLDPair.profile_nonneg (L : PLDPair) (ε : ℝ) :
    0 ≤ L.profile ε := by
  simpa [PLDPair.profile] using
    expHockeyStickLaw_nonneg ε L.forward

theorem PLDPair.profile_antitone
    (L : PLDPair) [MeasureTheory.IsProbabilityMeasure L.forward]
    {ε ε' : ℝ} (hε : ε ≤ ε') :
    L.profile ε' ≤ L.profile ε := by
  simpa [PLDPair.profile] using
    expHockeyStickLaw_antitone L.forward hε

/--
Two-sided hockey-stick profile induced by a `PLDPair`.

`PLDPair.profile` is intentionally forward-law facing. Calibration-facing
accountants that need an `(ε, δ)` certificate for both neighboring directions
should consume this max of the forward profile and the profile of the dual pair.
-/
def PLDPair.twoSidedProfile (L : PLDPair) (ε : ℝ) : ℝ :=
  max (L.profile ε) (L.dual.profile ε)

theorem PLDPair.twoSidedProfile_nonneg (L : PLDPair) (ε : ℝ) :
    0 ≤ L.twoSidedProfile ε := by
  exact le_trans (PLDPair.profile_nonneg L ε) (le_max_left _ _)

@[simp] theorem PLDPair.twoSidedProfile_eq (L : PLDPair) (ε : ℝ) :
    L.twoSidedProfile ε = max (L.profile ε) (L.dual.profile ε) := rfl

@[simp] theorem PLDPair.dual_twoSidedProfile (L : PLDPair) (ε : ℝ) :
    L.dual.twoSidedProfile ε = L.twoSidedProfile ε := by
  simp [PLDPair.twoSidedProfile, max_comm]

/--
Binary PRV/convolution identity for `PLDPair.comp` at the profile surface.

Independent PLD composition is already encoded by pushing the product forward
through addition. This theorem simply exposes that exact object at the
profile layer, so downstream accountant packets can reason about
`(L₁.comp L₂).profile ε` without re-unfolding both `PLDPair.comp` and
`PLDPair.profile`.
-/
@[simp] theorem PLDPair.comp_profile_eq_expHockeyStickLaw_map_add
    (L₁ L₂ : PLDPair) (ε : ℝ) :
    (L₁.comp L₂).profile ε
      =
    expHockeyStickLaw ε
      (MeasureTheory.Measure.map (fun x : ℝ × ℝ => x.1 + x.2)
        (L₁.forward.prod L₂.forward)) := by
  rfl

/--
Binary PRV/convolution identity at the forward-law level for `PLDPair.comp`.

This is the same exact bridge as
`PLDPair.comp_profile_eq_expHockeyStickLaw_map_add`, but stated directly on
the forward law so later packets can rewrite either before or after applying
`PLDPair.profile`.
-/
@[simp] theorem PLDPair.expHockeyStickLaw_comp_forward_eq_map_add
    (L₁ L₂ : PLDPair) (ε : ℝ) :
    expHockeyStickLaw ε (L₁.comp L₂).forward
      =
    expHockeyStickLaw ε
      (MeasureTheory.Measure.map (fun x : ℝ × ℝ => x.1 + x.2)
        (L₁.forward.prod L₂.forward)) := by
  rfl

/--
Profile-facing upper bound exported by the `k`-out-of-`t` reduction layer.

This packages the right-hand side of `lem:multAlloc` using the existing
`PLDPair.profile` interface on the composed `1`-out-of-`⌊ t / k ⌋` upper pair.

Important: this is only the paper's packaged right-hand side. The exact
left-hand `k`-out-of-`t` profile theorem is not yet formalized here.
-/
def kOutOfTReductionUpperProfile (L : PLDPair) (t k : ℕ) (ε : ℝ) : ℝ :=
  (kOutOfTReductionUpperPair L t k).profile ε

/--
Corrected public upper profile for the `k`-out-of-`t` theorem surface.
-/
def correctedKOutOfTReductionUpperProfile (L : PLDPair) (t k : ℕ) (ε : ℝ) : ℝ :=
  (correctedKOutOfTReductionUpperPair L t k).profile ε

@[simp] theorem kOutOfTReductionUpperProfile_eq
    (L : PLDPair) (t k : ℕ) (ε : ℝ) :
    kOutOfTReductionUpperProfile L t k ε
      = (kOutOfTReductionUpperPair L t k).profile ε := rfl

@[simp] theorem correctedKOutOfTReductionUpperProfile_eq
    (L : PLDPair) (t k : ℕ) (ε : ℝ) :
    correctedKOutOfTReductionUpperProfile L t k ε
      = (correctedKOutOfTReductionUpperPair L t k).profile ε := rfl

@[simp] theorem
    correctedKOutOfTReductionUpperProfile_eq_kOutOfTReductionUpperProfile_shifted_divisible
    (L : PLDPair) (k m : ℕ) (ε : ℝ) (hk1 : 1 ≤ k) (hm1 : 1 ≤ m) :
    correctedKOutOfTReductionUpperProfile L (k * m - 1) k ε
      = kOutOfTReductionUpperProfile L (k * m - 1) k ε := by
  unfold correctedKOutOfTReductionUpperProfile kOutOfTReductionUpperProfile
  simp [hk1, hm1]

theorem correctedKOutOfTReductionUpperProfile_eq_floorRepair
    (L : PLDPair) {t k : ℕ} (ε : ℝ) (hk1 : 1 ≤ k) (hkt1 : k ≤ t + 1) :
    correctedKOutOfTReductionUpperProfile L (k * ((t + 1) / k) - 1) k ε
      = correctedKOutOfTReductionUpperProfile L t k ε := by
  unfold correctedKOutOfTReductionUpperProfile
  simp [correctedKOutOfTReductionWidth_floorRepair, hk1, hkt1]

/--
Paper-facing `k = 1` sanity check for the packaged reduction right-hand side.

This is the explicit specialization showing that the `k`-out-of-`t` packaged
upper profile collapses to the existing single-allocation object when `k = 1`.
-/
@[simp] theorem kOutOfTReductionUpperProfile_one (L : PLDPair) (t : ℕ) (ε : ℝ) :
    kOutOfTReductionUpperProfile L t 1 ε
      = (PLDPair.id.comp (randomAllocationTransforms L t)).profile ε := by
  simp [kOutOfTReductionUpperProfile, kOutOfTReductionUpperPair, kOutOfTSingleAllocationPair]

/--
Legacy pair-level privacy-profile-style expression used by the earlier
`pldDelta` interface.
-/
def pldDelta (L : PLDPair) (ε : ℝ) : ℝ :=
  pldTailRight L.forward ε - Real.exp ε * pldTailLeft L.reverse (-ε)

/--
`U` dominates `L` if it upper-bounds the privacy-loss tail formula pointwise in
`ε`. This is the theorem-facing domination interface for the generic
random-allocation PLD layer at the privacy-profile level. The realization-level
stochastic-domination interface is `PLDPair.RealizationDominates`.
-/
def PLDPair.Dominates (U L : PLDPair) : Prop :=
  ∀ ε : ℝ, pldDelta L ε ≤ pldDelta U ε

@[simp] theorem PLDPair.dominates_refl (L : PLDPair) :
    L.Dominates L := by
  intro ε
  exact le_rfl

/--
Product density `Q^t` written pointwise over a finite product space.

This is a concrete density helper for the pointwise ratio identity at the core
of `thm:PLDrandAlloc`.
-/
def prodDensity {α : Type} {t : ℕ}
    (q : α → ℝ) (x : Fin (t + 1) → α) : ℝ :=
  ∏ i : Fin (t + 1), q (x i)

/--
The `i`-th summand in the random-allocation mixture density:
use `p` at coordinate `i` and `q` elsewhere.
-/
def allocDensitySummand {α : Type} {t : ℕ}
    (p q : α → ℝ) (i : Fin (t + 1)) (x : Fin (t + 1) → α) : ℝ :=
  p (x i) * ∏ j ∈ (Finset.univ : Finset (Fin (t + 1))).erase i, q (x j)

/-- Pointwise density of the random-allocation mixture `\bar P_t`. -/
def barDensity {α : Type} {t : ℕ}
    (p q : α → ℝ) (x : Fin (t + 1) → α) : ℝ :=
  ((∑ i : Fin (t + 1), allocDensitySummand p q i x) / (t + 1 : ℝ))

/--
Subset-indexed density summand for the fixed-size `k`-out-of-`t` scheme.

For a participating set `s`, use density `p` on the selected coordinates and
`q` on the remaining coordinates. This is the direct size-`k` generalization of
`allocDensitySummand`.

Under the current Lean convention the horizon is indexed by `Fin (t + 1)`.
This matches the exact `k = 1` layer already present in this file and is the
theorem-facing left-hand surface later consumed by the paper reduction target
`lem:multAlloc`.
-/
def kOutOfTSubsetDensitySummand {α : Type} {t : ℕ}
    (p q : α → ℝ) (s : Finset (Fin (t + 1))) (x : Fin (t + 1) → α) : ℝ :=
  ∏ i : Fin (t + 1), if i ∈ s then p (x i) else q (x i)

/--
Uniform size-`k` active-side mixture density for the fixed-size random
allocation scheme.

This averages `kOutOfTSubsetDensitySummand` over all subsets of cardinality
`k`, matching the paper semantics where each example participates in exactly
`k` distinct steps chosen uniformly at random.

The public theorem-facing regime is `1 ≤ k` and `k ≤ t + 1`; the definition is
kept total so downstream changes can still name it outside that range if
needed.
-/
def kOutOfTBarDensity {α : Type} {t : ℕ}
    (p q : α → ℝ) (k : ℕ) (x : Fin (t + 1) → α) : ℝ :=
  (Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
      (fun s => kOutOfTSubsetDensitySummand p q s x) / (Nat.choose (t + 1) k : ℝ))

theorem kOutOfTSubsetDensitySummand_singleton
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (i : Fin (t + 1))
    (x : Fin (t + 1) → α) :
    kOutOfTSubsetDensitySummand p q ({i} : Finset (Fin (t + 1))) x
      = allocDensitySummand p q i x := by
  classical
  unfold kOutOfTSubsetDensitySummand allocDensitySummand
  rw [← Finset.mul_prod_erase (Finset.univ : Finset (Fin (t + 1)))
    (fun j => if j ∈ ({i} : Finset (Fin (t + 1))) then p (x j) else q (x j))
    (Finset.mem_univ i)]
  simp only [Finset.mem_singleton, if_true]
  congr 1
  refine Finset.prod_congr rfl ?_
  intro j hj
  have hjne : j ≠ i := (Finset.mem_erase.mp hj).1
  simp [hjne]

@[simp] theorem kOutOfTBarDensity_one
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (x : Fin (t + 1) → α) :
    kOutOfTBarDensity p q 1 x = barDensity p q x := by
  classical
  unfold kOutOfTBarDensity barDensity
  rw [Finset.powersetCard_one]
  simp [kOutOfTSubsetDensitySummand_singleton]

/--
Subset-indexed density summands can be factored into the all-`Q` product density
times a product of coordinate-wise likelihood ratios over the participating set.

This is the fixed-size `k` counterpart of
`allocDensitySummand_eq_ratio_mul_prodDensity`.
-/
theorem kOutOfTSubsetDensitySummand_eq_subsetRatio_mul_prodDensity
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (s : Finset (Fin (t + 1)))
    (x : Fin (t + 1) → α)
    (hq : ∀ i : Fin (t + 1), q (x i) ≠ 0) :
    kOutOfTSubsetDensitySummand p q s x
      =
    (Finset.prod s (fun i => p (x i) / q (x i))) * prodDensity q x := by
  classical
  unfold kOutOfTSubsetDensitySummand prodDensity
  calc
    Finset.prod Finset.univ (fun i : Fin (t + 1) => if i ∈ s then p (x i) else q (x i))
      = Finset.prod Finset.univ
          (fun i : Fin (t + 1) => ((if i ∈ s then p (x i) / q (x i) else 1) * q (x i))) := by
          refine Finset.prod_congr rfl ?_
          intro i hi
          by_cases hs : i ∈ s
          · simp [hs, hq i]
          · simp [hs]
    _ = (Finset.prod Finset.univ (fun i : Fin (t + 1) => if i ∈ s then p (x i) / q (x i) else 1))
          * Finset.prod Finset.univ (fun i : Fin (t + 1) => q (x i)) := by
          rw [Finset.prod_mul_distrib]
    _ = (Finset.prod s (fun i => p (x i) / q (x i)))
          * Finset.prod Finset.univ (fun i : Fin (t + 1) => q (x i)) := by
          rw [Finset.prod_ite_mem_eq]
    _ = (Finset.prod s (fun i => p (x i) / q (x i))) * prodDensity q x := by
          simp [prodDensity]

/--
The uniform size-`k` density can be factored into the all-`Q` product density
times the average subset-ratio term over all participating sets of size `k`.

This is the fixed-size counterpart of
`barDensity_eq_avg_ratio_mul_prodDensity`.
-/
theorem kOutOfTBarDensity_eq_avg_subsetRatio_mul_prodDensity
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (k : ℕ)
    (x : Fin (t + 1) → α)
    (hq : ∀ i : Fin (t + 1), q (x i) ≠ 0) :
    kOutOfTBarDensity p q k x
      =
    (((Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
          (fun s => Finset.prod s (fun i => p (x i) / q (x i)))) / (Nat.choose (t + 1) k : ℝ)))
      * prodDensity q x := by
  classical
  have hsum :
      Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
          (fun s => kOutOfTSubsetDensitySummand p q s x)
        =
      (Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
          (fun s => Finset.prod s (fun i => p (x i) / q (x i))))
        * prodDensity q x := by
    calc
      Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
          (fun s => kOutOfTSubsetDensitySummand p q s x)
        =
      Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
          (fun s => (Finset.prod s (fun i => p (x i) / q (x i))) * prodDensity q x) := by
            refine Finset.sum_congr rfl ?_
            intro s hs
            rw [kOutOfTSubsetDensitySummand_eq_subsetRatio_mul_prodDensity p q s x hq]
      _ =
        (Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
            (fun s => Finset.prod s (fun i => p (x i) / q (x i))))
          * prodDensity q x := by
            rw [Finset.sum_mul]
  unfold kOutOfTBarDensity
  rw [hsum]
  ring

/--
Division by the all-`Q` product density turns the fixed-size mixture density
into the average subset-ratio term.
-/
theorem kOutOfTBarDensity_div_prodDensity_eq_avg_subsetRatio
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (k : ℕ)
    (x : Fin (t + 1) → α)
    (hq : ∀ i : Fin (t + 1), q (x i) ≠ 0) :
    kOutOfTBarDensity p q k x / prodDensity q x
      =
    ((Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
        (fun s => Finset.prod s (fun i => p (x i) / q (x i))) / (Nat.choose (t + 1) k : ℝ))) := by
  rw [kOutOfTBarDensity_eq_avg_subsetRatio_mul_prodDensity p q k x hq]
  have hprod : prodDensity q x ≠ 0 := by
    unfold prodDensity
    exact Finset.prod_ne_zero_iff.mpr (by
      intro i hi
      exact hq i)
  field_simp [hprod]

theorem allocDensitySummand_eq_ratio_mul_prodDensity
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (x : Fin (t + 1) → α)
    (i : Fin (t + 1))
    (hq : q (x i) ≠ 0) :
    allocDensitySummand p q i x
      = (p (x i) / q (x i)) * prodDensity q x := by
  unfold allocDensitySummand prodDensity
  rw [← Finset.mul_prod_erase (Finset.univ : Finset (Fin (t + 1)))
    (fun j => q (x j)) (Finset.mem_univ i)]
  field_simp [hq]

theorem prodDensity_ne_zero
    {α : Type} {t : ℕ}
    (q : α → ℝ)
    (x : Fin (t + 1) → α)
    (hq : ∀ i : Fin (t + 1), q (x i) ≠ 0) :
    prodDensity q x ≠ 0 := by
  unfold prodDensity
  exact Finset.prod_ne_zero_iff.mpr (by
    intro i hi
    exact hq i)

theorem barDensity_eq_avg_ratio_mul_prodDensity
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (x : Fin (t + 1) → α)
    (hq : ∀ i : Fin (t + 1), q (x i) ≠ 0) :
    barDensity p q x
      = (((∑ i : Fin (t + 1), p (x i) / q (x i)) / (t + 1 : ℝ)))
          * prodDensity q x := by
  have hsum :
      ∑ i : Fin (t + 1), allocDensitySummand p q i x
        = (∑ i : Fin (t + 1), p (x i) / q (x i)) * prodDensity q x := by
    calc
      ∑ i : Fin (t + 1), allocDensitySummand p q i x
        = ∑ i : Fin (t + 1), (p (x i) / q (x i)) * prodDensity q x := by
            refine Finset.sum_congr rfl ?_
            intro i hi
            rw [allocDensitySummand_eq_ratio_mul_prodDensity p q x i (hq i)]
      _ = (∑ i : Fin (t + 1), p (x i) / q (x i)) * prodDensity q x := by
            rw [Finset.sum_mul]
  unfold barDensity
  rw [hsum]
  have ht : (t + 1 : ℝ) ≠ 0 := by exact_mod_cast Nat.succ_ne_zero t
  field_simp [ht]

theorem barDensity_div_prodDensity_eq_avg_ratio
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (x : Fin (t + 1) → α)
    (hq : ∀ i : Fin (t + 1), q (x i) ≠ 0) :
    barDensity p q x / prodDensity q x
      = ((∑ i : Fin (t + 1), p (x i) / q (x i)) / (t + 1 : ℝ)) := by
  rw [barDensity_eq_avg_ratio_mul_prodDensity p q x hq]
  have hprod : prodDensity q x ≠ 0 := prodDensity_ne_zero q x hq
  field_simp [hprod]

/-- One-step forward privacy-loss value `log (p / q)`. -/
def forwardLossValue {α : Type} (p q : α → ℝ) (a : α) : ℝ :=
  Real.log (p a / q a)

/-- One-step reverse privacy-loss value `log (q / p)`. -/
def reverseLossValue {α : Type} (p q : α → ℝ) (a : α) : ℝ :=
  Real.log (q a / p a)

/-- The density measure with real-valued density `f` over a base measure `μ`. -/
def densityMeasure {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α) (f : α → ℝ) : MeasureTheory.Measure α :=
  μ.withDensity (fun a => ENNReal.ofReal (f a))

/-- One-step PLD law of `(P,Q)` sampled from the `P` side. -/
def forwardLossLaw {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) : MeasureTheory.Measure ℝ :=
  (densityMeasure μ p).map (forwardLossValue p q)

/-- One-step PLD law of `(Q,P)` sampled from the `Q` side. -/
def reverseLossLaw {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) : MeasureTheory.Measure ℝ :=
  (densityMeasure μ q).map (forwardLossValue q p)

/-- The concrete PLD pair generated by densities `p` and `q` over a base measure `μ`. -/
def concretePLDPair {α : Type} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) : PLDPair :=
  ⟨forwardLossLaw μ p q, reverseLossLaw μ p q⟩

/-- Distinguished-coordinate source measure `P × Q^t` used in the remove-direction proof. -/
def removeSourceMeasure {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) :
    MeasureTheory.Measure (Fin (t + 1) → α) :=
  MeasureTheory.Measure.pi (fun i : Fin (t + 1) =>
    if i.1 = 0 then densityMeasure μ p else densityMeasure μ q)

/-- All-`Q` product source measure used in the add-direction proof. -/
def addSourceMeasure {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (q : α → ℝ) :
    MeasureTheory.Measure (Fin (t + 1) → α) :=
  MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => densityMeasure μ q)

/--
Product base measure on the full horizon state space.

This is the neutral ambient measure used to define exact averaged-source laws
for the `k`-out-of-`t` scheme directly from their densities.
-/
def productBaseMeasure {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) :
    MeasureTheory.Measure (Fin (t + 1) → α) :=
  MeasureTheory.Measure.pi (fun _ : Fin (t + 1) => μ)

/--
Canonical fixed-size active-source measure used by the theorem-facing
`k`-out-of-`t` exact profile surface.

This keeps the current file convention of using a distinguished active block in
the source measure. Under `k = 1` it reduces definitionally to
`removeSourceMeasure`.
-/
def kOutOfTRemoveSourceMeasure {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (k : ℕ) :
    MeasureTheory.Measure (Fin (t + 1) → α) :=
  MeasureTheory.Measure.pi (fun i : Fin (t + 1) =>
    if i.1 < k then densityMeasure μ p else densityMeasure μ q)

@[simp] theorem kOutOfTRemoveSourceMeasure_one
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) :
    kOutOfTRemoveSourceMeasure (t := t) μ p q 1 = removeSourceMeasure (t := t) μ p q := by
  unfold kOutOfTRemoveSourceMeasure removeSourceMeasure
  simp [Nat.lt_one_iff]


lemma measurable_forwardLossValue {α : Type} [MeasurableSpace α]
    {p q : α → ℝ} (hp : Measurable p) (hq : Measurable q) :
    Measurable (forwardLossValue p q) := by
  unfold forwardLossValue
  exact Measurable.log <| hp.div hq

lemma measurable_removeCoordLoss {α : Type} [MeasurableSpace α] {t : ℕ}
    {p q : α → ℝ} (hp : Measurable p) (hq : Measurable q) :
    Measurable (fun x : Fin (t + 1) → α =>
      fun i : Fin (t + 1) =>
        if i.1 = 0 then forwardLossValue p q (x i) else forwardLossValue q p (x i)) := by
  classical
  rw [measurable_pi_iff]
  intro i
  by_cases h : i.1 = 0
  · simpa [h, Function.comp_def] using
      (measurable_forwardLossValue hp hq).comp (measurable_pi_apply i)
  · simpa [h, Function.comp_def] using
      (measurable_forwardLossValue hq hp).comp (measurable_pi_apply i)

lemma removeSourceMeasure_map_coordLoss
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp : Measurable p) (hq : Measurable q)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p))) :
    (removeSourceMeasure (t := t) μ p q).map
        (fun x : Fin (t + 1) → α =>
          fun i : Fin (t + 1) =>
            if i.1 = 0 then forwardLossValue p q (x i) else forwardLossValue q p (x i))
      =
    MeasureTheory.Measure.pi (fun i : Fin (t + 1) =>
      removeCoordLaw (concretePLDPair μ p q) i) := by
  let ν : Fin (t + 1) → MeasureTheory.Measure α :=
    fun i => if i.1 = 0 then densityMeasure μ p else densityMeasure μ q
  let g : ∀ i : Fin (t + 1), α → ℝ :=
    fun i => if i.1 = 0 then forwardLossValue p q else forwardLossValue q p
  have hg : ∀ i, AEMeasurable (g i) (ν i) := by
    intro i
    by_cases h0 : i.1 = 0
    · have hg0 : g i = forwardLossValue p q := by
        rw [show g i =
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
            rfl]
        simp [h0]
      have hν0 : ν i = densityMeasure μ p := by
        rw [show ν i = (if i.1 = 0 then densityMeasure μ p else densityMeasure μ q) by
          rfl]
        simp [h0]
      rw [hg0, hν0]
      exact (measurable_forwardLossValue hp hq).aemeasurable
    · have hg1 : g i = forwardLossValue q p := by
        rw [show g i =
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
            rfl]
        simp [h0]
      have hν1 : ν i = densityMeasure μ q := by
        rw [show ν i = (if i.1 = 0 then densityMeasure μ p else densityMeasure μ q) by
          rfl]
        simp [h0]
      rw [hg1, hν1]
      exact (measurable_forwardLossValue hq hp).aemeasurable
  letI : ∀ i : Fin (t + 1), MeasureTheory.SigmaFinite ((ν i).map (g i)) := by
    intro i
    simpa [ν, g] using hσmap i
  have hmap :
      MeasureTheory.Measure.map (fun x i => g i (x i)) (MeasureTheory.Measure.pi ν)
        = MeasureTheory.Measure.pi (fun i => MeasureTheory.Measure.map (g i) (ν i)) := by
    rw [MeasureTheory.Measure.pi_map_pi (μ := ν) (f := g) (hf := hg)]
  rw [removeSourceMeasure]
  have hnormalizeFun :
      (fun x : Fin (t + 1) → α =>
        fun i : Fin (t + 1) =>
          if i = 0 then forwardLossValue p q (x i) else forwardLossValue q p (x i))
        =
      (fun x : Fin (t + 1) → α =>
        fun i : Fin (t + 1) =>
          if i.1 = 0 then forwardLossValue p q (x i) else forwardLossValue q p (x i)) := by
    funext x
    funext i
    exact ite_fin_eq_zero_to_val_eq_zero i _ _
  have hnormalizeMeasure :
      (fun i : Fin (t + 1) => if i = 0 then densityMeasure μ p else densityMeasure μ q)
        =
      (fun i : Fin (t + 1) => if i.1 = 0 then densityMeasure μ p else densityMeasure μ q) := by
    funext i
    exact ite_fin_eq_zero_to_val_eq_zero i _ _
  have hnormalizeFunApply :
      (fun x : Fin (t + 1) → α =>
        fun i : Fin (t + 1) =>
          if i = 0 then forwardLossValue p q (x i) else forwardLossValue q p (x i))
        =
      (fun x : Fin (t + 1) → α =>
        fun i : Fin (t + 1) =>
          (if i = 0 then forwardLossValue p q else forwardLossValue q p) (x i)) := by
    funext x
    funext i
    by_cases h : i = 0
    · simp [h]
    · simp [h]
  calc
    MeasureTheory.Measure.map
        (fun x i => if i.1 = 0 then forwardLossValue p q (x i) else forwardLossValue q p (x i))
        (MeasureTheory.Measure.pi
          fun i ↦ if i.1 = 0 then densityMeasure μ p else densityMeasure μ q)
      =
        MeasureTheory.Measure.map (fun x i => g i (x i)) (MeasureTheory.Measure.pi ν) := by
          rw [← hnormalizeFun, hnormalizeFunApply, ← hnormalizeMeasure]
          simp [ν, g]
    _ = MeasureTheory.Measure.pi (fun i => MeasureTheory.Measure.map (g i) (ν i)) := hmap
    _ = MeasureTheory.Measure.pi (fun i : Fin (t + 1) =>
          removeCoordLaw (concretePLDPair μ p q) i) := by
          have hcoord :
              (fun i => MeasureTheory.Measure.map (g i) (ν i))
                =
              (fun i : Fin (t + 1) =>
                removeCoordLaw (concretePLDPair μ p q) i) := by
            funext i
            by_cases h0 : i.1 = 0
            · have hg0 : g i = forwardLossValue p q := by
                rw [show g i =
                  (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
                    rfl]
                simp [h0]
              have hν0 : ν i = densityMeasure μ p := by
                rw [show ν i = (if i.1 = 0 then densityMeasure μ p else densityMeasure μ q) by
                  rfl]
                simp [h0]
              rw [hg0, hν0]
              simp [removeCoordLaw, concretePLDPair, forwardLossLaw, reverseLossLaw, h0]
            · have hg1 : g i = forwardLossValue q p := by
                rw [show g i =
                  (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
                    rfl]
                simp [h0]
              have hν1 : ν i = densityMeasure μ q := by
                rw [show ν i = (if i.1 = 0 then densityMeasure μ p else densityMeasure μ q) by
                  rfl]
                simp [h0]
              rw [hg1, hν1]
              simp [removeCoordLaw, concretePLDPair, forwardLossLaw, reverseLossLaw, h0]
          rw [hcoord]

/--
Concrete remove-direction privacy-loss value for the random-allocation pair
`(\bar P_t, Q^t)`.
-/
def removePrivacyLossValue {α : Type} {t : ℕ}
    (p q : α → ℝ) (x : Fin (t + 1) → α) : ℝ :=
  Real.log (barDensity p q x / prodDensity q x)

/--
Concrete add-direction privacy-loss value for the reverse random-allocation pair
`(Q^t, \bar P_t)`.
-/
def addPrivacyLossValue {α : Type} {t : ℕ}
    (p q : α → ℝ) (x : Fin (t + 1) → α) : ℝ :=
  Real.log (prodDensity q x / barDensity p q x)

/--
Concrete random-allocation PLD pair built directly from the remove/add source
measures and their privacy-loss values.
-/
def concreteRandomAllocationPLDPair {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) : PLDPair :=
  ⟨(removeSourceMeasure (t := t) μ p q).map (removePrivacyLossValue p q),
    (addSourceMeasure (t := t) μ q).map (addPrivacyLossValue p q)⟩

/--
Concrete remove-direction privacy-loss value for the size-`k` fixed-size
random-allocation surface.

The active-side density is the exact uniform size-`k` mixture
`kOutOfTBarDensity`; the inactive side remains the product baseline
`prodDensity q`.
-/
def kOutOfTRemovePrivacyLossValue {α : Type} {t : ℕ}
    (p q : α → ℝ) (k : ℕ) (x : Fin (t + 1) → α) : ℝ :=
  Real.log (kOutOfTBarDensity p q k x / prodDensity q x)

/--
Concrete add-direction privacy-loss value for the size-`k` fixed-size
random-allocation surface.
-/
def kOutOfTAddPrivacyLossValue {α : Type} {t : ℕ}
    (p q : α → ℝ) (k : ℕ) (x : Fin (t + 1) → α) : ℝ :=
  Real.log (prodDensity q x / kOutOfTBarDensity p q k x)

@[simp] theorem kOutOfTRemovePrivacyLossValue_one
    {α : Type} {t : ℕ}
    (p q : α → ℝ) (x : Fin (t + 1) → α) :
    kOutOfTRemovePrivacyLossValue p q 1 x = removePrivacyLossValue p q x := by
  simp [kOutOfTRemovePrivacyLossValue, removePrivacyLossValue, kOutOfTBarDensity_one]

/--
Pointwise rewrite of the fixed-size remove privacy loss as the logarithm of the
average subset-ratio term under the all-`Q` product baseline.

This is the most explicit local form of the exact size-`k` remove privacy loss
currently available. It exposes the combinatorial object that the remaining
`k`-out-of-`t` reduction proof still needs to compare against the blockwise
upper profile.
-/
theorem kOutOfTRemovePrivacyLossValue_eq_log_avg_subsetRatio
    {α : Type} {t : ℕ}
    (p q : α → ℝ) (k : ℕ) (x : Fin (t + 1) → α)
    (hq : ∀ i : Fin (t + 1), q (x i) ≠ 0) :
    kOutOfTRemovePrivacyLossValue p q k x
      =
    Real.log
      ((Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
          (fun s => Finset.prod s (fun i => p (x i) / q (x i))))
        / (Nat.choose (t + 1) k : ℝ)) := by
  unfold kOutOfTRemovePrivacyLossValue
  rw [kOutOfTBarDensity_div_prodDensity_eq_avg_subsetRatio p q k x hq]

@[simp] theorem kOutOfTAddPrivacyLossValue_one
    {α : Type} {t : ℕ}
    (p q : α → ℝ) (x : Fin (t + 1) → α) :
    kOutOfTAddPrivacyLossValue p q 1 x = addPrivacyLossValue p q x := by
  simp [kOutOfTAddPrivacyLossValue, addPrivacyLossValue, kOutOfTBarDensity_one]

/--
Concrete theorem-facing PLD pair for the fixed-size `k`-out-of-`t` surface.

This packages the new size-`k` remove/add privacy-loss values with the current
Lean source-measure convention. The `k = 1` compatibility theorems below are
the intended sanity checks before any later `lem:multAlloc` proof is attempted.

Important: for general `k`, this is still a proxy theorem object built from a
distinguished-coordinate source convention. The exact uniform-subset active
source is added separately below as `exactKOutOfTRandomAllocationPLDPair`.
-/
def concreteKOutOfTRandomAllocationPLDPair {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (k : ℕ) : PLDPair :=
  ⟨(kOutOfTRemoveSourceMeasure (t := t) μ p q k).map (kOutOfTRemovePrivacyLossValue p q k),
    (addSourceMeasure (t := t) μ q).map (kOutOfTAddPrivacyLossValue p q k)⟩

/--
Exact active-side source measure for the fixed-size `k`-out-of-`t` law.

Unlike `kOutOfTRemoveSourceMeasure`, this is built directly from the averaged
uniform-subset density `kOutOfTBarDensity` over the full product base measure.
This is the honest left-hand source object suggested by the paper definition of
the random-allocation scheme.
-/
def exactKOutOfTRemoveSourceMeasure {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (k : ℕ) :
    MeasureTheory.Measure (Fin (t + 1) → α) :=
  densityMeasure (productBaseMeasure (t := t) μ) (kOutOfTBarDensity p q k)

/--
Exact inactive-side source measure for the fixed-size `k`-out-of-`t` law.

This is the all-`Q` product law expressed directly as a density over the full
product base measure.
-/
def exactKOutOfTAddSourceMeasure {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (q : α → ℝ) :
    MeasureTheory.Measure (Fin (t + 1) → α) :=
  densityMeasure (productBaseMeasure (t := t) μ) (prodDensity q)

/--
Exact PLD pair for the fixed-size `k`-out-of-`t` random-allocation scheme.

This uses the honest averaged active source `kOutOfTBarDensity` rather than the
distinguished-source proxy. It is the intended left-hand theorem object for the
later combinatorial reduction theorem.
-/
def exactKOutOfTRandomAllocationPLDPair {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (k : ℕ) : PLDPair :=
  ⟨(exactKOutOfTRemoveSourceMeasure (t := t) μ p q k).map (kOutOfTRemovePrivacyLossValue p q k),
    (exactKOutOfTAddSourceMeasure (t := t) μ q).map (kOutOfTAddPrivacyLossValue p q k)⟩

/--
Exact profile alias for the honest averaged-source fixed-size `k`-out-of-`t`
law.

This is the profile object the combinatorial `lem:multAlloc` theorem should
ultimately upper-bound.
-/
def exactKOutOfTExactProfile {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (k : ℕ) (ε : ℝ) : ℝ :=
  (exactKOutOfTRandomAllocationPLDPair (t := t) μ p q k).profile ε

/--
Theorem-facing reduction goal phrased against the honest averaged-source
size-`k` profile object.

This is the strengthened replacement for `concreteKOutOfTReductionGoal` once the
combinatorial bridge is proved against the exact uniform-subset law. It is the
intended Lean left-hand target for `lem:multAlloc` from
`paper/bnb-accounting-wo-mc/PLD_components/body.tex`.
-/
def exactKOutOfTReductionGoal {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (k : ℕ) (ε : ℝ) : Prop :=
  exactKOutOfTExactProfile (t := t) μ p q k ε
    ≤ kOutOfTReductionUpperProfile (concretePLDPair μ p q) t k ε

/--
Corrected public theorem-facing reduction target for the `k`-out-of-`t` path.
-/
def correctedExactKOutOfTReductionGoal {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (k : ℕ) (ε : ℝ) : Prop :=
  exactKOutOfTExactProfile (t := t) μ p q k ε
    ≤ correctedKOutOfTReductionUpperProfile (concretePLDPair μ p q) t k ε

/--
`k = 1` rewrite for the honest averaged-source reduction goal.

This is the exact-side sanity check needed by downstream reduction changes after
the theorem-facing target is migrated away from the distinguished-source proxy.
-/
@[simp] theorem exactKOutOfTReductionGoal_one_iff
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (ε : ℝ) :
    exactKOutOfTReductionGoal (t := t) μ p q 1 ε
      ↔
    exactKOutOfTExactProfile (t := t) μ p q 1 ε
      ≤ (PLDPair.id.comp (randomAllocationTransforms (concretePLDPair μ p q) t)).profile ε := by
  unfold exactKOutOfTReductionGoal
  simp

/--
Exact profile alias exported from the theorem-facing size-`k` PLD pair.

This is the left-hand profile object that the later reduction theorem should
upper-bound, under the current `Fin (t + 1)` horizon convention and explicit
public hypotheses `1 ≤ k`, `k ≤ t + 1`.
-/
def concreteKOutOfTExactProfile {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (k : ℕ) (ε : ℝ) : ℝ :=
  (concreteKOutOfTRandomAllocationPLDPair (t := t) μ p q k).profile ε

@[simp] theorem concreteKOutOfTRandomAllocationPLDPair_one
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) :
    concreteKOutOfTRandomAllocationPLDPair (t := t) μ p q 1
      = concreteRandomAllocationPLDPair (t := t) μ p q := by
  unfold concreteKOutOfTRandomAllocationPLDPair concreteRandomAllocationPLDPair
  have hremove :
      MeasureTheory.Measure.map (kOutOfTRemovePrivacyLossValue p q 1)
          (kOutOfTRemoveSourceMeasure (t := t) μ p q 1)
        =
      MeasureTheory.Measure.map (removePrivacyLossValue p q)
          (removeSourceMeasure (t := t) μ p q) := by
    rw [kOutOfTRemoveSourceMeasure_one]
    refine congrArg (fun f => MeasureTheory.Measure.map f (removeSourceMeasure (t := t) μ p q)) ?_
    funext x
    simp
  have hadd :
      MeasureTheory.Measure.map (kOutOfTAddPrivacyLossValue p q 1)
          (addSourceMeasure (t := t) μ q)
        =
      MeasureTheory.Measure.map (addPrivacyLossValue p q)
          (addSourceMeasure (t := t) μ q) := by
    refine congrArg (fun f => MeasureTheory.Measure.map f (addSourceMeasure (t := t) μ q)) ?_
    funext x
    simp
  simpa [PLDPair.mk.injEq] using And.intro hremove hadd

@[simp] theorem concreteKOutOfTExactProfile_one
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (ε : ℝ) :
    concreteKOutOfTExactProfile (t := t) μ p q 1 ε
      = (concreteRandomAllocationPLDPair (t := t) μ p q).profile ε := by
  simp [concreteKOutOfTExactProfile]

/--
Theorem-facing left/right profile comparison target for the exact size-`k`
surface and the packaged `lem:multAlloc` right-hand side.

This is the precise proposition the later reduction theorem should prove. It is
kept as a named alias so downstream numerical-accounting changes can cite the
reduction goal without rebuilding either side.
-/
def concreteKOutOfTReductionGoal {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (k : ℕ) (ε : ℝ) : Prop :=
  concreteKOutOfTExactProfile (t := t) μ p q k ε
    ≤ kOutOfTReductionUpperProfile (concretePLDPair μ p q) t k ε

/--
`k = 1` rewrite for the exact-versus-packaged reduction goal.

This does not prove the reduction theorem. It only normalizes the left-hand
exact profile and the packaged right-hand side into the existing `1`-out-of-`t`
objects so later changes can cite a stable base case.
-/
@[simp] theorem concreteKOutOfTReductionGoal_one_iff
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) (p q : α → ℝ) (ε : ℝ) :
    concreteKOutOfTReductionGoal (t := t) μ p q 1 ε
      ↔
    (concreteRandomAllocationPLDPair (t := t) μ p q).profile ε
      ≤ (PLDPair.id.comp (randomAllocationTransforms (concretePLDPair μ p q) t)).profile ε := by
  unfold concreteKOutOfTReductionGoal
  simp [concreteKOutOfTExactProfile_one]

/--
Pointwise remove-direction identity in `loss = log-average-exp` form.

This is the direct Lean analogue of the appendix proof step for
`L_{\bar P_t || Q^t}` before any law packaging.
-/
theorem removePrivacyLossValue_eq_removeTransformValue
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (x : Fin (t + 1) → α)
    (hp : ∀ i : Fin (t + 1), 0 < p (x i))
    (hq : ∀ i : Fin (t + 1), 0 < q (x i)) :
    removePrivacyLossValue p q x
      =
    removeTransformValue
      (fun i : Fin (t + 1) =>
        if i.1 = 0 then forwardLossValue p q (x i) else forwardLossValue q p (x i)) := by
  unfold removePrivacyLossValue removeTransformValue forwardLossValue
  rw [barDensity_div_prodDensity_eq_avg_ratio p q x (fun i => ne_of_gt (hq i))]
  refine congrArg (fun z : ℝ => Real.log (z / (t + 1 : ℝ))) ?_
  exact Finset.sum_congr rfl (fun i _ => by
    by_cases h : i.1 = 0
    · simp only [h, ↓reduceIte]
      simpa using
        (Real.exp_log (div_pos (hp i) (hq i))).symm
    · simp only [h, ↓reduceIte]
      calc
        p (x i) / q (x i)
          = (q (x i) / p (x i))⁻¹ := by
              field_simp [ne_of_gt (hp i), ne_of_gt (hq i)]
        _ = Real.exp (-Real.log (q (x i) / p (x i))) := by
              rw [Real.exp_neg, Real.exp_log (div_pos (hq i) (hp i))])

/--
Pointwise add-direction identity in `loss = -log-average-exp` form.

This is the direct Lean analogue of the appendix proof step for
`L_{Q^t || \bar P_t}` before any law packaging.
-/
theorem addPrivacyLossValue_eq_addTransformValue
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (x : Fin (t + 1) → α)
    (hp : ∀ i : Fin (t + 1), 0 < p (x i))
    (hq : ∀ i : Fin (t + 1), 0 < q (x i)) :
    addPrivacyLossValue p q x
      =
    addTransformValue (fun i : Fin (t + 1) => forwardLossValue q p (x i)) := by
  unfold addPrivacyLossValue addTransformValue forwardLossValue
  set avg : ℝ := ((∑ i : Fin (t + 1), p (x i) / q (x i)) / (t + 1 : ℝ)) with havg
  have hsum_pos : 0 < ∑ i : Fin (t + 1), p (x i) / q (x i) := by
    refine Finset.sum_pos ?_ ?_
    · intro i hi
      exact div_pos (hp i) (hq i)
    · simp
  have ht_pos : 0 < (t + 1 : ℝ) := by
    exact_mod_cast Nat.succ_pos t
  have havg_pos : 0 < avg := by
    dsimp [avg]
    exact div_pos hsum_pos ht_pos
  have hbar :
      barDensity p q x = avg * prodDensity q x := by
    simpa [avg] using
      (barDensity_eq_avg_ratio_mul_prodDensity p q x (fun i => ne_of_gt (hq i)))
  have hprod : prodDensity q x ≠ 0 := prodDensity_ne_zero q x (fun i => ne_of_gt (hq i))
  have hdiv : prodDensity q x / barDensity p q x = avg⁻¹ := by
    rw [hbar]
    field_simp [hprod, ne_of_gt havg_pos, avg]
  have hsum :
      ∑ i : Fin (t + 1), Real.exp (-Real.log (q (x i) / p (x i)))
        =
      ∑ i : Fin (t + 1), p (x i) / q (x i) := by
    refine Finset.sum_congr rfl ?_
    intro i hi
    calc
      Real.exp (-Real.log (q (x i) / p (x i)))
        = (q (x i) / p (x i))⁻¹ := by
            rw [Real.exp_neg, Real.exp_log (div_pos (hq i) (hp i))]
      _ = p (x i) / q (x i) := by
            field_simp [ne_of_gt (hp i), ne_of_gt (hq i)]
  calc
    Real.log (prodDensity q x / barDensity p q x)
      = Real.log avg⁻¹ := by rw [hdiv]
    _ = -Real.log avg := by rw [Real.log_inv]
    _ =
        -Real.log
          ((∑ i : Fin (t + 1), Real.exp (-Real.log (q (x i) / p (x i)))) / (t + 1 : ℝ)) := by
          rw [hsum, havg]

theorem removePrivacyLossLaw_eq_removeTransform_distinguished
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a) :
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p))) →
    (removeSourceMeasure (t := t) μ p q).map (removePrivacyLossValue p q)
      =
    removeTransform (concretePLDPair μ p q) t := by
  intro hσmap
  let ν : Fin (t + 1) → MeasureTheory.Measure α :=
    fun i => if i.1 = 0 then densityMeasure μ p else densityMeasure μ q
  let g : ∀ i : Fin (t + 1), α → ℝ :=
    fun i => if i.1 = 0 then forwardLossValue p q else forwardLossValue q p
  let G : (Fin (t + 1) → α) → (Fin (t + 1) → ℝ) :=
    fun x i => g i (x i)
  let F : (Fin (t + 1) → ℝ) → ℝ := removeTransformValue
  have hg : ∀ i, AEMeasurable (g i) (ν i) := by
    intro i
    by_cases h0 : i.1 = 0
    · have hg0 : g i = forwardLossValue p q := by
        rw [show g i =
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
            rfl]
        simp [h0]
      have hν0 : ν i = densityMeasure μ p := by
        rw [show ν i = (if i.1 = 0 then densityMeasure μ p else densityMeasure μ q) by
          rfl]
        simp [h0]
      rw [hg0, hν0]
      exact (measurable_forwardLossValue hp_meas hq_meas).aemeasurable
    · have hg1 : g i = forwardLossValue q p := by
        rw [show g i =
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
            rfl]
        simp [h0]
      have hν1 : ν i = densityMeasure μ q := by
        rw [show ν i = (if i.1 = 0 then densityMeasure μ p else densityMeasure μ q) by
          rfl]
        simp [h0]
      rw [hg1, hν1]
      exact (measurable_forwardLossValue hq_meas hp_meas).aemeasurable
  have hG : Measurable G := by
    rw [measurable_pi_iff]
    intro i
    by_cases h0 : i.1 = 0
    · have hg0 : g i = forwardLossValue p q := by
        rw [show g i =
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
            rfl]
        simp [h0]
      rw [show (fun x : Fin (t + 1) → α => g i (x i)) =
          (fun x : Fin (t + 1) → α => forwardLossValue p q (x i)) by
            funext x; simp [hg0]]
      exact (measurable_forwardLossValue hp_meas hq_meas).comp (measurable_pi_apply i)
    · have hg1 : g i = forwardLossValue q p := by
        rw [show g i =
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
            rfl]
        simp [h0]
      rw [show (fun x : Fin (t + 1) → α => g i (x i)) =
          (fun x : Fin (t + 1) → α => forwardLossValue q p (x i)) by
            funext x; simp [hg1]]
      exact (measurable_forwardLossValue hq_meas hp_meas).comp (measurable_pi_apply i)
  have hF : Measurable F := by
    simpa [F] using (measurable_removeTransformValue (t := t))
  haveI : ∀ i : Fin (t + 1), MeasureTheory.SigmaFinite ((ν i).map (g i)) := by
    intro i
    simpa [ν, g] using hσmap i
  have hpoint :
      removePrivacyLossValue p q = F ∘ G := by
    funext x
    dsimp [F, G]
    have hfun :
        (fun i : Fin (t + 1) =>
          if i.1 = 0 then forwardLossValue p q (x i) else forwardLossValue q p (x i))
          =
        (fun i : Fin (t + 1) => g i (x i)) := by
      funext i
      by_cases h0 : i.1 = 0
      · have hg0 : g i = forwardLossValue p q := by
          rw [show g i =
            (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
              rfl]
          simp [h0]
        simp [hg0, h0]
      · have hg1 : g i = forwardLossValue q p := by
          rw [show g i =
            (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
              rfl]
          simp [h0]
        simp [hg1, h0]
    calc
      removePrivacyLossValue p q x
        = removeTransformValue
            (fun i : Fin (t + 1) =>
              if i.1 = 0 then forwardLossValue p q (x i) else forwardLossValue q p (x i)) := by
              simpa using
                (removePrivacyLossValue_eq_removeTransformValue p q x
                  (fun i => hp_pos (x i)) (fun i => hq_pos (x i)))
      _ = removeTransformValue (fun i : Fin (t + 1) => g i (x i)) := by rw [hfun]
      _ = (F ∘ G) x := by simp [F, G, Function.comp]
  rw [removeSourceMeasure, removeTransform, concretePLDPair, hpoint]
  change MeasureTheory.Measure.map (F ∘ G) (MeasureTheory.Measure.pi ν) =
    MeasureTheory.Measure.map F (MeasureTheory.Measure.pi (fun i : Fin (t + 1) => removeCoordLaw ⟨
      forwardLossLaw μ p q, reverseLossLaw μ p q⟩ i))
  rw [← MeasureTheory.Measure.map_map hF hG]
  have hmap :
      MeasureTheory.Measure.map G (MeasureTheory.Measure.pi ν)
        = MeasureTheory.Measure.pi (fun i => MeasureTheory.Measure.map (g i) (ν i)) := by
    rw [MeasureTheory.Measure.pi_map_pi (μ := ν) (f := g) (hf := hg)]
  rw [hmap]
  have hpi :
      (fun i => MeasureTheory.Measure.map (g i) (ν i))
        =
      (fun i : Fin (t + 1) =>
        removeCoordLaw { forward := forwardLossLaw μ p q, reverse := reverseLossLaw μ p q } i) := by
    funext i
    by_cases h0 : i.1 = 0
    · have hg0 : g i = forwardLossValue p q := by
        rw [show g i =
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
            rfl]
        simp [h0]
      have hν0 : ν i = densityMeasure μ p := by
        rw [show ν i = (if i.1 = 0 then densityMeasure μ p else densityMeasure μ q) by
          rfl]
        simp [h0]
      rw [hg0, hν0]
      simp [removeCoordLaw, forwardLossLaw, h0]
    · have hg1 : g i = forwardLossValue q p := by
        rw [show g i =
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p) by
            rfl]
        simp [h0]
      have hν1 : ν i = densityMeasure μ q := by
        rw [show ν i = (if i.1 = 0 then densityMeasure μ p else densityMeasure μ q) by
          rfl]
        simp [h0]
      rw [hg1, hν1]
      simp [removeCoordLaw, reverseLossLaw, h0]
  rw [hpi]

theorem addPrivacyLossLaw_eq_addTransform
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a) :
    MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p)) →
    (addSourceMeasure (t := t) μ q).map (addPrivacyLossValue p q)
      =
    addTransform (concretePLDPair μ p q).dual t := by
  intro hσadd
  let ν : Fin (t + 1) → MeasureTheory.Measure α := fun _ => densityMeasure μ q
  let g : ∀ i : Fin (t + 1), α → ℝ := fun _ => forwardLossValue q p
  let G : (Fin (t + 1) → α) → (Fin (t + 1) → ℝ) := fun x i => g i (x i)
  let F : (Fin (t + 1) → ℝ) → ℝ := addTransformValue
  have hg : ∀ i, AEMeasurable (g i) (ν i) := by
    intro i
    simpa [ν, g] using (measurable_forwardLossValue hq_meas hp_meas).aemeasurable
  have hG : Measurable G := by
    rw [measurable_pi_iff]
    intro i
    simpa [G, g, Function.comp_def] using
      (measurable_forwardLossValue hq_meas hp_meas).comp (measurable_pi_apply i)
  have hF : Measurable F := by
    simpa [F] using (measurable_addTransformValue (t := t))
  haveI : ∀ i : Fin (t + 1), MeasureTheory.SigmaFinite ((ν i).map (g i)) := by
    intro i
    simpa [ν, g] using hσadd
  have hpoint :
      addPrivacyLossValue p q = F ∘ G := by
    funext x
    dsimp [F, G, g]
    exact addPrivacyLossValue_eq_addTransformValue p q x
      (fun i => hp_pos (x i)) (fun i => hq_pos (x i))
  rw [addSourceMeasure, addTransform, concretePLDPair, PLDPair.dual, hpoint]
  change MeasureTheory.Measure.map (F ∘ G) (MeasureTheory.Measure.pi ν) =
    MeasureTheory.Measure.map F (MeasureTheory.Measure.pi (fun _ : Fin (t + 1) =>
      forwardLossLaw μ q p))
  rw [← MeasureTheory.Measure.map_map hF hG]
  rw [MeasureTheory.Measure.pi_map_pi (μ := ν) (f := g) (hf := hg)]
  rfl

theorem concreteRandomAllocationPLDPair_eq_transforms
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p))) :
    concreteRandomAllocationPLDPair (t := t) μ p q
      =
    randomAllocationTransforms (concretePLDPair μ p q) t := by
  cases hremove : concreteRandomAllocationPLDPair (t := t) μ p q with
  | mk forward reverse =>
    cases htransform : randomAllocationTransforms (concretePLDPair μ p q) t with
    | mk forward' reverse' =>
    injection hremove with hforward hreverse
    injection htransform with hforward' hreverse'
    have hfwd : forward = forward' := by
      rw [← hforward, ← hforward']
      exact removePrivacyLossLaw_eq_removeTransform_distinguished
        μ p q hp_meas hq_meas hp_pos hq_pos hσmap
    have hrev : reverse = reverse' := by
      rw [← hreverse, ← hreverse']
      exact addPrivacyLossLaw_eq_addTransform μ p q hp_meas hq_meas hp_pos hq_pos hσadd
    cases hfwd
    cases hrev
    rfl

theorem concreteRandomAllocationPLDPair_approxRealizationDominates_transforms
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p))) :
    (randomAllocationTransforms (concretePLDPair μ p q) t).ApproxRealizationDominates 0 0
      (concreteRandomAllocationPLDPair (t := t) μ p q) := by
  rw [concreteRandomAllocationPLDPair_eq_transforms
    μ p q hp_meas hq_meas hp_pos hq_pos hσmap hσadd]
  exact PLDPair.approxRealizationDominates_refl _

/--
Paper-facing remove-direction corollary packaging the exact theorem
`L_{\bar P_t || Q^t} = ψ_t^rem(L_{P||Q})` at the forward-law level.
-/
theorem concreteRandomAllocation_removeTransport_eq_transform
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p))) :
    (concreteRandomAllocationPLDPair (t := t) μ p q).forward
      =
    removeTransform (concretePLDPair μ p q) t := by
  simpa [randomAllocationTransforms] using congrArg PLDPair.forward
    (concreteRandomAllocationPLDPair_eq_transforms
      μ p q hp_meas hq_meas hp_pos hq_pos hσmap hσadd)

/--
Paper-facing add-direction corollary packaging the exact theorem
`L_{Q^t || \bar P_t} = ψ_t^add(L_{Q||P})` at the reverse-law level.
-/
theorem concreteRandomAllocation_addTransport_eq_transform
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p))) :
    (concreteRandomAllocationPLDPair (t := t) μ p q).reverse
      =
    addTransform (concretePLDPair μ p q).dual t := by
  simpa [randomAllocationTransforms] using congrArg PLDPair.reverse
    (concreteRandomAllocationPLDPair_eq_transforms
      μ p q hp_meas hq_meas hp_pos hq_pos hσmap hσadd)

theorem concreteRandomAllocation_profile_eq_transforms
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p)))
    (ε : ℝ) :
    (concreteRandomAllocationPLDPair (t := t) μ p q).profile ε
      =
    (randomAllocationTransforms (concretePLDPair μ p q) t).profile ε := by
  rw [concreteRandomAllocationPLDPair_eq_transforms
    μ p q hp_meas hq_meas hp_pos hq_pos hσmap hσadd]

/--
Remove-direction profile corollary exported from the exact random-allocation
law theorem. This is the privacy-facing wrapper for the forward side.
-/
theorem concreteRandomAllocation_removeTransport_profile_eq
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p)))
    (ε : ℝ) :
    (concreteRandomAllocationPLDPair (t := t) μ p q).profile ε
      =
    (randomAllocationTransforms (concretePLDPair μ p q) t).profile ε := by
  exact concreteRandomAllocation_profile_eq_transforms
    μ p q hp_meas hq_meas hp_pos hq_pos hσmap hσadd ε

/--
Add-direction profile corollary exported through dualization so the forward-law
profile API can still express the reverse-side random-allocation theorem.
-/
theorem concreteRandomAllocation_addTransport_profile_eq
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p)))
    (ε : ℝ) :
    (concreteRandomAllocationPLDPair (t := t) μ p q).dual.profile ε
      =
    (randomAllocationTransforms (concretePLDPair μ p q) t).dual.profile ε := by
  unfold PLDPair.profile
  exact congrArg (expHockeyStickLaw ε)
    (concreteRandomAllocation_addTransport_eq_transform
      μ p q hp_meas hq_meas hp_pos hq_pos hσmap hσadd)

theorem concreteRandomAllocation_addTransport_profile_le
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p)))
    (ε : ℝ) :
    (concreteRandomAllocationPLDPair (t := t) μ p q).dual.profile ε
      ≤
    (randomAllocationTransforms (concretePLDPair μ p q) t).dual.profile ε := by
  rw [concreteRandomAllocation_addTransport_profile_eq
    μ p q hp_meas hq_meas hp_pos hq_pos hσmap hσadd ε]

theorem concreteRandomAllocation_profile_le_transforms
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p)))
    (ε : ℝ) :
    (concreteRandomAllocationPLDPair (t := t) μ p q).profile ε
      ≤
    (randomAllocationTransforms (concretePLDPair μ p q) t).profile ε := by
  rw [concreteRandomAllocation_profile_eq_transforms
    μ p q hp_meas hq_meas hp_pos hq_pos hσmap hσadd ε]

/--
Remove-direction profile inequality corollary. This is stated as an inequality
to match the theorem surface used downstream, even though the current proof path
is exact.
-/
theorem concreteRandomAllocation_removeTransport_profile_le
    {α : Type} [MeasurableSpace α] {t : ℕ}
    (μ : MeasureTheory.Measure α) [MeasureTheory.SigmaFinite μ]
    (p q : α → ℝ)
    (hp_meas : Measurable p) (hq_meas : Measurable q)
    (hp_pos : ∀ a, 0 < p a) (hq_pos : ∀ a, 0 < q a)
    (hσmap : ∀ i : Fin (t + 1),
      MeasureTheory.SigmaFinite
        ((if i.1 = 0 then densityMeasure μ p else densityMeasure μ q).map
          (if i.1 = 0 then forwardLossValue p q else forwardLossValue q p)))
    (hσadd : MeasureTheory.SigmaFinite ((densityMeasure μ q).map (forwardLossValue q p)))
    (ε : ℝ) :
    (concreteRandomAllocationPLDPair (t := t) μ p q).profile ε
      ≤
    (randomAllocationTransforms (concretePLDPair μ p q) t).profile ε := by
  exact concreteRandomAllocation_profile_le_transforms
    μ p q hp_meas hq_meas hp_pos hq_pos hσmap hσadd ε

private def expHockeyStickIntegrand (ε : ℝ) (x : ℝ) : ℝ :=
  max (1 - Real.exp (ε - x)) 0

private lemma measurable_expHockeyStickIntegrand (ε : ℝ) :
    Measurable (expHockeyStickIntegrand ε) := by
  unfold expHockeyStickIntegrand
  fun_prop

private lemma expHockeyStickIntegrand_nonneg (ε x : ℝ) :
    0 ≤ expHockeyStickIntegrand ε x := by
  unfold expHockeyStickIntegrand
  exact le_max_right _ _

private lemma expHockeyStickIntegrand_le_one (ε x : ℝ) :
    expHockeyStickIntegrand ε x ≤ 1 := by
  unfold expHockeyStickIntegrand
  refine max_le ?_ (by norm_num)
  have hexp_nonneg : 0 ≤ Real.exp (ε - x) := by positivity
  linarith

private lemma integrable_expHockeyStickIntegrand (ε : ℝ) (μ : MeasureTheory.Measure ℝ)
    [MeasureTheory.IsFiniteMeasure μ] :
    MeasureTheory.Integrable (expHockeyStickIntegrand ε) μ := by
  refine MeasureTheory.Integrable.mono' (MeasureTheory.integrable_const (1 : ℝ))
    (measurable_expHockeyStickIntegrand ε).aestronglyMeasurable ?_
  filter_upwards with x
  have hnon : 0 ≤ expHockeyStickIntegrand ε x := expHockeyStickIntegrand_nonneg ε x
  have hone : expHockeyStickIntegrand ε x ≤ 1 := expHockeyStickIntegrand_le_one ε x
  simpa [Real.norm_eq_abs, abs_of_nonneg hnon] using hone

private lemma lt_expHockeyStickIntegrand_iff
    {ε t x : ℝ} (ht0 : 0 < t) (ht1 : t < 1) :
    t < expHockeyStickIntegrand ε x ↔ ε - Real.log (1 - t) < x := by
  have h1t : 0 < 1 - t := sub_pos.mpr ht1
  by_cases hA : 1 - Real.exp (ε - x) ≤ 0
  · have hmax : expHockeyStickIntegrand ε x = 0 := by
      unfold expHockeyStickIntegrand
      simp [max_eq_right hA]
    constructor
    · intro hx
      rw [hmax] at hx
      linarith
    · intro hx
      have hlog : ε - x < Real.log (1 - t) := by
        linarith
      have hexp_lt : Real.exp (ε - x) < 1 - t := by
        exact (Real.lt_log_iff_exp_lt h1t).1 hlog
      linarith
  · have hA' : 0 ≤ 1 - Real.exp (ε - x) := le_of_not_ge hA
    have hmax : expHockeyStickIntegrand ε x = 1 - Real.exp (ε - x) := by
      unfold expHockeyStickIntegrand
      simp [max_eq_left hA']
    constructor
    · intro hx
      rw [hmax] at hx
      have hexp_lt : Real.exp (ε - x) < 1 - t := by
        linarith
      have hlog : ε - x < Real.log (1 - t) := by
        exact (Real.lt_log_iff_exp_lt h1t).2 hexp_lt
      linarith
    · intro hx
      have hlog : ε - x < Real.log (1 - t) := by
        linarith
      have hexp_lt : Real.exp (ε - x) < 1 - t := by
        exact (Real.lt_log_iff_exp_lt h1t).1 hlog
      rw [hmax]
      linarith

private lemma expHockeyStickIntegrand_levelSet
    {ε t : ℝ} (ht0 : 0 < t) (ht1 : t < 1) :
    {x : ℝ | t < expHockeyStickIntegrand ε x} = Set.Ioi (ε - Real.log (1 - t)) := by
  ext x
  simp [lt_expHockeyStickIntegrand_iff ht0 ht1]

/--
Integral form of the law-level hockey-stick functional
`E[(1 - exp(ε - X))_+]`.

This is the generic measure-theoretic entry point for the quasi-convexity /
finite-mixture arguments used in the corrected random-allocation paper route.

Look first:
- `paper/random-allocation/main_RA.tex` lines 355-357
- `paper/random-allocation/main_RA.tex` lines 615-622
-/
theorem expHockeyStickLaw_eq_integral_integrand
    (ε : ℝ) (μ : MeasureTheory.Measure ℝ) :
    expHockeyStickLaw ε μ = ∫ x, expHockeyStickIntegrand ε x ∂μ := by
  unfold expHockeyStickLaw hockeyStickLaw
  apply MeasureTheory.integral_congr_ae
  exact Filter.Eventually.of_forall fun x => by
    unfold expHockeyStickIntegrand
    rw [show ε - x = ε + (-x) by ring, Real.exp_add]

/--
The hockey-stick functional is bounded by the total mass of its privacy-loss
law.

This public wrapper exposes the elementary fact that the hockey-stick
integrand lies in `[0, 1]`.  Downstream certificate consumers use it for loose
fully-formal smoke routes, while sharp routes should still supply dedicated
profile evidence.
-/
theorem expHockeyStickLaw_le_real_univ
    (ε : ℝ) (μ : MeasureTheory.Measure ℝ)
    [MeasureTheory.IsFiniteMeasure μ] :
    expHockeyStickLaw ε μ ≤ μ.real Set.univ := by
  rw [expHockeyStickLaw_eq_integral_integrand]
  have hle :
      (∫ x, expHockeyStickIntegrand ε x ∂μ)
        ≤ (∫ x, (1 : ℝ) ∂μ) := by
    exact MeasureTheory.integral_mono
      (integrable_expHockeyStickIntegrand ε μ)
      (MeasureTheory.integrable_const (1 : ℝ))
      (fun x => expHockeyStickIntegrand_le_one ε x)
  calc
    (∫ x, expHockeyStickIntegrand ε x ∂μ)
        ≤ (∫ x, (1 : ℝ) ∂μ) := hle
    _ = μ.real Set.univ := by simp

/-- A mass-at-most-one privacy-loss law has hockey-stick profile at most one. -/
theorem expHockeyStickLaw_le_one_of_real_univ_le_one
    (ε : ℝ) (μ : MeasureTheory.Measure ℝ)
    [MeasureTheory.IsFiniteMeasure μ]
    (hmass : μ.real Set.univ ≤ 1) :
    expHockeyStickLaw ε μ ≤ 1 :=
  le_trans (expHockeyStickLaw_le_real_univ ε μ) hmass

/-- The hockey-stick profile of a probability privacy-loss law is at most one. -/
theorem expHockeyStickLaw_le_one
    (ε : ℝ) (μ : MeasureTheory.Measure ℝ)
    [MeasureTheory.IsProbabilityMeasure μ] :
    expHockeyStickLaw ε μ ≤ 1 := by
  exact expHockeyStickLaw_le_one_of_real_univ_le_one ε μ (by simp)

/--
Forward PLD profile upper bound for probability privacy-loss laws.

This is intentionally conservative (`≤ 1`).  It is useful as a fully formal
certificate smoke route, not as a tight accountant.
-/
theorem PLDPair.profile_le_one_of_forward_probability
    (L : PLDPair) (ε : ℝ)
    [MeasureTheory.IsProbabilityMeasure L.forward] :
    L.profile ε ≤ 1 := by
  simpa [PLDPair.profile] using expHockeyStickLaw_le_one ε L.forward

/-- Two-sided conservative PLD profile bound for probability PLD laws. -/
theorem PLDPair.twoSidedProfile_le_one_of_probability
    (L : PLDPair) (ε : ℝ)
    [MeasureTheory.IsProbabilityMeasure L.forward]
    [MeasureTheory.IsProbabilityMeasure L.reverse] :
    L.twoSidedProfile ε ≤ 1 := by
  unfold PLDPair.twoSidedProfile
  haveI : MeasureTheory.IsProbabilityMeasure L.dual.forward := by
    simpa [PLDPair.dual] using
      (inferInstance : MeasureTheory.IsProbabilityMeasure L.reverse)
  exact max_le
    (PLDPair.profile_le_one_of_forward_probability L ε)
    (by
      simpa [PLDPair.dual] using
        PLDPair.profile_le_one_of_forward_probability L.dual ε)

/--
Uniform finite mixture of privacy-loss laws.

This packages the finite convex combination used by the corrected
random-allocation proof route: average finitely many branch laws with equal
weights.
-/
def uniformFiniteMixtureLaw {ι : Type} [Fintype ι]
    (μ : ι → MeasureTheory.Measure ℝ) : MeasureTheory.Measure ℝ :=
  ENNReal.ofReal ((Fintype.card ι : ℝ)⁻¹) • ∑ i, μ i

/--
The hockey-stick functional of a uniform finite mixture is the corresponding
average of the branch-wise hockey-stick functionals.

This is the finite-mixture equality behind the quasi-convexity step used in the
corrected random-allocation paper.
-/
theorem expHockeyStickLaw_uniformFiniteMixtureLaw_eq
    {ι : Type} [Fintype ι]
    (ε : ℝ) (μ : ι → MeasureTheory.Measure ℝ)
    [∀ i, MeasureTheory.IsFiniteMeasure (μ i)] :
    expHockeyStickLaw ε (uniformFiniteMixtureLaw μ)
      = (Fintype.card ι : ℝ)⁻¹ * ∑ i, expHockeyStickLaw ε (μ i) := by
  classical
  have hsum_measure : (∑ i, μ i) = (Finset.univ.sum μ) := by
    simp
  have hbranch :
      (∑ i, ∫ x, expHockeyStickIntegrand ε x ∂μ i)
        =
      ∑ i, expHockeyStickLaw ε (μ i) := by
    refine Finset.sum_congr rfl ?_
    intro i hi
    rw [expHockeyStickLaw_eq_integral_integrand]
  calc
    expHockeyStickLaw ε (uniformFiniteMixtureLaw μ)
      = ∫ x, expHockeyStickIntegrand ε x ∂(uniformFiniteMixtureLaw μ) := by
          rw [expHockeyStickLaw_eq_integral_integrand]
    _ = (ENNReal.ofReal ((Fintype.card ι : ℝ)⁻¹)).toReal
          * ∫ x, expHockeyStickIntegrand ε x ∂(∑ i, μ i) := by
          unfold uniformFiniteMixtureLaw
          rw [MeasureTheory.integral_smul_measure, smul_eq_mul]
    _ = (Fintype.card ι : ℝ)⁻¹
          * ∫ x, expHockeyStickIntegrand ε x ∂(∑ i, μ i) := by
          congr 1
          rw [ENNReal.toReal_ofReal]
          positivity
    _ = (Fintype.card ι : ℝ)⁻¹
          * ∑ i, ∫ x, expHockeyStickIntegrand ε x ∂μ i := by
          congr 1
          rw [hsum_measure]
          rw [MeasureTheory.integral_finset_sum_measure]
          intro i hi
          exact integrable_expHockeyStickIntegrand ε (μ i)
    _ = (Fintype.card ι : ℝ)⁻¹ * ∑ i, expHockeyStickLaw ε (μ i) := by
          rw [hbranch]

/--
Finite-mixture hockey-stick quasi-convexity: the hockey-stick functional of a
uniform finite mixture is bounded by the worst branch value.

This is the reusable finite-mixture upper-bound layer the corrected
random-allocation proof route needs.
-/
theorem expHockeyStickLaw_uniformFiniteMixtureLaw_le_max
    {ι : Type} [Fintype ι] [Nonempty ι]
    (ε : ℝ) (μ : ι → MeasureTheory.Measure ℝ)
    [∀ i, MeasureTheory.IsFiniteMeasure (μ i)] :
    expHockeyStickLaw ε (uniformFiniteMixtureLaw μ)
      ≤ (Finset.univ : Finset ι).sup' Finset.univ_nonempty fun i => expHockeyStickLaw ε (μ i) := by
  classical
  let M : ℝ := (Finset.univ : Finset ι).sup' Finset.univ_nonempty fun i => expHockeyStickLaw ε (μ i)
  have hsum_le : ∑ i, expHockeyStickLaw ε (μ i) ≤ (Fintype.card ι : ℝ) * M := by
    calc
      ∑ i, expHockeyStickLaw ε (μ i)
        ≤ ∑ _i : ι, M := by
            refine Finset.sum_le_sum ?_
            intro i hi
            exact Finset.le_sup' (s := (Finset.univ : Finset ι))
              (f := fun i => expHockeyStickLaw ε (μ i))
              (by simp)
      _ = (Fintype.card ι : ℕ) • M := by simp
      _ = (Fintype.card ι : ℝ) * M := by simp [nsmul_eq_mul]
  have hcard_pos : 0 < (Fintype.card ι : ℝ) := by
    exact_mod_cast Fintype.card_pos
  rw [expHockeyStickLaw_uniformFiniteMixtureLaw_eq]
  calc
    (Fintype.card ι : ℝ)⁻¹ * ∑ i, expHockeyStickLaw ε (μ i)
      ≤ (Fintype.card ι : ℝ)⁻¹ * ((Fintype.card ι : ℝ) * M) := by
          gcongr
    _ = M := by
          ring_nf
          field_simp [hcard_pos.ne']

/--
Uniform finite mixture of PLD pairs, averaging forward and reverse laws
branch-wise.
-/
def uniformFiniteMixturePair {ι : Type} [Fintype ι]
    (L : ι → PLDPair) : PLDPair :=
  ⟨uniformFiniteMixtureLaw (fun i => (L i).forward),
    uniformFiniteMixtureLaw (fun i => (L i).reverse)⟩

/--
Random-allocation-friendly corollary of the finite-mixture quasi-convexity
theorem.

Later partition-conditioned proofs can consume this profile-level theorem
directly instead of rebuilding the measure-theoretic finite-mixture argument.
-/
theorem uniformFiniteMixturePair_profile_le_max
    {ι : Type} [Fintype ι] [Nonempty ι]
    (ε : ℝ) (L : ι → PLDPair)
    [∀ i, MeasureTheory.IsFiniteMeasure (L i).forward] :
    (uniformFiniteMixturePair L).profile ε
      ≤ (Finset.univ : Finset ι).sup' Finset.univ_nonempty fun i => (L i).profile ε := by
  simpa [uniformFiniteMixturePair, PLDPair.profile]
    using expHockeyStickLaw_uniformFiniteMixtureLaw_le_max ε (fun i => (L i).forward)

/--
Tail-integrand form of the law-level hockey-stick functional
`E[(1 - exp(ε - X))_+]`.
-/
theorem expHockeyStickLaw_eq_integral_tail
    (ε : ℝ) (μ : MeasureTheory.Measure ℝ) [MeasureTheory.IsFiniteMeasure μ] :
    expHockeyStickLaw ε μ
      =
    ∫ t in Set.Ioi 0,
      if t < 1 then pldTailRight μ (ε - Real.log (1 - t)) else 0 := by
  have hbase :=
    MeasureTheory.Integrable.integral_eq_integral_meas_lt
      (integrable_expHockeyStickIntegrand ε μ)
      (Filter.Eventually.of_forall (expHockeyStickIntegrand_nonneg ε))
  unfold expHockeyStickLaw hockeyStickLaw
  have hrewrite :
      (∫ x, max (1 - Real.exp ε * Real.exp (-x)) 0 ∂μ)
        =
      ∫ x, expHockeyStickIntegrand ε x ∂μ := by
    apply MeasureTheory.integral_congr_ae
    exact Filter.Eventually.of_forall fun x => by
      unfold expHockeyStickIntegrand
      rw [show ε - x = ε + (-x) by ring, Real.exp_add]
  rw [hrewrite, hbase]
  apply MeasureTheory.integral_congr_ae
  filter_upwards [MeasureTheory.ae_restrict_mem measurableSet_Ioi] with t ht0
  by_cases ht1 : t < 1
  · rw [expHockeyStickIntegrand_levelSet ht0 ht1]
    simp [pldTailRight, ht1]
  · have hset : {x : ℝ | t < expHockeyStickIntegrand ε x} = ∅ := by
      ext x
      constructor
      · intro hx
        have hone : expHockeyStickIntegrand ε x ≤ 1 := expHockeyStickIntegrand_le_one ε x
        have h1le : 1 ≤ t := le_of_not_gt ht1
        exact False.elim ((not_lt_of_ge (le_trans hone h1le)) hx)
      · intro hx
        exact False.elim hx
    simp [hset, ht1]

theorem ApproxStochDominates.expHockeyStickLaw_le
    {upper lower : MeasureTheory.Measure ℝ}
    [MeasureTheory.IsFiniteMeasure upper] [MeasureTheory.IsFiniteMeasure lower]
    {α β ε : ℝ}
    (hdom : ApproxStochDominates α β upper lower)
    (hβ : 0 ≤ β) :
    expHockeyStickLaw ε lower ≤ expHockeyStickLaw (ε - α) upper + β := by
  let f : ℝ → ℝ := fun t => pldTailRight lower (ε - Real.log (1 - t))
  let g : ℝ → ℝ := fun t => pldTailRight upper ((ε - α) - Real.log (1 - t))
  have hf_meas : Measurable f := by
    dsimp [f]
    exact measurable_pldTailRight lower |>.comp <| by fun_prop
  have hg_meas : Measurable g := by
    dsimp [g]
    exact measurable_pldTailRight upper |>.comp <| by fun_prop
  have hf_nonneg : ∀ t, 0 ≤ f t := by
    intro t
    dsimp [f, pldTailRight]
    positivity
  have hg_nonneg : ∀ t, 0 ≤ g t := by
    intro t
    dsimp [g, pldTailRight]
    positivity
  have hf_bdd : ∀ t ∈ Set.Ioo (0 : ℝ) 1, ‖f t‖ ≤ lower.real Set.univ := by
    intro t ht
    have hle : f t ≤ lower.real Set.univ := by
      dsimp [f]
      exact MeasureTheory.measureReal_mono (Set.subset_univ _)
    simpa [Real.norm_eq_abs, abs_of_nonneg (hf_nonneg t)] using hle
  have hg_bdd : ∀ t ∈ Set.Ioo (0 : ℝ) 1, ‖g t‖ ≤ upper.real Set.univ := by
    intro t ht
    have hle : g t ≤ upper.real Set.univ := by
      dsimp [g]
      exact MeasureTheory.measureReal_mono (Set.subset_univ _)
    simpa [Real.norm_eq_abs, abs_of_nonneg (hg_nonneg t)] using hle
  have hf_int : MeasureTheory.IntegrableOn f (Set.Ioo (0 : ℝ) 1) MeasureTheory.volume := by
    refine MeasureTheory.Measure.integrableOn_of_bounded (μ := MeasureTheory.volume)
      (s := Set.Ioo (0 : ℝ) 1) (M := lower.real Set.univ) measure_Ioo_lt_top.ne
      hf_meas.aestronglyMeasurable ?_
    filter_upwards [MeasureTheory.ae_restrict_mem measurableSet_Ioo] with t ht
    exact hf_bdd t ht
  have hg_int : MeasureTheory.IntegrableOn g (Set.Ioo (0 : ℝ) 1) MeasureTheory.volume := by
    refine MeasureTheory.Measure.integrableOn_of_bounded (μ := MeasureTheory.volume)
      (s := Set.Ioo (0 : ℝ) 1) (M := upper.real Set.univ) measure_Ioo_lt_top.ne
      hg_meas.aestronglyMeasurable ?_
    filter_upwards [MeasureTheory.ae_restrict_mem measurableSet_Ioo] with t ht
    exact hg_bdd t ht
  have hconst_int : MeasureTheory.IntegrableOn (fun _ : ℝ => β) (Set.Ioo (0 : ℝ) 1)
      MeasureTheory.volume := by
    refine MeasureTheory.Measure.integrableOn_of_bounded (μ := MeasureTheory.volume)
      (s := Set.Ioo (0 : ℝ) 1) (M := β) measure_Ioo_lt_top.ne
      measurable_const.aestronglyMeasurable ?_
    filter_upwards [MeasureTheory.ae_restrict_mem measurableSet_Ioo] with t ht
    exact by
      simp [Real.norm_eq_abs, abs_of_nonneg hβ]
  have hlower_cut_aux :
      ∫ t in Set.Ioo (0 : ℝ) 1, (if t < 1 then f t else 0)
        =
      ∫ t in Set.Ioo (0 : ℝ) 1, f t := by
    apply MeasureTheory.integral_congr_ae
    filter_upwards [MeasureTheory.ae_restrict_mem measurableSet_Ioo] with t ht
    simp [ht.2]
  have hlower_cut :
      ∫ t in Set.Ioi (0 : ℝ), (if t < 1 then f t else 0)
        =
      ∫ t in Set.Ioo (0 : ℝ) 1, f t := by
    calc
      ∫ t in Set.Ioi (0 : ℝ), (if t < 1 then f t else 0)
          =
        ∫ t in Set.Ioo (0 : ℝ) 1, (if t < 1 then f t else 0) := by
          apply MeasureTheory.setIntegral_eq_of_subset_of_ae_diff_eq_zero
            nullMeasurableSet_Ioi Set.Ioo_subset_Ioi_self
          refine Filter.Eventually.of_forall ?_
          intro t ht
          have ht1 : ¬ t < 1 := by
            intro hlt
            exact ht.2 ⟨ht.1, hlt⟩
          simp [ht1]
      _ = ∫ t in Set.Ioo (0 : ℝ) 1, f t := hlower_cut_aux
  have hupper_cut_aux :
      ∫ t in Set.Ioo (0 : ℝ) 1, (if t < 1 then g t else 0)
        =
      ∫ t in Set.Ioo (0 : ℝ) 1, g t := by
    apply MeasureTheory.integral_congr_ae
    filter_upwards [MeasureTheory.ae_restrict_mem measurableSet_Ioo] with t ht
    simp [ht.2]
  have hupper_cut :
      ∫ t in Set.Ioi (0 : ℝ), (if t < 1 then g t else 0)
        =
      ∫ t in Set.Ioo (0 : ℝ) 1, g t := by
    calc
      ∫ t in Set.Ioi (0 : ℝ), (if t < 1 then g t else 0)
          =
        ∫ t in Set.Ioo (0 : ℝ) 1, (if t < 1 then g t else 0) := by
          apply MeasureTheory.setIntegral_eq_of_subset_of_ae_diff_eq_zero
            nullMeasurableSet_Ioi Set.Ioo_subset_Ioi_self
          refine Filter.Eventually.of_forall ?_
          intro t ht
          have ht1 : ¬ t < 1 := by
            intro hlt
            exact ht.2 ⟨ht.1, hlt⟩
          simp [ht1]
      _ = ∫ t in Set.Ioo (0 : ℝ) 1, g t := hupper_cut_aux
  have hslack_cut_aux :
      ∫ t in Set.Ioo (0 : ℝ) 1, (if t < 1 then β else 0)
        =
      ∫ t in Set.Ioo (0 : ℝ) 1, β := by
    apply MeasureTheory.integral_congr_ae
    filter_upwards [MeasureTheory.ae_restrict_mem measurableSet_Ioo] with t ht
    simp [ht.2]
  have hslack_cut :
      ∫ t in Set.Ioi (0 : ℝ), (if t < 1 then β else 0)
        =
      ∫ t in Set.Ioo (0 : ℝ) 1, β := by
    calc
      ∫ t in Set.Ioi (0 : ℝ), (if t < 1 then β else 0)
          =
        ∫ t in Set.Ioo (0 : ℝ) 1, (if t < 1 then β else 0) := by
          apply MeasureTheory.setIntegral_eq_of_subset_of_ae_diff_eq_zero
            nullMeasurableSet_Ioi Set.Ioo_subset_Ioi_self
          refine Filter.Eventually.of_forall ?_
          intro t ht
          have ht1 : ¬ t < 1 := by
            intro hlt
            exact ht.2 ⟨ht.1, hlt⟩
          simp [ht1]
      _ = ∫ t in Set.Ioo (0 : ℝ) 1, β := hslack_cut_aux
  have hmono :
      ∫ t in Set.Ioo (0 : ℝ) 1, f t
        ≤
      ∫ t in Set.Ioo (0 : ℝ) 1, (g t + β) := by
    refine MeasureTheory.integral_mono_ae hf_int ?_ ?_
    · exact hg_int.add hconst_int
    · filter_upwards [MeasureTheory.ae_restrict_mem measurableSet_Ioo] with t ht
      have := hdom (ε - Real.log (1 - t))
      simpa [f, g, sub_eq_add_neg, add_assoc, add_left_comm, add_comm] using this
  have hadd :
      ∫ t in Set.Ioo (0 : ℝ) 1, (g t + β)
        =
      (∫ t in Set.Ioo (0 : ℝ) 1, g t) + ∫ t in Set.Ioo (0 : ℝ) 1, β := by
    exact MeasureTheory.integral_add hg_int hconst_int
  have hconst :
      ∫ t in Set.Ioo (0 : ℝ) 1, β = β := by
    rw [MeasureTheory.setIntegral_const, smul_eq_mul]
    norm_num
  calc
    expHockeyStickLaw ε lower
      = ∫ t in Set.Ioi (0 : ℝ), (if t < 1 then f t else 0) := by
          simp [expHockeyStickLaw_eq_integral_tail, f]
    _ = ∫ t in Set.Ioo (0 : ℝ) 1, f t := hlower_cut
    _ ≤ ∫ t in Set.Ioo (0 : ℝ) 1, (g t + β) := hmono
    _ = (∫ t in Set.Ioo (0 : ℝ) 1, g t) + ∫ t in Set.Ioo (0 : ℝ) 1, β := hadd
    _ = (∫ t in Set.Ioo (0 : ℝ) 1, g t) + β := by rw [hconst]
    _ = (∫ t in Set.Ioi (0 : ℝ), (if t < 1 then g t else 0)) + β := by
      exact congrArg (fun z : ℝ => z + β) hupper_cut.symm
    _ = expHockeyStickLaw (ε - α) upper + β := by
      simp [expHockeyStickLaw_eq_integral_tail, g]

theorem PLDPair.ApproxRealizationDominates.profile_le
    {U L : PLDPair} {α β ε : ℝ}
    [MeasureTheory.IsFiniteMeasure U.forward] [MeasureTheory.IsFiniteMeasure L.forward]
    (h : U.ApproxRealizationDominates α β L)
    (hβ : 0 ≤ β) :
    L.profile ε ≤ U.profile (ε - α) + β := by
  exact ApproxStochDominates.expHockeyStickLaw_le h.1 hβ

end
end DP
end Mf
