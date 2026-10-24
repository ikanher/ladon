import Lean

open Lean

private def nm (s : String) : Name := Name.mkSimple s

-- The maintained helper collector is inserted here by the Python test.
-- INSERT_HELPER_COLLECTOR

-- Previous tree-recursive implementation: name deduplication only.
private partial def collectConstantsOld (expression : Expr)
    (names : Std.HashSet Name := {}) : Std.HashSet Name :=
  let names := match expression with
    | .const name _ => names.insert name
    | _ => names
  match expression with
  | .forallE _ domain body _ =>
      collectConstantsOld body (collectConstantsOld domain names)
  | .lam _ domain body _ =>
      collectConstantsOld body (collectConstantsOld domain names)
  | .letE _ type value body _ =>
      collectConstantsOld body (collectConstantsOld value (collectConstantsOld type names))
  | .app function argument =>
      collectConstantsOld argument (collectConstantsOld function names)
  | .mdata _ body => collectConstantsOld body names
  | .proj _ _ body => collectConstantsOld body names
  | _ => names

private def sortedNew (expression : Expr) : Array Name :=
  (collectConstants expression).names.toArray.qsort Name.quickLt

private def sortedOld (expression : Expr) : Array Name :=
  (collectConstantsOld expression).toArray.qsort Name.quickLt

-- Exercises forallE, lam, letE type/value/body, app function/argument,
-- mdata body, proj body, repeated names, distinct equal Expr nodes, and a
-- shared expression node. Projection names are metadata, not expression
-- constants, and are omitted by both visitors.
private def smallFixture : Expr := Id.run do
  let repeatedA := Expr.const (nm "Repeated") []
  let repeatedB := Expr.const (nm "Repeated") []
  let shared := Expr.app (Expr.const (nm "SharedFn") [])
    (Expr.const (nm "SharedArg") [])
  let sharedTwice := Expr.app shared shared
  let projected := Expr.proj (nm "ProjectionOnly") 7
    (Expr.app (Expr.const (nm "AppFn") []) (Expr.const (nm "AppArg") []))
  let body := Expr.app projected sharedTwice
  let annotated := Expr.letE (nm "local") (Expr.const (nm "LetType") [])
    (Expr.app repeatedA repeatedB) (Expr.mdata MData.empty body) false
  let lambda := Expr.lam (nm "y") (Expr.const (nm "LambdaType") []) annotated .default
  return Expr.forallE (nm "x") (Expr.const (nm "ForallType") []) lambda .default

#guard (sortedNew smallFixture == sortedOld smallFixture)
#guard (collectConstants smallFixture).names.contains (nm "ForallType")
#guard (collectConstants smallFixture).names.contains (nm "LambdaType")
#guard (collectConstants smallFixture).names.contains (nm "LetType")
#guard (collectConstants smallFixture).names.contains (nm "Repeated")
#guard (collectConstants smallFixture).names.contains (nm "AppFn")
#guard (collectConstants smallFixture).names.contains (nm "AppArg")
#guard (collectConstants smallFixture).names.contains (nm "SharedFn")
#guard (collectConstants smallFixture).names.contains (nm "SharedArg")
#guard !(collectConstants smallFixture).names.contains (nm "ProjectionOnly")
#guard (sortedNew smallFixture).size == 8

-- Shared DAG with 2^60 tree paths but only 61 unique Expr nodes. This is
-- intentionally checked only by the memoized visitor; evaluating the old
-- visitor here would be impractical.
private def sharedDag : Nat → Expr
  | 0 => Expr.const (nm "DeepLeaf") []
  | n + 1 =>
      let child := sharedDag n
      Expr.app child child

#guard sortedNew (sharedDag 60) == #[nm "DeepLeaf"]
