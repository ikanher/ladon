import Lean
import Lean.Elab.Frontend
import Lean.Meta
import Lean.Meta.Tactic.Apply
import Lean.Util.Path

/-!
The semantic-candidate helper owns only Lean facts.  It loads the requested
module environment, parses and elaborates the goal directly with Lean's term
elaborator, and returns exact structural expressions plus the imported `.olean`
paths.  It never creates a declaration or a `sorry` probe.  The Python
supervisor owns process outcomes, byte digests, limits, and the eventual
ProofIR check-run identity.
-/

open Lean

def ladonSemanticCandidateProtocol : String :=
  "ladon-lean-semantic-v3/check-candidate"

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

structure SemanticLocalDecl where
  localId : String
  userName : String
  binderInfo : String
  typeDisplay : String
  typeStructural : String
  valueDisplay : String
  valueStructural : String
  dependencies : Array String
  origin : String
  deriving ToJson

structure SemanticSubstitution where
  «variable» : String
  termDisplay : String
  termStructural : String
  deriving ToJson

structure SemanticCandidateOutput where
  protocol : String
  frameVersion : Nat
  sequence : Nat
  terminal : Bool
  universePolicy : String
  requestId : String
  leanVersion : String
  leanCommit : String
  executablePath : String
  module : String
  probe : SemanticSubject
  candidate : SemanticSubject
  importedModules : Array SemanticModule
  substitutions : Array SemanticSubstitution
  residualPremises : Array SemanticExpression
  localContext : Array SemanticLocalDecl
  deriving ToJson

private def runMetaIO {α : Type} (env : Environment) (file : String)
    (fileMap : FileMap) (action : MetaM α) : IO α := do
  let (value, _, _) ← action.toIO
    { fileName := file, fileMap, options := {} }
    { env }
  return value

private def subject (env : Environment) (file : String) (fileMap : FileMap)
    (name : Name) : IO SemanticSubject := do
  let some info := env.find? name
    | throw <| IO.userError s!"declaration not found: {name}"
  let display ← runMetaIO env file fileMap (Meta.ppExpr info.type)
  return {
    name := toString name
    typeDisplay := display.pretty
    -- `repr` retains the complete Lean expression tree; Python hashes these
    -- bytes under a versioned scheme instead of trusting Lean's machine hash.
    typeStructural := (repr info.type).pretty
  }

private def expressionSubject (env : Environment) (file : String) (fileMap : FileMap)
    (name : Name) (type : Expr) : IO SemanticSubject := do
  let display ← runMetaIO env file fileMap (Meta.ppExpr type)
  return {
    name := toString name
    typeDisplay := display.pretty
    typeStructural := (repr type).pretty
  }

private def elaborateGoal (env : Environment) (file : String) (fileMap : FileMap)
    (goal : String) : IO Expr := do
  let parsed ← match Parser.runParserCategory env `term goal file with
    | .ok termSyntax => pure termSyntax
    | .error message => throw <| IO.userError s!"goal parse failed: {message}"
  let elaborated ← runMetaIO env file fileMap <|
    Elab.Term.TermElabM.run' (ctx := { errToSorry := false, mayPostpone := false }) <|
      Elab.Term.elabTermEnsuringType parsed (some (mkSort .zero)) false false <*
        Elab.Term.synthesizeSyntheticMVarsNoPostponing
  -- Standalone term parsing can leave an unconstrained universe metavariable
  -- (for example the universe parameter of `Eq`).  A proposition's operands
  -- live in at least `Type`, so close that otherwise-unobservable parser
  -- metavariable at level one before handing the expression to MetaM.
  return Expr.replaceLevel (fun
    | .mvar _ => some (.succ .zero)
    | _ => none) elaborated

private def importedModules (env : Environment) : IO (Array SemanticModule) :=
  env.header.moduleNames.mapM fun module => do
    let path ← findOLean module
    return { module := toString module, oleanPath := toString path }

private def parseLeanName (env : Environment) (text : String) : IO Name :=
  match Parser.runParserCategory env `term text with
  | .ok stx =>
      if stx.isIdent then
        pure stx.getId
      else
        throw <| IO.userError s!"invalid Lean name: {text}"
  | .error message => throw <| IO.userError s!"invalid Lean name: {message}"

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

