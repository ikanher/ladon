import Lean
import Lean.Server.InfoUtils
open Lean Elab Meta

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
  nondep : Bool
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

structure Observation where
  frame : String
  protocolVersion : String
  helperVersion : String
  leanVersion : String
  leanCommit : String
  leanExecutablePath : String
  requestId : String
  contextRef : String
  module : String
  filename : String
  sourceDigest : String
  line : Nat
  column : Nat
  byteOffset : Nat
  goals : Array GoalRow
  goalCount : Nat
  useAfter : Bool
  rangeStartByte : Nat
  rangeEndByte : Nat
  selectionEndByte : Nat
  namespaceName : String
  openDeclarationsStructural : String
  optionsStructural : String
  importedModules : Array String
  compiledModulePaths : Array CompiledModulePath
  observationCount : Nat
  deriving ToJson

def localRow (decl : LocalDecl) : MetaM LocalRow := do
  let type ← instantiateMVars decl.type
  let value? ← (decl.value? true).mapM instantiateMVars
  let nondep := match decl with
    | .ldecl _ _ _ _ _ nondep _ => nondep
    | .cdecl .. => false
  let dependencies := ((value?.map (collectFVars (collectFVars {} type))).getD
    (collectFVars {} type)).fvarIds.map (fun id => id.name.toString)
  return {
    localId := decl.fvarId.name.toString
    userName := decl.userName.toString
    binderInfo := (repr decl.binderInfo).pretty
    typeDisplay := (← ppExpr type).pretty
    typeStructural := (repr type).pretty
    valueDisplay := (← value?.mapM ppExpr).map (·.pretty) |>.getD ""
    valueStructural := (value?.map fun value => (repr value).pretty).getD ""
    dependencies
    implementationDetail := decl.isImplementationDetail
    nondep
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
    typeStructural := (repr type).pretty
    localContext := rows
  }

