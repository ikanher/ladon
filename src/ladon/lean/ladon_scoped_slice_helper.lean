import Lean
-- LADON_TARGET_IMPORT

open Lean Elab Command Meta

/- A bounded, read-only proposal for extracting an exact application from an
   imported theorem value.  Root owns compilation and runtime qualification. -/

-- LADON_EXPR_GRAPH

private structure ScopedOccurrence where
  expr : Expr
  lctx : LocalContext
  instances : LocalInstances
  scopePath : Array Nat
  nestedLocalIds : Array String
  deriving Inhabited

private partial def scopedOccurrences (root : Expr) (needle : Name)
    (maxNodes := 8192) (maxDepth := 64) : MetaM (Array ScopedOccurrence) := do
  let visited ← IO.mkRef 0
  let rec walk (e : Expr) (depth : Nat) (path : Array Nat)
      (isLeading : Bool) (nestedIds : Array String) : MetaM (Array ScopedOccurrence) := do
    if depth > maxDepth then throwError "expression depth exceeds {maxDepth}"
    let n ← visited.get
    if n >= maxNodes then throwError "expression node count exceeds {maxNodes}"
    visited.set (n + 1)
    let mut found := #[]
    if let .const name _ := e.getAppFn then
      if name == needle && e.isApp then
        found := #[{ expr := e, lctx := ← getLCtx, instances := ← getLocalInstances, scopePath := path, nestedLocalIds := nestedIds }]
    match e with
    | .app .. =>
      found := found ++ (← walk e.getAppFn (depth + 1) (path.push 0) false nestedIds)
      for i in [:e.getAppArgs.size] do
        found := found ++ (← walk e.getAppArgs[i]! (depth + 1) (path.push (i + 1)) false nestedIds)
    | .lam name type body bi =>
      found := found ++ (← walk type (depth + 1) (path.push 0) false nestedIds)
      let nested ← withLocalDecl name bi type fun fvar =>
        walk (body.instantiate1 fvar) (depth + 1) (path.push 1) isLeading
          (if isLeading then nestedIds else nestedIds.push (repr fvar.fvarId!.name).pretty)
      found := found ++ nested
    | .forallE name type body bi =>
      found := found ++ (← walk type (depth + 1) (path.push 0) false nestedIds)
      let nested ← withLocalDecl name bi type fun fvar =>
        walk (body.instantiate1 fvar) (depth + 1) (path.push 1) isLeading
          (if isLeading then nestedIds else nestedIds.push (repr fvar.fvarId!.name).pretty)
      found := found ++ nested
    | .letE name type value body _ =>
      found := found ++ (← walk type (depth + 1) (path.push 0) false nestedIds)
      found := found ++ (← walk value (depth + 1) (path.push 1) false nestedIds)
      let nested ← withLetDecl name type value fun fvar =>
        walk (body.instantiate1 fvar) (depth + 1) (path.push 2) isLeading
          (if isLeading then nestedIds else nestedIds.push (repr fvar.fvarId!.name).pretty)
      found := found ++ nested
    | .mdata _ body => found := found ++ (← walk body (depth + 1) (path.push 0) isLeading nestedIds)
    | .proj _ _ body => found := found ++ (← walk body (depth + 1) (path.push 0) false nestedIds)
    | .bvar _ | .fvar _ | .mvar _ | .sort _ | .const _ _ | .lit _ => pure ()
    return found
  walk root 0 #[] true #[]

private def resolveName (requested : Name) : CoreM Name := do
  let env ← getEnv
  if env.contains requested then return requested
  throwError "constant not found; supply a qualified name: {requested}"

private def jsonExpr (expr : Expr) : MetaM Json := do
  let display ← withOptions (fun o => o.setBool `pp.all true |>.setBool `pp.explicit true
    |>.setBool `pp.fullNames true |>.setBool `pp.notation false) do
    pure (← ppExpr expr).pretty
  let result := Json.mkObj [
    ("display", toJson display), ("structural", toJson (structuralText expr))]
  if result.compress.utf8ByteSize > 1048576 then
    throwError "serialized expression exceeds 1 MiB"
  pure result

/-- Print/reparse the closed proof and type under an empty local context. -/
private def checkedRoundtrip (target proof : Expr) : MetaM (String × String) := do
  withLCtx {} {} do
    withTheReader Lean.Core.Context
      (fun c => { c with currNamespace := Name.anonymous, openDecls := [] }) do
      withOptions (fun o => o.setBool `pp.all true |>.setBool `pp.explicit true
        |>.setBool `pp.fullNames true |>.setBool `pp.notation false) do
        let targetText := (← ppExpr target).pretty
        let proofText := (← ppExpr proof).pretty
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

