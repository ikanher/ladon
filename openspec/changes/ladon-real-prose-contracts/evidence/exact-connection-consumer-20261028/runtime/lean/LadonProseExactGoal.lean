import Lean
import Lean.Meta.Transform

/-! Additive exact local-owner target construction. This is not admission.
    Source/import custody and independent kernel proof replay are owned by the
    capture/completion caller; original-to-copy mapping remains its obligation. -/
namespace Ladon.ProseExactGoal
open Lean Meta Elab Term

private def maxNodes : Nat := 100000
private def maxDepth : Nat := 128
private def maxRequestBytes : Nat := 8 * 1024 * 1024

private def binderInfoName : BinderInfo → String
  | .default => "explicit"
  | .implicit => "implicit"
  | .strictImplicit => "strict-implicit"
  | .instImplicit => "instance-implicit"

private abbrev RenderM := ExceptT String (StateM Nat)

private def renderNode (depth : Nat) (value : Json) : RenderM Json := do
  if depth > maxDepth then throw "expression depth exceeds 128"
  let seen ← get
  if seen >= maxNodes then throw "expression node count exceeds 100000"
  set (seen + 1)
  return value

private partial def exprJson (depth : Nat) (expression : Expr) : RenderM Json := do
  let _ ← renderNode depth Json.null
  match expression with
    | .bvar index => pure <| Json.mkObj [("bvar", toJson index)]
    | .fvar id => pure <| Json.mkObj [("fvar", toJson id.name)]
    | .mvar id => pure <| Json.mkObj [("mvar", toJson id.name)]
    | .sort level => pure <| Json.mkObj [("sort", toJson (toString level))]
    | .const name levels => pure <| Json.mkObj [
        ("const", toJson name), ("levels", toJson (levels.map toString))]
    | .app function argument => do
        if depth > maxDepth then throw "expression depth exceeds 128"
        let f ← exprJson (depth + 1) function
        let a ← exprJson (depth + 1) argument
        pure <| Json.mkObj [("app", Json.arr #[f, a])]
    | .lam name type body info => do
        let t ← exprJson (depth + 1) type
        let b ← exprJson (depth + 1) body
        pure <| Json.mkObj [("lam", Json.mkObj [
          ("name", toJson "_"), ("type", t), ("body", b),
          ("binderInfo", toJson (binderInfoName info))])]
    | .forallE name type body info => do
        let t ← exprJson (depth + 1) type
        let b ← exprJson (depth + 1) body
        pure <| Json.mkObj [("forallE", Json.mkObj [
          ("name", toJson "_"), ("type", t), ("body", b),
          ("binderInfo", toJson (binderInfoName info))])]
    | .letE name type value body nondep => do
        let t ← exprJson (depth + 1) type
        let v ← exprJson (depth + 1) value
        let b ← exprJson (depth + 1) body
        pure <| Json.mkObj [("letE", Json.mkObj [
          ("name", toJson "_"), ("type", t), ("value", v), ("body", b),
          ("nondep", toJson nondep)])]
    | .lit (.natVal value) => pure <| Json.mkObj [("nat", toJson value)]
    | .lit (.strVal value) => pure <| Json.mkObj [("string", toJson value)]
    | .mdata _ body => exprJson (depth + 1) body
    | .proj typeName index value => do
        let v ← exprJson (depth + 1) value
        pure <| Json.mkObj [("proj", Json.mkObj [
          ("typeName", toJson typeName), ("index", toJson index), ("structure", v)])]

private def render (e : Expr) : MetaM Json := do
  match ((exprJson 0 e).run 0).1 with
  | .ok j =>
    if j.compress.utf8ByteSize > maxRequestBytes then
      throwError "exact goal expression exceeds 8 MiB"
    return j
  | .error msg => throwError "{msg}"

private def field (j : Json) (key : String) : MetaM Json :=
  match j.getObjVal? key with
  | .ok value => pure value
  | .error _ => throwError "missing exact goal field: {key}"

private def stringField (j : Json) (key : String) : MetaM String :=
  match j.getObjValAs? String key with
  | .ok value => pure value
  | .error _ => throwError "invalid exact goal string: {key}"

private def closed (j : Json) (keys : List String) : MetaM Unit := do
  let fields ← match j.getObj? with
    | .ok fields => pure fields.toArray
    | .error _ => throwError "exact goal object required"
  if fields.size != keys.length || fields.any (fun (key, _) => !keys.contains key) then
    throwError "unknown or missing exact goal fields"

private def rangeJson (ranges : DeclarationRanges) : Json := Json.mkObj [
  ("startLine",toJson ranges.range.pos.line),
  ("startColumn",toJson ranges.range.pos.column),
  ("endLine",toJson ranges.range.endPos.line),
  ("endColumn",toJson ranges.range.endPos.column),
  ("selectionStartLine",toJson ranges.selectionRange.pos.line),
  ("selectionStartColumn",toJson ranges.selectionRange.pos.column),
  ("selectionEndLine",toJson ranges.selectionRange.endPos.line),
  ("selectionEndColumn",toJson ranges.selectionRange.endPos.column)]

private def ensureClosed (e : Expr) : MetaM Unit := do
  if e.hasFVar || e.hasLooseBVars || e.hasExprMVar || e.hasLevelMVar then
    throwError "exact goal owner expression is not closed"

private def owner (row : Json) (kind : String) : MetaM (Name × Expr) := do
  closed row ["name", "kind", "expression", "range"]
  unless (← stringField row "kind") == kind do throwError "exact goal owner kind mismatch"
  let text ← stringField row "name"
  let name := text.toName
  if text.isEmpty || name.toString != text then throwError "invalid exact declaration name"
  let env ← getEnv
  if (env.getModuleIdxFor? name).isSome then throwError "exact goal owner must be local to copied source"
  let ranges ← match ← findDeclarationRanges? name with
    | some ranges => pure ranges
    | none => throwError "exact goal owner lacks source declaration range"
  unless rangeJson ranges == (← field row "range") do
    throwError "exact goal owner source range mismatch"
  let info ← getConstInfo name
  let expression ← match kind, info with
    | "theorem-type", .thmInfo data => zetaReduce (← instantiateMVars data.type)
    | "proposition-value", .defnInfo data => do
      unless ← isDefEq data.type (mkSort .zero) do
        throwError "exact goal definition must be declared Prop"
      pure data.value
    | _, _ => throwError "exact goal declaration kind mismatch"
  ensureClosed expression
  unless ← isProp expression do throwError "exact goal owner does not contain a proposition"
  unless (← render expression) == (← field row "expression") do
    throwError "exact goal owner full expression mismatch"
  return (name, expression)

/-- Build one live target without printing/reparsing or renaming its binders.
    The formal theorem remains a premise, and every supplied premise is retained. -/
def constructGoal (text : String) : MetaM Expr := do
  if text.utf8ByteSize > maxRequestBytes then throwError "exact goal request exceeds 8 MiB"
  let parsed ← match Json.parse text with
    | .ok j => pure j
    | .error _ => throwError "invalid exact goal request JSON"
  -- Canonical encoding also excludes duplicate JSON keys before owner lookup.
  if parsed.compress != text then throwError "exact goal request must use canonical JSON"
  closed parsed ["schema", "module", "formal", "authored", "premises"]
  unless (← stringField parsed "schema") == "ladon-prose-exact-goal-v1" do
    throwError "unknown exact goal schema"
  unless (← stringField parsed "module") == (← getEnv).header.mainModule.toString do
    throwError "exact goal copied module mismatch"
  let premises ← match (← field parsed "premises").getArr? with
    | .ok rows => pure rows
    | .error _ => throwError "exact goal premises must be ordered array"
  if premises.size > 16 then throwError "exact goal exceeds 16 premises"
  let (formalName, formal) ← owner (← field parsed "formal") "theorem-type"
  let (authoredName, authored) ← owner (← field parsed "authored") "proposition-value"
  if formalName == authoredName then throwError "duplicate exact goal owner"
  let mut names := #[formalName, authoredName]
  let mut types : Array Expr := #[]
  for row in premises do
    let (name, type) ← owner row "proposition-value"
    if names.contains name then throwError "duplicate exact goal owner"
    names := names.push name
    types := types.push type
  let mut result := authored
  for index in [:types.size] do
    let i := types.size - 1 - index
    result := mkForall (Name.mkSimple s!"premise{i}") .default types[i]! result
  result := mkForall (Name.mkSimple "formal") .default formal result
  ensureClosed result
  -- Enforce the same total target renderer bound, not only per-owner bounds.
  let _ ← render result
  return result

elab "ladon_prose_exact_goal% " request:str : term =>
  constructGoal request.getString

end Ladon.ProseExactGoal
