import Mf.DP.ClassicalEventDPSubsetReplacementCounting

namespace InheritedOrderCountermodel
abbrev Input := Fin 4 × Fin 4
abbrev Event := Bool × Bool

-- Bernoulli probability of releasing true; the mechanism sees an ordered pair.
def releaseTrue (x : Input) : ℚ :=
  if x.1 = 0 then (if x.2 = 1 then 2/3 else 1/3)
  else (if x.2 = 1 then 1/3 else 1/6)

def Adjacent (x y : Input) : Prop :=
  (x.1 = y.1 ∧ x.2 ≠ y.2) ∨ (x.1 ≠ y.1 ∧ x.2 = y.2)

-- All events of the binary output space: membership of true, then false.
def eventMass (p : ℚ) (event : Event) : ℚ :=
  (if event.1 then p else 0) + (if event.2 then 1-p else 0)

theorem normalized : ∀ x : Input, 0 ≤ releaseTrue x ∧ releaseTrue x ≤ 1 := by
  unfold releaseTrue
  decide

theorem total_mass_one (x : Input) : eventMass (releaseTrue x) (true,true) = 1 := by
  simp [eventMass]

-- Both directions and ALL events are covered by finite quantification.
theorem base_pure_dp : ∀ x y : Input, Adjacent x y →
    ∀ event : Event, eventMass (releaseTrue x) event ≤ 2 * eventMass (releaseTrue y) event := by
  unfold Adjacent eventMass releaseTrue
  decide

def D : Fin 3 → Fin 4 := ![0,1,2]
def D' : Fin 3 → Fin 4 := ![3,1,2]

theorem source_neighbors : D 0 ≠ D' 0 ∧ ∀ i : Fin 3, i ≠ 0 → D i = D' i := by
  unfold D D'
  decide

-- Three equally likely exact-size subsets; only the Bernoulli output is released.
def sampledTrue (d : Fin 3 → Fin 4) : ℚ :=
  (releaseTrue (d 0,d 1) + releaseTrue (d 0,d 2) + releaseTrue (d 1,d 2)) / 3

theorem sampled_values : sampledTrue D = 7/18 ∧ sampledTrue D' = 2/9 := by
  norm_num [sampledTrue,releaseTrue,D,D']

theorem sampled_is_probability (d : Fin 3 → Fin 4) :
    0 ≤ sampledTrue d ∧ sampledTrue d ≤ 1 := by
  have h01 := normalized (d 0,d 1)
  have h02 := normalized (d 0,d 2)
  have h12 := normalized (d 1,d 2)
  dsimp [sampledTrue]
  constructor <;> linarith

theorem amplification_failure :
    eventMass (sampledTrue D) (true,false) >
      (5/3 : ℚ) * eventMass (sampledTrue D') (true,false) := by
  obtain ⟨h,h'⟩ := sampled_values
  norm_num [eventMass,h,h']

theorem exact_gap : sampledTrue D - (5/3 : ℚ)*sampledTrue D' = 1/54 := by
  obtain ⟨h,h'⟩ := sampled_values
  norm_num [h,h']

-- Source pure-DP testing curve and the source's displayed sampled curve formula.
def pureTradeoff (ratio alpha : ℚ) : ℚ :=
  max 0 (max (1-ratio*alpha) ((1-alpha)/ratio))
def sourceSampledCurve (alpha : ℚ) : ℚ :=
  max (pureTradeoff (5/3) alpha) (1-(2/3)*(2-1)/(2+1)-alpha)

theorem testing_bound_failure :
    1 - sampledTrue D < sourceSampledCurve (sampledTrue D') := by
  obtain ⟨h,h'⟩ := sampled_values
  norm_num [sourceSampledCurve,pureTradeoff,h,h']

#print base_pure_dp
#print amplification_failure
#print exact_gap
#print testing_bound_failure
#print axioms normalized
#print axioms total_mass_one
#print axioms base_pure_dp
#print axioms source_neighbors
#print axioms sampled_values
#print axioms sampled_is_probability
#print axioms amplification_failure
#print axioms exact_gap
#print axioms testing_bound_failure
end InheritedOrderCountermodel
