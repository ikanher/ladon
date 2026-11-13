import Mf.DP.Profile.RationalStandardGaussianCDFIntervalConvergence
import Mf.DP.Profile.RationalExpIntervalConvergence

/-! # Effective finite Gaussian-expression enclosures

Finite products, sums and hinges used in a fixed reference partition are
expressions built from rational constants, exponentials and Gaussian CDFs at
rational arguments. This evaluator encloses each such expression and proves
that its rational endpoint widths tend to zero. The least precision search is
executable and terminates for every positive tolerance. Geometry is fixed
before this search; no bound independent of the number of cells is assumed.
-/

namespace Mf.DP
open Filter Topology

inductive RationalGaussianExpression where
  | constant (x : ℚ)
  | exponential (x : ℚ)
  | gaussianCDF (x : ℚ)
  | add (x y : RationalGaussianExpression)
  | sub (x y : RationalGaussianExpression)
  | mul (x y : RationalGaussianExpression)
  | max (x y : RationalGaussianExpression)
  deriving Repr

namespace RationalGaussianExpression

/-- Finite expression sums and products are evaluated without a real oracle. -/
def sum : List RationalGaussianExpression → RationalGaussianExpression
  | [] => .constant 0
  | x :: xs => .add x (sum xs)

def product : List RationalGaussianExpression → RationalGaussianExpression
  | [] => .constant 1
  | x :: xs => .mul x (product xs)

noncomputable def value : RationalGaussianExpression → ℝ
  | .constant x => x
  | .exponential x => Real.exp x
  | .gaussianCDF x => stdNormalCDFReal x
  | .add x y => x.value + y.value
  | .sub x y => x.value - y.value
  | .mul x y => x.value * y.value
  | .max x y => Max.max x.value y.value

@[simp] theorem value_sum (es : List RationalGaussianExpression) :
    (sum es).value = (es.map value).sum := by
  induction es with
  | nil => simp [sum, value]
  | cons e es ih => simp [sum, value, ih]

@[simp] theorem value_product (es : List RationalGaussianExpression) :
    (product es).value = (es.map value).prod := by
  induction es with
  | nil => simp [product, value]
  | cons e es ih => simp [product, value, ih]

def productFin {n : ℕ} (f : Fin n → RationalGaussianExpression) :
    RationalGaussianExpression := product (List.ofFn f)

@[simp] theorem value_productFin {n : ℕ} (f : Fin n → RationalGaussianExpression) :
    (productFin f).value = ∏ i, (f i).value := by
  simp [productFin, List.map_ofFn, List.prod_ofFn]

private theorem exists_expPower (x : ℚ) :
    ∃ p : ℕ, RationalExpInterval.PowerSufficient x p := by
  obtain ⟨p, hp⟩ := pow_unbounded_of_one_lt
    (RationalExpInterval.magnitude x) (by norm_num : (1 : ℚ) < 2)
  refine ⟨p, ?_⟩
  show RationalExpInterval.magnitude x ≤ ((2 ^ p : ℕ) : ℚ)
  simpa using hp.le

/-- Least sufficient dyadic exponential range, found by rational comparison. -/
def expPower (x : ℚ) : ℕ := Nat.find (exists_expPower x)

theorem expPower_sufficient (x : ℚ) :
    RationalExpInterval.PowerSufficient x (expPower x) :=
  Nat.find_spec (exists_expPower x)

/-- Exact outward evaluation at a single common precision. -/
def interval : RationalGaussianExpression → ℕ → RationalOutwardInterval
  | .constant x, _ => .point x
  | .exponential x, n => RationalExpInterval.interval x (expPower x) (n+1)
  | .gaussianCDF x, n => RationalStandardGaussianCDFInterval.coupledInterval x n
  | .add x y, n => (x.interval n).add (y.interval n)
  | .sub x y, n => (x.interval n).sub (y.interval n)
  | .mul x y, n => (x.interval n).mul (y.interval n)
  | .max x y, n => (x.interval n).max (y.interval n)

theorem interval_encloses (e : RationalGaussianExpression) (n : ℕ) :
    (e.interval n).Encloses e.value := by
  induction e with
  | constant x => exact RationalOutwardInterval.point_encloses x
  | exponential x =>
      exact RationalExpInterval.interval_encloses x (expPower x)
        (n+1) (expPower_sufficient x) (by omega)
  | gaussianCDF x => exact RationalStandardGaussianCDFInterval.coupledInterval_encloses x n
  | add x y hx hy => exact RationalOutwardInterval.add_encloses hx hy
  | sub x y hx hy => exact RationalOutwardInterval.sub_encloses hx hy
  | mul x y hx hy => exact RationalOutwardInterval.mul_encloses hx hy
  | max x y hx hy => exact RationalOutwardInterval.max_encloses hx hy

