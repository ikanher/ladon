import Mathlib.Analysis.InnerProductSpace.PiL2
import Mf.DP.OptionalSlotAdjacency

/-!
# Padded optional-record adjacency and slot queries

A one-slot deletion changes a present record to `none`; symmetric adjacency
allows either deletion direction. Absent slots contribute the zero query.
These shared definitions require no privacy transcript or sampler accountant.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD

/-- Padded datasets with a fixed public number of slots. -/
abbrev OneRecordDeletion {Record : Type} {n : ℕ}
    (D D' : Fin n → Option Record) : Prop :=
  Mf.DP.OneRecordDeletion D D'

abbrev OptionalRecordAdjacent {Record : Type} {n : ℕ}
    (D D' : Fin n → Option Record) : Prop :=
  Mf.DP.OptionalRecordAdjacent D D'

def slotGradient {Record : Type} {n d : ℕ}
    (g : Record → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (D : Fin n → Option Record) : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d) :=
  fun i => (D i).elim (fun _ => 0) g

end Mf.Optimization.PoissonClippedSGD
