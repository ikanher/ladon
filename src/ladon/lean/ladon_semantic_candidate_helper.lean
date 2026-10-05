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
  "ladon-lean-semantic-v4/check-candidate"

def ladonSemanticBatchProtocol : String := "ladon-lean-semantic-v4/check-candidates"

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

structure SemanticDischargedHypothesis where
  premiseOrdinal : Nat
  premiseTypeDisplay : String
  dischargedByLocalRef : String
  method : String
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

structure SemanticResidualContext where
  goalId : String
  localContext : Array SemanticLocalDecl
  deriving ToJson

structure SemanticCandidateOutput where
  protocol : String
  frameVersion : Nat
  sequence : Nat
  terminal : Bool
  universePolicy : String
  requestId : String
  goalRequestDigest : String
  leanVersion : String
  leanCommit : String
  executablePath : String
  executionContextRef : String
  module : String
  probe : SemanticSubject
  candidate : SemanticSubject
  applicationTerm : String
  dischargedHypotheses : Array SemanticDischargedHypothesis
  importedModules : Array SemanticModule
  substitutions : Array SemanticSubstitution
  residualPremises : Array SemanticExpression
  localContext : Array SemanticLocalDecl
  residualContexts : Array SemanticResidualContext
  declarationBinders : Array SemanticLocalDecl
  deriving ToJson

structure SemanticCandidateRejectionOutput where
  protocol : String
  frameVersion : Nat
  sequence : Nat
  terminal : Bool
  universePolicy : String
  requestId : String
  goalRequestDigest : String
  leanVersion : String
  leanCommit : String
  executablePath : String
  executionContextRef : String
  module : String
  probe : SemanticSubject
  candidateName : String
  status : String
  failureStage : String
  diagnostic : String
  importedModules : Array SemanticModule
  localContext : Array SemanticLocalDecl
  deriving ToJson

structure SemanticBatchRow where
  candidate : String
  status : String
  candidateSubject : Option SemanticSubject
  applicationTerm : String
  dischargedHypotheses : Array SemanticDischargedHypothesis
  substitutions : Array SemanticSubstitution
  residualPremises : Array SemanticExpression
  residualContexts : Array SemanticResidualContext
  declarationBinders : Array SemanticLocalDecl
  failureStage : String
  diagnostic : String
  deriving ToJson

structure SemanticBatchHeader where
  protocol : String
  frameVersion : Nat
  frameKind : String
  sequence : Nat
  terminal : Bool
  universePolicy : String
  requestId : String
  goalRequestDigest : String
  executionContextRef : String
  leanVersion : String
  leanCommit : String
  executablePath : String
  module : String
  probe : SemanticSubject
  importedModules : Array SemanticModule
  localContext : Array SemanticLocalDecl
  deriving ToJson

structure SemanticBatchRowFrame where
  protocol : String
  frameVersion : Nat
  frameKind : String
  sequence : Nat
  terminal : Bool
  requestId : String
  row : SemanticBatchRow
  deriving ToJson

structure SemanticBatchSummary where
  protocol : String
  frameVersion : Nat
  frameKind : String
  sequence : Nat
  terminal : Bool
  requestId : String
  completed : Nat
  total : Nat
  deriving ToJson

private def emitFrame {α : Type} [ToJson α] (frame : α) : IO Unit := do
  IO.println s!"LADON_FRAME {Json.compress (toJson frame)}"
  (← IO.getStdout).flush

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
    Elab.Term.TermElabM.run' (ctx := { errToSorry := false, mayPostpone := false }) do
      let elaborated ←
        Elab.Term.elabTermEnsuringType parsed (some (mkSort .zero)) false false
      Elab.Term.synthesizeSyntheticMVarsNoPostponing
      -- Do not return an expression that refers to assignments owned by this
      -- temporary TermElabM state. The application check runs in a fresh
      -- MetaM state and cannot resolve those metavariable identifiers.
      instantiateMVars elaborated
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

private partial def introduceForall (goal : MVarId) : MetaM MVarId := goal.withContext do
  let goalType ← Meta.whnf (← goal.getType)
  match goalType with
  | Expr.forallE .. =>
      let (_, next) ← goal.intro1P
      introduceForall next
  | _ => return goal

