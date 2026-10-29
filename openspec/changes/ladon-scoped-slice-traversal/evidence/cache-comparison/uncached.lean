import Lean
import NavierStokes.SmoothFamilyTorusInverse

open Lean Elab Command Meta

/- A bounded, read-only proposal for extracting an exact application from an
   imported theorem value.  Root owns compilation and runtime qualification. -/

-- LADON_EXPR_GRAPH

private structure ScopedOccurrence where
  expr : Expr
  lctx : LocalContext
  instances : LocalInstances
  scopePath : Array Nat
  nestedLocalIds : Array String
  deriving Inhabited

private partial def scopedOccurrences (root : Expr) (needle : Name)
    (maxNodes := 131072) (maxDepth := 64) : MetaM (Array ScopedOccurrence) := do
  let visited ← IO.mkRef 0
  let rec walk (e : Expr) (depth : Nat) (path : Array Nat)
      (isLeading : Bool) (nestedIds : Array String) : MetaM (Array ScopedOccurrence) := do
    if depth > maxDepth then throwError "expression depth exceeds {maxDepth}"
    let n ← visited.get
    if n >= maxNodes then throwError "expression node count exceeds {maxNodes}"
    visited.set (n + 1)
    let mut found := #[]
    if let .const name _ := e.getAppFn then
      if name == needle && e.isApp then
        found := #[{ expr := e, lctx := ← getLCtx, instances := ← getLocalInstances, scopePath := path, nestedLocalIds := nestedIds }]
    match e with
    | .app .. =>
      found := found ++ (← walk e.getAppFn (depth + 1) (path.push 0) false nestedIds)
      for i in [:e.getAppArgs.size] do
        found := found ++ (← walk e.getAppArgs[i]! (depth + 1) (path.push (i + 1)) false nestedIds)
    | .lam name type body bi =>
      found := found ++ (← walk type (depth + 1) (path.push 0) false nestedIds)
      let nested ← withLocalDecl name bi type fun fvar =>
        walk (body.instantiate1 fvar) (depth + 1) (path.push 1) isLeading
          (if isLeading then nestedIds else nestedIds.push (repr fvar.fvarId!.name).pretty)
      found := found ++ nested
    | .forallE name type body bi =>
      found := found ++ (← walk type (depth + 1) (path.push 0) false nestedIds)
      let nested ← withLocalDecl name bi type fun fvar =>
        walk (body.instantiate1 fvar) (depth + 1) (path.push 1) isLeading
          (if isLeading then nestedIds else nestedIds.push (repr fvar.fvarId!.name).pretty)
      found := found ++ nested
    | .letE name type value body _ =>
      found := found ++ (← walk type (depth + 1) (path.push 0) false nestedIds)
      found := found ++ (← walk value (depth + 1) (path.push 1) false nestedIds)
      let nested ← withLetDecl name type value fun fvar =>
        walk (body.instantiate1 fvar) (depth + 1) (path.push 2) isLeading
          (if isLeading then nestedIds else nestedIds.push (repr fvar.fvarId!.name).pretty)
      found := found ++ nested
    | .mdata _ body => found := found ++ (← walk body (depth + 1) (path.push 0) isLeading nestedIds)
    | .proj _ _ body => found := found ++ (← walk body (depth + 1) (path.push 0) false nestedIds)
    | .bvar _ | .fvar _ | .mvar _ | .sort _ | .const _ _ | .lit _ => pure ()
    return found
  let start ← IO.monoNanosNow
  let result ← walk root 0 #[] true #[]
  let elapsed := (← IO.monoNanosNow) - start
  logInfo m!"visited={(← visited.get)} occurrences={result.size} nanos={elapsed}"
  return result


run_meta do
  let info ← getConstInfo `NavierStokes.SmoothFamilyTorusInverse.norm_derivativeWord_inverse_le
  let _ ← scopedOccurrences (info.value! true) `NavierStokes.SmoothFourierData.coefficient_seminorm_bound