theorem interval_converges (e : RationalGaussianExpression) :
    RationalOutwardInterval.ConvergesTo e.interval e.value := by
  induction e with
  | constant x => exact RationalOutwardInterval.convergesTo_point x
  | exponential x =>
      apply RationalOutwardInterval.convergesTo_of_encloses_of_tendsto_width
      · exact Filter.Eventually.of_forall (fun n => interval_encloses (.exponential x) n)
      · exact (tendsto_add_atTop_iff_nat 1).2
          (RationalExpInterval.tendsto_interval_width_cast x (expPower x))
  | gaussianCDF x =>
      apply RationalOutwardInterval.convergesTo_of_encloses_of_tendsto_width
      · exact Filter.Eventually.of_forall (fun n => interval_encloses (.gaussianCDF x) n)
      · exact RationalStandardGaussianCDFInterval.tendsto_coupledInterval_width_cast x
  | add x y hx hy => exact hx.add hy
  | sub x y hx hy => exact hx.sub hy
  | mul x y hx hy => exact hx.mul hy
  | max x y hx hy =>
      constructor
      · simpa only [interval, RationalOutwardInterval.max, Rat.cast_max, value] using
          hx.1.max hy.1
      · simpa only [interval, RationalOutwardInterval.max, Rat.cast_max, value] using
          hx.2.max hy.2

theorem exists_width_le (e : RationalGaussianExpression) (tolerance : ℚ)
    (htol : 0 < tolerance) : ∃ n, (e.interval n).width ≤ tolerance := by
  have he := (interval_converges e).tendsto_width.eventually
    (Iio_mem_nhds (show (0 : ℝ) < tolerance by exact_mod_cast htol))
  obtain ⟨n, hn⟩ := he.exists
  exact ⟨n, by exact_mod_cast hn.le⟩

/-- Total terminating exact-rational search; invalid tolerance returns zero. -/
def firstPrecision (e : RationalGaussianExpression) (tolerance : ℚ) : ℕ :=
  if ht : 0 < tolerance then Nat.find (exists_width_le e tolerance ht) else 0

theorem firstPrecision_width_le (e : RationalGaussianExpression) (tolerance : ℚ)
    (ht : 0 < tolerance) :
    (e.interval (firstPrecision e tolerance)).width ≤ tolerance := by
  simp only [firstPrecision, dif_pos ht]
  exact Nat.find_spec (exists_width_le e tolerance ht)

/-- Outward bracket assembled from two expressions with distinct real values. -/
def bracket (lower upper : RationalGaussianExpression) (n : ℕ) : RationalOutwardInterval :=
  ⟨(lower.interval n).lower, (upper.interval n).upper⟩

theorem bracket_width_tendsto (lower upper : RationalGaussianExpression) :
    Tendsto (fun n => ((bracket lower upper n).width : ℝ)) atTop
      (𝓝 (upper.value - lower.value)) := by
  simpa only [bracket, RationalOutwardInterval.width, Rat.cast_sub] using
    (interval_converges upper).2.sub (interval_converges lower).1

theorem exists_bracket_width_le (lower upper : RationalGaussianExpression)
    (tolerance : ℚ) (hgap : upper.value - lower.value < tolerance) :
    ∃ n, (bracket lower upper n).width ≤ tolerance := by
  have he := (bracket_width_tendsto lower upper).eventually (Iio_mem_nhds hgap)
  obtain ⟨n, hn⟩ := he.exists
  exact ⟨n, by exact_mod_cast hn.le⟩

/-- Least precision that certifies the desired width after fixing geometry. -/
def bracketPrecision (lower upper : RationalGaussianExpression) (tolerance : ℚ)
    (hgap : upper.value - lower.value < tolerance) : ℕ :=
  Nat.find (exists_bracket_width_le lower upper tolerance hgap)

theorem bracketPrecision_sound (lower upper : RationalGaussianExpression)
    (tolerance : ℚ) (hgap : upper.value - lower.value < tolerance)
    {actual : ℝ} (hl : lower.value ≤ actual) (hu : actual ≤ upper.value) :
    let result := bracket lower upper (bracketPrecision lower upper tolerance hgap)
    result.Encloses actual ∧ result.width ≤ tolerance := by
  dsimp only
  constructor
  · exact ⟨(interval_encloses lower _).1.trans hl,
      hu.trans (interval_encloses upper _).2⟩
  · exact Nat.find_spec (exists_bracket_width_le lower upper tolerance hgap)

end RationalGaussianExpression
end Mf.DP
