import Lean

open Lean Meta

namespace Ladon.Feasibility

structure Premises where
  proposition : Expr
  parameters : Nat
  hypotheses : Nat

abbrev Check (α : Type) := ExceptT String MetaM α

-- Follow transparent aliases at the head, preserving the boundary at negation.
private partial def premiseHead (type : Expr) (fuel : Nat := 64) : Check Expr := do
  if let some unfolded ← delta? type (· != ``Not) then
    if fuel == 0 then throwThe String "premise-unfold-limit"
    premiseHead unfolded (fuel - 1)
  else
    match type with
    | .letE _ _ value body _ =>
      if fuel == 0 then throwThe String "premise-unfold-limit"
      premiseHead (body.instantiate1 value) (fuel - 1)
    | .mdata _ body => premiseHead body fuel
    | _ => return type

private partial def withBinders (type : Expr) (remaining : Nat) (xs : Array Expr)
    (finish : Array Expr → Expr → Check Premises) : Check Premises := do
  match ← premiseHead type with
  | .forallE name domain body info =>
    if remaining == 0 then throwThe String "binder-limit"
    ExceptT.mk <| withLocalDecl name info domain fun x =>
      (withBinders (body.instantiate1 x) (remaining - 1) (xs.push x) finish).run
  | conclusion => finish xs conclusion

def closePremises (type : Expr) (maxBinders : Nat) : Check Premises :=
  withBinders type maxBinders #[] fun xs conclusion => do
    unless ← isProp conclusion do throwThe String "unsupported-telescope"
    let domains ← (xs.mapM inferType : MetaM _)
    let mut hypotheses : Array Expr := #[]
    let mut parameters : Array (Expr × Expr × Level) := #[]
    for i in [:xs.size] do
      let x := xs[i]!
      let domain := domains[i]!
      -- A proof used in another binder type must be bound as a witness.
      if (← isProp domain) && !domains.any (·.containsFVar x.fvarId!) then
        hypotheses := hypotheses.push domain
      else
        let .sort level ← whnf (← inferType domain) |
          throwThe String "unsupported-parameter"
        parameters := parameters.push (x, domain, level)
    let mut tail : Option Expr := none
    for hypothesis in hypotheses.reverse do
      tail := some <| match tail with
        | none => hypothesis
        | some rhs => mkApp2 (mkConst ``And) hypothesis rhs
    let mut proposition := tail.getD (mkConst ``True)
    for (x, domain, level) in parameters.reverse do
      let predicate ← mkLambdaFVars #[x] proposition
      proposition := mkApp2 (mkConst ``Exists [level]) domain predicate
    if proposition.hasFVar || proposition.hasMVar || proposition.hasLooseBVars then
      throwThe String "open-premises"
    return ⟨proposition, parameters.size, hypotheses.size⟩

private def split (goal : MVarId) (h : Expr) : MetaM (MVarId × Expr × Expr) := do
  let #[branch] ← goal.cases h.fvarId! | throwError "expected a single constructor"
  let #[left, right] := branch.fields | throwError "expected two fields"
  return (branch.mvarId, left, right)

private def openPremises (goal : MVarId) (premises : Premises) :
    MetaM (MVarId × Array Expr × Array Expr) := do
  let (h, body) ← goal.intro1P
  let mut goal := body
  let mut tail := mkFVar h
  let mut witnesses := #[]
  for _ in [:premises.parameters] do
    let (next, witness, rest) ← split goal tail
    witnesses := witnesses.push witness
    goal := next
    tail := rest
  let mut hypotheses := #[]
  if premises.hypotheses > 0 then
    for _ in [:premises.hypotheses - 1] do
      let (next, left, right) ← split goal tail
      hypotheses := hypotheses.push left
      goal := next
      tail := right
    hypotheses := hypotheses.push tail
  return (goal, witnesses, hypotheses)

structure SearchLimits where
  projectionDepth : Nat
  derivedFacts : Nat
  inferences : Nat

