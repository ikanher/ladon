import Mf.DP.Training.Common.AdaptiveTranscript
import Mf.DP.BSRGaussianCore
import Mf.DP.OptimalSubsamplingBISLR

namespace Mf
namespace DP
namespace Training
namespace KOutOfT

noncomputable section

/-- Exact fixed-cardinality schedule mass on subsets of `Fin T`. -/
def fixedCardinalityScheduleMass (T k : ℕ) : Finset (Fin T) → ℝ :=
  bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k

theorem fixedCardinalityScheduleMass_nonneg
    (T k : ℕ) (schedule : Finset (Fin T)) :
    0 ≤ fixedCardinalityScheduleMass T k schedule := by
  exact bisFixedCardUniformMass_nonneg _ _ _

theorem fixedCardinalityScheduleMass_sum_eq_one
    (T k : ℕ) (hk : k ≤ T) :
    ∑ schedule : Finset (Fin T), fixedCardinalityScheduleMass T k schedule = 1 := by
  simpa [fixedCardinalityScheduleMass] using
    bisFixedCardUniformMass_sum_univ_eq_one
      (Finset.univ : Finset (Fin T)) k (by simpa using hk)

theorem fixedCardinalityScheduleMass_eq_zero_of_card_ne
    (T k : ℕ) (schedule : Finset (Fin T))
    (hcard : schedule.card ≠ k) :
    fixedCardinalityScheduleMass T k schedule = 0 := by
  unfold fixedCardinalityScheduleMass bisFixedCardUniformMass
  rw [if_neg]
  intro hmem
  exact hcard (Finset.mem_powersetCard.mp hmem).2

/-- One independently sampled fixed-cardinality schedule for every user. -/
abbrev UserScheduleAssignment
    {Record : Type*} [DecidableEq Record]
    (dataset : UserDataset Record) (T : ℕ) :=
  (record : {r // r ∈ dataset}) → Finset (Fin T)

/-- Product mass of an independent per-user schedule assignment. -/
def userScheduleAssignmentMass
    {Record : Type*} [DecidableEq Record]
    (dataset : UserDataset Record) (T k : ℕ)
    (assignment : UserScheduleAssignment dataset T) : ℝ :=
  ∏ record : {r // r ∈ dataset},
    fixedCardinalityScheduleMass T k (assignment record)

theorem userScheduleAssignmentMass_nonneg
    {Record : Type*} [DecidableEq Record]
    (dataset : UserDataset Record) (T k : ℕ)
    (assignment : UserScheduleAssignment dataset T) :
    0 ≤ userScheduleAssignmentMass dataset T k assignment := by
  exact Finset.prod_nonneg fun _ _ => fixedCardinalityScheduleMass_nonneg T k _

theorem userScheduleAssignmentMass_sum_eq_one
    {Record : Type*} [DecidableEq Record]
    (dataset : UserDataset Record) (T k : ℕ) (hk : k ≤ T) :
    ∑ assignment : UserScheduleAssignment dataset T,
      userScheduleAssignmentMass dataset T k assignment = 1 := by
  unfold userScheduleAssignmentMass
  rw [← Fintype.prod_sum]
  simp [fixedCardinalityScheduleMass_sum_eq_one T k hk]

/-- Clipped aggregate restricted to users whose retained schedule contains `step`. -/
def scheduledClippedAggregate
    {Record : Type*} [DecidableEq Record]
    {T d : ℕ}
    (oracle : AdaptiveTrainingOracle Record T d)
    (clippingNorm : ℝ)
    (dataset : UserDataset Record)
    (assignment : UserScheduleAssignment dataset T)
    (step : Fin T)
    (history : AdaptiveReleaseHistory (Fin d → ℝ)) : Fin d → ℝ :=
  ∑ record : {r // r ∈ dataset},
    if step ∈ assignment record then
      l2VectorClip clippingNorm (oracle.query step history record.1)
    else 0

/--
Adaptive ideal-Gaussian transcript conditional on one hidden schedule assignment.

The assignment is fixed for the entire bind chain. The branch at `n < T` is
definitionally the public release step; calls beyond the horizon are inert.
-/
def transcriptGivenScheduleAssignment
    {Record : Type*} [DecidableEq Record]
    {T d : ℕ}
    (oracle : AdaptiveTrainingOracle Record T d)
    (clippingNorm sigma : ℝ)
    (dataset : UserDataset Record)
    (assignment : UserScheduleAssignment dataset T)
    (initialHistory : AdaptiveReleaseHistory (Fin d → ℝ)) :
    ℕ → MeasureTheory.Measure (AdaptiveReleaseHistory (Fin d → ℝ))
  | 0 => MeasureTheory.Measure.dirac initialHistory
  | n + 1 =>
      if hn : n < T then
        (transcriptGivenScheduleAssignment oracle clippingNorm sigma dataset
          assignment initialHistory n).bind fun history =>
            (bsrGaussianMeasure sigma
              (scheduledClippedAggregate oracle clippingNorm dataset assignment
                ⟨n, hn⟩ history)).map
              (fun release => writeRelease n (history, release))
      else
        transcriptGivenScheduleAssignment oracle clippingNorm sigma dataset
          assignment initialHistory n

/--
Dataset-level k-out-of-T training transcript.

Each user receives one independent exact uniform `k`-subset schedule. The
schedule is hidden and marginalized only after constructing the full adaptive
Gaussian transcript conditional on that retained assignment.
-/
def kOutOfTTrainingTranscript
    {Record : Type*} [DecidableEq Record]
    {T d : ℕ}
    (oracle : AdaptiveTrainingOracle Record T d)
    (k : ℕ)
    (clippingNorm sigma : ℝ)
    (initialHistory : AdaptiveReleaseHistory (Fin d → ℝ))
    (dataset : UserDataset Record) :
    MeasureTheory.Measure (AdaptiveReleaseHistory (Fin d → ℝ)) :=
  ∑ assignment : UserScheduleAssignment dataset T,
    ENNReal.ofReal (userScheduleAssignmentMass dataset T k assignment) •
      transcriptGivenScheduleAssignment oracle clippingNorm sigma dataset
        assignment initialHistory T

end

end KOutOfT
end Training
end DP
end Mf