private partial def identityTransport (selected : Expr) : MetaM Json := do
  let sourceLocals := (← getLCtx).foldl (fun rows d => rows.push d) (#[] : Array LocalDecl)
  let rec rebuild (i : Nat) (oldVars newVars : Array Expr) (rows : Array Json) : MetaM Json := do
    if h : i < sourceLocals.size then
      let decl := sourceLocals[i]
      let type := decl.type.replaceFVars oldVars newVars
      let value := decl.value?.map (·.replaceFVars oldVars newVars)
      let mut freshName := Name.mkSimple s!"ladonFormal{i}"
      while sourceLocals.any (fun d => d.userName == freshName) do
        freshName := Name.mkSimple (freshName.toString ++ "_")
      let next (fresh : Expr) : MetaM Json := do
        if let some value := value then
          unless (← isDefEq (← inferType value) type) do
            throwError "transported let value changed type"
        let valueJson ← match value with
          | none => pure Json.null
          | some e => jsonExpr e
        let row := Json.mkObj [
          ("originalLocalId", toJson (repr decl.fvarId.name).pretty),
          ("localId", toJson (repr fresh.fvarId!.name).pretty),
          ("name", toJson freshName.toString), ("binderInfo", toJson (repr decl.binderInfo).pretty),
          ("isProp", toJson (← isProp type)), ("type", ← jsonExpr type), ("letValue", valueJson)]
        rebuild (i + 1) (oldVars.push (mkFVar decl.fvarId)) (newVars.push fresh) (rows.push row)
      match value with
      | none => withLocalDecl freshName decl.binderInfo type next
      | some value => withLetDecl freshName type value next
    else
      let application := selected.replaceFVars oldVars newVars
      let expectedType := (← inferType selected).replaceFVars oldVars newVars
      unless (← isDefEq (← inferType application) expectedType) do
        throwError "transported application changed its type"
      let closedType ← mkForallFVars newVars expectedType
        (usedOnly := false) (usedLetOnly := false) (generalizeNondepLet := false)
      let closedProof ← mkLambdaFVars newVars application
        (usedOnly := false) (usedLetOnly := false) (generalizeNondepLet := false)
      if closedType.hasFVar || closedProof.hasFVar || closedType.hasExprMVar
          || closedProof.hasExprMVar || closedType.hasLevelMVar || closedProof.hasLevelMVar then
        throwError "transport retains escaped locals or unresolved metavariables"
      unless (← isDefEq (← inferType closedProof) closedType) do
        throwError "transport closure changed its type"
      let (closedTypeText, closedProofText) ← checkedRoundtrip closedType closedProof
      let mut arguments := #[]
      for i in [:application.getAppArgs.size] do
        let arg := application.getAppArgs[i]!
        let argType ← inferType arg
        arguments := arguments.push <| Json.mkObj [
          ("index", toJson i), ("expression", ← jsonExpr arg), ("type", ← jsonExpr argType),
          ("isProp", toJson (← isProp argType)), ("binderInfo", toJson "transported")]
      return Json.mkObj [
        ("profile", toJson "fvar-substitution-v1"), ("localContext", Json.arr rows),
        ("application", ← jsonExpr application), ("applicationType", ← jsonExpr expectedType),
        ("arguments", Json.arr arguments), ("closedType", toJson closedTypeText),
        ("closedProof", toJson closedProofText)]
  rebuild 0 #[] #[] #[]

elab "#ladon_proof_slice " decl:ident app:ident : command => do
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
    let occurrences ← scopedOccurrences value appName
    let (locals, resultRows) ← lambdaLetTelescope value fun proofLocals _ => do
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
      if occurrences.isEmpty then throwError "no exact application head {appName} in {declName}"
      let mut rows := #[]
      for occurrence in [:occurrences.size] do
        let selected :=  occurrences[occurrence]!
        let row ← withLCtx selected.lctx selected.instances do
          let matched := selected.expr
          if matched.hasExprMVar || matched.hasLevelMVar then
            throwError "matched application contains unresolved metavariables"
          let mut args := #[]
          let mut providers := #[]
          let mut occurrenceLocals := #[]
          for decl in selected.lctx do occurrenceLocals := occurrenceLocals.push (mkFVar decl.fvarId)
          let mut occurrenceLocalRows := #[]
          for decl in selected.lctx do
            let valueJson ← match decl.value? with
              | none => pure Json.null
              | some rhs => jsonExpr rhs
            occurrenceLocalRows := occurrenceLocalRows.push <| Json.mkObj [
              ("name", toJson decl.userName.toString),
              ("localId", toJson (repr decl.fvarId.name).pretty),
              ("isProp", toJson (← isProp decl.type)),
              ("binderInfo", toJson (repr decl.binderInfo).pretty),
              ("type", ← jsonExpr decl.type), ("letValue", valueJson)]
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
            if isProp then
              let mut status := "scoped-expression"
              let mut localId := Json.null
              let mut providerValue := Json.null
              let mut providerProof := arg
              if let .fvar id := arg then
                let decl ← id.getDecl
                localId := toJson (repr id.name).pretty
                match decl.value? with
                | none => status := "scoped-boundary"
                | some rhs =>
                  status := "scoped-local-value"
                  providerValue := ← jsonExpr rhs
                  providerProof := rhs
              let providerType ← inferType providerProof
              let closedProviderType ← mkForallFVars occurrenceLocals providerType
                (usedOnly := false) (usedLetOnly := false) (generalizeNondepLet := false)
              let closedProviderProof ← mkLambdaFVars occurrenceLocals providerProof
                (usedOnly := false) (usedLetOnly := false) (generalizeNondepLet := false)
              if closedProviderType.hasFVar || closedProviderProof.hasFVar
                  || closedProviderType.hasExprMVar || closedProviderProof.hasExprMVar
                  || closedProviderType.hasLevelMVar || closedProviderProof.hasLevelMVar then
                throwError "provider closure retains free variables or metavariables"
              unless (← isDefEq (← inferType closedProviderProof) closedProviderType) do
                throwError "provider proof does not have its closed type"
              if (structuralText closedProviderProof).utf8ByteSize > 1048576
                  || (structuralText closedProviderType).utf8ByteSize > 1048576 then
                throwError "serialized provider exceeds 1 MiB"
              let (closedProviderTypeText, closedProviderProofText) ←
                checkedRoundtrip closedProviderType closedProviderProof
              providers := providers.push <| Json.mkObj [
                ("index", toJson i), ("status", toJson status),
                ("localId", localId), ("value", providerValue),
                ("closedType", toJson closedProviderTypeText),
                ("closedProof", toJson closedProviderProofText)]
          let appType ← inferType matched
          if appType.hasExprMVar || appType.hasLevelMVar then
            throwError "application type contains unresolved metavariables"
          let closedType ← mkForallFVars occurrenceLocals appType
            (usedOnly := false) (usedLetOnly := false) (generalizeNondepLet := false)
          let closedProof ← mkLambdaFVars occurrenceLocals matched
            (usedOnly := false) (usedLetOnly := false) (generalizeNondepLet := false)
          if closedProof.hasFVar || closedType.hasFVar || closedProof.hasExprMVar
              || closedType.hasExprMVar || closedProof.hasLevelMVar || closedType.hasLevelMVar then
            throwError "closed application retains free variables or metavariables"
          unless (← isDefEq (← inferType closedProof) closedType) do
            throwError "closed application proof does not have its closed type"
          let (closedTypeText, closedProofText) ← checkedRoundtrip closedType closedProof
          let transport ← identityTransport matched
          let applicationJson ← jsonExpr matched
          let typeJson ← jsonExpr appType
          if (structuralText matched).utf8ByteSize > 1048576
              || (structuralText closedProof).utf8ByteSize > 1048576
              || (structuralText closedType).utf8ByteSize > 1048576 then
            throwError "serialized expression exceeds 1 MiB"
          pure <| Json.mkObj [
            ("occurrence", toJson occurrence), ("transport", transport), ("application", applicationJson),
            ("scopePath", toJson selected.scopePath),
            ("nestedLocalIds", toJson selected.nestedLocalIds),
            ("applicationType", typeJson), ("arguments", Json.arr args),
            ("localContext", Json.arr occurrenceLocalRows),
            ("providerObservations", Json.arr providers),
            ("closedApplicationTypeText", toJson closedTypeText),
            ("closedApplicationProofText", toJson closedProofText),
            ("closedApplicationTypeStructural", toJson (structuralText closedType)),
            ("closedApplicationProofStructural", toJson (structuralText closedProof))]
        rows := rows.push row
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