private structure Fact where
  proof : Expr
  type : Expr
  antecedent? : Option Expr
  deriving Inhabited

private def mkFact (proof : Expr) : MetaM Fact := do
  let type ← whnf (← inferType proof)
  if let .forallE _ antecedent consequent _ := type then
    if !consequent.hasLooseBVars && (← isProp antecedent) then
      return ⟨proof, type, some antecedent⟩
  return ⟨proof, type, none⟩

private structure Search where
  facts : Array Fact
  derived : Nat := 0
  stop? : Option String := none
  refutation? : Option (String × Expr) := none

-- Each queue entry is a value and its projection depth. Keeping the actual
-- value gives every field of a structure the same parent witness.
private def projectFields (roots : Array Expr) (initial : Search)
    (limits : SearchLimits) : MetaM Search := do
  let mut pending := roots.map (·, 0)
  let mut seen : ExprSet := roots.foldl (fun seen value => seen.insert value) {}
  let mut search := initial
  let mut index := 0
  while index < pending.size do
    let (value, depth) := pending[index]!
    index := index + 1
    let type ← whnf (← inferType value)
    let .const name _ := type.getAppFn | continue
    let some info := getStructureInfo? (← getEnv) name | continue
    if info.fieldInfo.isEmpty then continue
    if depth >= limits.projectionDepth then
      search := { search with stop? := some "projection-depth-limit" }
      continue
    for field in info.fieldInfo do
      let projection ← mkProjection value field.fieldName
      if seen.contains projection then continue
      if search.derived >= limits.derivedFacts then
        return { search with stop? := some "derived-fact-limit" }
      seen := seen.insert projection
      search := { search with derived := search.derived + 1 }
      if ← isProof projection then
        let fact ← mkFact projection
        if fact.type.isConstOf ``False then
          return { search with refutation? := some ("projection", projection) }
        search := { search with facts := search.facts.push fact }
      pending := pending.push (projection, depth + 1)
  return search

-- Consider each pair in both directions once, including pairs involving
-- newly derived facts.
private def derivePropositions (initial : Search) (limits : SearchLimits) : MetaM Search := do
  let mut search := initial
  let mut inferences := 0
  let mut index := 0
  while index < search.facts.size do
    let current := search.facts[index]!
    for earlier in [:index] do
      let previous := search.facts[earlier]!
      for (fn, arg) in #[(current, previous), (previous, current)] do
        let some antecedent := fn.antecedent? | continue
        if inferences >= limits.inferences then
          return { search with stop? := some "inference-limit" }
        inferences := inferences + 1
        unless ← isDefEq antecedent arg.type do continue
        let fact ← mkFact (mkApp fn.proof arg.proof)
        if ← search.facts.anyM (fun known => isDefEq known.type fact.type) then continue
        if search.derived >= limits.derivedFacts then
          return { search with stop? := some "derived-fact-limit" }
        if fact.type.isConstOf ``False then
          return { search with refutation? := some ("propositional", fact.proof) }
        search := { search with facts := search.facts.push fact, derived := search.derived + 1 }
        -- An implication can produce a structure whose fields supply new facts.
        search ← projectFields #[fact.proof] search limits
        if search.refutation?.isSome then return search
    index := index + 1
  return search

-- Give grind conditional field proofs. Abstract the temporary antecedent
-- so each field stays conditional on having a proof of that antecedent.
private def projectImplicationFields (initial : Search) (limits : SearchLimits) :
    MetaM Search := do
  let mut search := initial
  for fact in initial.facts do
    let some antecedent := fact.antecedent? | continue
    let (rules, count, stop?) ← withLocalDeclD `premise antecedent fun premise => do
      let applied := mkApp fact.proof premise
      let projected ← projectFields #[applied] { facts := #[], derived := search.derived } limits
      let proofs : Array Expr := match projected.refutation? with
        | some (_, proof) => #[proof]
        | none => projected.facts.map Fact.proof
      let rules ← proofs.mapM fun proof => mkLambdaFVars #[premise] proof
      return (rules, projected.derived, projected.stop?)
    search := { search with facts := search.facts ++ (← rules.mapM mkFact), derived := count }
    if let some reason := stop? then
      search := { search with stop? := some reason }
      if reason == "derived-fact-limit" then break
  return search

def certificateName : Name := `LadonFeasibility.certificate

