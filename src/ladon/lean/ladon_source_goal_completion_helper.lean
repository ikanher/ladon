import Lean
import Lean.Server.InfoUtils
open Lean Elab Meta

-- LADON_EXPR_GRAPH

structure LocalRow where
  localId : String
  userName : String
  binderInfo : String
  typeDisplay : String
  typeStructural : String
  valueDisplay : String
  valueStructural : String
  dependencies : Array String
  implementationDetail : Bool
  deriving ToJson

structure GoalRow where
  goalId : String
  typeDisplay : String
  typeStructural : String
  localContext : Array LocalRow
  deriving ToJson

structure CompiledModulePath where
  module : String
  path : String
  deriving ToJson

structure Diagnostic where
  code : String
  message : String
  deriving ToJson

structure CompletionFrame where
  frame : String
  protocolVersion : String
  helperVersion : String
  requestId : String
  captureId : String
  termDigest : String
  contextRef : String
  module : String
  filename : String
  sourceDigest : String
  line : Nat
  column : Nat
  leanVersion : String
  leanCommit : String
  leanExecutablePath : String
  goalOrdinal : Nat
  goalCount : Nat
  useAfter : Bool
  byteOffset : Nat
  rangeStartByte : Nat
  rangeEndByte : Nat
  selectionEndByte : Nat
  namespaceName : String
  openDeclarationsStructural : String
  optionsStructural : String
  importedModules : Array String
  compiledModulePaths : Array CompiledModulePath
  directImports : Array String
  sourceContextModule : String
  selectedGoal : Option GoalRow
  status : String
  termDisplay : String
  termStructural : String
  residualGoals : Array GoalRow
  closedTargetText : String
  closedProofText : String
  diagnostic : Option Diagnostic
  deriving ToJson

/-- Elaborate the submitted term against the observed target and close only its real
    local dependencies. This is intentionally the value-preserving r58 route. -/
def hasOriginalContextMVars (goal : MVarId) : MetaM Bool := goal.withContext do
  let target ← instantiateMVars (← goal.getType)
  if target.hasExprMVar || target.hasLevelMVar then return true
  for decl in ← getLCtx do
    let type ← instantiateMVars decl.type
    if type.hasExprMVar || type.hasLevelMVar then return true
    if let some value := decl.value? true then
      let value ← instantiateMVars value
      if value.hasExprMVar || value.hasLevelMVar then return true
  return false

def closeChecked (goal : MVarId) (target term : Expr) : MetaM (Expr × Expr × Array String) := goal.withContext do
  let mut decls := #[]
  for decl in ← getLCtx do decls := decls.push decl
  let mut used := (collectFVars (collectFVars {} target) term).fvarIds
  for decl in decls.reverse do
    if used.contains decl.fvarId then
      if decl.isImplementationDetail then
        throwError "transitive dependency reaches implementation-detail local {decl.userName}"
      for id in (collectFVars {} decl.type).fvarIds do
        if !used.contains id then used := used.push id
      match decl with
      | .ldecl _ _ _ _ value _ _ =>
        let value ← instantiateMVars value
        unless (← isDefEq (← inferType value) (← instantiateMVars decl.type)) do
          throwError "used local value for {decl.userName} is not type-correct"
        for id in (collectFVars {} value).fvarIds do
          if !used.contains id then used := used.push id
      | .cdecl .. => pure ()
  let support := decls.filterMap fun decl =>
    if decl.isImplementationDetail then none else some (mkFVar decl.fvarId)
  let closedTarget ← mkForallFVars support target (usedOnly := false)
    (usedLetOnly := false) (generalizeNondepLet := false)
  let closedProof ← mkLambdaFVars support term (usedOnly := false)
    (usedLetOnly := false) (generalizeNondepLet := false)
  let closedTarget ← instantiateMVars closedTarget
  let closedProof ← instantiateMVars closedProof
  if closedTarget.hasFVar || closedProof.hasFVar || closedTarget.hasExprMVar
      || closedTarget.hasLevelMVar || closedProof.hasExprMVar || closedProof.hasLevelMVar then
    throwError "closed completion retains free variables or metavariables"
  unless (← isDefEq (← inferType closedProof) closedTarget) do
    throwError "closed proof does not have the closed target type"
  let supportIds := support.map fun expr => expr.fvarId!.name.toString
  pure (closedTarget, closedProof, supportIds)

/-- The closed expressions must survive controlled explicit printing and reparsing
    with no locals, instances, namespace or open declarations in scope. -/
