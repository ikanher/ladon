import Lean
import Lean.Elab.Frontend

open Lean

private def helperVersion := "ladon-prose-proposition-helper-v1"
private def schema := "ladon-prose-proposition-worker-v1"
private def maxNodes : Nat := 100000
private def maxDepth : Nat := 128
private def maxOutputBytes : Nat := 8 * 1024 * 1024

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

private partial def exprJson (depth : Nat) : Expr → RenderM Json
  | .bvar index => renderNode depth <| Json.mkObj [("bvar", toJson index)]
  | .fvar id => renderNode depth <| Json.mkObj [("fvar", toJson id.name)]
  | .mvar id => renderNode depth <| Json.mkObj [("mvar", toJson id.name)]
  | .sort level => renderNode depth <| Json.mkObj [("sort", toJson (toString level))]
  | .const name levels => renderNode depth <| Json.mkObj [
      ("const", toJson name), ("levels", toJson (levels.map toString))]
  | .app function argument => do
      if depth > maxDepth then throw "expression depth exceeds 128"
      let f ← exprJson (depth + 1) function
      let a ← exprJson (depth + 1) argument
      renderNode depth <| Json.mkObj [("app", Json.arr #[f, a])]
  | .lam name type body info => do
      let t ← exprJson (depth + 1) type
      let b ← exprJson (depth + 1) body
      renderNode depth <| Json.mkObj [("lam", Json.mkObj [
        ("name", toJson name), ("type", t), ("body", b),
        ("binderInfo", toJson (binderInfoName info))])]
  | .forallE name type body info => do
      let t ← exprJson (depth + 1) type
      let b ← exprJson (depth + 1) body
      renderNode depth <| Json.mkObj [("forallE", Json.mkObj [
        ("name", toJson name), ("type", t), ("body", b),
        ("binderInfo", toJson (binderInfoName info))])]
  | .letE name type value body nondep => do
      let t ← exprJson (depth + 1) type
      let v ← exprJson (depth + 1) value
      let b ← exprJson (depth + 1) body
      renderNode depth <| Json.mkObj [("letE", Json.mkObj [
        ("name", toJson name), ("type", t), ("value", v), ("body", b),
        ("nondep", toJson nondep)])]
  | .lit (.natVal value) => renderNode depth <| Json.mkObj [("nat", toJson value)]
  | .lit (.strVal value) => renderNode depth <| Json.mkObj [("string", toJson value)]
  | .mdata _ body => exprJson (depth + 1) body
  | .proj typeName index value => do
      let v ← exprJson (depth + 1) value
      renderNode depth <| Json.mkObj [("proj", Json.mkObj [
        ("typeName", toJson typeName), ("index", toJson index), ("structure", v)])]

private def common (module file target status : String) : List (String × Json) := [
  ("schema", toJson schema), ("helperVersion", toJson helperVersion),
  ("module", toJson module), ("file", toJson file), ("target", toJson target),
  ("leanVersion", toJson Lean.versionString), ("status", toJson status)]

private def emitJson (destination : String) (record : Json) : IO Unit := do
  let encoded := record.compress
  if encoded.utf8ByteSize > maxOutputBytes then
    throw <| IO.userError "proposition observation exceeds 8 MiB output bound"
  IO.FS.writeFile destination encoded

private def emitFailure (destination module file target status reason : String) : IO Unit :=
  emitJson destination <| Json.mkObj (common module file target status ++
    [("reason", toJson reason)])

private def runMeta {α : Type} (env : Environment) (file : String)
    (fileMap : FileMap) (action : MetaM α) : IO α := do
  let (value, _, _) ← action.toIO
    { fileName := file, fileMap, options := {} }
    { env }
  return value

private def runHelper (module file snapshot target destination : String) : IO UInt32 := do
  let contents ← IO.FS.readFile snapshot
  unsafe Lean.enableInitializersExecution
  let options := Elab.async.set ({} : Options) false
  let env? ← Elab.runFrontend contents options file module.toName
  match env? with
  | none =>
      emitFailure destination module file target "elaboration-failed"
        "Lean frontend did not produce an environment"
      return 0
  | some env =>
      if env.header.mainModule != module.toName then
        emitFailure destination module file target "not-found"
          "frontend environment main module differs from request"
        return 0
      let targetName := target.toName
      let ranges? ← runMeta env file contents.toFileMap (findDeclarationRanges? targetName)
      let sourceModuleOwned := (env.getModuleIdxFor? targetName).isNone
      match env.find? targetName, ranges? with
      | some (.defnInfo info), some ranges =>
          let lineCount := (contents.splitOn "\n").length
          let range := ranges.range
          let selection := ranges.selectionRange
          let rangeInSource := range.pos.line > 0 && range.endPos.line <= lineCount
          if !sourceModuleOwned || !rangeInSource then
            emitFailure destination module file target "not-found"
              "target is imported or has no declaration range in the selected source"
            return 0
          let (typeIsProp, bodyIsProp) ← runMeta env file contents.toFileMap do
            let declaredIsProp ← isDefEq info.type (mkSort Level.zero)
            let bodyType ← inferType info.value
            let bodyIsProp ← isDefEq bodyType (mkSort Level.zero)
            pure (declaredIsProp, bodyIsProp)
          if !typeIsProp || !bodyIsProp then
            emitFailure destination module file target "not-a-proposition"
              "target must be a local definition declared as Prop with a proposition body"
            return 0
          let rendered := (exprJson 0 info.value).run 0
          match rendered.1 with
          | .error reason =>
              emitFailure destination module file target "render-limit" reason
              return 0
          | .ok propositionExpr =>
              let declarationRange := Json.mkObj [
                ("startLine", toJson range.pos.line),
                ("startColumn", toJson range.pos.column),
                ("endLine", toJson range.endPos.line),
                ("endColumn", toJson range.endPos.column),
                ("selectionStartLine", toJson selection.pos.line),
                ("selectionStartColumn", toJson selection.pos.column),
                ("selectionEndLine", toJson selection.endPos.line),
                ("selectionEndColumn", toJson selection.endPos.column)]
              let record := Json.mkObj (common module file target "observed" ++ [
                ("propositionExpr", propositionExpr),
                ("sourceModuleOwned", toJson true),
                ("declarationRange", declarationRange)])
              emitJson destination record
              return 0
      | _, _ =>
          emitFailure destination module file target "not-found"
            "exact local definition was absent from the selected source module"
          return 0
      | some _, some _ =>
          emitFailure destination module file target "not-a-proposition"
            "target is not a local definition"
          return 0

def main (args : List String) : IO UInt32 := do
  match args with
  | [module, file, snapshot, target, destination] =>
      runHelper module file snapshot target destination
  | _ =>
      IO.eprintln "usage: ladon_prose_observation MODULE FILE SNAPSHOT TARGET RESULT"
      return 2
