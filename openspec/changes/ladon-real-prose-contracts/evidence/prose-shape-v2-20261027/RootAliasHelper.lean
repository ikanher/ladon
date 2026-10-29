import Lean
import Lean.Elab.Frontend

open Lean Lean.Meta

private def helperVersion := "ladon-prose-alias-helper-v1"
private def schema := "ladon-prose-alias-worker-v1"
private def requestSchema := "ladon-prose-alias-request-v1"
private def maxNodes : Nat := 100000
private def maxDepth : Nat := 128
private def maxPath : Nat := 256
private def maxPrefix : Nat := 64
private def maxUnfold : Nat := 32
private def maxLiteral : Nat := 9007199254740991
private def maxOutputBytes : Nat := 8 * 1024 * 1024

private def binderInfoName : BinderInfo → String
  | .default => "explicit"
  | .implicit => "implicit"
  | .strictImplicit => "strict-implicit"
  | .instImplicit => "instance-implicit"

private abbrev RenderM := ExceptT String (StateM Nat)
private def countNode (depth : Nat) : RenderM Unit := do
  if depth > maxDepth then throw "expression depth exceeds 128"
  let seen ← get
  if seen >= maxNodes then throw "expression node count exceeds 100000"
  set (seen + 1)

private partial def exprJson (depth : Nat) (e : Expr) : RenderM Json := do
  countNode depth
  match e with
  | .bvar i => pure <| Json.mkObj [("bvar", toJson i)]
  | .fvar id => pure <| Json.mkObj [("fvar", toJson id.name)]
  | .mvar id => pure <| Json.mkObj [("mvar", toJson id.name)]
  | .sort u => pure <| Json.mkObj [("sort", toJson (toString u))]
  | .const n us => pure <| Json.mkObj [("const", toJson n), ("levels", toJson (us.map toString))]
  | .app f a => return Json.mkObj [("app", Json.arr #[← exprJson (depth+1) f, ← exprJson (depth+1) a])]
  | .lam n t b bi => return Json.mkObj [("lam", Json.mkObj [("name",toJson n),("type",←exprJson (depth+1) t),("body",←exprJson (depth+1) b),("binderInfo",toJson (binderInfoName bi))])]
  | .forallE n t b bi => return Json.mkObj [("forallE", Json.mkObj [("name",toJson n),("type",←exprJson (depth+1) t),("body",←exprJson (depth+1) b),("binderInfo",toJson (binderInfoName bi))])]
  | .letE n t v b nd => return Json.mkObj [("letE", Json.mkObj [("name",toJson n),("type",←exprJson (depth+1) t),("value",←exprJson (depth+1) v),("body",←exprJson (depth+1) b),("nondep",toJson nd)])]
  | .lit (.natVal n) => pure <| Json.mkObj [("nat", toJson n)]
  | .lit (.strVal s) => pure <| Json.mkObj [("string", toJson s)]
  | .mdata _ b => exprJson (depth+1) b
  | .proj n i b => return Json.mkObj [("proj", Json.mkObj [("typeName",toJson n),("index",toJson i),("structure",←exprJson (depth+1) b)])]

private def common (module file target status : String) : List (String × Json) := [
  ("schema",toJson schema),("helperVersion",toJson helperVersion),("module",toJson module),
  ("file",toJson file),("target",toJson target),("leanVersion",toJson Lean.versionString),("status",toJson status)]

private def emitJson (dest : String) (j : Json) : IO Unit := do
  let s := j.compress
  if s.utf8ByteSize > maxOutputBytes then throw <| IO.userError "alias helper output exceeds 8 MiB"
  IO.FS.writeFile dest s

private def unresolved (kind path code message : String) : Json := Json.mkObj [
  ("kind",toJson kind),("originPath",toJson path),("state",toJson "unresolved"),
  ("code",toJson code),("message",toJson message)]

private def pathParts (s : String) : Array String :=
  let parts := (s.splitOn "/").filter (· != "") |>.toArray
  if parts.size > 0 && parts[0]! == "propositionExpr" then parts.extract 1 parts.size else parts

private def jsonIndex (s : String) : Option Nat := s.toNat?

/-- Resolve a JSON-expression path in the live source scope. Binder bodies are opened
    with their exact source binder; their fvars are retained in the ordered prefix. -/
private partial def atPath {α : Type} (e : Expr) (parts : Array String) (i : Nat)
    (scope : Array Expr) (cont : Expr → Array Expr → MetaM α) : MetaM α := do
  if i == parts.size then return ← cont e scope
  if i >= maxPath then throwError "path token bound exceeded"
  match e with
  | .mdata _ body => atPath body parts i scope cont
  | .app f a =>
      if parts[i]! != "app" || i+1 >= parts.size then throwError "invalid app path"
      if parts[i+1]! == "0" then atPath f parts (i+2) scope cont
      else if parts[i+1]! == "1" then atPath a parts (i+2) scope cont
      else throwError "invalid app selector"
  | .forallE n t b bi | .lam n t b bi =>
      let tag := if e.isForall then "forallE" else "lam"
      if parts[i]! != tag || i+1 >= parts.size then throwError "invalid binder path"
      if parts[i+1]! == "type" then atPath t parts (i+2) scope cont
      else if parts[i+1]! == "body" then
        if scope.size >= maxPrefix then throwError "source prefix exceeds 64"
        withLocalDecl n bi t fun x => atPath (b.instantiate1 x) parts (i+2) (scope.push x) cont
      else throwError "invalid binder selector"
  | .letE n t v b _ =>
      if parts[i]! != "letE" || i+1 >= parts.size then throwError "invalid let path"
      if parts[i+1]! == "type" then atPath t parts (i+2) scope cont
      else if parts[i+1]! == "value" then atPath v parts (i+2) scope cont
      else if parts[i+1]! == "body" then
        withLetDecl n t v fun x => atPath (b.instantiate1 x) parts (i+2) (scope.push x) cont
      else throwError "invalid let selector"
  | .proj _ _ b =>
      if parts[i]! == "proj" && i+1 < parts.size && parts[i+1]! == "structure" then
        atPath b parts (i+2) scope cont
      else throwError "invalid projection path"
  | _ => throwError "path continues below atomic expression"

private def render (e : Expr) : MetaM Json := do
  match ((exprJson 0 e).run 0).1 with
  | .error reason => throwError "{reason}"
  | .ok result => return result

private def headStep (e : Expr) : MetaM (Option Expr) := do
  let e := e.consumeMData
  let beta := e.headBeta
  if beta != e then return some beta
  match e with
  | .letE _ _ value body _ => return some (body.instantiate1 value)
  | _ => unfoldDefinition? e (ignoreTransparency := true)

private partial def collectFVars (e : Expr) : Array FVarId :=
  match e with
  | .fvar id => #[id]
  | .app f a => collectFVars f ++ collectFVars a
  | .lam _ t b _ | .forallE _ t b _ => collectFVars t ++ collectFVars b
  | .letE _ t v b _ => collectFVars t ++ collectFVars v ++ collectFVars b
  | .mdata _ b | .proj _ _ b => collectFVars b
  | _ => #[]

private def mkNatLitExpr (n : Nat) : Expr := mkNatLit n

private def headOrderOffset (e : Expr) (order : Expr) : MetaM (Option Nat) := do
  let mut cur := e
  for _ in [:maxUnfold] do
    if cur == order then return some 0
    let fn := cur.getAppFn
    let args := cur.getAppArgs
    if (fn.isConstOf ``HAdd.hAdd || fn.isConstOf ``Nat.add) && args.size >= 2 then
      let rhs := args[args.size-1]!
      let rhs ← whnf rhs
      match rhs with
      | .lit (.natVal n) => return if n <= maxLiteral then some n else none
      | .app (.const ``OfNat.ofNat _) (.lit (.natVal n)) => return if n <= maxLiteral then some n else none
      | _ => return none
    let next? ← headStep cur
    match next? with
    | none => return none
    | some next =>
        if next == cur then return none
        cur := next
  return none

private def targetResult (kind path : String) (roles : Json) (proposition : Expr) (levelParams : List Name) : MetaM Json := do
  atPath proposition (pathParts path) 0 #[] fun selected scope => do
    let orderIdx := (roles.getObjValAs? Nat "order").toOption
    let boundIdx := (roles.getObjValAs? Nat "bound").toOption
    let constantIdx := (roles.getObjValAs? Nat "constant").toOption
    let _ := constantIdx
    if selected.hasExprMVar || selected.hasLevelMVar then
      return unresolved kind path "metavariable" "selected source expression contains a metavariable"
    let allowed := scope.foldl (fun s x => s.insert x.fvarId!) ({} : FVarIdSet)
    if (collectFVars selected).any (!allowed.contains ·) then
      return unresolved kind path "foreign-fvar" "selected expression contains a free variable outside its observed source prefix"
    let canonical? ← match kind with
      | "input-order" => do
        match orderIdx with
        | none => pure none
        | some index =>
          if index >= scope.size then pure none else
          let base := scope[index]!
          let off? ← headOrderOffset selected base
          match off? with
          | none => pure none
          | some n => pure <| some (mkApp2 (mkConst ``Nat.add) base (mkNatLitExpr n), toJson n)
      | "output-bound" => do
        match constantIdx with
        | none => pure none
        | some index =>
          if index >= scope.size then pure none else
          let k := scope[index]!
          match boundIdx with
          | none => pure none
          | some cIndex =>
            if cIndex >= scope.size then pure none else
            let c := scope[cIndex]!
            -- Head-only unfolding is bounded and only discovers a candidate. The
            -- synchronous theorem check below decides whether the source alias is equal.
            let mut candidate := selected
            let mut found : Option Expr := none
            for _ in [:maxUnfold] do
              let fn := candidate.getAppFn
              let args := candidate.getAppArgs
              if fn.isConstOf ``HMul.hMul && args.size == 6 then
                found := some candidate
                break
              let next? ← headStep candidate
              match next? with
              | none => break
              | some next =>
                if next == candidate then break
                candidate := next
            match found with
            | none => pure none
            | some product =>
              let args := product.getAppArgs
              let real := mkConst ``Real
              if args[0]! != real || args[1]! != real || args[2]! != real ||
                  (← inferType selected) != real then
                pure none
              else
                let canonical := mkAppN product.getAppFn #[args[0]!,args[1]!,args[2]!,args[3]!,k,c]
                pure <| some (canonical, Json.null)
      | _ => pure none
    match canonical? with
    | none => return unresolved kind path "unsupported" "no bounded, source-scoped alias interpretation was established"
    | some (canonical, loss) => do
        let foreign := (collectFVars canonical ++ collectFVars selected).any (!allowed.contains ·)
        if foreign then return unresolved kind path "foreign-fvar" "canonical expression contains a free variable outside the exact source prefix"
        let eq ← mkEq selected canonical
        let goal ← mkForallFVars scope eq (usedOnly := false)
        let proof ← mkLambdaFVars scope (← mkEqRefl selected) (usedOnly := false)
        if goal.hasFVar || goal.hasExprMVar || goal.hasLevelMVar || proof.hasFVar || proof.hasExprMVar || proof.hasLevelMVar then
          return unresolved kind path "closure" "certificate did not close over the exact source prefix"
        let checkName := Name.mkSimple s!"_ladon_prose_alias_check_{kind.replace "-" "_"}"
        let decl := Declaration.thmDecl { name := checkName, levelParams := levelParams, type := goal, value := proof }
        let options := debug.skipKernelTC.set ({} : Options) false
        match (← getEnv).toKernelEnv.addDecl options decl with
        | .error _ => return unresolved kind path "kernel-rejected" "synchronous source-context theorem check rejected the alias"
        | .ok _ =>
          let originalClosed ← mkLambdaFVars scope selected (usedOnly := false)
          let canonicalClosed ← mkLambdaFVars scope canonical (usedOnly := false)
          return Json.mkObj [
            ("kind",toJson kind),("originPath",toJson path),("state",toJson "checked"),
            ("lossLiteral",loss),("original",← render originalClosed),
            ("canonical",← render canonicalClosed),("goal",← render goal),
            ("proof",← render proof),("kernelCheck",toJson "synchronous"),
            ("scopeCount",toJson scope.size),("levelParams",toJson (levelParams.map toString))]

private def runMeta {α} (env : Environment) (file : String) (fm : FileMap) (act : MetaM α) : IO α := do
  let (v,_,_) ← act.toIO { fileName := file, fileMap := fm, options := {} } { env }
  pure v

private def emitUnavailable (dest module file target reason : String) : IO Unit :=
  emitJson dest <| Json.mkObj (common module file target "unavailable" ++ [
    ("propositionExpr",Json.null),("results",Json.arr #[]),("importedModules",Json.arr #[]),
    ("compiledModulePaths",Json.arr #[]),("reason",toJson reason)])

private def runHelper (module file snapshot target requestFile destination : String) : IO UInt32 := do
  let requestText ← IO.FS.readFile requestFile
  let request ← match Json.parse requestText with
    | .ok j => pure j
    | .error _ => emitUnavailable destination module file target "malformed alias request JSON"; return 0
  let requestKind := (request.getObjValAs? String "schema").toOption.getD ""
  let targets := (request.getObjValAs? (Array Json) "targets").toOption.getD #[]
  if requestKind != requestSchema || targets.size > 2 then
    emitUnavailable destination module file target "invalid request schema or more than two targets"
    return 0
  let contents ← IO.FS.readFile snapshot
  unsafe Lean.enableInitializersExecution
  let options := Elab.async.set ({} : Options) false
  let env? ← Elab.runFrontend contents options file module.toName
  match env? with
  | none => emitUnavailable destination module file target "Lean frontend produced no source environment"; return 0
  | some env =>
    if env.header.mainModule != module.toName then
      emitUnavailable destination module file target "frontend environment main module differs from request"
      return 0
    let targetName := target.toName
    let ranges? ← runMeta env file contents.toFileMap (findDeclarationRanges? targetName)
    match env.find? targetName, ranges? with
    | some (.defnInfo info), some ranges =>
      if (env.getModuleIdxFor? targetName).isSome || ranges.range.pos.line == 0 ||
          ranges.range.endPos.line > (contents.splitOn "\n").length then
        emitUnavailable destination module file target "target is imported or lacks its own source range"
        return 0
      let valid ← runMeta env file contents.toFileMap do
        let declared ← isDefEq info.type (mkSort .zero)
        let bodyType ← inferType info.value
        let bodyIsProp ← isDefEq bodyType (mkSort .zero)
        pure (declared && bodyIsProp)
      if !valid then
        emitUnavailable destination module file target "target must be a local proposition definition"
        return 0
      let rendered := (exprJson 0 info.value).run 0
      match rendered.1 with
      | .error reason => emitUnavailable destination module file target reason; return 0
      | .ok propositionJson =>
        let resultRows ← runMeta env file contents.toFileMap do
          targets.mapM fun row => do
            let kind := (row.getObjValAs? String "kind").toOption.getD ""
            let path := (row.getObjValAs? String "originPath").toOption.getD ""
            let roles := (row.getObjVal? "roles").toOption.getD Json.null
            if kind != "input-order" && kind != "output-bound" then
              pure <| unresolved kind path "invalid-kind" "target kind must be input-order or output-bound"
            else if pathParts path |>.size > maxPath then
              pure <| unresolved kind path "path-limit" "origin path exceeds 256 tokens"
            else
              try targetResult kind path roles info.value info.levelParams
              catch _ => pure <| unresolved kind path "recognition-error" "bounded path or certificate construction failed"
        let paths ← env.header.moduleNames.mapM fun name => do
          let p ← Lean.findOLean name
          pure <| Json.mkObj [("module",toJson (toString name)),("path",toJson p.toString)]
        let complete := resultRows.all fun r => (r.getObjValAs? String "state").toOption.getD "" == "checked"
        let status := if complete && resultRows.size == 2 then "checked" else "partial"
        let record := Json.mkObj (common module file target status ++ [
          ("propositionExpr",propositionJson),("results",Json.arr resultRows),
          ("importedModules",toJson (env.header.moduleNames.map toString)),
          ("compiledModulePaths",Json.arr paths),("reason",Json.null)])
        emitJson destination record
        return 0
    | _, _ => emitUnavailable destination module file target "exact local proposition definition or declaration range absent"; return 0

def main (args : List String) : IO UInt32 := do
  match args with
  | [module,file,snapshot,target,requestFile,destination] => runHelper module file snapshot target requestFile destination
  | _ =>
    IO.eprintln "usage: ladon_prose_alias MODULE FILE SNAPSHOT TARGET REQUEST RESULT"
    return 2