private def localRef (id : FVarId) : MetaM String := do
  let mut ordinal := 0
  for decl in ← getLCtx do
    if decl.fvarId == id then
      return s!"local:{ordinal}"
    ordinal := ordinal + 1
  throwError "local declaration is absent from the active context"

private def localContextTypes (origin : String := "goal-introduced") : MetaM (Array SemanticLocalDecl) := do
  let mut rows := #[]
  for decl in ← getLCtx do
    let type ← instantiateMVars decl.type
    let typeDisplay ← Meta.ppExpr type
    let value? := decl.value? true
    let value? ← value?.mapM instantiateMVars
    let valueDisplay ← value?.mapM Meta.ppExpr
    let valueDependencies := match value? with
      | none => #[]
      | some value => (collectFVars {} value).fvarIds
    let allDependencies := (collectFVars {} type).fvarIds ++ valueDependencies
    let mut seenDependencies := #[]
    for dependency in allDependencies do
      if !seenDependencies.contains dependency then
        seenDependencies := seenDependencies.push dependency
    let dependencies ← seenDependencies.mapM localRef
    rows := rows.push {
      localId := ← localRef decl.fvarId
      userName := toString decl.userName
      binderInfo := (repr decl.binderInfo).pretty
      typeDisplay := typeDisplay.pretty
      typeStructural := (repr type).pretty
      valueDisplay := valueDisplay.map (·.pretty) |>.getD ""
      valueStructural := value?.map (fun value => (repr value).pretty) |>.getD ""
      dependencies
      origin
    }
  return rows

private def dischargeResiduals (residualGoals : Array MVarId) : MetaM (Array SemanticDischargedHypothesis × Array MVarId) := do
  let mut discharged := #[]
  let mut remaining := #[]
  for h : ordinal in [0:residualGoals.size] do
    let residual := residualGoals[ordinal]
    -- Earlier premise matching can solve this argument. Preserve that assignment.
    if ← residual.isAssigned then
      continue
    let result ← residual.withContext do
      let type ← instantiateMVars (← residual.getType)
      let mut match? : Option LocalDecl := none
      for decl in ← getLCtx do
        if match?.isNone then
          try
            if ← Meta.isDefEq type (← instantiateMVars decl.type) then
              match? := some decl
          catch _ => pure ()
      match match? with
      | none => pure (none, type)
      | some localDecl =>
          residual.assign (mkFVar localDecl.fvarId)
          let display ← Meta.ppExpr type
          pure (some {
          premiseOrdinal := ordinal
          premiseTypeDisplay := display.pretty
          dischargedByLocalRef := ← localRef localDecl.fvarId
          method := "assumption-definitional-equality"
          }, type)
    match result.1 with
    | none => remaining := remaining.push residual
    | some row => discharged := discharged.push row
  return (discharged, remaining)

private def analyzeLocalContext (env : Environment) (file : String)
    (fileMap : FileMap) (goalType : Expr) : IO (Array SemanticLocalDecl) :=
  runMetaIO env file fileMap (do
    let goal ← Meta.mkFreshExprMVar goalType
    let focused ← introduceForall goal.mvarId!
    focused.withContext do localContextTypes)

