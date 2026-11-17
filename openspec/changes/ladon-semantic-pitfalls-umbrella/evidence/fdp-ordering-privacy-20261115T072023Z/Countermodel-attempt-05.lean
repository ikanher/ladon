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
  intro x
  unfold releaseTrue
  split_ifs <;> norm_num

theorem total_mass_one (x : Input) : eventMass (releaseTrue x) (true,true) = 1 := by
  simp [eventMass]

-- Both directions and ALL events are covered by finite quantification.
theorem base_pure_dp : ∀ x y : Input, Adjacent x y →
    ∀ event : Event, eventMass (releaseTrue x) event ≤ 2 * eventMass (releaseTrue y) event := by
  rintro ⟨a,b⟩ ⟨c,d⟩ h ⟨u,v⟩
  change (a = c ∧ b ≠ d) ∨ (a ≠ c ∧ b = d) at h
  rcases h with ⟨rfl, h⟩ | ⟨h, rfl⟩
  · cases u <;> cases v <;> simp only [eventMass, releaseTrue, Prod.fst, Prod.snd]
    all_goals split_ifs <;> norm_num at *
  · cases u <;> cases v <;> simp only [eventMass, releaseTrue, Prod.fst, Prod.snd]
    all_goals split_ifs <;> norm_num at *

-- Original privacy also implies the pure-DP curve for EVERY real randomized test.
theorem base_testing_bound (x y : Input) (h : Adjacent x y)
    (u v : ℝ) (hu0 : 0 ≤ u) (hu1 : u ≤ 1) (hv0 : 0 ≤ v) (hv1 : v ≤ 1) :
    max 0 (max (1-2*((releaseTrue x : ℝ)*u + (1-(releaseTrue x : ℝ))*v))
      ((1-((releaseTrue x : ℝ)*u + (1-(releaseTrue x : ℝ))*v))/2)) ≤
    1-((releaseTrue y : ℝ)*u + (1-(releaseTrue y : ℝ))*v) := by
  have hrev : Adjacent y x := by
    rcases h with ⟨h1,h2⟩ | ⟨h1,h2⟩
    · exact Or.inl ⟨h1.symm, Ne.symm h2⟩
    · exact Or.inr ⟨Ne.symm h1, h2.symm⟩
  have xy1 : (releaseTrue x : ℝ) ≤ 2*(releaseTrue y : ℝ) := by
    exact_mod_cast (show releaseTrue x ≤ 2*releaseTrue y by
      simpa [eventMass] using base_pure_dp x y h (true,false))
  have xy0 : 1-(releaseTrue x : ℝ) ≤ 2*(1-(releaseTrue y : ℝ)) := by
    exact_mod_cast (show 1-releaseTrue x ≤ 2*(1-releaseTrue y) by
      simpa [eventMass] using base_pure_dp x y h (false,true))
  have yx1 : (releaseTrue y : ℝ) ≤ 2*(releaseTrue x : ℝ) := by
    exact_mod_cast (show releaseTrue y ≤ 2*releaseTrue x by
      simpa [eventMass] using base_pure_dp y x hrev (true,false))
  have yx0 : 1-(releaseTrue y : ℝ) ≤ 2*(1-(releaseTrue x : ℝ)) := by
    exact_mod_cast (show 1-releaseTrue y ≤ 2*(1-releaseTrue x) by
      simpa [eventMass] using base_pure_dp y x hrev (false,true))
  have hy0 : (0:ℝ) ≤ releaseTrue y := by exact_mod_cast (normalized y).1
  have hy1 : (releaseTrue y : ℝ) ≤ 1 := by exact_mod_cast (normalized y).2
  apply max_le
  · nlinarith [mul_nonneg hy0 (sub_nonneg.mpr hu1),
      mul_nonneg (sub_nonneg.mpr hy1) (sub_nonneg.mpr hv1)]
  · apply max_le
    · nlinarith [mul_le_mul_of_nonneg_right yx1 hu0,
        mul_le_mul_of_nonneg_right yx0 hv0]
    · nlinarith [mul_le_mul_of_nonneg_right xy1 (sub_nonneg.mpr hu1),
        mul_le_mul_of_nonneg_right xy0 (sub_nonneg.mpr hv1)]

def D : Fin 3 → Fin 4 := fun i => if i = 0 then 0 else if i = 1 then 1 else 2
def D' : Fin 3 → Fin 4 := fun i => if i = 0 then 3 else if i = 1 then 1 else 2

theorem source_neighbors : D 0 ≠ D' 0 ∧ ∀ i : Fin 3, i ≠ 0 → D i = D' i := by
  unfold D D'
  decide

-- Three equally likely exact-size subsets; only the Bernoulli output is released.
def sampledTrue (d : Fin 3 → Fin 4) : ℚ :=
  (releaseTrue (d 0,d 1) + releaseTrue (d 0,d 2) + releaseTrue (d 1,d 2)) / 3

theorem sampled_values : sampledTrue D = 7/18 ∧ sampledTrue D' = 2/9 := by
  norm_num [sampledTrue,releaseTrue,D,D', Fin.ext_iff]

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

#print base_testing_bound
#print axioms base_testing_bound
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
