import LadonRealBoundBinding
import Mathlib.Analysis.Calculus.ContDiff.FTaylorSeries

namespace Ladon.RealBound
universe u v w

/-- Full joint real Frechet derivative, measured in its multilinear operator norm. -/
noncomputable def jointDerivativeMeasure {P : Type u} {Y : Type v} {Z : Type w}
    [NormedAddCommGroup P] [NormedSpace Real P]
    [NormedAddCommGroup Y] [NormedSpace Real Y]
    [NormedAddCommGroup Z] [NormedSpace Real Z]
    (f : P × Y → Z) (p : P) (y : Y) (j : Nat) : Real :=
  ‖iteratedFDeriv Real j f (p, y)‖

end Ladon.RealBound

namespace Ladon.RealBoundBinding
open Lean Meta Elab Term

private def derivativeMeasure : BoundMeasureBuilder := fun xs source => do
  let sourceType ← whnf (← inferType source)
  let .forallE _ objectType _ _ := sourceType
    | throwError "derivative predicate has no object argument"
  let .forallE _ domain codomain _ ← whnf objectType
    | throwError "derivative object must be a function on a product"
  if codomain.hasLooseBVars then
    throwError "dependent derivative codomains are unsupported"
  let domain ← whnf domain
  let factors := domain.getAppArgs
  if !domain.getAppFn.isConstOf ``Prod || factors.size != 2 then
    throwError "joint derivative domain must be a product"
  -- Use source-owned local instances; missing instances fail without adding assumptions.
  withNewLocalInstances xs 0 do
    mkAppOptM ``Ladon.RealBound.jointDerivativeMeasure
      #[some factors[0]!, some factors[1]!, some codomain,
        none, none, none, none, none, none]

elab "ladon_derivative_admission% " target:str expected:str : term => do
  let expected ← match Json.parse expected.getString with
    | .ok value => pure value
    | .error _ => throwError "invalid expected derivative expression"
  observedBoundLaw target.getString.toName expected derivativeMeasure

end Ladon.RealBoundBinding