private def analyzeApplication (env : Environment) (file : String)
    (fileMap : FileMap) (goalType : Expr) (candidateName : Name) :
    IO (String × Array SemanticSubstitution × Array SemanticDischargedHypothesis × Array SemanticExpression × Array SemanticLocalDecl × Array SemanticResidualContext × Array SemanticLocalDecl) :=
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
    focused.withContext do
      let localContext ← focused.withContext do localContextTypes
      let residualGoals ← try
        focused.applyConst candidateName
      catch _ =>
        if ← Meta.isDefEq candidateInfo.type goalType then
          goal.mvarId!.assign (← mkConstWithLevelParams candidateName)
          pure []
        else
          throwError "candidate application did not unify with the elaborated goal"
      let (discharged, remainingGoals) ← dischargeResiduals residualGoals.toArray
      let some rawFocusedAssignment ← getExprMVarAssignment? focused
        | throwError "candidate application did not assign the focused probe goal"
      let focusedAssignment ← instantiateMVars rawFocusedAssignment
      if remainingGoals.isEmpty then
        Meta.checkWithKernel focusedAssignment
      let applicationDisplay ← focused.withContext do Meta.ppExpr focusedAssignment
      let substitutions ← applicationSubstitutions candidateInfo.type focusedAssignment.getAppArgs
      let residuals ← remainingGoals.mapM fun residual => do
        residual.withContext do
          let type ← instantiateMVars (← residual.getType)
          let display ← Meta.ppExpr type
          return {
            typeDisplay := display.pretty
            typeStructural := (repr type).pretty
          }
      let residualContexts ← remainingGoals.mapM fun residual => residual.withContext do
        return { goalId := toString residual.name, localContext := ← localContextTypes }
      let declarationBinders ← Meta.withLCtx {} {} do
        Meta.forallTelescope candidateInfo.type fun _ _ => localContextTypes "declaration-parameter"
      return (applicationDisplay.pretty, substitutions, discharged, residuals, localContext, residualContexts, declarationBinders))

private def runHelper (module file goal goalRequestDigest probeName candidateName requestId executionContextRef : String) : IO UInt32 := do
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
      let goalType ← elaborateGoal env file fileMap goal
      let probe ← expressionSubject env file fileMap probeName.toName goalType
      let modules ← importedModules env
      let localContext ← analyzeLocalContext env file fileMap goalType
      let executable ← IO.appPath
      let emitRejected (failureStage diagnostic : String) : IO Unit := do
        let output : SemanticCandidateRejectionOutput := {
          protocol := ladonSemanticCandidateProtocol
          frameVersion := 1
          sequence := 0
          terminal := true
          universePolicy := "lean-level-mvar-succ-zero/v1"
          requestId
          goalRequestDigest
          executionContextRef
          leanVersion := Lean.versionString
          leanCommit := Lean.githash
          executablePath := toString executable
          module
          probe
          candidateName
          status := "rejected"
          failureStage
          diagnostic
          importedModules := modules
          localContext
        }
        IO.println s!"LADON_FRAME {Json.compress (toJson output)}"
      let candidateResult : Except String Name ← try
        pure (Except.ok (← parseLeanName env candidateName))
      catch error =>
        pure (Except.error error.toString)
      let candidateLeanName ← match candidateResult with
        | Except.ok name => pure name
        | Except.error diagnostic =>
            emitRejected "candidate-name-invalid" diagnostic
            return 0
      if (env.find? candidateLeanName).isNone then
        emitRejected "candidate-not-found" s!"declaration not found: {candidateName}"
        return 0
      let applicationResult ← try
        pure (Except.ok (← analyzeApplication env file fileMap goalType candidateLeanName))
      catch error =>
        pure (Except.error error.toString)
      let (applicationTerm, substitutions, dischargedHypotheses, residuals, localContext, residualContexts, declarationBinders) ←
        match applicationResult with
        | Except.ok result => pure result
        | Except.error diagnostic =>
            emitRejected "application-rejected" diagnostic
            return 0
      let candidate ← subject env file fileMap candidateLeanName
      let output : SemanticCandidateOutput := {
        protocol := ladonSemanticCandidateProtocol
        frameVersion := 1
        sequence := 0
        terminal := true
        universePolicy := "lean-level-mvar-succ-zero/v1"
        requestId
        goalRequestDigest
        executionContextRef
        leanVersion := Lean.versionString
        leanCommit := Lean.githash
        executablePath := toString executable
        module
        probe
        candidate
        applicationTerm
        dischargedHypotheses
        importedModules := modules
        substitutions
        residualPremises := residuals
        localContext
        residualContexts
        declarationBinders
      }
      IO.println s!"LADON_FRAME {Json.compress (toJson output)}"
      return 0

