import Lean
-- LADON_TARGET_IMPORT

open Lean Elab Command Meta

/- A bounded, read-only proposal for extracting an exact application from an
   imported theorem value.  Root owns compilation and runtime qualification. -/

-- LADON_EXPR_GRAPH
-- LADON_ROUNDTRIP_PRINT

private def boundedOccurrences (root : Expr) (needle : Name)
    (maxNodes := 8192) (maxDepth := 64) : MetaM (Array Expr) := do
  let mut todo : Array (Expr × Nat) := #[(root, 0)]
  let mut visited := 0
  let mut found := #[]
  while !todo.isEmpty do
    let (e, depth) := todo.back!
    todo := todo.pop
    if depth > maxDepth then throwError "expression depth exceeds {maxDepth}"
    visited := visited + 1
    if visited > maxNodes then throwError "expression node count exceeds {maxNodes}"
    let fn := e.getAppFn
    if let .const name _ := fn then
      if name == needle && e.isApp then found := found.push e
    let d := depth + 1
    match e with
    | .app .. =>
      todo := todo.push (e.getAppFn, d)
      for arg in e.getAppArgs.reverse do todo := todo.push (arg, d)
    | .lam _ t b _ => todo := todo.push (t, d) |>.push (b, d)
    | .forallE _ t b _ => todo := todo.push (t, d) |>.push (b, d)
    | .letE _ t v b _ => todo := todo.push (t, d) |>.push (v, d) |>.push (b, d)
    | .mdata _ b => todo := todo.push (b, d)
    | .proj _ _ b => todo := todo.push (b, d)
    | .bvar _ | .fvar _ | .mvar _ | .sort _ | .const _ _ | .lit _ => pure ()
  return found

private def resolveName (requested : Name) : CoreM Name := do
  let env ← getEnv
  if env.contains requested then return requested
  throwError "constant not found; supply a qualified name: {requested}"

private def jsonExpr (expr : Expr) : MetaM Json := do
  let display ← withOptions (fun o => o.setBool `pp.all true |>.setBool `pp.explicit true
    |>.setBool `pp.fullNames true |>.setBool `pp.notation false) do
    pure (← ppExpr expr).pretty
  pure <| Json.mkObj [
    ("display", toJson display), ("structural", toJson (structuralText expr))]

/-- Print/reparse the closed proof and type under an empty local context. -/
private def checkedRoundtrip (target proof : Expr) : MetaM (String × String) := do
  withLCtx {} {} do
    withTheReader Lean.Core.Context
      (fun c => { c with currNamespace := Name.anonymous, openDecls := [] }) do
      withOptions (fun o => o.setBool `pp.all true |>.setBool `pp.explicit true
        |>.setBool `pp.fullNames true |>.setBool `pp.notation false) do
        let targetText := (← ppExpr target).pretty
        let proofText ← roundtripProofText proof
        if targetText.utf8ByteSize > 1048576 || proofText.utf8ByteSize > 1048576 then
          throwError "serialized closed expression exceeds 1 MiB"
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