def freshCertificateName (env : Environment) : Name := Id.run do
  let mut name := certificateName
  let mut index := 0
  while env.contains name do
    index := index + 1
    name := Name.num certificateName index
  return name

private def tryGrind (goal : MVarId) (derived : Array Fact) : MetaM Bool := do
  let saved ← saveState
  try
    let hypotheses ← derived.mapM fun fact => do
      let userName ← mkFreshUserName `premise
      return ({ userName, type := fact.type, value := fact.proof } : Hypothesis)
    let (_, goal) ← goal.assertHypotheses hypotheses
    let config : Grind.Config := { splits := 4, ematch := 4 }
    let params ← Grind.mkOnlyParams config
    Grind.withProtectedMCtx config goal fun protectedGoal => do
      if (← Grind.main protectedGoal params).hasFailed then
        throwError "grind found no refutation"
    return true
  catch e =>
    restoreState saved
    if e.isRuntime then throw e
    if let .internal .. := e then throw e
    return false

private def elaborateLemma (stx : Syntax) : MetaM Expr :=
  Elab.Term.TermElabM.run' (ctx := { errToSorry := false, mayPostpone := false }) do
    let proof ← Elab.Term.elabTerm stx none
    Elab.Term.synthesizeSyntheticMVarsNoPostponing
    instantiateMVars proof

private def noNatDescent : MetaM Expr := do
  elaborateLemma (← `(term|
    fun (rank : Nat → Nat) (step : ∀ i : Nat, rank (i + 1) < rank i) => show False from by
      have bound (i : Nat) : rank i + i ≤ rank 0 := by
        induction i with
        | zero => exact Nat.le_refl _
        | succ i ih =>
          rw [Nat.add_succ, ← Nat.succ_add]
          exact Nat.le_trans (Nat.add_le_add_right (Nat.succ_le_of_lt (step i)) i) ih
      exact Nat.not_succ_le_self (rank 0)
        (Nat.le_trans (Nat.le_add_left _ _) (bound (rank 0 + 1)))))

private def refuteNatDescent (facts : Array Fact) : MetaM (Option Expr) := do
  let mut lemma : Option Expr := none
  for fact in facts do
    let .forallE _ domain body _ := fact.type | continue
    unless body.getAppFn.isConstOf ``LT.lt || body.getAppFn.isConstOf ``Nat.lt do continue
    let .app rank (.bvar 0) := body.getAppArgs.back! | continue
    if rank.hasLooseBVars then continue
    unless ← isDefEq domain (mkConst ``Nat) do continue
    unless ← isDefEq (← inferType rank) (← mkArrow (mkConst ``Nat) (mkConst ``Nat)) do continue
    if lemma.isNone then lemma := some (← noNatDescent)
    let applied := mkApp lemma.get! rank
    let .forallE _ step _ _ ← inferType applied | continue
    if ← isDefEq step fact.type then return some (mkApp applied fact.proof)
  return none

private def intSelfProductFactor (e : Expr) : Option Expr := do
  let .app (.app fn x) y := e | none
  unless x == y && !x.hasLooseBVars do none
  unless fn.getAppFn.isConstOf ``HMul.hMul || fn.isConstOf ``Int.mul do none
  return x