private def runBatchHelper (module file goal goalRequestDigest probeName requestId executionContextRef : String)
    (candidateNames : List String) : IO UInt32 := do
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
      let goalType ← elaborateGoal env file fileMap goal
      let probe ← expressionSubject env file fileMap probeName.toName goalType
      let modules ← importedModules env
      let localContext ← analyzeLocalContext env file fileMap goalType
      let executable ← IO.appPath
      emitFrame ({
        protocol := ladonSemanticBatchProtocol
        frameVersion := 1
        frameKind := "header"
        sequence := 0
        terminal := false
        universePolicy := "lean-level-mvar-succ-zero/v1"
        requestId
        goalRequestDigest
        executionContextRef
        leanVersion := Lean.versionString
        leanCommit := Lean.githash
        executablePath := toString executable
        module
        probe
        importedModules := modules
        localContext
      } : SemanticBatchHeader)
      for h : index in [0:candidateNames.length] do
        let candidateName := candidateNames[index]
        let nameResult : Except String Name ← try
          pure (Except.ok (← parseLeanName env candidateName))
        catch error => pure (Except.error error.toString)
        let row : SemanticBatchRow ← match nameResult with
          | Except.error diagnostic => pure {
              candidate := candidateName
              status := "rejected"
              candidateSubject := none
              applicationTerm := ""
              dischargedHypotheses := #[]
              substitutions := #[]
              residualPremises := #[]
              residualContexts := #[]
              declarationBinders := #[]
              failureStage := "candidate-name-invalid"
              diagnostic
            }
          | Except.ok candidateLeanName =>
              if (env.find? candidateLeanName).isNone then
                pure {
                  candidate := candidateName
                  status := "rejected"
                  candidateSubject := none
                  applicationTerm := ""
                  dischargedHypotheses := #[]
                  substitutions := #[]
                  residualPremises := #[]
                  residualContexts := #[]
                  declarationBinders := #[]
                  failureStage := "candidate-not-found"
                  diagnostic := s!"declaration not found: {candidateName}"
                }
              else try
                let candidate ← subject env file fileMap candidateLeanName
                let (applicationTerm, substitutions, dischargedHypotheses, residuals, _, residualContexts, declarationBinders) ← analyzeApplication env file fileMap goalType candidateLeanName
                pure {
                  candidate := candidateName
                  status := if residuals.isEmpty then "accepted" else "applicable-with-residuals"
                  candidateSubject := some candidate
                  applicationTerm
                  dischargedHypotheses
                  substitutions
                  residualPremises := residuals
                  residualContexts
                  declarationBinders
                  failureStage := ""
                  diagnostic := ""
                }
              catch error => pure {
                candidate := candidateName
                status := "rejected"
                candidateSubject := none
                applicationTerm := ""
                dischargedHypotheses := #[]
                substitutions := #[]
                residualPremises := #[]
                residualContexts := #[]
                declarationBinders := #[]
                failureStage := "application-rejected"
                diagnostic := error.toString
              }
        emitFrame ({
          protocol := ladonSemanticBatchProtocol
          frameVersion := 1
          frameKind := "candidate"
          sequence := index + 1
          terminal := false
          requestId
          row
        } : SemanticBatchRowFrame)
      emitFrame ({
        protocol := ladonSemanticBatchProtocol
        frameVersion := 1
        frameKind := "summary"
        sequence := candidateNames.length + 1
        terminal := true
        requestId
        completed := candidateNames.length
        total := candidateNames.length
      } : SemanticBatchSummary)
      return 0
def main (args : List String) : IO UInt32 := do
  match args with
  | "--batch" :: module :: file :: goal :: goalRequestDigest :: probeName :: requestId :: executionContextRef :: candidates =>
      runBatchHelper module file goal goalRequestDigest probeName requestId executionContextRef candidates
  | "--" :: "--batch" :: module :: file :: goal :: goalRequestDigest :: probeName :: requestId :: executionContextRef :: candidates =>
      runBatchHelper module file goal goalRequestDigest probeName requestId executionContextRef candidates
  | ["--", module, file, goal, goalRequestDigest, probeName, candidateName, requestId, executionContextRef] =>
      runHelper module file goal goalRequestDigest probeName candidateName requestId executionContextRef
  | [module, file, goal, goalRequestDigest, probeName, candidateName, requestId, executionContextRef] =>
      runHelper module file goal goalRequestDigest probeName candidateName requestId executionContextRef
  | _ =>
      IO.eprintln
        "usage: ladon_semantic_candidate_helper MODULE FILE PROBE CANDIDATE"
      return 2