elab "#ladon_proof_slice " decl:ident app:ident maxNodes:num : command => do
  liftTermElabM do
    let declName ← resolveName decl.getId
    let appName ← resolveName app.getId
    let info ← getConstInfo declName
    if info.type.hasExprMVar || info.type.hasLevelMVar then
      throwError "declaration type contains unresolved metavariables"
    let some value := info.value? true
      | throwError "declaration has no exposed value: {declName}"
    let declarationType ← jsonExpr info.type
    let declarationBinders ← forallTelescope info.type fun binders _ => do
      binders.mapM fun binder => do
        let d ← binder.fvarId!.getDecl
        pure <| Json.mkObj [
          ("name", toJson d.userName.toString),
          ("localId", toJson (repr d.fvarId.name).pretty),
          ("isProp", toJson (← isProp d.type)),
          ("binderInfo", toJson (repr d.binderInfo).pretty),
          ("type", ← jsonExpr d.type),
          ("isImplementationDetail", toJson d.isImplementationDetail)]
    let range? ← findDeclarationRanges? declName
    let (locals, resultRows) ← lambdaLetTelescope value fun proofLocals body => do
      let localRows ← proofLocals.mapM fun fvar => do
        let d ← fvar.fvarId!.getDecl
        let valueJson ← match d.value? with
          | none => pure Json.null
          | some rhs => jsonExpr rhs
        pure <| Json.mkObj [
          ("name", toJson d.userName.toString),
          ("localId", toJson (repr d.fvarId.name).pretty),
          ("isProp", toJson (← isProp d.type)),
          ("binderInfo", toJson (repr d.binderInfo).pretty),
          ("type", ← jsonExpr d.type), ("letValue", valueJson)]
      let occurrences ← boundedOccurrences body appName maxNodes.getNat
      if occurrences.isEmpty then throwError "no exact application head {appName} in {declName}"
      let mut rows := #[]
      for occurrence in [:occurrences.size] do
        let matched := occurrences[occurrence]!
        if matched.hasExprMVar || matched.hasLevelMVar then
          throwError "matched application contains unresolved metavariables"
        let mut args := #[]
        let appArgs := matched.getAppArgs
        let head := matched.getAppFn
        let .const headName _ := head
          | throwError "matched application head is not a constant"
        let headInfo ← getConstInfo headName
        let binderInfos ← forallTelescope headInfo.type fun binders _ =>
          binders.mapM fun binder => do
            let d ← binder.fvarId!.getDecl
            pure (repr d.binderInfo).pretty
        for i in [:appArgs.size] do
          let arg := appArgs[i]!
          let argType ← inferType arg
          if argType.hasExprMVar || argType.hasLevelMVar then
            throwError "application argument type contains unresolved metavariables"
          let isProp ← isProp argType
          args := args.push <| Json.mkObj [
            ("index", toJson i), ("expression", ← jsonExpr arg),
            ("type", ← jsonExpr argType), ("isProp", toJson isProp),
            ("binderInfo", toJson (binderInfos[i]?.getD "unknown"))]
        let appType ← inferType matched
        if appType.hasExprMVar || appType.hasLevelMVar then
          throwError "application type contains unresolved metavariables"
        let closedType ← mkForallFVars proofLocals appType
          (usedOnly := false) (usedLetOnly := false) (generalizeNondepLet := false)
        let closedProof ← mkLambdaFVars proofLocals matched
          (usedOnly := false) (usedLetOnly := false) (generalizeNondepLet := false)
        if closedProof.hasFVar || closedType.hasFVar || closedProof.hasExprMVar
            || closedType.hasExprMVar || closedProof.hasLevelMVar || closedType.hasLevelMVar then
          throwError "closed application retains free variables or metavariables"
        unless (← isDefEq (← inferType closedProof) closedType) do
          throwError "closed application proof does not have its closed type"
        let (closedTypeText, closedProofText) ← checkedRoundtrip closedType closedProof
        let applicationJson ← jsonExpr matched
        let typeJson ← jsonExpr appType
        if (structuralText matched).utf8ByteSize > 1048576
            || (structuralText closedProof).utf8ByteSize > 1048576
            || (structuralText closedType).utf8ByteSize > 1048576 then
          throwError "serialized expression exceeds 1 MiB"
        rows := rows.push <| Json.mkObj [
          ("occurrence", toJson occurrence), ("application", applicationJson),
          ("applicationType", typeJson), ("arguments", Json.arr args),
          ("closedApplicationTypeText", toJson closedTypeText),
          ("closedApplicationProofText", toJson closedProofText),
          ("closedApplicationTypeStructural", toJson (structuralText closedType)),
          ("closedApplicationProofStructural", toJson (structuralText closedProof))]
      pure (localRows, rows)
    let declRange := toString (repr range?)
    let modules := (← getEnv).header.moduleNames
    let paths ← modules.mapM fun name => do
      let path ← Lean.findOLean name
      pure <| Json.mkObj [("module", toJson name.toString), ("path", toJson path.toString)]
    let output := Json.mkObj [
      ("protocol", toJson "ladon-proof-slice-proposal-v1"),
      ("declaration", toJson declName.toString), ("declarationType", declarationType),
      ("declarationBinders", Json.arr declarationBinders),
      ("proofLocalsAndLets", Json.arr locals),
      ("sourceAttribution", Json.mkObj [
        ("scope", toJson "declaration"), ("range", toJson declRange)]),
      ("applicationHead", toJson appName.toString),
      ("importedModules", toJson (modules.map toString)),
      ("compiledModulePaths", Json.arr paths),
      ("applications", Json.arr resultRows)]
    let frame := "LADON_PROOF_SLICE " ++ Json.compress output
    if frame.utf8ByteSize > 8388608 then throwError "serialized result exceeds 8 MiB"
    logInfo frame

-- LADON_SELECTION