private def addSquareFacts (initial : Search) (limits : SearchLimits) : MetaM Search := do
  let mut search := initial
  let mut seen : ExprSet := {}
  let mut lemma : Option Expr := none
  for fact in initial.facts do
    let collect : StateRefT (Array Expr) MetaM Unit := fact.type.forEach fun e => do
      if let some x := intSelfProductFactor e then modify (·.push x)
    let (_, factors) ← collect.run #[]
    for x in factors do
      if seen.contains x then continue
      seen := seen.insert x
      unless ← isDefEq (← inferType x) (mkConst ``Int) do continue
      if search.derived >= limits.derivedFacts then
        return { search with stop? := some "derived-fact-limit" }
      if lemma.isNone then
        lemma := some (← elaborateLemma (← `(term| fun n : Int =>
          show 0 ≤ n * n from by
            have eq : n ^ 2 = n * n :=
              (Int.pow_succ n 1).trans (congrArg (fun x : Int => x * n) (Int.pow_one n))
            exact eq ▸ Int.sq_nonneg n)))
      let proof := mkApp lemma.get! x
      search := { search with facts := search.facts.push (← mkFact proof),
                              derived := search.derived + 1 }
  return search

private def tryEmptyInductive (goal : MVarId) (witnesses : Array Expr) : MetaM Bool := do
  for witness in witnesses do
    let type ← whnf (← inferType witness)
    let .const name _ := type.getAppFn | continue
    let .inductInfo info ← getConstInfo name | continue
    unless info.isRec && info.numIndices == 0 && info.all.length == 1 do continue
    let recursor := mkRecName name
    let .recInfo recursorInfo ← getConstInfo recursor | continue
    if recursorInfo.rules.any (·.nfields == 0) then continue
    let saved ← saveState
    try
      let branches ← goal.induction witness.fvarId! recursor
      if ← branches.allM (·.mvarId.assumptionCore) then return true
    catch e =>
      if e.isRuntime then throw e
      if let .internal .. := e then throw e
    restoreState saved
  return false

private def solve (goal : MVarId) (witnesses hypotheses : Array Expr)
    (limits : SearchLimits) : Check (Option String) := goal.withContext do
  let proofWitnesses ← (witnesses.filterM isProof : MetaM _)
  let hypotheses := hypotheses ++ proofWitnesses
  let facts ← (hypotheses.mapM mkFact : MetaM _)
  if let some fact := facts.find? (·.type.isConstOf ``False) then
    goal.assign fact.proof
    return some "false-hypothesis"
  let projected ← projectFields (hypotheses ++ witnesses) { facts } limits
  let search ← if projected.refutation?.isSome then pure projected
    else derivePropositions projected limits
  if let some (route, proof) := search.refutation? then
    goal.assign proof
    return some route
  if let some proof ← refuteNatDescent search.facts then
    goal.assign proof
    return some "nat-descent"
  let search ← addSquareFacts search limits
  unless search.facts.isEmpty do
    let saved ← saveState
    try
      Elab.Tactic.Omega.omega (search.facts.toList.map (·.proof)) goal
      return some "omega"
    catch e =>
      restoreState saved
      if e.isRuntime then throw e
      if let .internal .. := e then throw e
  if let some reason := search.stop? then throwThe String reason
  if hypotheses.isEmpty && witnesses.isEmpty then return none
  if ← tryEmptyInductive goal witnesses then return some "empty-inductive"
  let fallback ← projectImplicationFields search limits
  if ← tryGrind goal (fallback.facts.extract hypotheses.size fallback.facts.size) then
    return some "grind"
  if let some reason := fallback.stop? then throwThe String reason
  return none

private def refute (premises : Premises) (limits : SearchLimits) :
    Check (Option (String × TheoremVal)) := do
  let target := mkApp (mkConst ``Not) premises.proposition
  let root ← mkFreshExprSyntheticOpaqueMVar target
  let (goal, witnesses, hypotheses) ← openPremises root.mvarId! premises
  let some route ← solve goal witnesses hypotheses limits | return none
  let value ← instantiateMVars root
  let levels := collectLevelParams (collectLevelParams {} target) value
  return some (route, {
    name := freshCertificateName (← getEnv)
    levelParams := levels.params.toList
    type := target
    value := value })

private def dependencies (info : ConstantInfo) : NameSet :=
  match info with
  | .recInfo recInfo =>
    recInfo.rules.foldl (init := info.getUsedConstantsAsSet)
      fun names rule => names ++ rule.rhs.getUsedConstantsAsSet
  | _ => info.getUsedConstantsAsSet

-- Only reachable additions from the tactic environment travel with the proof.
-- Save them dependency-first so the replay kernel can check them one at a time.
private partial def collectAuxiliaries (base current : Environment) (name : Name)
    (visited : NameSet) (out : Array ConstantInfo) : Except String (NameSet × Array ConstantInfo) := do
  if (base.checked.get.find? name).isSome || visited.contains name then return (visited, out)
  if visited.size >= 1024 then throwThe String "auxiliary-limit"
  let some info := current.checked.get.find? name | throwThe String "missing-auxiliary"
  let mut state := (visited.insert name, out)
  for dep in dependencies info do
    state ← collectAuxiliaries base current dep state.1 state.2
  return (state.1, state.2.push info)

def saveCertificate (path : System.FilePath) (entries : Array ConstantInfo) : IO Unit :=
  saveModuleData path (entries.back?.map (·.name) |>.getD certificateName)
    { (default : ModuleData) with constNames := entries.map (·.name), constants := entries }

private def prove (premises : Premises) (path : System.FilePath) (limits : SearchLimits) :
    Check (Option String) := do
  let initial ← getEnv
  let some (route, proof) ← refute premises limits | return none
  let env ← getEnv
  let mut state : NameSet × Array ConstantInfo := ({}, #[])
  for name in dependencies (.thmInfo proof) do
    match collectAuxiliaries initial env name state.1 state.2 with
    | .ok next => state := next
    | .error reason => throwThe String reason
  liftM <| saveCertificate path (state.2.push (.thmInfo proof))
  return some route

private def audit (env : Environment) (target certificate : Name) (limit : Nat) :
    Check (Array Name) := do
  if limit == 0 then throwThe String "dependency-limit"
  let mut pending := #[certificate]
  let mut seen : NameSet := ({} : NameSet).insert certificate
  let mut axioms := #[]
  let mut index := 0
  while index < pending.size do
    checkSystem "feasibility dependency audit"
    let name := pending[index]!
    index := index + 1
    if name == target then throwThe String "reviewed-theorem-dependency"
    let some info := env.checked.get.find? name | throwThe String "missing-dependency"
    if info.isUnsafe then throwThe String "unsafe-dependency"
    if let .axiomInfo _ := info then axioms := axioms.push name
    for dep in dependencies info do
      if !seen.contains dep then
        if pending.size >= limit then throwThe String "dependency-limit"
        seen := seen.insert dep
        pending := pending.push dep
  return axioms.qsort Name.quickLt

private def kernelAdd (decl : Declaration) : Check Unit := ExceptT.mk do
  tryCatchRuntimeEx
    (do
      withOptions (fun opts => opts.setBool `Elab.async false |>.setBool `debug.skipKernelTC false) do
        Lean.addDecl decl
      return .ok ())
    fun e => return .error (if e.isRuntime then "kernel-resource-limit" else "kernel-rejected-certificate")

def replay (premises : Premises) (entries : Array ConstantInfo) (target : Name)
    (limit : Nat) : Check (Array Name) := do
  let some (.thmInfo proof) := entries.back? | throwThe String "invalid-certificate"
  if (← getEnv).contains proof.name then throwThe String "certificate-name-conflict"
  if entries.size > 1025 then throwThe String "auxiliary-limit"
  for entry in entries.pop do
    if entry.name == proof.name then throwThe String "invalid-certificate"
    let decl ← match entry with
      | .thmInfo info => pure (.thmDecl info)
      | .defnInfo info => pure (.defnDecl info)
      | .opaqueInfo info => pure (.opaqueDecl info)
      | _ => throwThe String "unsupported-auxiliary"
    kernelAdd decl
  let expected := mkApp (mkConst ``Not) premises.proposition
  unless ← isDefEq proof.type expected do throwThe String "certificate-subject-mismatch"
  kernelAdd (.thmDecl { proof with type := expected })
  audit (← getEnv) target proof.name limit

private def subject (env : Environment) (module name : Name) : Option TheoremVal := do
  let idx ← env.getModuleIdxFor? name
  unless env.header.moduleNames[idx.toNat]? == some module do none
  let .thmInfo decl ← env.checked.get.find? name | none
  return decl

private def emit (fields : List (String × Json)) : IO Unit :=
  IO.println ("LADON_FEASIBILITY " ++ (Json.mkObj fields).compress)

private def closure (env : Environment) : IO Json := do
  let paths ← env.header.moduleNames.mapM fun name => do
    let path ← findOLean name
    return Json.mkObj [("module", toJson name.toString), ("path", toJson path.toString)]
  return toJson paths

def run (mode : String) (module : Name) (requestedName : String) (certificate : System.FilePath)
    (maxBinders maxDependencies : Nat) (limits : SearchLimits) : IO Unit := do
  let options := ({} : Options).set `maxHeartbeats 2000 |>.set `maxRecDepth 1024
  let modules : Array Import :=
    #[{module := `Lean.Elab.Tactic.Omega}, {module := `Lean.Meta.Tactic.Grind.Main}, {module}]
  let env ← importModules modules options
    (loadExts := mode == "prove") (level := .private)
  let common := [("module", toJson module.toString), ("declaration", toJson requestedName)]
  let invalid := emit (("status", toJson "invalid-selection") :: common)
  let .ok (.ident _ _ name _) := Parser.runParserCategory env `term requestedName | invalid
  let some decl := subject env module name | invalid
  let common := ("compiledModules", ← closure env) :: common
  if mode == "inspect" then
    emit (("status", toJson "selected") :: common)
  else
    let action : MetaM (List (String × Json)) := do
      match ← (closePremises decl.type maxBinders).run with
      | .error reason => return [("status", toJson "unresolved"), ("reason", toJson reason)]
      | .ok premises =>
        let display := (← ppExpr premises.proposition).pretty
        let details := [("premises", toJson display)]
        let result ← if mode == "prove" then do
          match ← (prove premises certificate limits).run with
          | .error reason => pure [("status", toJson "unresolved"), ("reason", toJson reason)]
          | .ok none => pure [("status", toJson "unresolved"), ("reason", toJson "no-refutation")]
          | .ok (some route) => pure [("status", toJson "produced"), ("route", toJson route)]
        else do
          let (data, _) ← liftM <| readModuleData certificate
          match ← (replay premises data.constants name maxDependencies).run with
          | .error reason => pure [("status", toJson "rejected"), ("reason", toJson reason)]
          | .ok axioms => pure [("status", toJson "replayed"),
              ("axioms", toJson (axioms.map Name.toString))]
        return details ++ result
    let (fields, _, _) ← action.toIO
      { fileName := "<ladon feasibility>", fileMap := default, options } { env }
    emit (fields ++ common)

end Ladon.Feasibility

unsafe def main (args : List String) : IO UInt32 := do
  let [mode, module, name, certificate, binders, deps, depth, facts, inferences] := args |
    throw (IO.userError "invalid feasibility worker arguments")
  unless ["inspect", "prove", "replay"].contains mode do
    throw (IO.userError "invalid feasibility worker stage")
  Lean.initSearchPath (← Lean.findSysroot)
  if mode == "prove" then Lean.enableInitializersExecution
  Ladon.Feasibility.run mode module.toName name certificate binders.toNat! deps.toNat!
    ⟨depth.toNat!, facts.toNat!, inferences.toNat!⟩
  return 0