private partial def introduceForall (goal : MVarId) : MetaM MVarId := do
  let goalType ← Meta.whnf (← goal.getType)
  match goalType with
  | Expr.forallE .. =>
      let (_, next) ← goal.intro1P
      introduceForall next
  | _ => return goal

private def localContextTypes : MetaM (Array SemanticLocalDecl) := do
  let mut rows := #[]
  for decl in ← getLCtx do
    let type ← instantiateMVars decl.type
    let typeDisplay ← Meta.ppExpr type
    let value? := decl.value? true
    let valueDisplay ← value?.mapM Meta.ppExpr
    let dependencies := (collectFVars {} type).fvarIds.map fun id =>
      "local:" ++ (repr id).pretty
    rows := rows.push {
      localId := "local:" ++ (repr decl.fvarId).pretty
      userName := toString decl.userName
      binderInfo := (repr decl.binderInfo).pretty
      typeDisplay := typeDisplay.pretty
      typeStructural := (repr type).pretty
      valueDisplay := valueDisplay.map (·.pretty) |>.getD ""
      valueStructural := value?.map (fun value => (repr value).pretty) |>.getD ""
      dependencies
      origin := "goal-introduced"
    }
  return rows

private def analyzeApplication (env : Environment) (file : String)
    (fileMap : FileMap) (goalType : Expr) (candidateName : Name) :
    IO (Array SemanticSubstitution × Array SemanticExpression × Array SemanticLocalDecl) :=
  runMetaIO env file fileMap (do
    let some candidateInfo := env.find? candidateName
      | throwError "candidate declaration not found"
    try
      discard <| Meta.isDefEq candidateInfo.type goalType
    catch _ =>
      pure ()
    let goalType ← instantiateMVars goalType
    let goal ← Meta.mkFreshExprMVar goalType
    let focused ← introduceForall goal.mvarId!
    let localContext ← focused.withContext do localContextTypes
    let residualGoals ← try
      focused.applyConst candidateName
    catch _ =>
      if ← Meta.isDefEq candidateInfo.type goalType then
        goal.mvarId!.assign (← mkConstWithLevelParams candidateName)
        pure []
      else
        throwError "candidate application did not unify with the elaborated goal"
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
    return (substitutions, residuals, localContext))

private def runHelper (module file goal probeName candidateName requestId : String) : IO UInt32 := do
  let contents ← IO.FS.readFile file
  -- Lean's frontend requires initializer execution to load the target
  -- project's compiled environment. It runs in the supervised helper process;
  -- protocol output remains request-framed and target stdout cannot mint a
  -- semantic result without the supervisor's terminal validation.
  unsafe Lean.enableInitializersExecution
  let options := Elab.async.set ({} : Options) false
  let env? ← Elab.runFrontend contents options file module.toName
  match env? with
  | none =>
      IO.eprintln s!"ELABORATION_FAILURE {file}"
      return 1
  | some env =>
      let fileMap := contents.toFileMap
      let candidateLeanName ← parseLeanName env candidateName
      let goalType ← elaborateGoal env file fileMap goal
      let (substitutions, residuals, localContext) ← analyzeApplication env file fileMap goalType candidateLeanName
      let probe ← expressionSubject env file fileMap probeName.toName goalType
      let candidate ← subject env file fileMap candidateLeanName
      let modules ← importedModules env
      let executable ← IO.appPath
      let output : SemanticCandidateOutput := {
        protocol := ladonSemanticCandidateProtocol
        frameVersion := 1
        sequence := 0
        terminal := true
        universePolicy := "lean-level-mvar-succ-zero/v1"
        requestId
        leanVersion := Lean.versionString
        leanCommit := Lean.githash
        executablePath := toString executable
        module
        probe
        candidate
        importedModules := modules
        substitutions
        residualPremises := residuals
        localContext
      }
      IO.println s!"LADON_FRAME {Json.compress (toJson output)}"
      return 0
def main (args : List String) : IO UInt32 := do
  match args with
  | ["--", module, file, goal, probeName, candidateName, requestId] =>
      runHelper module file goal probeName candidateName requestId
  | [module, file, goal, probeName, candidateName, requestId] =>
      runHelper module file goal probeName candidateName requestId
  | _ =>
      IO.eprintln
        "usage: ladon_semantic_candidate_helper MODULE FILE PROBE CANDIDATE"
      return 2
