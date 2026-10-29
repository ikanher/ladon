import Lean
import Lean.Server.InfoUtils
import LadonProseExactGoal
open Lean Elab Meta

-- LADON_EXPR_GRAPH

private def check (goal : MVarId) (request proofText : String) : MetaM Json := goal.withContext do
  let expected ← Ladon.ProseExactGoal.constructGoal request
  let actual ← instantiateMVars (← goal.getType)
  unless structuralText expected == structuralText actual do
    throwError "connection target differs from independently constructed owner implication"
  let witness ← getConstInfo `LadonCheckedConnectionWitness
  unless structuralText witness.type == structuralText expected do
    throwError "connection witness has a different owner implication"
  let proofSyntax ← match Parser.runParserCategory (← getEnv) `term proofText with
    | .ok stx => pure stx
    | .error reason => throwError "connection proof is not an isolated term: {reason}"
  let action : Term.TermElabM Expr := do
    let value ← Term.elabTermEnsuringType proofSyntax expected
    Term.synthesizeSyntheticMVarsNoPostponing
    instantiateMVars value
  let (proof, _) ← action.run { errToSorry := false, mayPostpone := false } {}
  if proof.hasFVar || proof.hasLooseBVars || proof.hasExprMVar || proof.hasLevelMVar then
    throwError "connection requested proof is not closed"
  let name := `LadonIndependentConnectionCommitment
  if (← getEnv).contains name then throwError "reserved commitment declaration already exists"
  let decl := Declaration.thmDecl {
    name, levelParams := witness.levelParams, type := expected, value := proof }
  match (← getEnv).toKernelEnv.addDecl (debug.skipKernelTC.set ({} : Options) false) decl with
  | .error _ => throwError "synchronous connection kernel check rejected requested proof"
  | .ok _ => pure ()
  addDecl decl
  let axioms ← collectAxioms name
  unless axioms.all (fun n => [``propext, ``Classical.choice, ``Quot.sound].contains n) do
    throwError "connection requested proof has unsupported axioms"
  return Json.mkObj [
    ("schema", toJson "ladon-connection-target-commitment-v1"),
    ("expectedStructural", toJson (structuralText expected)),
    ("actualStructural", toJson (structuralText actual)),
    ("kernelCheck", toJson "synchronous"),
    ("axioms", toJson (axioms.map toString)),
    ("ownerRequest", toJson request), ("requestedTerm", toJson proofText)]

unsafe def main (args : List String) : IO UInt32 := do
  let [requestFile, destination] := args | throw <| IO.userError "expected request and output paths"
  enableInitializersExecution
  let .ok request := Json.parse (← IO.FS.readFile requestFile)
    | throw <| IO.userError "invalid commitment request JSON"
  let getString (key : String) := (request.getObjValAs? String key).toOption.getD ""
  let filename := getString "filename"
  let module := getString "module"
  let contents ← IO.FS.readFile (getString "snapshotPath")
  let inputCtx := Parser.mkInputContext contents filename
  let (header, _, _) ← Parser.parseHeader inputCtx
  if HeaderSyntax.isModule header then throw <| IO.userError "modular source unsupported"
  let opts := Lean.internal.cmdlineSnapshots.set (Elab.async.set ({} : Options) false) true
  let setup (header : HeaderSyntax) : Language.ProcessingT IO
      (Except Language.Lean.HeaderProcessedSnapshot Language.Lean.SetupImportsResult) := do
    return .ok { imports := header.imports, isModule := false, mainModuleName := module.toName, opts }
  let snapshot ← Language.Lean.process setup none { inputCtx with }
  let tree := Language.toSnapshotTree snapshot
  let _ ← tree.waitAll
  let trees := tree.getAll.filterMap (·.infoTree?)
  let line := (request.getObjValAs? Nat "line").toOption.getD 0
  let column := (request.getObjValAs? Nat "column").toOption.getD 0
  let pos := inputCtx.fileMap.ofPosition ⟨line, column⟩
  let mut found : Array (ContextInfo × MVarId) := #[]
  for tree in trees do
    for selected in tree.goalsAt? inputCtx.fileMap pos do
      let ti := selected.tacticInfo
      let ctx := { selected.ctxInfo with mctx := if selected.useAfter then ti.mctxAfter else ti.mctxBefore }
      let goals := if selected.useAfter then ti.goalsAfter else ti.goalsBefore
      if goals.length != 1 then throw <| IO.userError "commitment requires one exact goal"
      for goal in goals do found := found.push (ctx, goal)
  unless found.size == 1 do throw <| IO.userError "commitment requires one exact source observation"
  let some (ctx, goal) := found[0]? | throw <| IO.userError "no commitment context"
  let result ← ctx.runMetaM {} (check goal (getString "ownerRequest") (getString "requestedTerm"))
  let paths ← ctx.env.header.moduleNames.mapM fun name => do
    let path ← Lean.findOLean name
    pure <| Json.mkObj [("module",toJson name.toString),("path",toJson path.toString)]
  let executable ← IO.appPath
  let namespaceName ← ctx.runMetaM {} getCurrNamespace
  let environment := Json.mkObj [
    ("leanVersion",toJson Lean.versionString),("leanCommit",toJson Lean.githash),
    ("leanExecutablePath",toJson executable.toString),("namespace",toJson namespaceName.toString),
    ("openDeclarationsStructural",toJson (String.intercalate "\n" (ctx.openDecls.map toString))),
    ("optionsStructural",toJson (toString ctx.options ++ "|hasTrace=" ++ toString ctx.options.hasTrace)),
    ("importedModules",toJson (ctx.env.header.moduleNames.map toString)),
    ("compiledModulePaths",Json.arr paths)]
  let result := result.setObjVal! "environment" environment
  let text := result.compress
  if text.utf8ByteSize > 8*1024*1024 then throw <| IO.userError "commitment exceeds 8 MiB"
  IO.FS.writeFile destination text
  return 0
