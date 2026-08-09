import Lean
import Lean.Elab.Frontend
import Lean.Meta
import Lean.Meta.Tactic.Apply
import Lean.Util.Path

/-!
The semantic-candidate helper owns only Lean facts.  It elaborates a generated,
finite probe file and returns exact structural expressions plus the imported
`.olean` paths that formed its environment.  The Python supervisor owns process
outcomes, byte digests, limits, and the eventual ProofIR check-run identity.
-/

open Lean

def ladonSemanticCandidateProtocol : String :=
  "ladon-lean-semantic-v2/check-candidate"

structure SemanticModule where
  module : String
  oleanPath : String
  deriving ToJson

structure SemanticSubject where
  name : String
  typeDisplay : String
  typeStructural : String
  deriving ToJson

structure SemanticExpression where
  typeDisplay : String
  typeStructural : String
  deriving ToJson

structure SemanticSubstitution where
  «variable» : String
  termDisplay : String
  termStructural : String
  deriving ToJson

structure SemanticCandidateOutput where
  protocol : String
  leanVersion : String
  leanCommit : String
  executablePath : String
  module : String
  probe : SemanticSubject
  candidate : SemanticSubject
  importedModules : Array SemanticModule
  substitutions : Array SemanticSubstitution
  residualPremises : Array SemanticExpression
  localContext : Array SemanticExpression
  deriving ToJson

private def runMeta {α : Type} (env : Environment) (file : String)
    (fileMap : FileMap) (action : MetaM α) : IO α := do
  let (value, _, _) ← action.toIO
    { fileName := file, fileMap, options := {} }
    { env }
  return value

private def subject (env : Environment) (file : String) (fileMap : FileMap)
    (name : Name) : IO SemanticSubject := do
  let some info := env.find? name
    | throw <| IO.userError s!"declaration not found: {name}"
  let display ← runMeta env file fileMap (Meta.ppExpr info.type)
  return {
    name := toString name
    typeDisplay := display.pretty
    -- `repr` retains the complete Lean expression tree; Python hashes these
    -- bytes under a versioned scheme instead of trusting Lean's machine hash.
    typeStructural := (repr info.type).pretty
  }

private def importedModules (env : Environment) : IO (Array SemanticModule) :=
  env.header.moduleNames.mapM fun module => do
    let path ← findOLean module
    return { module := toString module, oleanPath := toString path }

private partial def applicationSubstitutions (type : Expr) (arguments : Array Expr)
    (index : Nat := 0) : MetaM (Array SemanticSubstitution) := do
  if h : index < arguments.size then
    match type with
    | .forallE binderName _ body _ =>
        let argument ← instantiateMVars arguments[index]
        let display ← Meta.ppExpr argument
        let variableName := if binderName.isAnonymous then s!"_{index}" else toString binderName
        let rest ← applicationSubstitutions (body.instantiate1 argument) arguments (index + 1)
        return #[{
          «variable» := variableName
          termDisplay := display.pretty
          termStructural := (repr argument).pretty
        }] ++ rest
    | _ => return #[]
  else
    return #[]

private def analyzeApplication (env : Environment) (file : String)
    (fileMap : FileMap) (probeName candidateName : Name) :
    IO (Array SemanticSubstitution × Array SemanticExpression) :=
  runMeta env file fileMap (do
    let some probeInfo := env.find? probeName
      | throwError "probe declaration not found"
    let some candidateInfo := env.find? candidateName
      | throwError "candidate declaration not found"
    let goal ← Meta.mkFreshExprMVar probeInfo.type
    let residualGoals ← goal.mvarId!.applyConst candidateName
    let some rawAssignment ← getExprMVarAssignment? goal.mvarId!
      | throwError "candidate application did not assign the probe goal"
    let assignment ← instantiateMVars rawAssignment
    let substitutions ← applicationSubstitutions candidateInfo.type assignment.getAppArgs
    let residuals ← residualGoals.toArray.mapM fun residual => do
      let type ← instantiateMVars (← residual.getType)
      let display ← Meta.ppExpr type
      return {
        typeDisplay := display.pretty
        typeStructural := (repr type).pretty
      }
    return (substitutions, residuals))

private def runHelper (module file probeName candidateName : String) : IO UInt32 := do
  let contents ← IO.FS.readFile file
  unsafe Lean.enableInitializersExecution
  let options := Elab.async.set ({} : Options) false
  let env? ← Elab.runFrontend contents options file module.toName
  match env? with
  | none =>
      IO.eprintln s!"ELABORATION_FAILURE {file}"
      return 1
  | some env =>
      let fileMap := contents.toFileMap
      let probe ← subject env file fileMap probeName.toName
      let candidate ← subject env file fileMap candidateName.toName
      let (substitutions, residuals) ←
        analyzeApplication env file fileMap probeName.toName candidateName.toName
      let modules ← importedModules env
      let executable ← IO.appPath
      let output : SemanticCandidateOutput := {
        protocol := ladonSemanticCandidateProtocol
        leanVersion := Lean.versionString
        leanCommit := Lean.githash
        executablePath := toString executable
        module
        probe
        candidate
        importedModules := modules
        substitutions
        residualPremises := residuals
        localContext := #[]
      }
      IO.println <| Json.pretty <| toJson output
      return 0

def main (args : List String) : IO UInt32 := do
  match args with
  | ["--", module, file, probeName, candidateName] =>
      runHelper module file probeName candidateName
  | [module, file, probeName, candidateName] =>
      runHelper module file probeName candidateName
  | _ =>
      IO.eprintln
        "usage: ladon_semantic_candidate_helper MODULE FILE PROBE CANDIDATE"
      return 2