def emptyContextRoundtrip (target proof : Expr) : MetaM (String × String) := do
  withLCtx {} {} do
    withTheReader Lean.Core.Context
        (fun c => { c with currNamespace := Name.anonymous, openDecls := [] }) do
      withOptions (fun o => o.setBool `pp.all true |>.setBool `pp.explicit true
        |>.setBool `pp.fullNames true |>.setBool `pp.notation false) do
        let targetText := (← ppExpr target).pretty
        let proofText := (← ppExpr proof).pretty
        let targetStx ← match Parser.runParserCategory (← getEnv) `term targetText with
          | .ok stx => pure stx
          | .error msg => throwError "closed target parse failed: {msg}"
        let proofStx ← match Parser.runParserCategory (← getEnv) `term proofText with
          | .ok stx => pure stx
          | .error msg => throwError "closed proof parse failed: {msg}"
        let sort ← inferType target
        let (targetAgain, _) ← Lean.Elab.Term.TermElabM.run
          (Lean.Elab.Term.elabTermEnsuringType targetStx (some sort) (catchExPostpone := false))
          { errToSorry := false, mayPostpone := false }
        let targetAgain ← instantiateMVars targetAgain
        if targetAgain.hasExprMVar || targetAgain.hasLevelMVar || !(← isDefEq targetAgain target) then
          throwError "closed target round-trip changed its expression"
        let (proofAgain, _) ← Lean.Elab.Term.TermElabM.run
          (Lean.Elab.Term.elabTermEnsuringType proofStx (some targetAgain) (catchExPostpone := false))
          { errToSorry := false, mayPostpone := false }
        let proofAgain ← instantiateMVars proofAgain
        if proofAgain.hasExprMVar || proofAgain.hasLevelMVar || !(← isDefEq proofAgain proof) then
          throwError "closed proof round-trip changed its expression"
        pure (targetText, proofText)

def localRow (decl : LocalDecl) : MetaM LocalRow := do
  let type ← instantiateMVars decl.type
  let value? ← (decl.value? true).mapM instantiateMVars
  let dependencies := ((value?.map (collectFVars (collectFVars {} type))).getD
    (collectFVars {} type)).fvarIds.map (fun id => id.name.toString)
  return {
    localId := decl.fvarId.name.toString
    userName := decl.userName.toString
    binderInfo := (repr decl.binderInfo).pretty
    typeDisplay := (← ppExpr type).pretty
    typeStructural := structuralText type
    valueDisplay := (← value?.mapM ppExpr).map (·.pretty) |>.getD ""
    valueStructural := (value?.map fun value => structuralText value).getD ""
    dependencies
    implementationDetail := decl.isImplementationDetail
  }

def goalRow (goal : MVarId) : MetaM GoalRow := goal.withContext do
  let mut rows := #[]
  for decl in ← getLCtx do
    rows := rows.push (← localRow decl)
  let type ← instantiateMVars (← goal.getType)
  let typeDisplay ← ppExpr type
  return {
    goalId := goal.name.toString
    typeDisplay := typeDisplay.pretty
    typeStructural := structuralText type
    localContext := rows
  }

structure CheckResult where
  status : String
  termDisplay : String := ""
  termStructural : String := ""
  residualGoals : Array GoalRow := #[]
  closedTargetText : String := ""
  closedProofText : String := ""
  diagnostic : Option Diagnostic := none

def rejected (code message : String) : CheckResult :=
  { status := "rejected", diagnostic := some { code, message } }

