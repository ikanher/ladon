import Lean
import Lean.Elab.Frontend
import Lean.Meta.Transform

open Lean

structure FormalContractWorkerOutput where
  version : String
  helperVersion : String
  protocolVersion : String
  leanVersion : String
  module : String
  file : String
  target : String
  status : String
  reason? : Option String := none
  typeFingerprint? : Option String := none
  typeExpr? : Option Json := none
  normalizedTypeFingerprint? : Option String := none
  normalizedTypeExpr? : Option Json := none
  sourceModuleOwned? : Option Bool := none
  declarationRange? : Option Json := none
  deriving Inhabited, ToJson

private def helperVersion := "experimental-proposition-value-v1"
private def protocolVersion := "experimental-proposition-value-v1"

private def runMeta {α : Type} (env : Environment) (file : String)
    (fileMap : FileMap) (action : MetaM α) : IO α := do
  let (value, _, _) ← action.toIO
    { fileName := file, fileMap, options := {} }
    { env }
  return value

private def binderInfoName : BinderInfo → String
  | .default => "explicit"
  | .implicit => "implicit"
  | .strictImplicit => "strict-implicit"
  | .instImplicit => "instance-implicit"

private partial def exprJson : Expr → Json
  | .bvar index => Json.mkObj [("bvar", toJson index)]
  | .fvar id => Json.mkObj [("fvar", toJson id.name)]
  | .mvar id => Json.mkObj [("mvar", toJson id.name)]
  | .sort level => Json.mkObj [("sort", toJson (toString level))]
  | .const name levels => Json.mkObj [
      ("const", toJson name),
      ("levels", toJson (levels.map toString))]
  | .app function argument => Json.mkObj [
      ("app", Json.arr #[exprJson function, exprJson argument])]
  | .lam name type body info => Json.mkObj [("lam", Json.mkObj [
      ("name", toJson name), ("type", exprJson type),
      ("body", exprJson body), ("binderInfo", toJson (binderInfoName info))])]
  | .forallE name type body info => Json.mkObj [("forallE", Json.mkObj [
      ("name", toJson name), ("type", exprJson type),
      ("body", exprJson body), ("binderInfo", toJson (binderInfoName info))])]
  | .letE name type value body nondep => Json.mkObj [("letE", Json.mkObj [
      ("name", toJson name), ("type", exprJson type),
      ("value", exprJson value), ("body", exprJson body),
      ("nondep", toJson nondep)])]
  | .lit (.natVal value) => Json.mkObj [("nat", toJson value)]
  | .lit (.strVal value) => Json.mkObj [("string", toJson value)]
  | .mdata _ body => exprJson body
  | .proj typeName index value => Json.mkObj [("proj", Json.mkObj [
      ("typeName", toJson typeName), ("index", toJson index),
      ("structure", exprJson value)])]

private def output (module file target status : String)
    (reason? : Option String := none) (type? : Option Expr := none)
    (normalizedType? : Option Expr := none) (sourceModuleOwned? : Option Bool := none)
    (declarationRange? : Option Json := none) : FormalContractWorkerOutput :=
  {
    version := "1"
    helperVersion
    protocolVersion
    leanVersion := Lean.versionString
    module
    file
    target
    status
    reason?
    typeFingerprint? := type?.map fun expression => toString (hash expression)
    typeExpr? := type?.map exprJson
    normalizedTypeFingerprint? := normalizedType?.map fun expression => toString (hash expression)
    normalizedTypeExpr? := normalizedType?.map exprJson
    sourceModuleOwned?
    declarationRange?
  }

private def emit (destination : String) (record : FormalContractWorkerOutput) : IO Unit := do
  let encoded := (toJson record).compress
  if encoded.utf8ByteSize > 8 * 1024 * 1024 then
    throw <| IO.userError "formal statement result exceeds output bound"
  IO.FS.writeFile destination encoded

private def runHelper (module file snapshot target destination : String) : IO UInt32 := do
  let contents ← IO.FS.readFile snapshot
  unsafe Lean.enableInitializersExecution
  let options := Elab.async.set ({} : Options) false
  let env? ← Elab.runFrontend contents options file module.toName
  match env? with
  | none =>
      emit destination <|
        output module file target "elaboration_failed"
          (some "Lean frontend did not produce an environment")
      return 0
  | some env =>
      let targetName := target.toName
      if env.header.mainModule != module.toName then
        emit destination <|
          output module file target "module_mismatch"
            (some "frontend environment main module differs from request")
        return 0
      let ranges? ← runMeta env file contents.toFileMap
        (findDeclarationRanges? targetName)
      let sourceModuleOwned := (env.getModuleIdxFor? targetName).isNone
      match env.find? targetName, ranges? with
      | some info, some ranges =>
          let sourceLineCount := (contents.splitOn "\n").length
          let range := ranges.range
          let selection := ranges.selectionRange
          let rangeInSource := range.pos.line > 0 && range.endPos.line <= sourceLineCount
          if !sourceModuleOwned || !rangeInSource then
            emit destination <|
              output module file target "not_found"
                (some "target is imported or has no declaration range in the selected source")
            return 0
          let value ← match info with
            | .defnInfo definition => pure definition.value
            | _ => throw <| IO.userError "Only local proposition definitions are allowed"
          let valid ← runMeta env file contents.toFileMap do
            return (← isDefEq info.type (.sort .zero)) && (← isProp value)
          if !valid then
            throw <| IO.userError "Selected definition does not describe a proposition"
          let normalizedType ← runMeta env file contents.toFileMap do
            let instantiated ← instantiateMVars value
            Lean.Meta.zetaReduce instantiated
          emit destination <|
            output module file target "observed" none
              (some value) (some normalizedType) (some true) (some <| Json.mkObj [
                ("startLine", toJson range.pos.line),
                ("startColumn", toJson range.pos.column),
                ("endLine", toJson range.endPos.line),
                ("endColumn", toJson range.endPos.column),
                ("selectionStartLine", toJson selection.pos.line),
                ("selectionStartColumn", toJson selection.pos.column),
                ("selectionEndLine", toJson selection.endPos.line),
                ("selectionEndColumn", toJson selection.endPos.column)])
          return 0
      | _, _ =>
          emit destination <|
            output module file target "not_found"
              (some "exact declaration was absent from the selected source module")
          return 0

def main (args : List String) : IO UInt32 := do
  match args with
  | [module, file, snapshot, target, destination] =>
      runHelper module file snapshot target destination
  | _ =>
      IO.eprintln "usage: ladon_formal_contract_helper MODULE FILE SNAPSHOT TARGET RESULT"
      return 2