unsafe def main (_args : List String) : IO UInt32 := do
  enableInitializersExecution
  let stdin ← IO.getStdin
  let input ← stdin.readToEnd
  let requestPrefix := "LADON_GOAL_REQUEST "
  if !input.startsWith requestPrefix then
    throw <| IO.userError "missing framed source goal request"
  let requestText := input.drop requestPrefix.length |>.toString.trimAscii.toString
  let .ok request := Json.parse requestText | throw <| IO.userError "malformed source goal request JSON"
  let .ok fields := request.getObj? | throw <| IO.userError "source goal request must be an object"
  let expectedKeys := ["column", "contextRef", "filename", "line",
    "module", "protocolVersion", "requestId", "snapshotPath", "sourceDigest"]
  let fieldNames := fields.toList.map Prod.fst
  if fieldNames.length != expectedKeys.length || expectedKeys.any (!fieldNames.contains ·) then
    throw <| IO.userError "source goal request fields are not closed"
  let getString (key : String) := ((request.getObjValAs? String key).toOption.getD "")
  let getNat (key : String) := ((request.getObjValAs? Nat key).toOption.getD 0)
  let snapshotPath := getString "snapshotPath"
  let filename := getString "filename"
  let module := getString "module"
  let requestId := getString "requestId"
  let contextRef := getString "contextRef"
  let sourceDigest := getString "sourceDigest"
  let line := getNat "line"
  let column := getNat "column"
  if getString "protocolVersion" != "ladon-lean-source-goal-v1/capture"
      || requestId.isEmpty || contextRef.isEmpty || filename.isEmpty || module.isEmpty
      || snapshotPath.isEmpty || sourceDigest.isEmpty || line == 0 then
    throw <| IO.userError "source goal request identity or position is invalid"
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
  let mut found : Array (ContextInfo × TacticInfo × Bool × Array GoalRow) := #[]
  for tree in trees do
    for selected in tree.goalsAt? inputCtx.fileMap pos do
      let ti := selected.tacticInfo
      let ctx := { selected.ctxInfo with mctx := if selected.useAfter then ti.mctxAfter else ti.mctxBefore }
      let goals := if selected.useAfter then ti.goalsAfter else ti.goalsBefore
      let rows ← goals.toArray.mapM fun goal => ctx.runMetaM {} (goalRow goal)
      found := found.push (selected.ctxInfo, ti, selected.useAfter, rows)
  if found.size != 1 then
    throw <| IO.userError (if found.isEmpty then "no goal at selected position" else "ambiguous source observations")
  let some (ctxInfo, ti, useAfter, goals) := found[0]? | throw <| IO.userError "no selected context"
  let activeCtx := { ctxInfo with mctx := if useAfter then ti.mctxAfter else ti.mctxBefore }
  let activeGoals := if useAfter then ti.goalsAfter else ti.goalsBefore
  let experiment := activeCtx.runMetaM {} do
    let some goal := activeGoals[0]? | throwError "fixture has no goals"
    let (closedTarget, closedProof, support, implementationLocals) ← goal.withContext do
      let target ← instantiateMVars (← goal.getType)
      let stx ← match Parser.runParserCategory (← getEnv) `term "h" with
        | .ok stx => pure stx
        | .error msg => throwError "term parse failed: {msg}"
      let (term, termState) ← Lean.Elab.Term.TermElabM.run
        (Lean.Elab.Term.elabTermEnsuringType stx (some target) (catchExPostpone := false))
        { errToSorry := false, mayPostpone := false }
      let (_, termState) ← Lean.Elab.Term.TermElabM.run
        Lean.Elab.Term.synthesizeSyntheticMVarsNoPostponing
        { errToSorry := false, mayPostpone := false } termState
      if !termState.pendingMVars.isEmpty then throwError "pending synthetic metavariables remain"
      let term ← instantiateMVars term
      if term.hasExprMVar || term.hasLevelMVar then throwError "residual expression/universe metavariable in term"
      let inferred ← inferType term
      unless (← isDefEq inferred target) do throwError "term has wrong target"
      let lctx ← getLCtx
      let mut decls := #[]
      for decl in lctx do decls := decls.push decl
      let usedIds := (collectFVars (collectFVars {} target) term).fvarIds
      let mut implementationLocals := #[]
      let mut support := #[]
      for decl in decls do
        if decl.isImplementationDetail then
          implementationLocals := implementationLocals.push decl.userName.toString
          if usedIds.contains decl.fvarId then
            throwError "term/target depends on implementation-detail local {decl.userName}"
        else
          support := support.push (mkFVar decl.fvarId)
      let closedTarget ← mkForallFVars support target (usedOnly := false)
        (usedLetOnly := false) (generalizeNondepLet := true)
      let closedProof ← mkLambdaFVars support term (usedOnly := false)
        (usedLetOnly := false) (generalizeNondepLet := true)
      if closedTarget.hasFVar || closedProof.hasFVar then
        throwError "closure retained free variables"
      let closedTarget ← instantiateMVars closedTarget
      let closedProof ← instantiateMVars closedProof
      if closedTarget.hasExprMVar || closedTarget.hasLevelMVar || closedProof.hasExprMVar || closedProof.hasLevelMVar then
        throwError "closure retained expression/universe metavariables"
      let inferredClosed ← inferType closedProof
      unless (← isDefEq inferredClosed closedTarget) do
        throwError "closed proof does not have closed target type"
      pure (closedTarget, closedProof,
        support.map (fun e => e.fvarId!.name.toString), implementationLocals)
    let roundtrip ← withLCtx {} {} do
      withOptions (fun o => o.setBool `pp.explicit true |>.setBool `pp.fullNames true |>.setBool `pp.notation false) do
        let targetText ← ppExpr closedTarget
        let proofText ← ppExpr closedProof
        let targetStx ← match Parser.runParserCategory (← getEnv) `term targetText.pretty with
          | .ok stx => pure stx
          | .error msg => throwError "closed target parse failed: {msg}"
        let proofStx ← match Parser.runParserCategory (← getEnv) `term proofText.pretty with
          | .ok stx => pure stx
          | .error msg => throwError "closed proof parse failed: {msg}"
        let closedSort ← inferType closedTarget
        let (roundTarget, _) ← Lean.Elab.Term.TermElabM.run
          (Lean.Elab.Term.elabTermEnsuringType targetStx (some closedSort) (catchExPostpone := false))
          { errToSorry := false, mayPostpone := false }
        let roundTarget ← instantiateMVars roundTarget
        if roundTarget.hasMVar then throwError "round-trip target has residual metavariable"
        unless (← isDefEq roundTarget closedTarget) do
          throwError "round-trip target differs from closed target"
        let (roundProof, _) ← Lean.Elab.Term.TermElabM.run
          (Lean.Elab.Term.elabTermEnsuringType proofStx (some roundTarget) (catchExPostpone := false))
          { errToSorry := false, mayPostpone := false }
        let roundProof ← instantiateMVars roundProof
        if roundProof.hasMVar then throwError "round-trip proof has residual metavariable"
        unless (← isDefEq roundProof closedProof) do
          throwError "round-trip proof differs from closed proof"
        pure (targetText.pretty, proofText.pretty)
    pure (goal.name.toString, (repr closedTarget).pretty, (repr closedProof).pretty,
      support, implementationLocals, roundtrip)
  let namespaceName ← ctxInfo.runMetaM {} getCurrNamespace
  let (experimentGoal, experimentTarget, experimentTerm, support, implementationLocals, roundtrip) ← experiment
  IO.println ("LADON_EXPERIMENT " ++ Json.compress (toJson (experimentGoal, experimentTarget, experimentTerm, support, implementationLocals, roundtrip)))
  let openDeclarationsStructural := String.intercalate "\n" (ctxInfo.openDecls.map toString)
  let optionsStructural := toString ctxInfo.options ++ "|hasTrace=" ++ toString ctxInfo.options.hasTrace
  let executablePath ← IO.appPath
  let compiledModulePaths : Array CompiledModulePath ← ctxInfo.env.header.moduleNames.mapM fun name => do
    let path ← Lean.findOLean name
    pure ({ module := name.toString, path := path.toString } : CompiledModulePath)
  -- goalsAt? accepts raw syntax plus its trailing trivia, including EOF.
  -- Keep that selection interval separate from the raw syntax interval.
  let rangeEndByte := (ti.stx.getTailPos?).map (fun p => p.byteIdx) |>.getD 0
  let trailingSize := ti.stx.getTrailingSize
  let sourceEnd := contents.rawEndPos.byteIdx
  let selectionEndByte := if rangeEndByte + trailingSize == sourceEnd then sourceEnd
    else min sourceEnd (rangeEndByte + max 1 trailingSize - 1)
  let output : Observation := {
    frame := "LADON_GOAL_FRAME"
    protocolVersion := "ladon-lean-source-goal-v1/capture"
    helperVersion := "ladon-source-goal-helper-v1"
    leanVersion := Lean.versionString
    leanCommit := Lean.githash
    leanExecutablePath := executablePath.toString
    requestId, contextRef, module, filename, sourceDigest, line, column
    byteOffset := pos.byteIdx
    goals
    goalCount := goals.size
    useAfter
    rangeStartByte := (ti.stx.getPos?).map (fun p => p.byteIdx) |>.getD 0
    rangeEndByte, selectionEndByte
    namespaceName := namespaceName.toString
    openDeclarationsStructural := openDeclarationsStructural
    optionsStructural := optionsStructural
    importedModules := ctxInfo.env.header.moduleNames.map toString
    compiledModulePaths := compiledModulePaths
    observationCount := found.size
  }
  IO.println ("LADON_GOAL_FRAME " ++ Json.compress (toJson output))
  return 0