unsafe def main (_args : List String) : IO UInt32 := do
  enableInitializersExecution
  let stdin ← IO.getStdin
  let input ← stdin.readToEnd
  let requestPrefix := "LADON_COMPLETION_REQUEST "
  if !input.startsWith requestPrefix then
    throw <| IO.userError "missing framed completion request"
  let requestText := input.drop requestPrefix.length |>.toString.trimAscii.toString
  let .ok request := Json.parse requestText | throw <| IO.userError "malformed completion request JSON"
  let .ok fields := request.getObj? | throw <| IO.userError "completion request must be an object"
  let expectedKeys := ["captureId", "column", "contextRef", "filename", "goalOrdinal", "line", "module", "protocolVersion", "requestId", "snapshotPath", "sourceDigest", "term", "termDigest"]
  let fieldNames := fields.toList.map Prod.fst
  if fieldNames.length != expectedKeys.length || expectedKeys.any (!fieldNames.contains ·) then
    throw <| IO.userError "completion request fields are not closed"
  let getString (key : String) := ((request.getObjValAs? String key).toOption.getD "")
  let getNat (key : String) := ((request.getObjValAs? Nat key).toOption.getD 0)
  let snapshotPath := getString "snapshotPath"
  let filename := getString "filename"
  let module := getString "module"
  let requestId := getString "requestId"
  let captureId := getString "captureId"
  let contextRef := getString "contextRef"
  let sourceDigest := getString "sourceDigest"
  let termDigest := getString "termDigest"
  let termText := getString "term"
  let line := getNat "line"
  let column := getNat "column"
  let goalOrdinal := getNat "goalOrdinal"
  if getString "protocolVersion" != "ladon-lean-source-completion-v1/check"
      || requestId.isEmpty || captureId.isEmpty || contextRef.isEmpty || filename.isEmpty
      || module.isEmpty || snapshotPath.isEmpty || sourceDigest.isEmpty || termDigest.isEmpty
      || line == 0 then
    throw <| IO.userError "completion request identity or position is invalid"
  let contents ← IO.FS.readFile snapshotPath
  let inputCtx := Parser.mkInputContext contents filename
  let (header, _, _) ← Parser.parseHeader inputCtx
  if HeaderSyntax.isModule header then
    throw <| IO.userError "modular source unsupported"
  let opts := Lean.internal.cmdlineSnapshots.set (Elab.async.set ({} : Options) false) true
  let setup (header : HeaderSyntax) : Language.ProcessingT IO
      (Except Language.Lean.HeaderProcessedSnapshot Language.Lean.SetupImportsResult) := do
    if header.isModule then
      return .error {
        diagnostics := ← Language.diagnosticsOfHeaderError "modular source unsupported"
        result? := none
        metaSnap := default
      }
    return .ok {
      imports := header.imports
      isModule := false
      mainModuleName := module.toName
      opts := opts
    }
  let snapshot ← Language.Lean.process setup none { inputCtx with }
  let tree := Language.toSnapshotTree snapshot
  let _ ← tree.waitAll
  let trees := tree.getAll.filterMap (·.infoTree?)
  let pos := inputCtx.fileMap.ofPosition ⟨line, column⟩
  let mut found : Array (ContextInfo × TacticInfo × Bool × Array MVarId × Array GoalRow) := #[]
  for tree in trees do
    for selected in tree.goalsAt? inputCtx.fileMap pos do
      let ti := selected.tacticInfo
      let ctx := { selected.ctxInfo with mctx := if selected.useAfter then ti.mctxAfter else ti.mctxBefore }
      let goals := if selected.useAfter then ti.goalsAfter else ti.goalsBefore
      let rows ← goals.toArray.mapM fun goal => ctx.runMetaM {} (goalRow goal)
      found := found.push (selected.ctxInfo, ti, selected.useAfter, goals.toArray, rows)
  if found.size != 1 then
    throw <| IO.userError (if found.isEmpty then "no goal at selected position" else "ambiguous source observations")
  let some (ctxInfo, ti, useAfter, activeGoals, goalRows) := found[0]? | throw <| IO.userError "no selected context"
  let namespaceName ← ctxInfo.runMetaM {} getCurrNamespace
  let openDeclarationsStructural := String.intercalate "\n" (ctxInfo.openDecls.map toString)
  let optionsStructural := toString ctxInfo.options ++ "|hasTrace=" ++ toString ctxInfo.options.hasTrace
  let executablePath ← IO.appPath
  let compiledModulePaths : Array CompiledModulePath ← ctxInfo.env.header.moduleNames.mapM fun name => do
    let path ← Lean.findOLean name
    pure ({ module := name.toString, path := path.toString } : CompiledModulePath)
  let rangeEndByte := (ti.stx.getTailPos?).map (fun p => p.byteIdx) |>.getD 0
  let trailingSize := ti.stx.getTrailingSize
  let sourceEnd := contents.rawEndPos.byteIdx
  let selectionEndByte := if rangeEndByte + trailingSize == sourceEnd then sourceEnd
    else min sourceEnd (rangeEndByte + max 1 trailingSize - 1)
  let startByte := (ti.stx.getPos?).map (fun p => p.byteIdx) |>.getD 0
  let selectedGoal := goalRows[goalOrdinal]?
  let checkResult ← match activeGoals[goalOrdinal]? with
    | none => pure (rejected "goal-ordinal" "requested goal ordinal is unavailable")
    | some goal => do
      let activeCtx := { ctxInfo with mctx := if useAfter then ti.mctxAfter else ti.mctxBefore }
      activeCtx.runMetaM {} do
        if ← hasOriginalContextMVars goal then
          pure { status := "unsupported", diagnostic := some { code := "original-context-mvar", message := "captured goal or local declarations contain unresolved expression/universe metavariables" } }
        else
          match Parser.runParserCategory (← getEnv) `term termText with
          | .error message => pure (rejected "term-parse" message)
          | .ok termSyntax =>
            try
              let target ← goal.withContext do instantiateMVars (← goal.getType)
              let (term, termState) ← goal.withContext do
                Lean.Elab.Term.TermElabM.run
                  (Lean.Elab.Term.elabTermEnsuringType termSyntax (some target) (catchExPostpone := false))
                  { errToSorry := false, mayPostpone := false }
              let (_, termState) ← goal.withContext do
                Lean.Elab.Term.TermElabM.run
                  Lean.Elab.Term.synthesizeSyntheticMVarsNoPostponing
                  { errToSorry := false, mayPostpone := false } termState
              let term ← instantiateMVars term
              let (display, structural) ← goal.withContext do
                pure ((← ppExpr term).pretty, structuralText term)
              let mut residualIds := termState.pendingMVars.toArray
              for id in ← getMVars term do
                if !(← id.isAssigned) && !residualIds.contains id then
                  residualIds := residualIds.push id
              residualIds ← residualIds.filterM fun id => not <$> id.isAssigned
              if !residualIds.isEmpty then
                let residual ← residualIds.mapM goalRow
                pure {
                  status := "incomplete"
                  termDisplay := display
                  termStructural := structural
                  residualGoals := residual
                  diagnostic := some { code := "residual-goals", message := "term elaboration left actual unresolved expression metavariables" }
                }
              else if term.hasExprMVar || term.hasLevelMVar then
                pure (rejected "term-mvar" "elaborated term retains expression or universe metavariables")
              else
                let target ← goal.withContext do instantiateMVars (← goal.getType)
                if target.hasExprMVar || target.hasLevelMVar then
                  pure (rejected "target-mvar" "captured target retains unresolved expression/universe metavariables")
                else do
                  let (closedTarget, closedProof, _) ← closeChecked goal target term
                  let (closedTargetText, closedProofText) ← emptyContextRoundtrip closedTarget closedProof
                  pure {
                    status := "accepted"
                    termDisplay := display
                    termStructural := structural
                    closedTargetText
                    closedProofText
                  }
            catch ex => do
              let message ← ex.toMessageData.toString
              pure (rejected "typecheck-or-closure" message)
  let sourceContextModule := if checkResult.status == "accepted" then
    "LadonCompletionContext_" ++ requestId else ""
  if !sourceContextModule.isEmpty then
    let contextPath := ((System.FilePath.mk snapshotPath).parent.getD ".") / (sourceContextModule ++ ".olean")
    Lean.writeModule (ctxInfo.env.setMainModule sourceContextModule.toName) contextPath (writeIR := false)
  let directImports := ((HeaderSyntax.imports header false).map (fun imp => imp.module.toString)).toList.eraseDups.toArray
  let output : CompletionFrame := {
    frame := "LADON_COMPLETION_FRAME"
    protocolVersion := "ladon-lean-source-completion-v1/check"
    helperVersion := "ladon-source-completion-helper-v2"
    requestId, captureId, termDigest, contextRef, module, filename, sourceDigest, line, column
    leanVersion := Lean.versionString
    leanCommit := Lean.githash
    leanExecutablePath := executablePath.toString
    goalOrdinal
    goalCount := goalRows.size
    useAfter
    byteOffset := pos.byteIdx
    rangeStartByte := startByte
    rangeEndByte
    selectionEndByte
    namespaceName := namespaceName.toString
    openDeclarationsStructural
    optionsStructural
    importedModules := ctxInfo.env.header.moduleNames.map toString
    compiledModulePaths
    directImports
    sourceContextModule
    selectedGoal
    status := checkResult.status
    termDisplay := checkResult.termDisplay
    termStructural := checkResult.termStructural
    residualGoals := checkResult.residualGoals
    closedTargetText := checkResult.closedTargetText
    closedProofText := checkResult.closedProofText
    diagnostic := checkResult.diagnostic
  }
  IO.println ("LADON_COMPLETION_FRAME " ++ Json.compress (toJson output))
  return 0
